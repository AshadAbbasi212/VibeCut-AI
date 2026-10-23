"""Tests for Phase 29: Optional Watermark, Headline Y Positioning, AI Smart Style, and Single Clip Rendering."""
import json
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from backend.api.app import app
from backend.api.runner import get_job_manager, JobInfo
from backend.schemas.timeline import Timeline, TimelineVideo, TimelineWord, TimelineEvent
from backend.pipeline.clips import slice_timeline_for_clip


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_parent_job(tmp_path, monkeypatch):
    """Create a mock parent job with valid timeline and input video for clip testing."""
    manager = get_job_manager()
    job_id = "job_test_parent_clips"
    job_dir = Path("jobs").resolve() / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    input_video = job_dir / "input.mp4"
    if not input_video.exists():
        input_video.write_bytes(b"\x00" * 1024)  # Stub video file

    sample_video = TimelineVideo(
        src="temp/input.mp4",
        fps=30,
        durationSec=60.0,
        layout="fill",
        originalWidth=1080,
        originalHeight=1920,
    )
    sample_words = [
        TimelineWord(i=0, text="Welcome", start=0.5, end=1.0),
        TimelineWord(i=1, text="to", start=1.1, end=1.3),
        TimelineWord(i=2, text="our", start=1.4, end=1.6),
        TimelineWord(i=3, text="podcast", start=1.7, end=2.4),
        TimelineWord(i=4, text="today", start=2.5, end=3.0),
        TimelineWord(i=5, text="viral", start=10.0, end=10.5),
        TimelineWord(i=6, text="moment", start=10.6, end=11.2),
        TimelineWord(i=7, text="right", start=11.3, end=11.6),
        TimelineWord(i=8, text="here", start=11.7, end=12.2),
    ]
    sample_events = [
        TimelineEvent(id="ev_0", start=0.5, end=3.0, text="Welcome to our podcast today", style="beast_impact", wordRange=[0, 4]),
        TimelineEvent(id="ev_1", start=10.0, end=12.2, text="viral moment right here", style="hormozi_bold", wordRange=[5, 8]),
    ]

    timeline = Timeline(
        version=1,
        video=sample_video,
        language="en",
        words=sample_words,
        events=sample_events,
        captionSize="medium",
        headlineHook="PARENT HOOK",
        headlineStyle="badge",
        headlineY=0.08,
    )

    timeline_file = job_dir / "timeline.json"
    timeline_file.write_text(json.dumps(timeline.model_dump(by_alias=True, exclude_none=True), indent=2), encoding="utf-8")

    job = JobInfo(
        id=job_id,
        status="completed",
        step="completed",
        progress=1.0,
        input_file=str(input_video),
        timeline_file=str(timeline_file),
    )
    manager.jobs[job_id] = job
    manager.save_job(job)
    return job_id, timeline


def test_slice_timeline_with_tweaker_parameters(mock_parent_job):
    """Verify slice_timeline_for_clip applies all new tweaker options (headline location, AI styles, watermark)."""
    job_id, base_timeline = mock_parent_job

    sliced = slice_timeline_for_clip(
        timeline=base_timeline,
        clip_start=10.0,
        clip_end=12.5,
        clip_headline="🔥 CUSTOM HEADLINE",
        clip_headline_style="cyber",
        clip_headline_duration=5.0,
        clip_headline_y=0.25,
        caption_size="large",
        subtitle_y=0.50,
        selected_styles="ai_auto",
        watermark_text="@creator",
        kinetic_zoom=True,
        sound_effects=True,
        bg_music="lofi",
        progress_bar=True,
        auto_emojis=True,
    )

    assert sliced.video.durationSec == 2.5
    assert sliced.headlineHook == "🔥 CUSTOM HEADLINE"
    assert sliced.headlineStyle == "cyber"
    assert sliced.headlineDuration == 5.0
    assert sliced.headlineY == 0.25
    assert sliced.watermarkText == "@creator"
    assert sliced.kineticZoom is True
    assert sliced.soundEffects is True
    assert sliced.bgMusic == "lofi"

    # Verify event shifting and style assignment
    assert len(sliced.events) == 1
    ev = sliced.events[0]
    assert ev.start == 0.0
    assert round(ev.end, 1) == 2.2
    assert ev.captionSize == "large"
    assert ev.subtitleY == 0.50
    # For short clip <= 20s, AI auto assigns beast_impact or hormozi_bold
    assert ev.style in ["beast_impact", "hormozi_bold"]


