"""Tests for Phase 5: schema validation, layout engine invariants, and planner fallback."""
import random
import pytest
from pydantic import ValidationError

from backend.schemas.timeline import (
    Timeline,
    TimelineVideo,
    TimelineWord,
    TimelineEvent,
    VALID_STYLES,
)
from backend.pipeline.chunk import Phrase
from backend.pipeline.transcribe import Word
from backend.pipeline.layout import assign_layout, split_lines_balanced
from backend.pipeline.plan_rules import RulePlanner as RuleCore
from backend.pipeline.plan_llm import (
    RulePlanner,
    GeminiPlanner,
    AnthropicPlanner,
    get_planner,
    _validate_and_parse_llm_json,
)


def _make_sample_words_and_phrases() -> tuple[list[Word], list[Phrase]]:
    """Create sample words and phrases matching the synthetic clip."""
    words_data = [
        ("Making", 0.1, 0.4),
        ("money", 0.45, 0.75),
        ("is", 0.8, 0.95),
        ("basically", 1.0, 1.3),
        ("a", 1.35, 1.45),
        ("skills", 1.5, 1.8),
        ("problem.", 1.85, 2.3),
        ("Stop", 2.6, 2.9),
        ("planning", 2.95, 3.4),
        ("and", 3.45, 3.6),
        ("take", 3.65, 3.9),
        ("action", 3.95, 4.4),
        ("today.", 4.45, 4.8),
    ]
    words = [Word(i=idx, text=t, start=s, end=e, probability=0.98) for idx, (t, s, e) in enumerate(words_data)]
    p1 = Phrase(
        id="p0",
        text="Making money is basically a skills problem.",
        start=0.1,
        end=2.3,
        speech_start=0.1,
        speech_end=2.3,
        words=words[:7],
        word_indices=list(range(7)),
    )
    p2 = Phrase(
        id="p1",
        text="Stop planning and take action today.",
        start=2.6,
        end=4.8,
        speech_start=2.6,
        speech_end=4.8,
        words=words[7:],
        word_indices=list(range(7, 13)),
    )
    return words, [p1, p2]


# ---------------------------------------------------------------------------
# 1. Schema Validation Tests (Valid + Invalid)
# ---------------------------------------------------------------------------


def test_schema_valid_timeline():
    video = TimelineVideo(src="video.mp4", width=1080, height=1920, fps=30.0, durationSec=5.0)
    words = [
        TimelineWord(i=0, text="Hello", start=0.1, end=0.5),
        TimelineWord(i=1, text="world", start=0.6, end=1.0),
    ]
    events = [
        TimelineEvent(
            id="base_1",
            style="pill_word",
            start=0.1,
            end=1.2,
            zone="lower",
            layer=1,
            wordRange=[0, 1],
            text="Hello world",
        ),
        TimelineEvent(
            id="feat_1",
            style="title3d",
            start=0.1,
            end=1.2,
            zone="center",
            layer=2,
            wordRange=[0, 1],
            text="Hello world",
        ),
    ]
    tl = Timeline(video=video, words=words, events=events)
    assert len(tl.events) == 2


def test_schema_invalid_style():
    with pytest.raises(ValidationError):
        TimelineEvent(
            id="e1",
            style="non_existent_fancy_style",
            start=0.0,
            end=1.0,
            text="Test",
        )


def test_schema_invalid_timing_end_before_start():
    with pytest.raises(ValidationError):
        TimelineEvent(
            id="e1",
            style="pill_word",
            start=2.0,
            end=1.0,
            text="Test",
        )


def test_schema_invalid_short_duration():
    with pytest.raises(ValidationError):
        TimelineEvent(
            id="e1",
            style="pill_word",
            start=1.0,
            end=1.1,  # < 0.3s
            text="Test",
        )


def test_schema_invalid_concurrency_over_three():
    video = TimelineVideo(src="video.mp4", width=1080, height=1920, fps=30.0, durationSec=10.0)
    # 4 concurrent events at t=1.0
    events = [
        TimelineEvent(id="e1", style="pill_word", start=0.5, end=2.0, zone="lower", layer=1, text="One"),
        TimelineEvent(id="e2", style="title3d", start=0.5, end=2.0, zone="center", layer=2, text="Two"),
        TimelineEvent(id="e3", style="handwritten", start=0.5, end=2.0, zone="upper", layer=3, text="Three"),
        TimelineEvent(id="e4", style="sticker", start=0.5, end=2.0, zone="free", layer=4, text="Four"),
    ]
    with pytest.raises(ValueError, match="More than 3 concurrent events"):
        Timeline(video=video, events=events)


def test_schema_invalid_zone_collision():
    video = TimelineVideo(src="video.mp4", width=1080, height=1920, fps=30.0, durationSec=10.0)
    # 2 events simultaneously in the same zone 'center'
    events = [
        TimelineEvent(id="e1", style="title3d", start=0.5, end=2.0, zone="center", layer=1, text="One"),
        TimelineEvent(id="e2", style="serif_title", start=0.8, end=2.5, zone="center", layer=2, text="Two"),
    ]
    with pytest.raises(ValueError, match="Zone collision"):
        Timeline(video=video, events=events)


# ---------------------------------------------------------------------------
# 2. Layout Engine & Invariants on Randomized Inputs
# ---------------------------------------------------------------------------


def test_split_lines_balanced():
    lines = split_lines_balanced("Making money is basically a skills problem", max_chars_per_line=16)
    assert len(lines) >= 2
    assert " ".join(lines) == "Making money is basically a skills problem"


