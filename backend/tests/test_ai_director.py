"""Tests for AI Director, Mistral planner, and scene analysis."""
import json
import pytest
from pathlib import Path
from backend.pipeline.chunk import Phrase
from backend.pipeline.transcribe import Word
from backend.pipeline.plan_llm import (
    get_planner,
    MistralPlanner,
    RulePlanner,
    _build_scene_aware_prompt,
    _build_base_events,
    _validate_and_parse_llm_json,
)
from backend.pipeline.analyze import (
    VideoAnalysis,
    SceneInfo,
    ExistingCaption,
    TopicSegment,
    _parse_json_response,
    analyze_video,
)


def _make_sample_phrases():
    w1 = Word(i=0, text="Welcome", start=0.0, end=0.5, probability=0.99)
    w2 = Word(i=1, text="to", start=0.5, end=0.7, probability=0.99)
    w3 = Word(i=2, text="my", start=0.7, end=0.9, probability=0.99)
    w4 = Word(i=3, text="podcast.", start=0.9, end=1.5, probability=0.99)
    w5 = Word(i=4, text="The", start=2.0, end=2.2, probability=0.99)
    w6 = Word(i=5, text="first", start=2.2, end=2.5, probability=0.99)
    w7 = Word(i=6, text="secret", start=2.5, end=3.0, probability=0.99)
    w8 = Word(i=7, text="is", start=3.0, end=3.2, probability=0.99)
    w9 = Word(i=8, text="focus.", start=3.2, end=3.8, probability=0.99)

    p1 = Phrase(
        id="p1",
        words=[w1, w2, w3, w4],
        start=0.0,
        end=1.5,
        speech_start=0.0,
        speech_end=1.5,
        word_indices=[0, 1, 2, 3],
        text="Welcome to my podcast.",
    )
    p2 = Phrase(
        id="p2",
        words=[w5, w6, w7, w8, w9],
        start=2.0,
        end=3.8,
        speech_start=2.0,
        speech_end=3.8,
        word_indices=[4, 5, 6, 7, 8],
        text="The first secret is focus.",
    )
    return [p1, p2]


def test_mistral_planner_fallback_without_key():
    planner = MistralPlanner(api_key=None)
    phrases = _make_sample_phrases()
    events = planner.plan(phrases, video_duration=4.0)
    assert len(events) >= 2
    # Base event should be present
    assert any(ev.id.startswith("base_") for ev in events)


def test_planner_factory_resolves_mistral():
    planner = get_planner(provider="mistral", api_key="test_key")
    assert isinstance(planner, MistralPlanner)
    assert planner.api_key == "test_key"


def test_scene_aware_prompt_generation():
    phrases = _make_sample_phrases()
    scene_data = {
        "video_type": "podcast",
        "dominant_mood": "educational",
        "num_speakers": 2,
        "has_burned_in_captions": True,
        "existing_captions": [
            {"start": 0.0, "end": 1.5, "text": "Episode 1: The Intro", "region": "upper"}
        ],
        "topic_segments": [
            {"start": 2.0, "end": 3.8, "title": "Secret 1: Focus", "importance": "heading", "energy": "high"}
        ],
    }

    prompt = _build_scene_aware_prompt(phrases, "bold_creator", scene_data)
    assert prompt is not None
    assert "podcast" in prompt
    assert "educational" in prompt
    assert "Episode 1: The Intro" in prompt
    assert "Secret 1: Focus" in prompt
    assert "DO NOT generate feature events overlapping" in prompt


def test_build_base_events_skips_burned_in_captions():
    phrases = _make_sample_phrases()
    # Scenario: first phrase 0.0 - 1.5 overlaps with existing burned-in caption
    scene_data = {
        "has_burned_in_captions": True,
        "existing_captions": [
            {"start": 0.0, "end": 1.5, "text": "Episode 1", "region": "upper"}
        ],
    }

    events = _build_base_events(phrases, scene_data)
    # Phrase p1 (0.0 to 1.5) should be skipped!
    phrase_ids = [ev.id for ev in events]
    assert "base_p1" not in phrase_ids
    assert "base_p2" in phrase_ids


def test_build_base_events_keeps_subtitles_on_watermarks():
    phrases = _make_sample_phrases()
    # Scenario: stationary podcast watermark spanning 0.0 - 60.0s
    scene_data = {
        "has_burned_in_captions": True,
        "existing_captions": [
            {"start": 0.0, "end": 60.0, "text": "BIG TECHNOLOGY PODCAST logo", "region": "lower"}
        ],
    }

    events = _build_base_events(phrases, scene_data)
    phrase_ids = [ev.id for ev in events]
    # Watermarks should NOT suppress spoken subtitles
    assert "base_p1" in phrase_ids
    assert "base_p2" in phrase_ids
    assert len(events) == 2


def test_parse_json_response_helper():
    # Test wrapped in markdown fence
    fenced = '```json\n{"video_type": "podcast", "num_speakers": 2}\n```'
    parsed = _parse_json_response(fenced)
    assert parsed == {"video_type": "podcast", "num_speakers": 2}

    # Test with surrounding conversational text
    messy = 'Here is the analysis:\n{"dominant_mood": "excited"}\nHope this helps!'
    parsed = _parse_json_response(messy)
    assert parsed == {"dominant_mood": "excited"}


def test_analyze_video_none_provider(tmp_path):
    dummy_video = tmp_path / "dummy.mp4"
    dummy_video.write_bytes(b"dummy")
    result = analyze_video(dummy_video, [], provider="none")
    assert isinstance(result, VideoAnalysis)
    assert len(result.scenes) == 0
    assert result.has_burned_in_captions is False


def test_api_accepts_ai_enhance_and_api_key(client=None):
    from fastapi.testclient import TestClient
    from backend.api.app import app
    client = TestClient(app)

    # Health check
    res = client.get("/api/health")
    assert res.status_code == 200
