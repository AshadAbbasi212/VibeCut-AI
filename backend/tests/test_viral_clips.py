"""Tests for AI Viral Clips Extractor and Headline Hook Duration."""
import pytest
from fastapi.testclient import TestClient
from backend.api.app import app
from backend.pipeline.clips import find_viral_clips, _snap_to_phrases, ViralClip
from backend.schemas.timeline import Timeline, TimelineVideo, TimelineWord, TimelineEvent


def test_snap_to_phrases():
    phrases = [
        {"start": 0.0, "end": 4.5, "text": "Welcome to the podcast."},
        {"start": 4.8, "end": 14.2, "text": "Today we reveal the secret to success."},
        {"start": 14.5, "end": 28.0, "text": "Nobody tells you how difficult it really is."},
        {"start": 28.4, "end": 45.0, "text": "You must never give up when things fail."},
    ]
    # Exact or near start snap
    s, e = _snap_to_phrases(5.0, 27.5, phrases)
    assert s == 4.8
    assert e == 28.0


def test_rule_based_clip_finder_15s():
    phrases = [
        {"start": 0.0, "end": 4.5, "text": "Welcome everyone to our deep dive session."},
        {"start": 5.0, "end": 10.2, "text": "Why do 99% of startups fail in the first year?"},
        {"start": 10.5, "end": 18.0, "text": "Because they build things nobody wants to buy!"},
        {"start": 18.5, "end": 25.0, "text": "Let us break down the exact math behind product market fit."},
        {"start": 25.5, "end": 35.0, "text": "First, you must validate before writing a single line of code."},
    ]
    clips = find_viral_clips(
        phrases=phrases,
        video_duration=35.0,
        target_length="15s",
        provider="none",
    )
    assert len(clips) > 0
    top = clips[0]
    assert isinstance(top, ViralClip)
    assert top.target_length == "15s"
    assert top.duration >= 8.0 and top.duration <= 25.0
    assert top.headline.startswith("🔥")
    assert top.virality_score >= 6.0


def test_rule_based_clip_finder_30s():
    phrases = [
        {"start": 0.0, "end": 5.0, "text": "Intro talking about random topics."},
        {"start": 6.0, "end": 12.0, "text": "Here is the biggest secret to scaling a business."},
        {"start": 12.5, "end": 20.0, "text": "You have to focus exclusively on customer retention."},
        {"start": 20.5, "end": 32.0, "text": "Never spend money on paid ads before your organic churn is low."},
        {"start": 32.5, "end": 40.0, "text": "That is how we reached 10 million in revenue."},
    ]
    clips = find_viral_clips(
        phrases=phrases,
        video_duration=40.0,
        target_length="30s",
        provider="none",
    )
    assert len(clips) > 0
    for c in clips:
        assert c.target_length == "30s"
        assert c.start >= 0.0
        assert c.end <= 40.0
        assert c.duration == round(c.end - c.start, 2)


def test_timeline_headline_duration_schema():
    # Test Timeline with headlineDuration=5.0
    tl = Timeline(
        version=1,
        video=TimelineVideo(src="video.mp4", width=1080, height=1920, fps=30, durationSec=10.0),
        words=[TimelineWord(i=0, text="test", start=0.0, end=1.0)],
        events=[
            TimelineEvent(
                id="e1",
                style="hormozi_bold",
                start=0.0,
                end=1.0,
                zone="lower",
                wordRange=[0, 0],
                text="test",
            )
        ],
        headlineHook="🔥 DISAPPEARING HOOK",
        headlineStyle="badge",
        headlineDuration=5.0,
    )
    assert tl.headlineDuration == 5.0
    data = tl.model_dump(by_alias=True)
    assert data["headlineDuration"] == 5.0

    # Test Timeline with sticky headline (None)
    tl_sticky = Timeline(
        version=1,
        video=TimelineVideo(src="video.mp4", width=1080, height=1920, fps=30, durationSec=10.0),
        words=[TimelineWord(i=0, text="test", start=0.0, end=1.0)],
        events=[
            TimelineEvent(
                id="e1",
                style="hormozi_bold",
                start=0.0,
                end=1.0,
                zone="lower",
                wordRange=[0, 0],
                text="test",
            )
        ],
        headlineHook="🔥 STICKY HOOK",
        headlineDuration=None,
    )
    assert tl_sticky.headlineDuration is None


def test_api_discover_clips_with_sample():
    client = TestClient(app)
    # Call discover clips on synthetic sample video
    resp = client.post("/api/clips/discover", data={"sample": "true", "target_length": "15s"})
    assert resp.status_code == 200
    data = resp.json()
    assert "clips" in data
    assert data["target_length"] == "15s"
    assert len(data["clips"]) > 0
    first_clip = data["clips"][0]
    assert "headline" in first_clip
    assert "start" in first_clip
    assert "end" in first_clip
    assert "virality_score" in first_clip


def test_api_create_job_with_headline_duration():
    client = TestClient(app)
    # Submit job with headline_hook and headline_duration
    with open("samples/synthetic.mp4", "rb") as f:
        resp = client.post(
            "/api/jobs",
            files={"file": ("synthetic.mp4", f, "video/mp4")},
            data={
                "preset": "fast",
                "headline_hook": "🔥 WATCH THIS",
                "headline_style": "glass",
                "headline_duration": "5.0",
                "draft": "true",
            },
        )
    assert resp.status_code == 201
    job = resp.json()
    assert job["headline_hook"] == "🔥 WATCH THIS"
    assert job["headline_style"] == "glass"
    assert job["headline_duration"] == 5.0
