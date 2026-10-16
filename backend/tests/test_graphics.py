"""Tests for Phase 6: graphics, emoji, icons, and doodles."""
import json
from pathlib import Path
import pytest

from backend.schemas.timeline import Timeline, Graphic, TimelineEvent
from backend.pipeline.plan_rules import detect_graphic_for_text, EMOJI_KEYWORDS, ICON_KEYWORDS


def test_detect_graphic_emoji():
    # Concrete nouns mapping to emojis
    g_money = detect_graphic_for_text("Making money is easy")
    assert g_money is not None
    assert g_money.kind == "emoji"
    assert g_money.value == "💰"

    g_fire = detect_graphic_for_text("This track is pure fire!")
    assert g_fire is not None
    assert g_fire.kind == "emoji"
    assert g_fire.value == "🔥"


def test_detect_graphic_icon():
    # Concrete keywords mapping to Lucide icons
    g_skills = detect_graphic_for_text("A skills problem")
    assert g_skills is not None
    assert g_skills.kind == "icon"
    assert g_skills.value == "zap"

    g_idea = detect_graphic_for_text("Monetize your ideas")
    assert g_idea is not None
    assert g_idea.kind == "icon"
    assert g_idea.value == "lightbulb"


def test_detect_graphic_none():
    assert detect_graphic_for_text("The and is of it") is None


def test_graphic_and_doodle_schema_validation():
    # Event with icon graphic and arrow doodle
    ev = TimelineEvent(
        id="e_test",
        style="serif_title",
        start=0.5,
        end=2.0,
        zone="upper",
        layer=2,
        text="Take action now",
        decorations=["arrow", "ellipse"],
        graphic=Graphic(kind="icon", value="zap", position="above"),
    )
    assert ev.graphic.kind == "icon"
    assert "arrow" in ev.decorations
    assert "ellipse" in ev.decorations


def test_sample_timeline_has_required_graphics_and_doodles():
    timeline_path = Path("out/timeline.json")
    assert timeline_path.exists(), "out/timeline.json must exist"

    with open(timeline_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    tl = Timeline.model_validate(data)

    has_emoji = False
    has_icon = False
    has_ellipse = False
    has_sparkles = False
    has_arrow = False

    for ev in tl.events:
        if ev.graphic:
            if ev.graphic.kind == "emoji":
                has_emoji = True
            elif ev.graphic.kind == "icon":
                has_icon = True
        if ev.decorations:
            if "ellipse" in ev.decorations:
                has_ellipse = True
            if "sparkles" in ev.decorations:
                has_sparkles = True
            if "arrow" in ev.decorations:
                has_arrow = True

    assert has_emoji, "Timeline must contain at least one emoji graphic"
    assert has_icon, "Timeline must contain at least one icon graphic"
    assert has_ellipse, "Timeline must contain at least one ellipse doodle"
    assert has_sparkles, "Timeline must contain at least one sparkles decoration"
    assert has_arrow, "Timeline must contain at least one arrow doodle"
