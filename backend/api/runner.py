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
    trim_start: Optional[float] = None
    trim_end: Optional[float] = None
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

    def __init__(self, base_jobs_dir: str = "jobs", max_workers: int = 1):
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
        trim_start: Optional[float] = None,
        trim_end: Optional[float] = None,
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
            trim_start=trim_start,
            trim_end=trim_end,
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

            concurrency_val = job.concurrency or min(os.cpu_count() or 4, 8)
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
            # 0. Optional Clip Trimming (0.00 -> 0.02)
            if job.trim_start is not None or job.trim_end is not None:
                update_progress("trimming", 0.01)
                t_start = max(0.0, float(job.trim_start or 0.0))
                trimmed_path = job_dir / "trimmed_input.mp4"
                trim_cmd = ["ffmpeg", "-y", "-ss", f"{t_start:.2f}"]
                if job.trim_end is not None and float(job.trim_end) > t_start:
                    trim_cmd.extend(["-to", f"{float(job.trim_end):.2f}"])
                trim_cmd.extend(["-i", str(input_path), "-c:v", "libx264", "-c:a", "aac", str(trimmed_path)])
                import subprocess
                subprocess.run(trim_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                input_path = trimmed_path

            # 1. Probing (0.00 -> 0.05)
            update_progress("probing", 0.02)
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

            # 3. Chunking (0.35 -> 0.45)
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
            update_progress("chunking", 0.45)

            # 4. Planning & Layout (0.45 -> 0.55)
            update_progress("planning", 0.48)
            planner = get_planner(provider=job.llm_provider, preset=job.preset)
            events = planner.plan(
                phrases=phrases_doc.phrases,
                video_duration=probe.duration,
                preset=job.preset,
                language=transcript.language or job.language,
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
            if job.subtitle_position in ["upper", "center", "lower"] and job.subtitle_position != "lower":
                for ev in events:
                    if ev.id.startswith("base_"):
                        has_collision = any(
                            other.zone == job.subtitle_position and max(other.start, ev.start) < min(other.end, ev.end)
                            for other in events if other.id != ev.id
                        )
                        if not has_collision:
                            ev.zone = job.subtitle_position

            tl_video = TimelineVideo(
                src=rel_src,
                width=target_w,
                height=target_h,
                fps=round(probe.fps),
                durationSec=round(probe.duration, 2),
            )
            tl_words = [
                TimelineWord(i=w.i, text=w.text, start=round(w.start, 2), end=round(w.end, 2))
                for w in transcript.words
            ]
            timeline = Timeline(
                version=1,
                video=tl_video,
                language=transcript.language or job.language,
                words=tl_words,
                events=events,
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

            concurrency_val = job.concurrency or min(os.cpu_count() or 4, 8)
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
