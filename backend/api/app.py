"""FastAPI application for Dynamic Captions Studio."""
import json
import os
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Optional, Literal
from dotenv import load_dotenv

# Load environment variables from .env (MISTRAL_API_KEY, etc.)
load_dotenv()

from pydantic import BaseModel
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, status, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from backend.api.runner import get_job_manager, JobInfo

app = FastAPI(
    title="Dynamic Captions Studio API",
    description="Render dynamic, multi-style, animated captions on vertical videos",
    version="1.0.0",
)

# CORS middleware for local development and web UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_no_cache_headers(request, call_next):
    """Ensure frontend HTML, JS, CSS, and layout image assets are never cached by browsers during development."""
    response = await call_next(request)
    path = request.url.path
    if path == "/" or path.endswith((".html", ".js", ".css", ".png", ".jpg", ".jpeg", ".webp", ".svg")):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


@app.get("/api/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "version": "1.0.0"}


@app.post("/api/jobs", status_code=status.HTTP_201_CREATED, response_model=JobInfo)
async def create_job(
    file: UploadFile = File(...),
    preset: str = Form("bold_creator"),
    llm_provider: Optional[str] = Form(None),
    language: str = Form("en"),
    concurrency: Optional[int] = Form(None),
    draft: bool = Form(False),
    aspect_ratio: str = Form("9:16"),
    subtitle_position: str = Form("lower"),
    caption_size: str = Form("medium"),
    background_style: str = Form("transparent"),
    style_pacing: str = Form("sentence"),
    highlight_color: str = Form("#38BDF8"),
    trim_start: Optional[float] = Form(None),
    trim_end: Optional[float] = Form(None),
    selected_styles: Optional[str] = Form(None),
    subtitle_y: Optional[float] = Form(None),
    video_layout: str = Form("split_podcast"),
    progress_bar: bool = Form(True),
    progress_bar_position: Literal["bottom", "top"] = Form("bottom"),
    headline_hook: Optional[str] = Form(None),
    headline_style: Literal["badge", "glass", "clean", "cyber"] = Form("badge"),
    headline_duration: Optional[float] = Form(None),
    headline_y: Optional[float] = Form(0.08),
    auto_emojis: bool = Form(True),
    kinetic_zoom: bool = Form(False),
    sound_effects: bool = Form(False),
    bg_music: Optional[str] = Form(None),
    watermark_text: Optional[str] = Form(None),
    ai_enhance: bool = Form(False),
    api_key: Optional[str] = Form(None),
    multi_style_variety: bool = Form(True),
):
    """Submit a video for captioned rendering."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Uploaded file has no filename")

    provider = llm_provider or os.getenv("LLM_PROVIDER", "none")

    # Save uploaded file to temp file
    suffix = Path(file.filename).suffix or ".mp4"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = Path(tmp.name)

    try:
        manager = get_job_manager()
        job = manager.submit_job(
            input_video_source=tmp_path,
            preset=preset,
            llm_provider=provider,
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
            headline_hook=headline_hook.strip() if headline_hook and headline_hook.strip() else None,
            headline_style=headline_style,
            headline_duration=headline_duration,
            headline_y=headline_y,
            auto_emojis=auto_emojis,
            kinetic_zoom=kinetic_zoom,
            sound_effects=sound_effects,
            bg_music=bg_music.strip() if bg_music and bg_music.strip() else None,
            watermark_text=watermark_text.strip() if watermark_text and watermark_text.strip() else None,
            ai_enhance=ai_enhance,
            api_key=api_key.strip() if api_key and api_key.strip() else None,
            multi_style_variety=multi_style_variety,
        )
        return job
    finally:
        # Clean up temporary upload copy
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except Exception:
                pass


@app.get("/api/jobs/{job_id}", response_model=JobInfo)
def get_job_status(job_id: str):
    """Get current status, step, and progress of a job."""
    manager = get_job_manager()
    job = manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
    return job


@app.post("/api/jobs/{job_id}/cancel")
def cancel_job(job_id: str):
    """Cancel a queued or running job."""
    manager = get_job_manager()
    success = manager.cancel_job(job_id)
    if not success:
        raise HTTPException(status_code=400, detail=f"Job '{job_id}' could not be cancelled or does not exist")
    return {"status": "cancelled", "job_id": job_id}


@app.api_route("/api/jobs/{job_id}/output", methods=["GET", "HEAD"])
def download_job_output(job_id: str):
    """Download the final rendered MP4 video."""
    manager = get_job_manager()
    job = manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

    if job.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Job '{job_id}' is not completed yet (current status: {job.status})",
        )

    if not job.output_file or not Path(job.output_file).exists():
        raise HTTPException(status_code=404, detail="Rendered output video file not found")

    return FileResponse(
        path=job.output_file,
        media_type="video/mp4",
        filename=f"{job_id}_captioned.mp4",
    )


@app.get("/api/jobs/{job_id}/timeline")
def get_job_timeline(job_id: str):
    """Retrieve the generated timeline JSON for a job."""
    manager = get_job_manager()
    job = manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

    if not job.timeline_file or not Path(job.timeline_file).exists():
        raise HTTPException(status_code=404, detail="Timeline JSON not yet generated for this job")

    data = json.loads(Path(job.timeline_file).read_text(encoding="utf-8"))
    return JSONResponse(content=data)


@app.put("/api/jobs/{job_id}/timeline")
async def update_job_timeline(job_id: str, updated_timeline: dict):
    """Update timeline events/captions before final render or re-render."""
    from backend.schemas.timeline import Timeline
    manager = get_job_manager()
    job = manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

    try:
        validated = Timeline.model_validate(updated_timeline)
        job_dir = Path("jobs").resolve() / job_id
        timeline_json = job_dir / "timeline.json"
        timeline_json.write_text(
            json.dumps(validated.model_dump(by_alias=True, exclude_none=True), indent=2),
            encoding="utf-8",
        )
        job.timeline_file = str(timeline_json)
        manager.save_job(job)
        return {"status": "ok", "message": "Timeline updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid timeline: {e}")


@app.post("/api/jobs/{job_id}/rerender", response_model=JobInfo)
def rerender_job(
    job_id: str,
    draft: Optional[bool] = Form(None),
    concurrency: Optional[int] = Form(None),
):
    """Re-render video after editing captions/styles without re-transcribing."""
    manager = get_job_manager()
    job = manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
    if not job.timeline_file or not Path(job.timeline_file).exists():
        raise HTTPException(status_code=400, detail="Cannot re-render: timeline not found")

    try:
        updated_job = manager.rerender_job(job_id=job_id, draft=draft, concurrency=concurrency)
        return updated_job
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/jobs/{job_id}/find-clips")
def find_job_clips(
    job_id: str,
    target_length: Literal["15s", "30s", "60s"] = "30s",
):
    """Find viral clips for a processed job based on its transcript and scene analysis."""
    from backend.pipeline.clips import find_viral_clips
    manager = get_job_manager()
    job = manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

    # Traverse to root ancestor job so we scan the master video and transcript
    curr = job
    while getattr(curr, "parent_job_id", None):
        parent = manager.get_job(curr.parent_job_id)
        if parent:
            curr = parent
        else:
            break
    root_job = curr
    root_job_id = root_job.id
    root_job_dir = Path("jobs").resolve() / root_job_id

    master_phrases_file = root_job_dir / "phrases_master.json"
    phrases_file = root_job_dir / "phrases.json"
    timeline_file = root_job_dir / "timeline.json"
    analysis_file = root_job_dir / "analysis.json"

    phrases = []
    duration = 30.0

    if master_phrases_file.exists():
        data = json.loads(master_phrases_file.read_text(encoding="utf-8"))
        phrases = data.get("phrases", [])
        duration = float(data.get("duration", 30.0))
    elif phrases_file.exists():
        data = json.loads(phrases_file.read_text(encoding="utf-8"))
        phrases = data.get("phrases", [])
        duration = float(data.get("duration", 30.0))
    elif timeline_file.exists():
        tl_data = json.loads(timeline_file.read_text(encoding="utf-8"))
        duration = float(tl_data.get("video", {}).get("durationSec", 30.0))
        for ev in tl_data.get("events", []):
            phrases.append({"start": ev.get("start", 0), "end": ev.get("end", 0), "text": ev.get("text", "")})
    else:
        raise HTTPException(status_code=400, detail="Transcript or phrases not yet generated for this job")

    # If the root phrases cover only a short trimmed fragment but the input file is longer,
    # transcribe the full master file so clips are found across the entire source video!
    input_file_path = None
    if getattr(root_job, "input_file", None) and Path(root_job.input_file).exists():
        input_file_path = Path(root_job.input_file)
    elif (root_job_dir / "input.mp4").exists():
        input_file_path = root_job_dir / "input.mp4"

    if input_file_path and not master_phrases_file.exists():
        from backend.pipeline.probe import probe_video
        try:
            probe = probe_video(input_file_path)
            if (duration < 15.0 or duration < 45.0) and probe.duration > (duration + 5.0):
                from backend.pipeline.transcribe import transcribe
                from backend.pipeline.chunk import chunk_words
                logger.info(f"Master file is {probe.duration:.1f}s while phrases cover {duration:.1f}s. Transcribing full video...")
                full_transcript = transcribe(path=input_file_path)
                full_chunked = chunk_words(words=full_transcript.words, duration=probe.duration)
                phrases = [c.model_dump() for c in full_chunked]
                duration = probe.duration
                master_phrases_file.write_text(json.dumps({"phrases": phrases, "duration": duration}, indent=2), encoding="utf-8")
        except Exception as e:
            logger.warning(f"Could not probe/transcribe full master video ({e}); using existing phrases.")

    topic_segments = None
    if analysis_file.exists():
        try:
            an_data = json.loads(analysis_file.read_text(encoding="utf-8"))
            topic_segments = an_data.get("topic_segments", [])
        except Exception:
            pass

    if not phrases:
        if input_file_path:
            from backend.pipeline.probe import probe_video
            probe = probe_video(input_file_path)
            if not probe.has_audio:
                raise HTTPException(
                    status_code=400,
                    detail="NO_AUDIO_TRACK: This video has no audio track. Captions and viral highlights require speech audio. Please upload a video with sound or attach an audio file."
                )
        raise HTTPException(
            status_code=400,
            detail="NO_SPEECH_DETECTED: No spoken words were detected in this video. Please ensure the video contains audible speech."
        )

    provider = root_job.llm_provider if root_job.llm_provider != "none" else os.getenv("LLM_PROVIDER", "none")
    clips = find_viral_clips(
        phrases=phrases,
        video_duration=duration,
        target_length=target_length,
        provider=provider,
        api_key=getattr(root_job, "api_key", None),
        topic_segments=topic_segments,
    )

    return {
        "job_id": job_id,
        "root_job_id": root_job_id,
        "target_length": target_length,
        "video_duration": duration,
        "clips": [c.model_dump() for c in clips],
        "total": len(clips),
    }


@app.post("/api/jobs/{job_id}/batch-render-clips")
def batch_render_clips_endpoint(
    job_id: str,
    payload: Optional[dict] = Body(None),
):
    """Batch render discovered viral clips into standalone MP4s bundled in a ZIP."""
    from backend.pipeline.clips import batch_render_viral_clips, find_viral_clips, ViralClip
    manager = get_job_manager()
    job = manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

    clips_data = None
    if payload and "clips" in payload:
        clips_data = payload["clips"]

    if not clips_data:
        # Discover clips if not provided in payload
        job_dir = Path("jobs").resolve() / job_id
        phrases_file = job_dir / "phrases.json"
        timeline_file = job_dir / "timeline.json"
        analysis_file = job_dir / "analysis.json"

        phrases = []
        duration = 30.0
        if phrases_file.exists():
            data = json.loads(phrases_file.read_text(encoding="utf-8"))
            phrases = data.get("phrases", [])
            duration = float(data.get("duration", 30.0))
        elif timeline_file.exists():
            tl_data = json.loads(timeline_file.read_text(encoding="utf-8"))
            duration = float(tl_data.get("video", {}).get("durationSec", 30.0))
            for ev in tl_data.get("events", []):
                phrases.append({"start": ev.get("start", 0), "end": ev.get("end", 0), "text": ev.get("text", "")})
        else:
            raise HTTPException(status_code=400, detail="Job has no transcript or phrases to extract clips")

        topic_segments = None
        if analysis_file.exists():
            try:
                an_data = json.loads(analysis_file.read_text(encoding="utf-8"))
                topic_segments = an_data.get("topic_segments", [])
            except Exception:
                pass

        provider = job.llm_provider if job.llm_provider != "none" else os.getenv("LLM_PROVIDER", "none")
        discovered = find_viral_clips(
            phrases=phrases,
            video_duration=duration,
            target_length="30s",
            provider=provider,
            api_key=getattr(job, "api_key", None),
            topic_segments=topic_segments,
        )
        clips_data = [c.model_dump() for c in discovered]

    if not clips_data:
        raise HTTPException(status_code=400, detail="No viral clips found or provided to batch render")

    try:
        multi_style_variety = payload.get("multi_style_variety", True) if payload else True
        zip_path = batch_render_viral_clips(
            job_id=job_id,
            clips=clips_data,
            draft=getattr(job, "draft", False),
            multi_style_variety=multi_style_variety,
        )
        return {
            "status": "completed",
            "zip_url": f"/api/jobs/{job_id}/download-zip",
            "clips_count": len(clips_data),
            "filename": zip_path.name,
            "message": f"Successfully rendered {len(clips_data)} viral reels into ZIP",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch render failed: {e}")


@app.get("/api/jobs/{job_id}/download-zip")
def download_job_zip(job_id: str):
    """Download the batch rendered viral reels ZIP package."""
    job_dir = Path("jobs").resolve() / job_id
    zip_path = job_dir / f"{job_id}_viral_reels.zip"
    if not zip_path.exists():
        raise HTTPException(status_code=404, detail="ZIP archive not found or not yet generated")
    return FileResponse(
        path=zip_path,
        media_type="application/zip",
        filename=f"{job_id}_viral_reels.zip",
    )


class RenderClipPayload(BaseModel):
    start: float
    end: float
    headline: Optional[str] = None
    headline_style: Optional[Literal["badge", "glass", "clean", "cyber"]] = "badge"
    headline_duration: Optional[float] = None
    headline_y: Optional[float] = 0.08
    caption_size: Optional[str] = "medium"
    subtitle_y: Optional[float] = 0.79
    selected_styles: Optional[str] = None
    watermark_text: Optional[str] = None
    video_layout: Optional[str] = "split_podcast"
    ai_enhance: Optional[bool] = False
    kinetic_zoom: Optional[bool] = False
    sound_effects: Optional[bool] = False
    bg_music: Optional[str] = None
    progress_bar: Optional[bool] = True
    auto_emojis: Optional[bool] = True
    aspect_ratio: Optional[str] = "9:16"
    draft: Optional[bool] = False
    concurrency: Optional[int] = None
    highlight_color: Optional[str] = "#38BDF8"
    multi_style_variety: Optional[bool] = True


@app.post("/api/jobs/{job_id}/render-clip", response_model=JobInfo, status_code=status.HTTP_201_CREATED)
def render_single_clip_endpoint(
    job_id: str,
    payload: RenderClipPayload,
):
    """Render a single customized viral reel into a standalone captioned MP4 rapidly from an existing job."""
    manager = get_job_manager()
    job = manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

    try:
        clip_job = manager.submit_clip_job(
            parent_job_id=job_id,
            start=payload.start,
            end=payload.end,
            headline=payload.headline,
            headline_style=payload.headline_style,
            headline_duration=payload.headline_duration,
            headline_y=payload.headline_y,
            caption_size=payload.caption_size,
            subtitle_y=payload.subtitle_y,
            selected_styles=payload.selected_styles,
            watermark_text=payload.watermark_text,
            video_layout=payload.video_layout,
            ai_enhance=payload.ai_enhance,
            kinetic_zoom=payload.kinetic_zoom,
            sound_effects=payload.sound_effects,
            bg_music=payload.bg_music,
            progress_bar=payload.progress_bar,
            auto_emojis=payload.auto_emojis,
            aspect_ratio=payload.aspect_ratio,
            draft=payload.draft or False,
            concurrency=payload.concurrency,
            highlight_color=payload.highlight_color,
            multi_style_variety=payload.multi_style_variety,
        )
        return clip_job
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/clips/discover")
def discover_clips_from_video(
    file: Optional[UploadFile] = File(None),
    audio_file: Optional[UploadFile] = File(None),
    sample: bool = Form(False),
    target_length: Literal["15s", "30s", "60s"] = Form("30s"),
    llm_provider: Optional[str] = Form(None),
):
    """Transcribe video and find viral clips on demand, with audio validation and persistent master caching."""
    from backend.pipeline.probe import probe_video
    from backend.pipeline.transcribe import transcribe
    from backend.pipeline.chunk import chunk_words
    from backend.pipeline.clips import find_viral_clips

    tmp_path = None
    tmp_audio_path = None
    tmp_merged_path = None
    try:
        if sample:
            source_path = Path("samples/synthetic.mp4").resolve()
            if not source_path.exists():
                raise HTTPException(status_code=404, detail="Synthetic sample not found")
        elif file and file.filename:
            suffix = Path(file.filename).suffix or ".mp4"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                shutil.copyfileobj(file.file, tmp)
                tmp_path = Path(tmp.name)
            source_path = tmp_path
        else:
            raise HTTPException(status_code=400, detail="Either file or sample=true must be provided")

        # If separate audio_file was provided, merge audio track with video track
        if audio_file and audio_file.filename:
            a_suffix = Path(audio_file.filename).suffix or ".m4a"
            with tempfile.NamedTemporaryFile(delete=False, suffix=a_suffix) as a_tmp:
                shutil.copyfileobj(audio_file.file, a_tmp)
                tmp_audio_path = Path(a_tmp.name)

            tmp_merged_path = Path(tempfile.gettempdir()) / f"merged_{uuid.uuid4().hex[:8]}.mp4"
            cmd = [
                "ffmpeg", "-y", "-v", "error",
                "-i", str(source_path),
                "-i", str(tmp_audio_path),
                "-c:v", "copy",
                "-c:a", "aac",
                "-map", "0:v:0",
                "-map", "1:a:0",
                "-shortest",
                str(tmp_merged_path)
            ]
            subprocess.run(cmd, check=True)
            source_path = tmp_merged_path

        probe = probe_video(source_path)
        if not probe.has_audio:
            raise HTTPException(
                status_code=400,
                detail="NO_AUDIO_TRACK: This video file has no audio stream (common with YouTube DASH video-only downloads). Dynamic captions and viral highlights require spoken audio. Please upload a video with sound or attach an audio file."
            )

        transcript = transcribe(path=source_path)
        if not transcript.words:
            raise HTTPException(
                status_code=400,
                detail="NO_SPEECH_DETECTED: No spoken words were detected in this video. Please ensure the video contains clear audible speech in an enabled language."
            )

        phrases = chunk_words(words=transcript.words, duration=probe.duration)
        phrases_list = [p.model_dump() for p in phrases]

        # Create master job on backend so subsequent duration changes (15s, 30s, 60s)
        # and reel rendering don't re-upload or re-transcribe!
        from backend.api.runner import JobInfo
        master_id = str(uuid.uuid4())
        master_job_dir = Path("jobs").resolve() / master_id
        master_job_dir.mkdir(parents=True, exist_ok=True)
        dest_input = master_job_dir / "input.mp4"
        shutil.copyfile(source_path, dest_input)

        master_job = JobInfo(
            id=master_id,
            preset="bold_creator",
            llm_provider=llm_provider or "none",
            language="en",
            status="completed",
            step="completed",
            progress=1.0,
            input_file=str(dest_input),
        )
        manager = get_job_manager()
        manager.save_job(master_job)

        (master_job_dir / "phrases.json").write_text(json.dumps({"phrases": phrases_list, "duration": probe.duration}, indent=2), encoding="utf-8")
        (master_job_dir / "phrases_master.json").write_text(json.dumps({"phrases": phrases_list, "duration": probe.duration}, indent=2), encoding="utf-8")

        provider = llm_provider or os.getenv("LLM_PROVIDER", "none")
        clips = find_viral_clips(
            phrases=phrases_list,
            video_duration=probe.duration,
            target_length=target_length,
            provider=provider,
        )

        return {
            "job_id": master_job.id,
            "root_job_id": master_job.id,
            "target_length": target_length,
            "video_duration": probe.duration,
            "clips": [c.model_dump() for c in clips],
            "total": len(clips),
        }
    finally:
        if tmp_path and tmp_path.exists():
            try: tmp_path.unlink()
            except Exception: pass
        if tmp_audio_path and tmp_audio_path.exists():
            try: tmp_audio_path.unlink()
            except Exception: pass
        if tmp_merged_path and tmp_merged_path.exists():
            try: tmp_merged_path.unlink()
            except Exception: pass


@app.post("/api/probe")
def probe_media_endpoint(file: UploadFile = File(...)):
    """Fast probe of uploaded video to verify duration, dimensions, FPS, and audio stream."""
    from backend.pipeline.probe import probe_video
    suffix = Path(file.filename or "video.mp4").suffix or ".mp4"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = Path(tmp.name)
    try:
        probe = probe_video(tmp_path)
        return {
            "filename": file.filename,
            "duration": probe.duration,
            "width": probe.width,
            "height": probe.height,
            "fps": probe.fps,
            "has_audio": probe.has_audio,
            "audio_codec": getattr(probe, "audio_codec", None),
        }
    finally:
        if tmp_path.exists():
            try: tmp_path.unlink()
            except Exception: pass


@app.post("/api/merge-audio")
def merge_video_audio_endpoint(
    video_file: UploadFile = File(...),
    audio_file: UploadFile = File(...),
):
    """Multiplex video stream and audio stream into a single MP4 container via ffmpeg."""
    v_suffix = Path(video_file.filename or "video.mp4").suffix or ".mp4"
    a_suffix = Path(audio_file.filename or "audio.m4a").suffix or ".m4a"

    with tempfile.NamedTemporaryFile(delete=False, suffix=v_suffix) as v_tmp:
        shutil.copyfileobj(video_file.file, v_tmp)
        v_path = Path(v_tmp.name)
    with tempfile.NamedTemporaryFile(delete=False, suffix=a_suffix) as a_tmp:
        shutil.copyfileobj(audio_file.file, a_tmp)
        a_path = Path(a_tmp.name)

    out_merged = Path(tempfile.gettempdir()) / f"merged_{uuid.uuid4().hex[:8]}.mp4"
    try:
        cmd = [
            "ffmpeg", "-y", "-v", "error",
            "-i", str(v_path),
            "-i", str(a_path),
            "-c:v", "copy",
            "-c:a", "aac",
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-shortest",
            str(out_merged)
        ]
        subprocess.run(cmd, check=True)
        return FileResponse(
            path=out_merged,
            media_type="video/mp4",
            filename=f"with_audio_{Path(video_file.filename or 'video').stem}.mp4",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to merge audio with video: {e}")
    finally:
        if v_path.exists():
            try: v_path.unlink()
            except Exception: pass
        if a_path.exists():
            try: a_path.unlink()
            except Exception: pass


@app.get("/api/styles")
def list_styles():
    """Return all available caption styles with rich metadata."""
    styles_meta = [
        {"id": "hormozi_bold", "name": "Hormozi Bold", "category": "bold", "tag": "Trending", "icon": "⚡", "description": "Alex Hormozi chunky uppercase font, yellow pop highlight, heavy drop shadow"},
        {"id": "retro_vaporwave", "name": "Retro 80s", "category": "aesthetic", "tag": "Aesthetic", "icon": "🌴", "description": "Dual chrome pink-to-cyan gradient, glowing grid card"},
        {"id": "karaoke_bounce", "name": "Karaoke Bounce", "category": "kinetic", "tag": "Kinetic", "icon": "🎤", "description": "Word-by-word hopping bounce physics dot with amber glow"},
        {"id": "fire_burn", "name": "Fiery Flame", "category": "bold", "tag": "High Energy", "icon": "🔥", "description": "Flame gradient text with flickering fiery red drop shadow"},
        {"id": "title3d", "name": "3D Title", "category": "bold", "tag": "High Energy", "icon": "🧊", "description": "Extruded 3D shadow, multi-line vertical gradients, twinkling stars"},
        {"id": "neon_glow", "name": "Neon Glow", "category": "bold", "tag": "Cyberpunk", "icon": "💡", "description": "Electric cyan luminous glow with subtle pulsing flicker on frosted glass"},
        {"id": "typewriter_terminal", "name": "Typewriter Terminal", "category": "tech", "tag": "Tech / Dev", "icon": "💻", "description": "Retro monospace terminal console with cyan prompt and blinking cursor"},
        {"id": "paper_cutout", "name": "Paper Cutout", "category": "editorial", "tag": "Vlog / Craft", "icon": "✂️", "description": "Angled (-2.5°) kraft-paper torn note with translucent washi tape overlay"},
        {"id": "glitch_kinetic", "name": "Glitch Kinetic", "category": "bold", "tag": "Glitch", "icon": "💥", "description": "High-energy chromatic aberration with cyan/magenta split RGB layers"},
        {"id": "quote_editorial", "name": "Quote Editorial", "category": "editorial", "tag": "Luxury", "icon": "📰", "description": "Magazine editorial serif typography with oversized warm amber quotation mark"},
        {"id": "comic_bubble", "name": "Comic Bubble", "category": "pop", "tag": "Pop Art", "icon": "💬", "description": "Pop-art comic book speech bubble with bold 3.5px black stroke and tail pointer"},
        {"id": "gradient_outline", "name": "Gradient Outline", "category": "bold", "tag": "Modern", "icon": "🌈", "description": "Iridescent pink/purple gradient-bordered capsule with subtle glow"},
        {"id": "minimal_underline", "name": "Minimal Underline", "category": "minimal", "tag": "Clean Swiss", "icon": "✨", "description": "Swiss minimalist typography with an animated expanding gradient underline bar"},
        {"id": "blob_card", "name": "Blob Card", "category": "editorial", "tag": "Organic", "icon": "🫧", "description": "Organic morphing SVG blob card with smooth spring pop-in"},
        {"id": "serif_title", "name": "Serif Title", "category": "editorial", "tag": "Editorial", "icon": "🏛️", "description": "Editorial Fraunces serif with oval hand-drawn doodle & keyword pills"},
        {"id": "numbered_point", "name": "Numbered Point", "category": "editorial", "tag": "List / Step", "icon": "🔢", "description": "Italic serif numeral badge with hand-drawn circle doodle for lists & steps"},
        {"id": "handwritten", "name": "Handwritten", "category": "editorial", "tag": "Casual Aside", "icon": "✍️", "description": "Caveat script typography with soft dark shadow for commentary or asides"},
        {"id": "arc_letters", "name": "Arc Letters", "category": "pop", "tag": "Curved", "icon": "🪐", "description": "Curved letter placement along an arc with pastel colors and floating bounce"},
        {"id": "sticker", "name": "Sticker Badge", "category": "pop", "tag": "Graphic", "icon": "🏷️", "description": "Lucide vector icon badge with drop-shadow glow and spring float"},
        {"id": "pill_word", "name": "Pill Word", "category": "minimal", "tag": "Synced Sub", "icon": "💊", "description": "Word-synced high-contrast spoken-word active pill"},
        {"id": "beast_impact", "name": "MrBeast Impact", "category": "bold", "tag": "Viral Hook", "icon": "⚡", "description": "MrBeast high-energy pop with 3D black stroke, lime & cyber-yellow punch"},
        {"id": "highlighter_marker", "name": "Ali Marker", "category": "minimal", "tag": "Educational", "icon": "🖍️", "description": "Ali Abdaal clean minimal text with animated pastel yellow highlighter sweep"},
        {"id": "cinematic_minimal", "name": "Cinematic A24", "category": "editorial", "tag": "Documentary", "icon": "🎬", "description": "A24 / Netflix widescreen frosted glass subtitle pill with amber warmth"},
        {"id": "cyber_hud", "name": "Cyberpunk HUD", "category": "tech", "tag": "Sci-Fi HUD", "icon": "🤖", "description": "Futuristic telemetry brackets, monospace console font, and electric cyan scanlines"},
    ]
    return {"styles": styles_meta, "total": len(styles_meta)}


@app.get("/api/jobs/{job_id}/export/srt")
def export_job_srt(job_id: str):
    """Export video captions as SubRip (.srt) subtitle file."""
    from fastapi.responses import Response
    from backend.schemas.timeline import Timeline
    from backend.api.runner import export_timeline_to_srt

    manager = get_job_manager()
    job = manager.get_job(job_id)
    if not job or not job.timeline_file or not Path(job.timeline_file).exists():
        raise HTTPException(status_code=404, detail="Timeline not available for export")

    tl_data = json.loads(Path(job.timeline_file).read_text(encoding="utf-8"))
    timeline = Timeline.model_validate(tl_data)
    srt_content = export_timeline_to_srt(timeline)

    return Response(
        content=srt_content,
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{job_id}.srt"'},
    )


@app.get("/api/jobs/{job_id}/export/vtt")
def export_job_vtt(job_id: str):
    """Export video captions as WebVTT (.vtt) subtitle file."""
    from fastapi.responses import Response
    from backend.schemas.timeline import Timeline
    from backend.api.runner import export_timeline_to_vtt

    manager = get_job_manager()
    job = manager.get_job(job_id)
    if not job or not job.timeline_file or not Path(job.timeline_file).exists():
        raise HTTPException(status_code=404, detail="Timeline not available for export")

    tl_data = json.loads(Path(job.timeline_file).read_text(encoding="utf-8"))
    timeline = Timeline.model_validate(tl_data)
    vtt_content = export_timeline_to_vtt(timeline)

    return Response(
        content=vtt_content,
        media_type="text/vtt; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{job_id}.vtt"'},
    )


@app.api_route("/api/sample", methods=["GET", "HEAD"])
def get_sample_video():
    """Return the synthetic sample video for testing."""
    sample_path = Path("samples/synthetic.mp4").resolve()
    if not sample_path.exists():
        raise HTTPException(status_code=404, detail="Synthetic sample video not found")
    return FileResponse(
        path=sample_path,
        media_type="video/mp4",
        filename="sample.mp4",
    )


@app.get("/api/storage/status")
def storage_status():
    """Return disk storage usage metrics for jobs and public assets."""
    from backend.pipeline.render import get_remotion_dir
    rem_dir = get_remotion_dir()
    manager = get_job_manager()

    def get_dir_size(path: Path) -> int:
        if not path.exists():
            return 0
        return sum(f.stat().st_size for f in path.rglob('*') if f.is_file())

    jobs_size = get_dir_size(manager.jobs_dir)
    pub_size = get_dir_size(rem_dir / "public" / "jobs")
    build_pub_size = get_dir_size(rem_dir / "build" / "public" / "jobs")

    total_bytes = jobs_size + pub_size + build_pub_size
    return {
        "total_mb": round(total_bytes / (1024 * 1024), 2),
        "jobs_dir_mb": round(jobs_size / (1024 * 1024), 2),
        "remotion_public_mb": round(pub_size / (1024 * 1024), 2),
        "remotion_build_mb": round(build_pub_size / (1024 * 1024), 2),
        "total_jobs": len(manager.jobs),
    }


@app.post("/api/storage/cleanup")
def cleanup_storage(max_kept_jobs: int = 15):
    """Prune historical jobs and orphaned public assets to reclaim disk space."""
    manager = get_job_manager()
    return manager.cleanup_storage(max_kept_jobs=max_kept_jobs)


# Mount frontend single page application
frontend_dir = Path(__file__).resolve().parent.parent.parent / "frontend"
if frontend_dir.exists():
    from fastapi.staticfiles import StaticFiles
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