def test_optional_watermark_toggle_none(mock_parent_job):
    """Verify watermark is optional and omitted when set to None or empty string."""
    job_id, base_timeline = mock_parent_job

    sliced_none = slice_timeline_for_clip(
        timeline=base_timeline,
        clip_start=10.0,
        clip_end=12.5,
        watermark_text=None,
    )
    assert sliced_none.watermarkText is None

    sliced_empty = slice_timeline_for_clip(
        timeline=base_timeline,
        clip_start=10.0,
        clip_end=12.5,
        watermark_text="",
    )
    assert sliced_empty.watermarkText is None


def test_render_clip_endpoint(client, mock_parent_job, monkeypatch):
    """Test POST /api/jobs/{job_id}/render-clip endpoint creates a render job without re-uploading."""
    job_id, _ = mock_parent_job

    # Mock ffmpeg and render so test doesn't launch actual long ffmpeg process
    def mock_subprocess_run(cmd, *args, **kwargs):
        target = cmd[-1]
        Path(target).touch()
        return None

    monkeypatch.setattr("subprocess.run", mock_subprocess_run)
    monkeypatch.setattr("backend.pipeline.render.prepare_video_asset", lambda p, job_id: f"temp/{job_id}.mp4")
    monkeypatch.setattr("backend.pipeline.render.render", lambda *args, **kwargs: None)
    monkeypatch.setattr("backend.api.runner.JobManager._run_clip_render_task", lambda self, jid: None)

    payload = {
        "start": 10.0,
        "end": 12.5,
        "headline": "🔥 VIRAL HIGHLIGHT HOOK",
        "headline_style": "glass",
        "headline_duration": 10.0,
        "headline_y": 0.42,
        "caption_size": "large",
        "subtitle_y": 0.50,
        "selected_styles": "beast_impact",
        "watermark_text": "@testbrand",
        "video_layout": "split_podcast",
        "ai_enhance": True,
        "kinetic_zoom": True,
        "sound_effects": True,
        "bg_music": "lofi",
        "progress_bar": True,
        "auto_emojis": True,
    }

    resp = client.post(f"/api/jobs/{job_id}/render-clip", json=payload)
    assert resp.status_code == 201
    data = resp.json()

    assert data["id"].startswith("job_clip_")
    assert data["status"] in ["queued", "processing", "completed"]
    assert data["headline_hook"] == "🔥 VIRAL HIGHLIGHT HOOK"
    assert data["headline_style"] == "glass"
    assert data["headline_y"] == 0.42
    assert data["watermark_text"] == "@testbrand"
    assert data["video_layout"] == "split_podcast"
    assert data["ai_enhance"] is True


