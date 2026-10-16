"""Tests for Remotion rendering and baseline video validation."""
import json
from pathlib import Path
import pytest
from backend.pipeline.probe import probe_video
from backend.schemas.timeline import Timeline


def test_phase3_timeline_validation():
    timeline_path = Path("out/test_timeline_phase3.json")
    if not timeline_path.exists():
        pytest.skip("out/test_timeline_phase3.json not generated yet")

    data = json.loads(timeline_path.read_text(encoding="utf-8"))
    timeline = Timeline.model_validate(data)
    assert timeline.video.width == 1080
    assert timeline.video.height == 1920
    assert len(timeline.events) > 0
    assert all(e.style == "pill_word" for e in timeline.events)


def test_rendered_video_baseline():
    rendered_mp4 = Path("out/phase3_render.mp4")
    if not rendered_mp4.exists():
        pytest.skip("out/phase3_render.mp4 not rendered yet")

    probe = probe_video(rendered_mp4)
    assert probe.width == 1080
    assert probe.height == 1920
    assert probe.fps == 30.0
    assert probe.duration >= 4.9
    assert probe.has_audio is True
