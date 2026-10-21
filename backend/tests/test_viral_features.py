"""Tests for Viral Boosters Pack: Retention Progress Bar, Headline Hook Card, and Auto-Emojis."""
import pytest
from backend.schemas.timeline import Timeline, TimelineVideo, TimelineWord, TimelineEvent
from backend.pipeline.chunk import Phrase
from backend.pipeline.transcribe import Word
from backend.pipeline.plan_rules import RulePlanner as RuleCore, detect_graphic_for_text


def _make_dummy_timeline(
    progress_bar=True,
    progress_bar_position="bottom",
    headline_hook="🔥 WAIT TILL THE END...",
    headline_style="badge",
    auto_emojis=True,
) -> Timeline:
    return Timeline(
        version=1,
        video=TimelineVideo(src="sample.mp4", width=1080, height=1920, fps=30, durationSec=5.0),
        words=[TimelineWord(i=0, text="viral", start=0.5, end=1.5)],
        events=[
            TimelineEvent(
                id="e1",
                style="hormozi_bold",
                start=0.5,
                end=1.5,
                zone="lower",
                wordRange=[0, 0],
                text="viral",
            )
        ],
        progressBar=progress_bar,
        progressBarPosition=progress_bar_position,
        headlineHook=headline_hook,
        headlineStyle=headline_style,
        autoEmojis=auto_emojis,
    )


def test_timeline_schema_viral_fields():
    tl = _make_dummy_timeline(
        progress_bar=True,
        progress_bar_position="top",
        headline_hook="🔥 STOP SCROLLING",
        headline_style="cyber",
        auto_emojis=True,
    )
    assert tl.progressBar is True
    assert tl.progressBarPosition == "top"
    assert tl.headlineHook == "🔥 STOP SCROLLING"
    assert tl.headlineStyle == "cyber"
    assert tl.autoEmojis is True

    # Check serialization
    data = tl.model_dump(by_alias=True)
    assert data["progressBar"] is True
    assert data["progressBarPosition"] == "top"
    assert data["headlineHook"] == "🔥 STOP SCROLLING"
    assert data["headlineStyle"] == "cyber"
    assert data["autoEmojis"] is True


def test_timeline_headline_hook_optional():
    # User can disable headline hook card by passing None
    tl = _make_dummy_timeline(headline_hook=None)
    assert tl.headlineHook is None


def test_auto_emojis_detection_and_toggle():
    # 1. Keywords produce emojis/icons
    g_money = detect_graphic_for_text("Making big money in 2026")
    assert g_money is not None
    assert g_money.kind == "emoji"
    assert g_money.value == "💰"

    g_fire = detect_graphic_for_text("This trick is straight fire")
    assert g_fire is not None
    assert g_fire.kind == "emoji"
    assert g_fire.value == "🔥"

    g_skills = detect_graphic_for_text("Focus on building your skills")
    assert g_skills is not None
    assert g_skills.kind == "icon"
    assert g_skills.value == "zap"

    # 2. Planner respects auto_emojis=True
    words = [
        Word(i=0, text="This", start=0.2, end=0.6, probability=0.99),
        Word(i=1, text="fire", start=0.7, end=1.2, probability=0.99),
        Word(i=2, text="action", start=1.3, end=1.8, probability=0.99),
    ]
    phrase = Phrase(
        id="p0",
        text="This fire action",
        start=0.2,
        end=1.8,
        speech_start=0.2,
        speech_end=1.8,
        words=words,
        word_indices=[0, 1, 2],
    )

    planner = RuleCore()
    events_with_emojis = planner.plan(
        phrases=[phrase],
        video_duration=3.0,
        selected_styles=["hormozi_bold"],
        auto_emojis=True,
    )
    assert len(events_with_emojis) == 1
    assert events_with_emojis[0].graphic is not None
    assert events_with_emojis[0].graphic.value == "🔥"

    # 3. Planner respects auto_emojis=False
    events_no_emojis = planner.plan(
        phrases=[phrase],
        video_duration=3.0,
        selected_styles=["hormozi_bold"],
        auto_emojis=False,
    )
    assert len(events_no_emojis) == 1
    assert events_no_emojis[0].graphic is None
