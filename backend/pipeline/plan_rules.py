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

            s = round(p.start, 2)
            e = max(round(p.end, 2), round(s + 0.35, 2))
            if video_duration > 0 and e > video_duration:
                e = round(video_duration, 2)
                s = max(0.0, round(e - 0.35, 2))

            events.append(
                TimelineEvent(
                    id=f"base_{p.id}",
                    style="pill_word",
                    start=s,
                    end=e,
                    zone="lower",
                    layer=1,
                    wordRange=[p.word_indices[0], p.word_indices[-1]],
                    text=p.text,
                )
            )

        if self.preset == "minimal_pill":
            # minimal_pill preset: only pill_word captions with highlights
            return events

        # Master pool of feature styles for maximum variety
        all_feature_styles = [
            "title3d",
            "neon_glow",
            "typewriter_terminal",
            "paper_cutout",
            "glitch_kinetic",
            "quote_editorial",
            "comic_bubble",
            "gradient_outline",
            "minimal_underline",
            "serif_title",
            "blob_card",
            "numbered_point",
            "handwritten",
            "sticker",
            "arc_letters",
        ] if self.preset != "calm_serif" else [
            "serif_title",
            "quote_editorial",
            "blob_card",
            "minimal_underline",
            "paper_cutout",
            "handwritten",
            "numbered_point",
        ]

        used_styles: set[str] = set()
        recent_styles: list[str] = []
        window_size = 6

        # 2. Add impact feature events across phrases ensuring 10-15 distinct styles
        for idx, p in enumerate(phrases):
            if not p.word_indices:
                continue

            text_lower = p.text.lower()
            word_count = len(p.words)
            words_in_phrase = [w.text.lower().strip(".,!?:;\"'") for w in p.words]

            feature_style: Optional[str] = None
            feature_zone = "upper"
            feature_variant: Optional[str] = None
            feature_palette = "monochrome" if self.preset == "calm_serif" else "sunset"
            feature_decorations: list[str] = []
            feature_graphic: Optional[Graphic] = None

            # Determine semantic candidate style
            if any(w in ORDINAL_WORDS for w in words_in_phrase) and any(
                kw in text_lower for kw in ["step", "number", "point", "having", "way"]
            ):
                feature_style = "numbered_point"
                feature_decorations = ["ellipse"]

            elif idx == 0:
                feature_style = "serif_title" if self.preset == "calm_serif" else "title3d"
                feature_zone = "center"
                feature_decorations = ["sparkles"]

            elif any(w in text_lower for w in ["code", "system", "logic", "terminal", "dollar", "percent", "data"]):
                feature_style = "typewriter_terminal"
                feature_zone = "upper"

            elif any(w in text_lower for w in ["fast", "electric", "power", "money", "future", "online", "crypto"]):
                feature_style = "neon_glow"
                feature_zone = "center"

            elif any(w in text_lower for w in ["quote", "remember", "said", "truth", "life", "why"]):
                feature_style = "quote_editorial"
                feature_zone = "upper"

            elif "?" in p.text or "!" in p.text or any(w in text_lower for w in ["wow", "crazy", "secret", "shout", "boom"]):
                feature_style = "comic_bubble"
                feature_zone = "center"

            elif any(w in text_lower for w in ["stop", "tip", "note", "rule", "warning", "advice"]):
                feature_style = "paper_cutout"
                feature_zone = "upper"

            elif any(w in text_lower for w in ["suddenly", "break", "glitch", "crash", "wrong", "shock", "never"]):
                feature_style = "glitch_kinetic"
                feature_zone = "center"

            elif any(w in text_lower for w in ["key", "grow", "core", "focus", "goal", "scale"]):
                feature_style = "minimal_underline"
                feature_zone = "upper"

            elif any(w in text_lower for w in ["how to", "plan", "start", "action"]):
                feature_style = "serif_title"
                feature_zone = "upper"
                feature_decorations = ["ellipse"]

            elif any(w in text_lower for w in ["everything", "basically", "definition", "concept"]):
                feature_style = "blob_card"
                feature_variant = "frosted" if self.preset == "calm_serif" else "glow"
                feature_zone = "center"
                feature_decorations = ["sparkles"]

            elif any(w in text_lower for w in ["rather than", "luck", "maybe", "whisper", "honestly"]):
                feature_style = "handwritten"
                feature_zone = "upper"

            elif len(p.words) in (2, 3) and all(len(w) <= 3 for w in words_in_phrase):
                feature_style = "arc_letters"
                feature_zone = "center"

            else:
                detected_graphic = detect_graphic_for_text(p.text) if self.preset != "calm_serif" else None
                if detected_graphic:
                    feature_style = "sticker"
                    feature_graphic = detected_graphic
                    feature_zone = "center"
                elif total_phrases >= 6 and (idx % 2 == 1 or len(used_styles) < min(14, total_phrases)):
                    # Rotate in fresh unused styles to guarantee at least 10-15 styles in the video
                    unused = [s for s in all_feature_styles if s not in used_styles]
                    if unused:
                        feature_style = unused[0]
                    else:
                        available = [s for s in all_feature_styles if s not in recent_styles]
                        feature_style = available[0] if available else all_feature_styles[idx % len(all_feature_styles)]
                    feature_zone = "upper" if idx % 2 == 0 else "center"

            if not feature_style:
                continue

            # Anti-repetition check: do not repeat recently used styles
            if feature_style in recent_styles:
                unused = [s for s in all_feature_styles if s not in used_styles and s not in recent_styles]
                if unused:
                    feature_style = unused[0]
                else:
                    alternates = [s for s in all_feature_styles if s not in recent_styles]
                    if alternates:
                        feature_style = alternates[0]

            used_styles.add(feature_style)
            recent_styles.append(feature_style)
            if len(recent_styles) > window_size:
                recent_styles.pop(0)

            # Highlights for the feature event
            event_highlights = detect_highlights(p.words)
            graphic_item = feature_graphic or detect_graphic_for_text(p.text)

            feat_s = round(p.start, 2)
            feat_e = max(round(p.end, 2), round(feat_s + 0.35, 2))
            if video_duration > 0 and feat_e > video_duration:
                feat_e = round(video_duration, 2)
                feat_s = max(0.0, round(feat_e - 0.35, 2))

            events.append(
                TimelineEvent(
                    id=f"feat_{p.id}",
                    style=feature_style,
                    start=feat_s,
                    end=feat_e,
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
