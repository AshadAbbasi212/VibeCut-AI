"""Background job runner for Dynamic Captions Studio pipeline."""
import concurrent.futures
import json
import logging
import os
import shutil
import time
import uuid
from pathlib import Path
from typing import Optional, Literal
from pydantic import BaseModel, Field

from backend.pipeline.probe import probe_video
from backend.pipeline.transcribe import transcribe
from backend.pipeline.chunk import chunk_words, PhrasesDocument
from backend.pipeline.plan_llm import get_planner
from backend.pipeline.render import render, prepare_video_asset
from backend.schemas.timeline import Timeline, TimelineVideo, TimelineWord

logger = logging.getLogger("captions_runner")

JobStatus = Literal["queued", "processing", "completed", "failed"]


class JobInfo(BaseModel):
    id: str
    status: JobStatus = "queued"
    step: str = "queued"
    progress: float = 0.0
    error: Optional[str] = None
    preset: str = "bold_creator"
    llm_provider: str = "none"
    language: str = "en"
    concurrency: Optional[int] = None
    draft: bool = False
    aspect_ratio: str = "9:16"
    subtitle_position: str = "lower"
    caption_size: str = "medium"
    background_style: str = "transparent"
    style_pacing: str = "sentence"
    highlight_color: str = "#38BDF8"
    trim_start: Optional[float] = None
    trim_end: Optional[float] = None
    selected_styles: Optional[str] = None
    subtitle_y: Optional[float] = None
    video_layout: str = "split_podcast"
    progress_bar: bool = True
    progress_bar_position: Literal["bottom", "top"] = "bottom"
    headline_hook: Optional[str] = None
    headline_style: Literal["badge", "glass", "clean", "cyber"] = "badge"
    headline_duration: Optional[float] = None
    auto_emojis: bool = True
    kinetic_zoom: bool = False
    sound_effects: bool = False
    bg_music: Optional[str] = None
    watermark_text: Optional[str] = None
    ai_enhance: bool = False
    api_key: Optional[str] = Field(default=None, exclude=True)
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
    input_file: str = ""
    output_file: Optional[str] = None
    timeline_file: Optional[str] = None


def format_srt_timestamp(sec: float) -> str:
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    ms = int(round((sec - int(sec)) * 1000))
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def format_vtt_timestamp(sec: float) -> str:
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    ms = int(round((sec - int(sec)) * 1000))
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


def export_timeline_to_srt(timeline: Timeline) -> str:
    """Generate standard SubRip (.srt) from timeline events."""
    lines = []
    # Use distinct time events (sorted by start)
    sorted_events = sorted(timeline.events, key=lambda x: (x.start, x.end))
    # Deduplicate overlapping base/feature with identical text
    seen = set()
    counter = 1
    for ev in sorted_events:
        key = (round(ev.start, 1), ev.text.strip())
        if key in seen:
            continue
        seen.add(key)
        start_str = format_srt_timestamp(ev.start)
        end_str = format_srt_timestamp(ev.end)
        lines.append(f"{counter}")
        lines.append(f"{start_str} --> {end_str}")
        lines.append(ev.text)
        lines.append("")
        counter += 1
    return "\n".join(lines)


def export_timeline_to_vtt(timeline: Timeline) -> str:
    """Generate standard WebVTT (.vtt) from timeline events."""
    lines = ["WEBVTT", ""]
    sorted_events = sorted(timeline.events, key=lambda x: (x.start, x.end))
    seen = set()
    counter = 1
    for ev in sorted_events:
        key = (round(ev.start, 1), ev.text.strip())
        if key in seen:
            continue
        seen.add(key)
        start_str = format_vtt_timestamp(ev.start)
        end_str = format_vtt_timestamp(ev.end)
        lines.append(f"{counter}")
        lines.append(f"{start_str} --> {end_str}")
        lines.append(ev.text)
        lines.append("")
        counter += 1
    return "\n".join(lines)


