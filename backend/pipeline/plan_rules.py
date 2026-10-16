"""Rule-based caption planner implementing intelligent styling heuristics from docs/05."""
import re
from typing import Optional
from backend.pipeline.chunk import Phrase
from backend.pipeline.transcribe import Word
from backend.schemas.timeline import TimelineEvent, Highlight, Graphic, AnimationConfig


# Concrete noun / keyword to emoji mappings
EMOJI_KEYWORDS: dict[str, str] = {
    "doctor": "🩺",
    "medicine": "🩺",
    "hospital": "🏥",
    "money": "💰",
    "cash": "💵",
    "brain": "🧠",
    "fire": "🔥",
    "rocket": "🚀",
    "action": "🚀",
    "time": "⏳",
    "heart": "❤️",
}

ICON_KEYWORDS: dict[str, str] = {
    "skills": "zap",
    "skill": "zap",
    "idea": "lightbulb",
    "ideas": "lightbulb",
    "target": "target",
    "growth": "trending-up",
    "spark": "sparkles",
}

EMPHASIS_KEYWORDS = {
    "not", "never", "no", "stop", "action", "money", "skills", "problem",
    "monetise", "monetize", "actually", "really", "everything", "best", "greatest"
}

ORDINAL_WORDS = {"one", "two", "three", "first", "second", "third", "1", "2", "3"}


def detect_graphic_for_text(text: str) -> Optional[Graphic]:
    """Detect concrete noun in text and return appropriate graphic sticker or icon."""
    lower_words = [w.lower().strip(".,!?:;\"'") for w in text.split()]
    for w in lower_words:
        if w in ICON_KEYWORDS:
            return Graphic(kind="icon", value=ICON_KEYWORDS[w], position="above")
        if w in EMOJI_KEYWORDS:
            return Graphic(kind="emoji", value=EMOJI_KEYWORDS[w], position="above")
    return None


def detect_highlights(phrase_words: list[Word]) -> list[Highlight]:
    """Identify emphasis keywords within words and create Highlight models."""
    highlights: list[Highlight] = []
    for w in phrase_words:
        clean = w.text.lower().strip(".,!?:;\"'")
        if clean in {"stop", "never", "not"}:
            highlights.append(Highlight(wordIndex=w.i, kind="pill", value="#FFFFFF"))
        elif clean in {"action", "monetise", "monetize", "skills", "money", "idea"}:
            highlights.append(Highlight(wordIndex=w.i, kind="color", value="#FBBF24"))
    return highlights[:2]  # Limit to max 2 highlights per event


