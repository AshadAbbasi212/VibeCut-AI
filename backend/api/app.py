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