def test_layout_randomized_invariants():
    """Property-style test: randomize event starts, durations, zones, and styles,
    and verify that assign_layout outputs a valid timeline that strictly satisfies all invariants.
    """
    rng = random.Random(42)
    video_duration = 30.0
    styles = list(VALID_STYLES)

    for iteration in range(25):
        raw_events: list[TimelineEvent] = []
        # Add random base events
        cur_t = 0.5
        idx = 0
        while cur_t < video_duration - 2.0:
            dur = rng.uniform(0.6, 2.5)
            raw_events.append(
                TimelineEvent(
                    id=f"base_{idx}",
                    style="pill_word",
                    start=cur_t,
                    end=cur_t + dur,
                    zone="lower",
                    layer=1,
                    text=f"Base sentence {idx}",
                )
            )
            cur_t += dur + rng.uniform(0.0, 0.5)
            idx += 1

        # Add random feature events with chaotic zones and styles
        for f_idx in range(15):
            st = rng.uniform(0.0, video_duration - 1.5)
            dur = rng.uniform(0.35, 4.0)
            raw_events.append(
                TimelineEvent(
                    id=f"feat_{f_idx}",
                    style=rng.choice(styles),
                    start=st,
                    end=st + dur,
                    zone=rng.choice(["upper", "center", "lower"]),
                    layer=rng.choice([1, 2, 3]),
                    text=f"Feature {f_idx}",
                )
            )

        # Run through layout engine
        laid_out = assign_layout(raw_events, video_duration=video_duration)

        # Check invariants:
        # 1. Bounds
        for ev in laid_out:
            assert 0.0 <= ev.start < ev.end <= video_duration + 0.05
            assert ev.end - ev.start >= 0.25

        # 2. Concurrency and zone collisions
        time_samples = [0.1 * i for i in range(int(video_duration * 10))]
        for t in time_samples:
            active = [e for e in laid_out if e.start <= t < e.end]
            assert len(active) <= 3, f"Iteration {iteration}: >3 active events at t={t}: {[e.id for e in active]}"

            active_zones = [e.zone for e in active if e.zone != "free"]
            assert len(active_zones) == len(set(active_zones)), (
                f"Iteration {iteration}: Zone collision at t={t}: {active_zones}"
            )

        # 3. Pacing: no more than 2 consecutive identical feature styles
        features = [e for e in laid_out if not e.id.startswith("base_")]
        consecutive = 1
        for i in range(1, len(features)):
            if features[i].style == features[i - 1].style:
                consecutive += 1
                assert consecutive <= 2, f"More than 2 consecutive {features[i].style}"
            else:
                consecutive = 1


# ---------------------------------------------------------------------------
# 3. Planner Fallback & LLM Resilience
# ---------------------------------------------------------------------------


def test_rule_planner_end_to_end():
    words, phrases = _make_sample_words_and_phrases()
    planner = RulePlanner(preset="bold_creator")
    events = planner.plan(phrases, video_duration=5.0)

    assert len(events) >= 2
    # Verify base track exists
    base_events = [e for e in events if e.style == "pill_word" and e.id.startswith("base_")]
    assert len(base_events) == 2

    # Verify feature track exists
    feature_events = [e for e in events if not e.id.startswith("base_")]
    assert len(feature_events) >= 1

    # Verify valid timeline creation
    video = TimelineVideo(src="video.mp4", width=1080, height=1920, fps=30.0, durationSec=5.0)
    tl_words = [TimelineWord(i=w.i, text=w.text, start=w.start, end=w.end) for w in words]
    tl = Timeline(video=video, words=tl_words, events=events)
    assert tl.version == 1


def test_get_planner_factory(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "none")
    p1 = get_planner()
    assert isinstance(p1, RulePlanner)

    p2 = get_planner("gemini")
    assert isinstance(p2, GeminiPlanner)

    p3 = get_planner("anthropic")
    assert isinstance(p3, AnthropicPlanner)


def test_gemini_planner_fallback_without_api_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    planner = GeminiPlanner(api_key=None)
    words, phrases = _make_sample_words_and_phrases()

    # Must fall back gracefully to RulePlanner and not crash
    events = planner.plan(phrases, video_duration=5.0)
    assert len(events) >= 2
    assert any(e.id.startswith("base_") for e in events)


def test_anthropic_planner_fallback_without_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    planner = AnthropicPlanner(api_key=None)
    words, phrases = _make_sample_words_and_phrases()

    # Must fall back gracefully to RulePlanner and not crash
    events = planner.plan(phrases, video_duration=5.0)
    assert len(events) >= 2
    assert any(e.id.startswith("base_") for e in events)


def test_validate_and_parse_llm_json_garbage_handling():
    words, phrases = _make_sample_words_and_phrases()

    # Garbage / plain prose
    with pytest.raises(Exception):
        _validate_and_parse_llm_json("Sorry I cannot help with that.", phrases, 5.0)

    # Valid JSON markdown block
    good_json = """```json
    [
      {
        "id": "feat_test",
        "style": "title3d",
        "start": 0.1,
        "end": 2.0,
        "zone": "center",
        "wordRange": [0, 6],
        "text": "Making money is basically a skills problem."
      }
    ]
    ```"""
    parsed = _validate_and_parse_llm_json(good_json, phrases, 5.0)
    assert len(parsed) == 1
    assert parsed[0].style == "title3d"
