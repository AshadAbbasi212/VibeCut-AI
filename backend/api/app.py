"""FastAPI application for Dynamic Captions Studio."""
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, status
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
    trim_start: Optional[float] = Form(None),
    trim_end: Optional[float] = Form(None),
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
            trim_start=trim_start,
            trim_end=trim_end,
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


@app.get("/api/jobs/{job_id}/output")
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


@app.get("/api/styles")
def list_styles():
    """Return all available caption styles with metadata."""
    styles_meta = [
        {"id": "title3d", "name": "3D Title", "category": "bold", "tag": "High Energy", "description": "Extruded 3D shadow, multi-line vertical gradients, twinkling stars"},
        {"id": "neon_glow", "name": "Neon Glow", "category": "bold", "tag": "Cyberpunk", "description": "Electric cyan luminous glow with subtle pulsing flicker on frosted glass"},
        {"id": "typewriter_terminal", "name": "Typewriter Terminal", "category": "tech", "tag": "Tech / Dev", "description": "Retro monospace terminal console with cyan prompt and blinking cursor"},
        {"id": "paper_cutout", "name": "Paper Cutout", "category": "editorial", "tag": "Vlog / Craft", "description": "Angled (-2.5°) kraft-paper torn note with translucent washi tape overlay"},
        {"id": "glitch_kinetic", "name": "Glitch Kinetic", "category": "bold", "tag": "Glitch", "description": "High-energy chromatic aberration with cyan/magenta split RGB layers"},
        {"id": "quote_editorial", "name": "Quote Editorial", "category": "editorial", "tag": "Luxury", "description": "Magazine editorial serif typography with oversized warm amber quotation mark"},
        {"id": "comic_bubble", "name": "Comic Bubble", "category": "pop", "tag": "Pop Art", "description": "Pop-art comic book speech bubble with bold 3.5px black stroke and tail pointer"},
        {"id": "gradient_outline", "name": "Gradient Outline", "category": "bold", "tag": "Modern", "description": "Iridescent pink/purple gradient-bordered capsule with subtle glow"},
        {"id": "minimal_underline", "name": "Minimal Underline", "category": "minimal", "tag": "Clean Swiss", "description": "Swiss minimalist typography with an animated expanding gradient underline bar"},
        {"id": "blob_card", "name": "Blob Card", "category": "editorial", "tag": "Organic", "description": "Organic morphing SVG blob card with smooth spring pop-in"},
        {"id": "serif_title", "name": "Serif Title", "category": "editorial", "tag": "Editorial", "description": "Editorial Fraunces serif with oval hand-drawn doodle & keyword pills"},
        {"id": "numbered_point", "name": "Numbered Point", "category": "editorial", "tag": "List / Step", "description": "Italic serif numeral badge with hand-drawn circle doodle for lists & steps"},
        {"id": "handwritten", "name": "Handwritten", "category": "editorial", "tag": "Casual Aside", "description": "Caveat script typography with soft dark shadow for commentary or asides"},
        {"id": "arc_letters", "name": "Arc Letters", "category": "pop", "tag": "Curved", "description": "Curved letter placement along an arc with pastel colors and floating bounce"},
        {"id": "sticker", "name": "Sticker Badge", "category": "pop", "tag": "Graphic", "description": "Lucide vector icon badge with drop-shadow glow and spring float"},
        {"id": "pill_word", "name": "Pill Word", "category": "minimal", "tag": "Synced Sub", "description": "Word-synced high-contrast spoken-word active pill"},
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


@app.get("/api/sample")
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


# Mount frontend single page application
frontend_dir = Path(__file__).resolve().parent.parent.parent / "frontend"
if frontend_dir.exists():
    from fastapi.staticfiles import StaticFiles
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
