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
    assert job["headline_duration"] == 5.0


def test_viral_clip_social_post():
    from backend.pipeline.clips import SocialPost
    post = SocialPost(
        hook="Wait till you hear this... 🤯",
        caption="The key to scaling is retention.",
        hashtags=["#viral", "#podcast", "#reels"],
    )
    clip = ViralClip(
        id="c1",
        start=0.0,
        end=15.0,
        duration=15.0,
        headline="🔥 THE SECRET TO SCALING",
        social_post=post,
    )
    assert clip.social_post is not None
    assert clip.social_post.hook.startswith("Wait")
    assert len(clip.social_post.hashtags) == 3


def test_slice_timeline_for_clip():
    from backend.pipeline.clips import slice_timeline_for_clip
    base_tl = Timeline(
        version=1,
        video=TimelineVideo(src="video.mp4", width=1080, height=1920, fps=30, durationSec=60.0),
        words=[
            TimelineWord(i=0, text="first", start=5.0, end=7.0),
            TimelineWord(i=1, text="second", start=12.0, end=14.0),
            TimelineWord(i=2, text="third", start=25.0, end=27.0),
        ],
        events=[
            TimelineEvent(
                id="e1",
                style="hormozi_bold",
                start=5.0,
                end=8.0,
                zone="lower",
                wordRange=[0, 0],
                text="first phrase",
            ),
            TimelineEvent(
                id="e2",
                style="hormozi_bold",
                start=12.0,
                end=15.0,
                zone="lower",
                wordRange=[1, 1],
                text="second phrase",
            ),
        ],
        headlineHook="🔥 OLD HEADLINE",
    )

    # Slice for clip from 10.0 to 20.0
    sub_tl = slice_timeline_for_clip(
        timeline=base_tl,
        clip_start=10.0,
        clip_end=20.0,
        clip_headline="🔥 NEW CLIP HOOK",
        trimmed_video_src="jobs/j1_batch_1/input.mp4",
    )

    assert sub_tl.video.durationSec == 10.0
    assert sub_tl.video.src == "jobs/j1_batch_1/input.mp4"
    assert sub_tl.headlineHook == "🔥 NEW CLIP HOOK"
    # Event e1 (5.0 - 8.0) is before clip start 10.0 -> should be excluded
    # Event e2 (12.0 - 15.0) -> shifted by -10.0 -> (2.0 - 5.0)
    assert len(sub_tl.events) == 1
    assert sub_tl.events[0].id == "e2"
    assert sub_tl.events[0].start == 2.0
    assert sub_tl.events[0].end == 5.0

    # Word 1 (12.0 - 14.0) -> shifted by -10.0 -> (2.0 - 4.0)
    assert len(sub_tl.words) == 1
    assert sub_tl.words[0].text == "second"
    assert sub_tl.words[0].start == 2.0
    assert sub_tl.words[0].end == 4.0


def test_api_create_job_with_booster_options():
    client = TestClient(app)
    with open("samples/synthetic.mp4", "rb") as f:
        resp = client.post(
            "/api/jobs",
            files={"file": ("synthetic.mp4", f, "video/mp4")},
            data={
                "preset": "fast",
                "kinetic_zoom": "true",
                "sound_effects": "true",
                "bg_music": "lofi",
                "watermark_text": "@creatorbrand",
                "draft": "true",
            },
        )
    assert resp.status_code == 201
    job = resp.json()
    assert job["kinetic_zoom"] is True
    assert job["sound_effects"] is True
    assert job["bg_music"] == "lofi"
    assert job["watermark_text"] == "@creatorbrand"


def test_multi_speaker_timeline_speaker_id_and_colors():
    # Verify speakerId and color mapping in TimelineEvent
    ev_host = TimelineEvent(
        id="ev_0",
        style="hormozi_bold",
        start=0.0,
        end=3.0,
        zone="lower",
        wordRange=[0, 1],
        text="Host speaking",
        speakerId="speaker_0",
        highlightColor="#38BDF8",
    )
    ev_guest = TimelineEvent(
        id="ev_1",
        style="hormozi_bold",
        start=3.5,
        end=7.0,
        zone="lower",
        wordRange=[2, 3],
        text="Guest speaking",
        speakerId="speaker_1",
        highlightColor="#F59E0B",
    )
    assert ev_host.speakerId == "speaker_0"
    assert ev_host.highlightColor == "#38BDF8"
    assert ev_guest.speakerId == "speaker_1"
    assert ev_guest.highlightColor == "#F59E0B"