def test_slice_timeline_reframe_and_scene_analysis(mock_parent_job):
    """Verify slice_timeline_for_clip sets chosen layout and recalculates scene-aware active speaker cuts."""
    job_id, base_timeline = mock_parent_job

    # 1. Test split_podcast layout (clears dynamic cuts so remotion uses split stack)
    sliced_split = slice_timeline_for_clip(
        timeline=base_timeline,
        clip_start=10.0,
        clip_end=12.5,
        video_layout="split_podcast",
    )
    assert sliced_split.video.layout == "split_podcast"
    assert sliced_split.videoLayout == "split_podcast"
    assert sliced_split.cameraCuts is None

    # 2. Test blur_fit layout
    sliced_blur = slice_timeline_for_clip(
        timeline=base_timeline,
        clip_start=10.0,
        clip_end=12.5,
        video_layout="blur_fit",
    )
    assert sliced_blur.video.layout == "blur_fit"
    assert sliced_blur.videoLayout == "blur_fit"
    assert sliced_blur.cameraCuts is None

    # 3. Test active_speaker layout with scene_analysis
    scene_data = {
        "num_speakers": 1,
        "scenes": [
            {
                "timestamp": 0.0,
                "speakers": [{"position": "center", "is_speaking": True}],
                "description": "Solo speaker centered",
            }
        ],
    }
    sliced_active = slice_timeline_for_clip(
        timeline=base_timeline,
        clip_start=10.0,
        clip_end=12.5,
        video_layout="active_speaker",
        ai_enhance=True,
        scene_analysis=scene_data,
    )
    assert sliced_active.video.layout == "active_speaker"
    assert sliced_active.cameraCuts is not None
    assert len(sliced_active.cameraCuts) > 0
    # Because scene has centered speaker, focusX is 0.50
    assert sliced_active.cameraCuts[0].focusX == 0.50


def test_slice_timeline_collision_avoidance(mock_parent_job):
    """Verify captions never render behind the headmarker or over the speaker's face."""
    job_id, base_timeline = mock_parent_job

    # Modify base timeline event to have zone='upper' and zone='center'
    ev_upper = base_timeline.events[0].model_copy(update={"zone": "upper", "start": 10.0, "end": 12.0})
    ev_center = base_timeline.events[1].model_copy(update={"zone": "center", "start": 10.0, "end": 12.0})
    modified_tl = base_timeline.model_copy(update={"events": [ev_upper, ev_center]})

    # With headline hook present, upper zone must be sanitized to callout_stack
    sliced = slice_timeline_for_clip(
        timeline=modified_tl,
        clip_start=10.0,
        clip_end=12.5,
        clip_headline="🔥 TOP HEADMARKER",
        highlight_color="#FBBF24",
    )

    for ev in sliced.events:
        assert ev.zone != "upper", "Event must not be placed in 'upper' zone behind headmarker!"
        assert ev.zone == "free"
        assert ev.y == 0.68
        assert ev.highlightColor == "#FBBF24"


def test_slice_timeline_vanishing_headline_and_highlight(mock_parent_job):
    """Verify custom vanishing duration (e.g. 3.0s) and custom highlight color propagate."""
    job_id, base_timeline = mock_parent_job

    sliced = slice_timeline_for_clip(
        timeline=base_timeline,
        clip_start=10.0,
        clip_end=12.5,
        clip_headline="💡 KEY TAKEAWAY",
        clip_headline_duration=3.0,
        highlight_color="#A855F7",
    )

    assert sliced.headlineHook == "💡 KEY TAKEAWAY"
    assert sliced.headlineDuration == 3.0
    assert sliced.highlightColor == "#A855F7"


def test_slice_timeline_ali_abdaal_content_aware_styles(mock_parent_job):
    """Verify Ali Abdaal content-aware style assignment picks numbered_point, typewriter_terminal, highlighter_marker based on text keywords."""
    job_id, base_timeline = mock_parent_job

    ev_step = base_timeline.events[0].model_copy(update={"text": "Step 1: Focus on your core output", "start": 10.0, "end": 12.0})
    ev_tech = base_timeline.events[1].model_copy(update={"text": "The AI model processes 100% of data", "start": 12.0, "end": 14.0})
    modified_tl = base_timeline.model_copy(update={"events": [ev_step, ev_tech]})

    sliced = slice_timeline_for_clip(
        timeline=modified_tl,
        clip_start=10.0,
        clip_end=25.0,
        selected_styles="ai_auto",
    )

    assert sliced.events[0].style == "numbered_point"
    assert sliced.events[1].style == "typewriter_terminal"


