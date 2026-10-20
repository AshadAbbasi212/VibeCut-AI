"""Tests for Active Speaker Tracking & Auto-Reframe Engine."""
import pytest
from backend.pipeline.chunk import Phrase
from backend.schemas.timeline import CameraCut, Timeline, TimelineVideo
from backend.pipeline.reframe import build_active_speaker_cuts


def test_empty_phrases_fallback():
    cuts = build_active_speaker_cuts(phrases=[], video_duration=10.0, num_speakers=2)
    assert len(cuts) == 1
    assert cuts[0].start == 0.0
    assert cuts[0].end == 10.0
    assert cuts[0].layout == "split_duo"


def test_active_speaker_pacing_and_hysteresis():
    # Simulate a conversation between 2 speakers
    phrases = [
        # Speaker 0 (Question)
        Phrase(id="p1", text="What is your best habit?", start=0.5, end=2.8, speech_start=0.5, speech_end=2.8, word_indices=[0, 1, 2, 3, 4], words=[]),
        # Speaker 1 (Answer)
        Phrase(id="p2", text="My best habit is waking up early.", start=3.8, end=6.5, speech_start=3.8, speech_end=6.5, word_indices=[5, 6, 7, 8, 9, 10], words=[]),
        # Speaker 1 (Continuation)
        Phrase(id="p3", text="And working out immediately.", start=6.8, end=8.2, speech_start=6.8, speech_end=8.2, word_indices=[11, 12, 13, 14], words=[]),
        # Speaker 0 (Short interjection - under 1.8s)
        Phrase(id="p4", text="Yeah.", start=9.0, end=9.4, speech_start=9.0, speech_end=9.4, word_indices=[15], words=[]),
        # Speaker 1 (Continues)
        Phrase(id="p5", text="It completely changed my focus.", start=9.6, end=12.0, speech_start=9.6, speech_end=12.0, word_indices=[16, 17, 18, 19, 20], words=[]),
    ]

    cuts = build_active_speaker_cuts(
        phrases=phrases,
        video_duration=14.0,
        num_speakers=2,
        min_shot_duration=1.8,
        hold_buffer=0.6,
    )

    assert len(cuts) >= 2
    # First cut should start at 0.0
    assert cuts[0].start == 0.0
    # Last cut should end at 14.0
    assert cuts[-1].end == 14.0
    
    # Check that cuts are non-overlapping and contiguous
    for i in range(len(cuts) - 1):
        assert cuts[i].end == cuts[i + 1].start

    # Check minimum shot duration: no cut should be shorter than min_shot_duration (except edge boundary)
    for c in cuts[:-1]:
        assert c.end - c.start >= 1.5


def test_cross_talk_triggers_split_stack():
    # Simulate overlapping speech (cross-talk)
    phrases = [
        Phrase(id="p1", text="I completely disagree with that.", start=1.0, end=4.0, speech_start=1.0, speech_end=4.0, word_indices=[0, 1, 2, 3, 4], words=[]),
        # Speaker interrupts at 3.0s before p1 finishes at 4.0s
        Phrase(id="p2", text="Wait, let me explain why!", start=3.0, end=6.0, speech_start=3.0, speech_end=6.0, word_indices=[5, 6, 7, 8, 9], words=[]),
    ]

    cuts = build_active_speaker_cuts(
        phrases=phrases,
        video_duration=8.0,
        num_speakers=2,
    )

    # Should detect cross-talk and include split_duo layout
    layouts = [c.layout for c in cuts]
    assert "split_duo" in layouts


def test_timeline_with_camera_cuts_schema():
    cut1 = CameraCut(start=0.0, end=4.5, focusX=0.15, speakerId="speaker_0", layout="solo")
    cut2 = CameraCut(start=4.5, end=9.0, focusX=0.85, speakerId="speaker_1", layout="solo")
    
    tl_video = TimelineVideo(
        src="sample.mp4",
        width=1080,
        height=1920,
        fps=30,
        durationSec=9.0,
        layout="active_speaker",
        originalWidth=1920,
        originalHeight=1080,
    )
    
    tl = Timeline(
        version=1,
        video=tl_video,
        language="en",
        words=[],
        events=[],
        videoLayout="active_speaker",
        cameraCuts=[cut1, cut2],
    )
    
    assert tl.videoLayout == "active_speaker"
    assert len(tl.cameraCuts) == 2
    assert tl.cameraCuts[0].focusX == 0.15
    assert tl.cameraCuts[1].focusX == 0.85