class RulePlanner:
    """Deterministic rule-based planner implementing styling heuristics."""

    def __init__(self, preset: str = "bold_creator"):
        self.preset = preset

    def plan(
        self,
        phrases: list[Phrase],
        video_duration: float,
        language: str = "en",
    ) -> list[TimelineEvent]:
        events: list[TimelineEvent] = []
        last_feature_time: dict[str, float] = {}
        last_feature_style: Optional[str] = None
        consecutive_same_style = 0

        total_phrases = len(phrases)

        # 1. Base track: every phrase gets a pill_word event in lower zone
        for idx, p in enumerate(phrases):
            if not p.word_indices:
                continue

            events.append(
                TimelineEvent(
                    id=f"base_{p.id}",
                    style="pill_word",
                    start=p.start,
                    end=p.end,
                    zone="lower",
                    layer=1,
                    wordRange=[p.word_indices[0], p.word_indices[-1]],
                    text=p.text,
                )
            )

        if self.preset == "minimal_pill":
            # minimal_pill preset: only pill_word captions with highlights
            return events

        # 2. Add impact feature events on ~30-40% of phrases
        for idx, p in enumerate(phrases):
            if not p.word_indices:
                continue

            text_lower = p.text.lower()
            text_clean = p.text.strip(".,!?:;\"'")
            word_count = len(p.words)
            words_in_phrase = [w.text.lower().strip(".,!?:;\"'") for w in p.words]

            feature_style: Optional[str] = None
            feature_zone = "upper"
            feature_variant: Optional[str] = None
            feature_palette = "sunset"
            feature_decorations: list[str] = []
            feature_graphic: Optional[Graphic] = None

            # Rule A: Ordinal marker -> numbered_point
            if any(w in ORDINAL_WORDS for w in words_in_phrase) and any(
                kw in text_lower for kw in ["step", "number", "point", "having", "way"]
            ):
                feature_style = "numbered_point"
                feature_zone = "upper"
                feature_decorations = ["ellipse"]

            # Rule B: First sentence / hook / strong claim -> title3d or serif_title
            elif idx == 0 or (idx == 1 and total_phrases > 3):
                if self.preset == "calm_serif":
                    feature_style = "serif_title"
                    feature_decorations = ["ellipse"]
                else:
                    feature_style = "title3d"
                    feature_palette = "sunset"
                    feature_decorations = ["sparkles"]
                feature_zone = "center"

            # Rule C: "How to" / action statement -> serif_title
            elif "how to" in text_lower or ("stop" in text_lower and "action" in text_lower):
                feature_style = "serif_title"
                feature_zone = "upper"
                feature_decorations = ["ellipse"]

            # Rule D: Definition / key takeaway / "everything that is" -> blob_card (glow)
            elif "everything" in text_lower or "skill can be" in text_lower or "basically" in text_lower:
                feature_style = "blob_card"
                feature_variant = "glow"
                feature_zone = "center"
                feature_decorations = ["sparkles"]

            # Rule E: Negation / strong advice / warning -> blob_card (frosted)
            elif "ignore" in text_lower or "advice" in text_lower or ("not" in text_lower and "want" in text_lower):
                feature_style = "blob_card"
                feature_variant = "frosted"
                feature_zone = "upper"

            # Rule F: Short letter sequence or list -> arc_letters
            elif len(p.words) in (3, 4) and all(len(w) <= 2 for w in words_in_phrase):
                feature_style = "arc_letters"
                feature_zone = "center"

            # Rule G: Asides / lower energy -> handwritten
            elif "rather than" in text_lower or "luck" in text_lower or word_count <= 4:
                feature_style = "handwritten"
                feature_zone = "upper"
                if "stop" in text_lower or "planning" in text_lower:
                    feature_decorations = ["arrow"]

            # Fallback for remaining phrases: occasional sticker or serif_title
            if not feature_style and (idx % 3 == 0) and word_count <= 6:
                detected_graphic = detect_graphic_for_text(p.text)
                if detected_graphic:
                    feature_style = "sticker"
                    feature_graphic = detected_graphic
                    feature_zone = "center"
                else:
                    feature_style = "serif_title"
                    feature_zone = "upper"

            if not feature_style:
                continue

            # Check pacing & variety constraints:
            # - No more than 2 consecutive identical feature styles
            if feature_style == last_feature_style:
                if consecutive_same_style >= 2:
                    feature_style = "blob_card" if feature_style != "blob_card" else "serif_title"
                    consecutive_same_style = 1
                else:
                    consecutive_same_style += 1
            else:
                consecutive_same_style = 1

            # - Breathing room: at least 1.0s gap for identical style
            prev_end = last_feature_time.get(feature_style, -10.0)
            if p.start - prev_end < 1.0:
                # Switch to an alternate style or skip
                alt_style = "serif_title" if feature_style != "serif_title" else "blob_card"
                if p.start - last_feature_time.get(alt_style, -10.0) >= 1.0:
                    feature_style = alt_style
                else:
                    continue

            # title3d at most once per 10-12s
            if feature_style == "title3d" and p.start - last_feature_time.get("title3d", -20.0) < 10.0:
                feature_style = "serif_title"

            last_feature_style = feature_style
            last_feature_time[feature_style] = p.end

            # Highlights for the feature event
            event_highlights = detect_highlights(p.words)
            graphic_item = feature_graphic or detect_graphic_for_text(p.text)

            events.append(
                TimelineEvent(
                    id=f"feat_{p.id}",
                    style=feature_style,
                    start=p.start,
                    end=p.end,
                    zone=feature_zone,
                    layer=2,
                    wordRange=[p.word_indices[0], p.word_indices[-1]],
                    text=p.text,
                    highlights=event_highlights if event_highlights else None,
                    palette=feature_palette,
                    variant=feature_variant,
                    decorations=feature_decorations if feature_decorations else None,
                    graphic=graphic_item,
                    animation=AnimationConfig(in_="pop", out="fade", wordStagger=0.04),
                )
            )

        return events
