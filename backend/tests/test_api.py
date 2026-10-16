"""Tests for Phase 7 FastAPI endpoints and job runner."""
import io
import time
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from backend.api.app import app
from backend.api.runner import get_job_manager, JobInfo


@pytest.fixture
def client():
    return TestClient(app)


def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_get_nonexistent_job(client):
    response = client.get("/api/jobs/non_existent_job_12345")
    assert response.status_code == 404


def test_job_submission_and_polling(client, tmp_path):
    # Create a small dummy video file for upload testing
    dummy_video = tmp_path / "test_dummy.mp4"
    dummy_video.write_bytes(b"dummy mp4 container bytes for upload test")

    with open(dummy_video, "rb") as f:
        response = client.post(
            "/api/jobs",
            files={"file": ("test_dummy.mp4", f, "video/mp4")},
            data={"preset": "bold_creator", "llm_provider": "none", "language": "en"},
        )

    assert response.status_code == 201
    job_data = response.json()
    job_id = job_data["id"]
    assert job_id.startswith("job_")
    assert job_data["status"] in {"queued", "processing", "failed"}

    # Poll status
    status_resp = client.get(f"/api/jobs/{job_id}")
    assert status_resp.status_code == 200
    polled = status_resp.json()
    assert polled["id"] == job_id


def test_job_timeline_and_output_routes(client, tmp_path):
    manager = get_job_manager()
    job_id = "job_mock_completed"
    job_dir = manager.jobs_dir / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    dummy_out = job_dir / "output.mp4"
    dummy_out.write_bytes(b"\x00\x00\x00 ftypisom\x00\x00\x02\x00isomiso2mp41")

    dummy_tl = job_dir / "timeline.json"
    dummy_tl.write_text('{"version": 1, "video": {"src": "input.mp4", "width": 1080, "height": 1920, "fps": 30, "durationSec": 5}, "events": []}')

    job = JobInfo(
        id=job_id,
        status="completed",
        step="completed",
        progress=1.0,
        output_file=str(dummy_out),
        timeline_file=str(dummy_tl),
    )
    manager.save_job(job)

    # 1. Timeline endpoint
    tl_resp = client.get(f"/api/jobs/{job_id}/timeline")
    assert tl_resp.status_code == 200
    assert tl_resp.json()["version"] == 1

    # 2. Output download endpoint
    out_resp = client.get(f"/api/jobs/{job_id}/output")
    assert out_resp.status_code == 200
    assert out_resp.headers["content-type"] == "video/mp4"
    assert len(out_resp.content) > 0


def test_download_incomplete_job_fails(client):
    manager = get_job_manager()
    job_id = "job_mock_processing"
    job = JobInfo(
        id=job_id,
        status="processing",
        step="rendering",
        progress=0.75,
    )
    manager.save_job(job)

    out_resp = client.get(f"/api/jobs/{job_id}/output")
    assert out_resp.status_code == 400
    assert "not completed yet" in out_resp.json()["detail"]


def test_frontend_serving(client):
    root_resp = client.get("/")
    assert root_resp.status_code == 200
    assert "Dynamic Captions" in root_resp.text
    assert "style.css" in root_resp.text
    assert "app.js" in root_resp.text


def test_sample_video_endpoint(client):
    sample_resp = client.get("/api/sample")
    assert sample_resp.status_code == 200
    assert sample_resp.headers["content-type"] == "video/mp4"
    assert len(sample_resp.content) > 0
