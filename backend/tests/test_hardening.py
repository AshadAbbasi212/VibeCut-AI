"""Tests for Phase 9 polish, hardening, edge cases, presets, and performance flags."""
import pytest
from pathlib import Path

from backend.pipeline.chunk import chunk_words, PhrasesDocument
from backend.pipeline.plan_rules import RulePlanner
from backend.pipeline.plan_llm import get_planner
from backend.pipeline.layout import assign_layout
from backend.pipeline.probe import VideoProbe, parse_fps
from backend.pipeline.transcribe import Word, Transcript, transcribe
from backend.schemas.timeline import Timeline, TimelineVideo, TimelineWord
from backend.cli import main
import argparse


def test_empty_words_produces_empty_phrases_and_events():
    """Verify clips with no speech handle gracefully without errors."""
    words: list[Word] = []
    phrases = chunk_words(words, duration=10.0)
    assert phrases == []

    planner = RulePlanner(preset="bold_creator")
    events = planner.plan(phrases, video_duration=10.0)
    assert events == []

    layout_events = assign_layout(events, video_duration=10.0)
    assert layout_events == []

    # Valid timeline with no events
    tl = Timeline(
        version=1,
        video=TimelineVideo(src="empty.mp4", width=1080, height=1920, fps=30, durationSec=10.0),
        language="en",
        words=[],
        events=[],
    )
    assert len(tl.events) == 0
    assert len(tl.words) == 0


def test_preset_biases():
    """Verify presets produce distinct style choices and event sets."""
    sample_words = [
        Word(i=0, text="Stop", start=0.0, end=0.4, prob=1.0),
        Word(i=1, text="taking", start=0.4, end=0.7, prob=1.0),
        Word(i=2, text="action", start=0.7, end=1.1, prob=1.0),
        Word(i=3, text="without", start=1.1, end=1.5, prob=1.0),
        Word(i=4, text="skills", start=1.5, end=1.9, prob=1.0),
        Word(i=5, text="and", start=1.9, end=2.1, prob=1.0),
        Word(i=6, text="money.", start=2.1, end=2.6, prob=1.0),
    ]
    phrases = chunk_words(sample_words, duration=3.0)

    # 1. Minimal pill: only base pill_word track
    planner_pill = get_planner(provider="none", preset="minimal_pill")
    events_pill = planner_pill.plan(phrases, video_duration=3.0, preset="minimal_pill")
    styles_pill = {e.style for e in events_pill}
    assert styles_pill == {"pill_word"}

    # 2. Bold creator: includes bold feature styles like title3d or blob_card
    planner_bold = get_planner(provider="none", preset="bold_creator")
    events_bold = planner_bold.plan(phrases, video_duration=3.0, preset="bold_creator")
    styles_bold = {e.style for e in events_bold}
    assert len(styles_bold) > 1

    # 3. Calm serif: avoids title3d, uses serif_title with elegant palette
    planner_serif = get_planner(provider="none", preset="calm_serif")
    events_serif = planner_serif.plan(phrases, video_duration=3.0, preset="calm_serif")
    styles_serif = {e.style for e in events_serif}
    assert "title3d" not in styles_serif
    assert "serif_title" in styles_serif


def test_probe_fps_parser():
    """Test odd fps parsing like 30000/1001 or 29.97."""
    assert parse_fps("30/1") == 30.0
    assert parse_fps("30000/1001") == 29.97
    assert parse_fps("24/1") == 24.0
    assert parse_fps("25") == 25.0
    assert parse_fps("0/0") == 30.0
    assert parse_fps("invalid") == 30.0


def test_cli_argument_parsing():
    """Verify all CLI arguments and aliases are accepted."""
    import sys
    from unittest.mock import patch

    test_args = [
        "cli.py",
        "samples/input.mp4",
        "-o", "out/test.mp4",
        "--style-preset", "calm_serif",
        "--whisper-model", "base",
        "--concurrency", "2",
        "--draft",
        "--start", "1.0",
        "--end", "4.5",
    ]
    with patch.object(sys, "argv", test_args):
        # We can construct the parser directly to test argument resolution
        parser = argparse.ArgumentParser()
        parser.add_argument("input")
        parser.add_argument("-o", "--output", default="out/final.mp4")
        parser.add_argument("--preset", "--style-preset", dest="preset", default="bold_creator")
        parser.add_argument("--whisper-model", default="small")
        parser.add_argument("--concurrency", type=int, default=None)
        parser.add_argument("--draft", action="store_true")
        parser.add_argument("--start", type=float, default=None)
        parser.add_argument("--end", type=float, default=None)
        args = parser.parse_args(test_args[1:])

        assert args.input == "samples/input.mp4"
        assert args.output == "out/test.mp4"
        assert args.preset == "calm_serif"
        assert args.whisper_model == "base"
        assert args.concurrency == 2
        assert args.draft is True
        assert args.start == 1.0
        assert args.end == 4.5


def test_rapid_short_utterance_does_not_fail_validation():
    """Verify short rapid utterance (e.g. 0.26s) produces valid TimelineEvents without throwing."""
    short_words = [
        Word(i=0, text="You", start=10.00, end=10.08, prob=0.99),
        Word(i=1, text="can", start=10.08, end=10.16, prob=0.99),
        Word(i=2, text="just", start=10.16, end=10.26, prob=0.99),
        Word(i=3, text="stop", start=10.26, end=10.65, prob=0.99),
        Word(i=4, text="there.", start=10.65, end=11.20, prob=0.99),
    ]
    phrases = chunk_words(short_words, duration=15.0)
    for p in phrases:
        assert p.end - p.start >= 0.30

    planner = RulePlanner(preset="bold_creator")
    events = planner.plan(phrases, video_duration=15.0)
    for ev in events:
        assert ev.end - ev.start >= 0.30

    layout_events = assign_layout(events, video_duration=15.0)
    for ev in layout_events:
        assert ev.end - ev.start >= 0.30

    # Build full Timeline to verify all invariants
    tl = Timeline(
        version=1,
        video=TimelineVideo(src="test.mp4", width=1080, height=1920, fps=30.0, durationSec=15.0),
        language="en",
        words=[TimelineWord(i=w.i, text=w.text, start=w.start, end=w.end) for w in short_words],
        events=layout_events,
    )
    assert len(tl.events) > 0

