"""Comprehensive integration tests verifying every frontend component connects to the backend."""
import io
import re
from pathlib import Path
from fastapi.testclient import TestClient
from backend.api.app import app

client = TestClient(app)


def test_frontend_dom_elements_exist_in_html():
    """Verify all DOM element IDs referenced in app.js actually exist in index.html."""
    res = client.get("/")
    assert res.status_code == 200
    html = res.text

    # Key DOM IDs required by app.js and rendered in index.html
    required_ids = [
        # File & Upload
        "videoFileInput", "browseBtn", "dropZone", "removeFileBtn", "loadSampleBtn", "quickSampleBtn",
        "fileName", "fileSize", "fileBadge", "dropPrompt",
        # Trimmer
        "trimTrackWrapper", "trimShadeLeft", "trimWindow", "trimHandleLeft", "trimHandleRight",
        "trimShadeRight", "trimPlayhead", "trimReadout", "trimStartBadge", "trimEndBadge", "trimDurBadge",
        # Layout & Aspect Ratio
        "phoneCanvas", "stageStatus", "layoutPhotoModal", "btnOpenPhotoModal", "btnClosePhotoModal",
        # AI Director & LLM
        "llmProvider", "aiDirectorBadge", "aiEnhanceToggle", "apiKeySection", "apiKeyInput",
        "toggleApiKeyVisibility", "saveApiKeyBtn", "apiKeySavedBadge",
        # Subtitles & Customization
        "videoLanguage", "subPosSlider", "subPosLabel", "captionSizeSlider",
        "draftToggle", "startJobBtn", "btnProgressFill", "btnTextLabel",
        # Viral Boosters
        "headlineHookToggle", "headlineHookInput", "headlineHookSettings", "progressBarToggle",
        "progBarBottomBtn", "progBarTopBtn", "autoEmojisToggle",
        # Pipeline Progress
        "pipelineProgressCard", "pipelineProgressTitle", "pipelineProgressPct", "pipelineProgressFill",
        "pipelineProgressDesc", "pipelineProgressTime",
        # Results & Actions
        "resultVideo", "downloadMp4Btn", "downloadSrtBtn", "downloadVttBtn", "resetBtn", "closeResultBtn",
        # Editor & Re-render
        "editorCard", "eventCount", "phrasesList", "saveEditsBtn", "rerenderBtn", "toast"
    ]

    missing = [elem_id for elem_id in required_ids if f'id="{elem_id}"' not in html]
    assert not missing, f"Missing DOM IDs in index.html: {missing}"


def test_api_health_endpoint():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_api_sample_endpoint():
    res = client.get("/api/sample")
    assert res.status_code == 200
    assert len(res.content) > 1000
    assert res.headers["content-type"].startswith("video/")


def test_api_styles_endpoint():
    res = client.get("/api/styles")
    assert res.status_code == 200
    data = res.json()
    assert "styles" in data
    assert data["total"] == 24
    style_ids = [s["id"] for s in data["styles"]]
    assert "hormozi_bold" in style_ids
    assert "beast_impact" in style_ids
    assert "highlighter_marker" in style_ids


def test_full_job_lifecycle_with_all_frontend_options(tmp_path):
    """Test job submission with every single parameter configured by the frontend."""
    # 1. Fetch sample video bytes to use as test file
    sample_res = client.get("/api/sample")
    video_bytes = sample_res.content

    files = {"file": ("test_clip.mp4", io.BytesIO(video_bytes), "video/mp4")}
    data = {
        "preset": "bold_creator",
        "llm_provider": "mistral",
        "ai_enhance": "true",
        "api_key": "test_dummy_key",
        "language": "en",
        "aspect_ratio": "9:16",
        "subtitle_position": "lower",
        "caption_size": "medium",
        "background_style": "glass",
        "style_pacing": "sentence",
        "highlight_color": "#38BDF8",
        "selected_styles": "hormozi_bold,beast_impact,highlighter_marker",
        "subtitle_y": "0.79",
        "video_layout": "split_podcast",
        "progress_bar": "true",
        "progress_bar_position": "bottom",
        "headline_hook": "🔥 WATCH TILL THE END",
        "headline_style": "badge",
        "auto_emojis": "true",
        "draft": "true",
        "trim_start": "0.0",
        "trim_end": "5.0",
    }

    # 2. Submit job (create_job)
    create_res = client.post("/api/jobs", files=files, data=data)
    assert create_res.status_code == 201
    job = create_res.json()
    job_id = job["id"]
    assert job["preset"] == "bold_creator"
    assert job["llm_provider"] == "mistral"
    assert job["ai_enhance"] is True
    assert job["video_layout"] == "split_podcast"
    assert job["headline_hook"] == "🔥 WATCH TILL THE END"

    # 3. Poll job status
    poll_res = client.get(f"/api/jobs/{job_id}")
    assert poll_res.status_code == 200
    assert poll_res.json()["id"] == job_id

    # 4. Cancel job
    cancel_res = client.post(f"/api/jobs/{job_id}/cancel")
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "cancelled"
    post_cancel = client.get(f"/api/jobs/{job_id}").json()
    assert post_cancel["status"] == "failed"
    assert "Cancelled" in post_cancel["error"]
