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


def test_export_srt_and_vtt(client, tmp_path):
    manager = get_job_manager()
    job_id = "job_mock_export"
    job_dir = manager.jobs_dir / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    timeline_content = """{
      "version": 1,
      "video": {"src": "input.mp4", "width": 1080, "height": 1920, "fps": 30, "durationSec": 5},
      "words": [],
      "events": [
        {"id": "e1", "style": "pill_word", "start": 0.5, "end": 2.0, "zone": "lower", "text": "First subtitle line"},
        {"id": "e2", "style": "neon_glow", "start": 2.2, "end": 4.5, "zone": "center", "text": "Second subtitle line"}
      ]
    }"""
    dummy_tl = job_dir / "timeline.json"
    dummy_tl.write_text(timeline_content)

    job = JobInfo(
        id=job_id,
        status="completed",
        step="completed",
        progress=1.0,
        timeline_file=str(dummy_tl),
    )
    manager.save_job(job)

    # Test SRT export
    srt_resp = client.get(f"/api/jobs/{job_id}/export/srt")
    assert srt_resp.status_code == 200
    assert "00:00:00,500 --> 00:00:02,000" in srt_resp.text
    assert "First subtitle line" in srt_resp.text
    assert "00:00:02,200 --> 00:00:04,500" in srt_resp.text
    assert "Second subtitle line" in srt_resp.text

    # Test VTT export
    vtt_resp = client.get(f"/api/jobs/{job_id}/export/vtt")
    assert vtt_resp.status_code == 200
    assert "WEBVTT" in vtt_resp.text
    assert "00:00:00.500 --> 00:00:02.000" in vtt_resp.text
    assert "First subtitle line" in vtt_resp.text


def test_update_timeline(client, tmp_path):
    manager = get_job_manager()
    job_id = "job_mock_edit"
    job_dir = manager.jobs_dir / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    dummy_tl = job_dir / "timeline.json"
    dummy_tl.write_text('{"version": 1, "video": {"src": "input.mp4", "width": 1080, "height": 1920, "fps": 30, "durationSec": 5}, "words": [], "events": []}')

    job = JobInfo(
        id=job_id,
        status="completed",
        step="completed",
        timeline_file=str(dummy_tl),
    )
    manager.save_job(job)

    updated_payload = {
        "version": 1,
        "video": {"src": "input.mp4", "width": 1080, "height": 1920, "fps": 30, "durationSec": 5},
        "words": [],
        "events": [
            {"id": "edited_e1", "style": "typewriter_terminal", "start": 0.5, "end": 2.5, "zone": "center", "text": "Edited caption text"}
        ]
    }
    put_resp = client.put(f"/api/jobs/{job_id}/timeline", json=updated_payload)
    assert put_resp.status_code == 200
    assert put_resp.json()["status"] == "ok"

    # Re-fetch timeline
    get_resp = client.get(f"/api/jobs/{job_id}/timeline")
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert len(data["events"]) == 1
    assert data["events"][0]["text"] == "Edited caption text"


def test_list_styles(client):
    resp = client.get("/api/styles")
    assert resp.status_code == 200
    data = resp.json()
    assert "styles" in data
    assert data["total"] == 16
    style_ids = [s["id"] for s in data["styles"]]
    assert "neon_glow" in style_ids
    assert "typewriter_terminal" in style_ids
    assert "comic_bubble" in style_ids
    assert "title3d" in style_ids


def test_rerender_endpoint(client, monkeypatch):
    manager = get_job_manager()
    job_id = "job_mock_rerender"
    job_dir = manager.jobs_dir / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    dummy_tl = job_dir / "timeline.json"
    dummy_tl.write_text('{"version": 1, "video": {"src": "input.mp4", "width": 1080, "height": 1920, "fps": 30, "durationSec": 5}, "words": [], "events": []}')

    job = JobInfo(
        id=job_id,
        status="completed",
        step="completed",
        timeline_file=str(dummy_tl),
    )
    manager.save_job(job)

    # Monkeypatch executor to avoid real rendering in unit test
    called = []
    monkeypatch.setattr(manager.executor, "submit", lambda fn, *args: called.append(args[0]))

    resp = client.post(f"/api/jobs/{job_id}/rerender", data={"draft": "true"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == job_id
    assert data["draft"] is True
    assert len(called) == 1
    assert called[0] == job_id


def test_job_submission_customization_options(client, tmp_path, monkeypatch):
    manager = get_job_manager()
    dummy_video = tmp_path / "test_custom.mp4"
    dummy_video.write_bytes(b"dummy mp4 container bytes for upload test")

    # Monkeypatch executor to avoid spawning real background pipeline task on dummy bytes
    monkeypatch.setattr(manager.executor, "submit", lambda fn, *args: None)

    with open(dummy_video, "rb") as f:
        response = client.post(
            "/api/jobs",
            files={"file": ("test_custom.mp4", f, "video/mp4")},
            data={
                "preset": "bold_creator",
                "caption_size": "large",
                "background_style": "glass",
                "style_pacing": "sentence",
                "highlight_color": "#EF4444",
            },
        )

    assert response.status_code == 201
    job_data = response.json()
    assert job_data["caption_size"] == "large"
    assert job_data["background_style"] == "glass"
    assert job_data["style_pacing"] == "sentence"
    assert job_data["highlight_color"] == "#EF4444"