class JobManager:
    """Manages job state, persistence, and execution queue."""

    def __init__(self, base_jobs_dir: str = "jobs", max_workers: int = 4):
        self.jobs_dir = Path(base_jobs_dir).resolve()
        self.jobs_dir.mkdir(parents=True, exist_ok=True)
        self.jobs: dict[str, JobInfo] = {}
        self.executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=max_workers, thread_name_prefix="caption_worker"
        )
        self._load_existing_jobs()

    def _load_existing_jobs(self):
        """Load past jobs from disk if available."""
        if not self.jobs_dir.exists():
            return
        for child in self.jobs_dir.iterdir():
            if child.is_dir():
                job_json = child / "job.json"
                if job_json.exists():
                    try:
                        data = json.loads(job_json.read_text(encoding="utf-8"))
                        info = JobInfo(**data)
                        # Sanitize lingering states from previous crashed runs
                        if info.status in ["queued", "processing"]:
                            info.status = "failed"
                            info.step = "failed"
                            info.error = "Interrupted by server restart"
                        self.jobs[info.id] = info
                    except Exception as e:
                        logger.warning(f"Failed to read existing job from {job_json}: {e}")

    def save_job(self, job: JobInfo):
        """Save job metadata to disk."""
        job.updated_at = time.time()
        self.jobs[job.id] = job
        job_dir = self.jobs_dir / job.id
        job_dir.mkdir(parents=True, exist_ok=True)
        job_file = job_dir / "job.json"
        job_file.write_text(job.model_dump_json(indent=2), encoding="utf-8")

    def get_job(self, job_id: str) -> Optional[JobInfo]:
        """Retrieve job information by ID."""
        return self.jobs.get(job_id)

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a queued or processing job."""
        job = self.jobs.get(job_id)
        if not job:
            return False
        if job.status in ["queued", "processing"]:
            job.status = "failed"
            job.step = "failed"
            job.error = "Cancelled by user"
            self.save_job(job)
            return True
        return False

    def submit_job(
        self,
        input_video_source: Path,
        preset: str = "bold_creator",
        llm_provider: str = "none",
        language: str = "en",
        concurrency: Optional[int] = None,
        draft: bool = False,
        aspect_ratio: str = "9:16",
        subtitle_position: str = "lower",
        caption_size: str = "medium",
        background_style: str = "transparent",
        style_pacing: str = "sentence",
        highlight_color: str = "#38BDF8",
        trim_start: Optional[float] = None,
        trim_end: Optional[float] = None,
        selected_styles: Optional[str] = None,
        subtitle_y: Optional[float] = None,
        video_layout: str = "split_podcast",
        progress_bar: bool = True,
        progress_bar_position: Literal["bottom", "top"] = "bottom",
        headline_hook: Optional[str] = None,
        headline_style: Literal["badge", "glass", "clean", "cyber"] = "badge",
        headline_duration: Optional[float] = None,
        auto_emojis: bool = True,
        kinetic_zoom: bool = False,
        sound_effects: bool = False,
        bg_music: Optional[str] = None,
        watermark_text: Optional[str] = None,
        ai_enhance: bool = False,
        api_key: Optional[str] = None,
    ) -> JobInfo:
        """Create and queue a new pipeline processing job."""
        job_id = f"job_{uuid.uuid4().hex[:10]}"
        job_dir = self.jobs_dir / job_id
        job_dir.mkdir(parents=True, exist_ok=True)

        target_input = job_dir / "input.mp4"
        shutil.copy2(input_video_source, target_input)

        job = JobInfo(
            id=job_id,
            status="queued",
            step="queued",
            progress=0.0,
            preset=preset,
            llm_provider=llm_provider,
            language=language,
            concurrency=concurrency,
            draft=draft,
            aspect_ratio=aspect_ratio,
            subtitle_position=subtitle_position,
            caption_size=caption_size,
            background_style=background_style,
            style_pacing=style_pacing,
            highlight_color=highlight_color,
            trim_start=trim_start,
            trim_end=trim_end,
            selected_styles=selected_styles,
            subtitle_y=subtitle_y,
            video_layout=video_layout,
            progress_bar=progress_bar,
            progress_bar_position=progress_bar_position,
            headline_hook=headline_hook,
            headline_style=headline_style,
            headline_duration=headline_duration,
            auto_emojis=auto_emojis,
            kinetic_zoom=kinetic_zoom,
            sound_effects=sound_effects,
            bg_music=bg_music,
            watermark_text=watermark_text,
            ai_enhance=ai_enhance,
            api_key=api_key,
            input_file=str(target_input),
        )
        self.save_job(job)

        # Submit task to worker pool
        self.executor.submit(self._run_job_task, job_id)
        return job

    def rerender_job(
        self,
        job_id: str,
        draft: Optional[bool] = None,
        concurrency: Optional[int] = None,
    ) -> JobInfo:
        """Queue a re-render of an existing job using its updated timeline."""
        job = self.get_job(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")
        if not job.timeline_file or not Path(job.timeline_file).exists():
            raise ValueError(f"Job {job_id} has no timeline file to re-render")

        if draft is not None:
            job.draft = draft
        if concurrency is not None:
            job.concurrency = concurrency

        job.status = "queued"
        job.step = "rendering"
        job.progress = 0.05
        job.error = None
        self.save_job(job)

        self.executor.submit(self._run_rerender_task, job_id)
        return job

    def _run_rerender_task(self, job_id: str):
        job = self.get_job(job_id)
        if not job or not job.timeline_file or not Path(job.timeline_file).exists():
            return

        job_dir = self.jobs_dir / job_id
        output_mp4 = job_dir / "output.mp4"
        timeline_json = Path(job.timeline_file)

        def update_progress(step: str, progress: float):
            job.status = "processing"
            job.step = step
            job.progress = round(progress, 3)
            self.save_job(job)

        try:
            update_progress("rendering", 0.05)
            tl_data = json.loads(timeline_json.read_text(encoding="utf-8"))
            timeline = Timeline.model_validate(tl_data)

            def on_render_progress(pct: float):
                update_progress("rendering", 0.05 + (pct * 0.93))

            concurrency_val = job.concurrency or min(max(2, (os.cpu_count() or 4) // 2), 4)
            render(
                timeline_input=timeline,
                output_path=output_mp4,
                concurrency=concurrency_val,
                draft=job.draft,
                progress_callback=on_render_progress,
            )

            job.status = "completed"
            job.step = "completed"
            job.progress = 1.0
            job.output_file = str(output_mp4)
            self.save_job(job)
            logger.info(f"Job {job_id} re-rendered successfully: {output_mp4}")
        except Exception as e:
            logger.exception(f"Re-render for {job_id} failed: {e}")
            job.status = "failed"
            job.step = "failed"
            job.error = str(e)
            self.save_job(job)

    def _run_job_task(self, job_id: str):
        job = self.get_job(job_id)
        if not job:
            return

        job_dir = self.jobs_dir / job_id
        input_path = Path(job.input_file)
        output_mp4 = job_dir / "output.mp4"
        timeline_json = job_dir / "timeline.json"
        words_json = job_dir / "words.json"
        phrases_json = job_dir / "phrases.json"

        def update_progress(step: str, progress: float):
            job.status = "processing"
            job.step = step
            job.progress = round(progress, 3)
            self.save_job(job)

        try:
            # 1. Probing & Validation (0.00 -> 0.03)
            update_progress("probing", 0.01)
            probe = probe_video(input_path)
            orig_duration = max(0.1, probe.duration)

            # 0. Optional Clip Trimming (0.03 -> 0.05)
            if job.trim_start is not None or job.trim_end is not None:
                t_start = max(0.0, float(job.trim_start or 0.0))
                if t_start >= orig_duration - 0.2:
                    t_start = 0.0
                
                t_end = float(job.trim_end) if job.trim_end is not None else orig_duration
                if t_end > orig_duration:
                    t_end = orig_duration
                if t_end <= t_start + 0.2:
                    t_end = orig_duration

                if t_start > 0.05 or t_end < orig_duration - 0.05:
                    update_progress("trimming", 0.03)
                    trimmed_path = job_dir / "trimmed_input.mp4"
                    trim_cmd = [
                        "ffmpeg", "-y",
                        "-ss", f"{t_start:.2f}",
                        "-to", f"{t_end:.2f}",
                        "-i", str(input_path),
                        "-c:v", "libx264", "-c:a", "aac",
                        str(trimmed_path)
                    ]
                    import subprocess
                    subprocess.run(trim_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    input_path = trimmed_path
                    probe = probe_video(input_path)

            update_progress("probing", 0.05)

            # 2. Transcription (0.05 -> 0.35)
            update_progress("transcribing", 0.08)
            transcript = transcribe(
                path=input_path,
                language=job.language if job.language != "auto" else None,
            )
            words_json.write_text(transcript.model_dump_json(indent=2), encoding="utf-8")
            update_progress("transcribing", 0.35)

            # 3. Chunking (0.35 -> 0.42)
            update_progress("chunking", 0.38)
            phrases = chunk_words(
                words=transcript.words,
                duration=probe.duration,
            )
            phrases_doc = PhrasesDocument(
                language=transcript.language or job.language,
                duration=probe.duration,
                phrases=phrases,
            )
            phrases_json.write_text(phrases_doc.model_dump_json(indent=2), encoding="utf-8")
            update_progress("chunking", 0.42)

            # 3.5. AI Scene Analysis (0.42 -> 0.50) — optional
            scene_analysis_data = None
            if getattr(job, 'ai_enhance', False) and job.llm_provider != "none":
                update_progress("analyzing", 0.43)
                try:
                    from backend.pipeline.analyze import analyze_video
                    # Prepare transcript phrases for the analyzer
                    analysis_phrases = [
                        {
                            "id": p.id,
                            "text": p.text,
                            "start": round(p.start, 2),
                            "end": round(p.end, 2),
                        }
                        for p in phrases_doc.phrases
                    ]
                    analysis_result = analyze_video(
                        video_path=input_path,
                        transcript_phrases=analysis_phrases,
                        provider=job.llm_provider,
                        api_key=getattr(job, 'api_key', None),
                        keyframes_dir=job_dir / "keyframes",
                    )
                    scene_analysis_data = analysis_result.model_dump()
                    # Save analysis to disk
                    analysis_json = job_dir / "analysis.json"
                    analysis_json.write_text(
                        json.dumps(scene_analysis_data, indent=2),
                        encoding="utf-8",
                    )
                    logger.info(f"Job {job_id}: AI scene analysis complete — "
                                f"{len(analysis_result.topic_segments)} topics, "
                                f"type={analysis_result.video_type}")
                except Exception as e:
                    logger.warning(f"Job {job_id}: AI scene analysis failed (non-fatal): {e}")
                    scene_analysis_data = None
            update_progress("analyzing" if scene_analysis_data else "chunking", 0.50)

            # 4. Planning & Layout (0.50 -> 0.55)
            update_progress("planning", 0.51)
            planner = get_planner(
                provider=job.llm_provider,
                preset=job.preset,
                api_key=getattr(job, 'api_key', None),
            )
            selected_styles_list = (
                [s.strip() for s in job.selected_styles.split(",") if s.strip()]
                if job.selected_styles
                else None
            )
            events = planner.plan(
                phrases=phrases_doc.phrases,
                video_duration=probe.duration,
                preset=job.preset,
                language=transcript.language or job.language,
                style_pacing=job.style_pacing,
                caption_size=job.caption_size,
                background_style=job.background_style,
                highlight_color=job.highlight_color,
                selected_styles=selected_styles_list,
                subtitle_y=job.subtitle_y,
                auto_emojis=getattr(job, "auto_emojis", True),
                scene_analysis=scene_analysis_data,
            )

            # Copy input asset to remotion public dir
            rel_src = prepare_video_asset(input_path, job_id=job_id)

            ar_map = {
                "9:16": (1080, 1920),
                "16:9": (1920, 1080),
                "1:1": (1080, 1080),
                "4:5": (1080, 1350),
            }
            target_w, target_h = ar_map.get(job.aspect_ratio, (probe.width, probe.height))

            # Apply custom subtitle position preference if specified without causing collisions
            if job.subtitle_position in ["upper", "center", "lower"] and job.subtitle_position != "lower" and job.subtitle_y is None:
                for ev in events:
                    if ev.id.startswith("base_") or ev.id.startswith("evt_"):
                        has_collision = any(
                            other.zone == job.subtitle_position and max(other.start, ev.start) < min(other.end, ev.end)
                            for other in events if other.id != ev.id
                        )
                        if not has_collision:
                            ev.zone = job.subtitle_position

            resolved_layout = getattr(job, "video_layout", "split_podcast") or "split_podcast"
            # If the video is already vertical or square, split screen is not appropriate; fallback to fill
            if probe.width <= probe.height and resolved_layout == "split_podcast":
                resolved_layout = "fill"

            tl_video = TimelineVideo(
                src=rel_src,
                width=target_w,
                height=target_h,
                fps=round(probe.fps),
                durationSec=round(probe.duration, 2),
                layout=resolved_layout,
                originalWidth=probe.width,
                originalHeight=probe.height,
            )
            tl_words = [
                TimelineWord(i=w.i, text=w.text, start=round(w.start, 2), end=round(w.end, 2))
                for w in transcript.words
            ]
            camera_cuts = None
            if resolved_layout == "active_speaker":
                from backend.pipeline.reframe import build_active_speaker_cuts
                num_spk = 2
                if scene_analysis_data:
                    num_spk = scene_analysis_data.get("num_speakers", 2)
                camera_cuts = build_active_speaker_cuts(
                    phrases=phrases_doc.phrases,
                    video_duration=probe.duration,
                    num_speakers=num_spk,
                    scene_analysis=scene_analysis_data,
                )

            # Multi-Speaker Diarization Auto Color Coding (Feature #5)
            if camera_cuts:
                for ev in events:
                    mid = (ev.start + ev.end) / 2.0
                    for cut in camera_cuts:
                        if cut.start <= mid <= cut.end:
                            ev.speakerId = cut.speakerId
                            if cut.speakerId == "speaker_1":
                                ev.highlightColor = "#F59E0B"
                            elif cut.speakerId == "speaker_0":
                                ev.highlightColor = "#38BDF8"
                            break

            timeline = Timeline(
                version=1,
                video=tl_video,
                language=transcript.language or job.language,
                words=tl_words,
                events=events,
                captionSize=job.caption_size,
                backgroundStyle=job.background_style,
                highlightColor=job.highlight_color,
                subtitleY=job.subtitle_y,
                videoLayout=resolved_layout,
                cameraCuts=camera_cuts,
                progressBar=getattr(job, "progress_bar", True),
                progressBarPosition=getattr(job, "progress_bar_position", "bottom"),
                headlineHook=getattr(job, "headline_hook", None),
                headlineStyle=getattr(job, "headline_style", "badge"),
                headlineDuration=getattr(job, "headline_duration", None),
                autoEmojis=getattr(job, "auto_emojis", True),
                kineticZoom=getattr(job, "kinetic_zoom", False),
                soundEffects=getattr(job, "sound_effects", False),
                bgMusic=getattr(job, "bg_music", None),
                watermarkText=getattr(job, "watermark_text", None),
            )
            timeline_json.write_text(
                json.dumps(timeline.model_dump(by_alias=True, exclude_none=True), indent=2),
                encoding="utf-8",
            )
            job.timeline_file = str(timeline_json)
            update_progress("planning", 0.55)

            # 5. Rendering with Remotion (0.55 -> 0.98)
            update_progress("rendering", 0.56)

            def on_render_progress(pct: float):
                # Map 0.0 - 1.0 to 0.56 - 0.98
                mapped = 0.56 + (pct * 0.42)
                update_progress("rendering", mapped)

            concurrency_val = job.concurrency or min(max(2, (os.cpu_count() or 4) // 2), 4)
            render(
                timeline_input=timeline,
                output_path=output_mp4,
                concurrency=concurrency_val,
                draft=job.draft,
                progress_callback=on_render_progress,
            )

            # 6. Complete (1.00)
            job.status = "completed"
            job.step = "completed"
            job.progress = 1.0
            job.output_file = str(output_mp4)
            self.save_job(job)
            logger.info(f"Job {job_id} successfully completed. Output: {output_mp4}")

        except Exception as e:
            logger.exception(f"Job {job_id} failed with error: {e}")
            job.status = "failed"
            job.step = "failed"
            job.error = str(e)
            self.save_job(job)


# Global singleton instance
_runner_instance: Optional[JobManager] = None


def get_job_manager() -> JobManager:
    global _runner_instance
    if _runner_instance is None:
        _runner_instance = JobManager()
    return _runner_instance
