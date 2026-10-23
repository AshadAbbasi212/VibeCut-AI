"""Rule-based caption planner implementing intelligent styling heuristics from docs/05."""
import re
from typing import Optional
from backend.pipeline.chunk import Phrase
from backend.pipeline.transcribe import Word
from backend.pipeline.layout import assign_layout
from backend.schemas.timeline import TimelineEvent, Highlight, Graphic, AnimationConfig


# Concrete noun / keyword to emoji mappings
EMOJI_KEYWORDS: dict[str, str] = {
    # Finance / Success
    "money": "💰",
    "cash": "💵",
    "dollar": "💵",
    "rich": "🤑",
    "wealth": "💎",
    "profit": "📈",
    "crypto": "🪙",
    "bitcoin": "🪙",
    "invest": "📊",
    # Energy / Viral
    "fire": "🔥",
    "lit": "🔥",
    "rocket": "🚀",
    "action": "🚀",
    "boom": "💥",
    "viral": "⚡",
    "power": "⚡",
    "magic": "✨",
    "star": "⭐",
    "super": "🌟",
    # Health / Mind
    "doctor": "🩺",
    "medicine": "🩺",
    "hospital": "🏥",
    "brain": "🧠",
    "mind": "🧠",
    "think": "🤔",
    "heart": "❤️",
    "love": "❤️",
    "hate": "💔",
    "time": "⏳",
    "clock": "⏰",
    "fast": "⚡",
    "speed": "🏎️",
    # Objects / Tools
    "phone": "📱",
    "call": "📞",
    "chat": "💬",
    "code": "💻",
    "laptop": "💻",
    "computer": "🖥️",
    "ai": "🤖",
    "robot": "🤖",
    "game": "🎮",
    "music": "🎵",
    "video": "🎥",
    "camera": "📸",
    # Actions / Emotions
    "win": "🏆",
    "winner": "🏆",
    "lose": "❌",
    "stop": "🛑",
    "danger": "⚠️",
    "warning": "⚠️",
    "secret": "🤫",
    "look": "👀",
    "see": "👀",
    "watch": "👀",
    "listen": "🎧",
    "speech": "🗣️",
    "cool": "😎",
    "party": "🎉",
    "lock": "🔒",
    "key": "🔑",
    "target": "🎯",
    "goal": "🎯",
}

ICON_KEYWORDS: dict[str, str] = {
    "skills": "zap",
    "skill": "zap",
    "idea": "lightbulb",
    "ideas": "lightbulb",
    "target": "target",
    "growth": "trending-up",
    "spark": "sparkles",
    "security": "shield",
    "check": "check-circle",
}

# Concrete noun / keyword to 3D sticker mappings
STICKER_3D_KEYWORDS: dict[str, str] = {
    # Finance / Wealth
    "money": "money_bag",
    "cash": "money_bag",
    "dollar": "coin",
    "rich": "money_bag",
    "wealth": "diamond",
    "profit": "chart",
    "crypto": "coin",
    "bitcoin": "coin",
    "invest": "chart",
    # Energy / Viral
    "fire": "fire",
    "lit": "fire",
    "rocket": "rocket",
    "action": "rocket",
    "boom": "boom",
    "viral": "lightning",
    "power": "lightning",
    "magic": "star",
    "star": "star",
    "super": "star",
    # Mind / Thinking
    "brain": "brain",
    "mind": "brain",
    "think": "brain",
    "idea": "lightbulb",
    "ideas": "lightbulb",
    "heart": "heart",
    "love": "heart",
    "time": "clock",
    "clock": "clock",
    "fast": "lightning",
    "speed": "rocket",
    # Tech / Devices
    "ai": "robot",
    "robot": "robot",
    "crown": "crown",
    "king": "crown",
    "queen": "crown",
    "skills": "lightning",
    "skill": "lightning",
    # Actions
    "win": "trophy",
    "winner": "trophy",
    "target": "target",
    "goal": "target",
    "stop": "stop",
    "danger": "warning",
    "warning": "warning",
    "look": "eyes",
    "see": "eyes",
    "watch": "eyes",
    "party": "party",
    "lock": "lock",
    "key": "key",
}

EMPHASIS_KEYWORDS = {
    "not", "never", "no", "stop", "action", "money", "skills", "problem",
    "monetise", "monetize", "actually", "really", "everything", "best", "greatest"
}

ORDINAL_WORDS = {"one", "two", "three", "first", "second", "third", "1", "2", "3"}


def detect_graphic_for_text(text: str, prefer_3d: bool = True) -> Optional[Graphic]:
    """Detect concrete noun in text and return appropriate 3D sticker or graphic."""
    lower_words = [w.lower().strip(".,!?:;\"'") for w in text.split()]
    for w in lower_words:
        if prefer_3d and w in STICKER_3D_KEYWORDS:
            return Graphic(kind="sticker3d", value=STICKER_3D_KEYWORDS[w], position="above")
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


def group_phrases_into_sentences(phrases: list[Phrase]) -> list[list[Phrase]]:
    """Group consecutive phrases into sentences based on punctuation and natural pauses."""
    if not phrases:
        return []

    sentences: list[list[Phrase]] = []
    current_sentence: list[Phrase] = [phrases[0]]

    for i in range(1, len(phrases)):
        prev_p = phrases[i - 1]
        curr_p = phrases[i]

        has_sent_end = any(prev_p.text.rstrip().endswith(p) for p in {".", "!", "?", "—"})
        pause = curr_p.start - prev_p.end
        word_count_in_curr = sum(len(p.words) for p in current_sentence)

        if has_sent_end or pause >= 0.65 or word_count_in_curr >= 14:
            sentences.append(current_sentence)
            current_sentence = [curr_p]
        else:
            current_sentence.append(curr_p)

    if current_sentence:
        sentences.append(current_sentence)

    return sentences


class RulePlanner:
    """Deterministic rule-based planner implementing styling heuristics."""

    def __init__(self, preset: str = "bold_creator"):
        self.preset = preset

    def plan(
        self,
        phrases: list[Phrase],
        video_duration: float,
        language: str = "en",
        style_pacing: str = "sentence",
        caption_size: str = "medium",
        background_style: str = "transparent",
        highlight_color: str = "#38BDF8",
        selected_styles: Optional[list[str]] = None,
        subtitle_y: Optional[float] = None,
        auto_emojis: bool = True,
        multi_style_variety: bool = True,
        **kwargs,
    ) -> list[TimelineEvent]:
        from backend.schemas.timeline import VALID_STYLES

        # Check if user picked custom caption style(s)
        custom_styles = (
            [s for s in selected_styles if s in VALID_STYLES]
            if selected_styles
            else []
        )

        # 1. Custom Single Style Selection (1 style picked or multi_style_variety=False)
        if not multi_style_variety or len(custom_styles) == 1:
            chosen_style = custom_styles[0] if custom_styles else "pill_word"
            events: list[TimelineEvent] = []
            for p in phrases:
                if not p.word_indices:
                    continue
                s = round(p.start, 2)
                e = max(round(p.end, 2), round(s + 0.35, 2))
                if video_duration > 0 and e > video_duration:
                    e = round(video_duration, 2)
                    s = max(0.0, round(e - 0.35, 2))

                highlights = detect_highlights(p.words)
                graphic = detect_graphic_for_text(p.text) if auto_emojis else None
                events.append(
                    TimelineEvent(
                        id=f"evt_{p.id}",
                        style=chosen_style,
                        start=s,
                        end=e,
                        zone="free" if subtitle_y is not None else "lower",
                        x=0.5 if subtitle_y is not None else None,
                        y=round(subtitle_y, 2) if subtitle_y is not None else None,
                        layer=1,
                        wordRange=[p.word_indices[0], p.word_indices[-1]],
                        text=p.text,
                        highlights=highlights if highlights else None,
                        graphic=graphic,
                        captionSize=caption_size,
                        backgroundStyle=background_style,
                        highlightColor=highlight_color,
                        subtitleY=subtitle_y,
                        animation=AnimationConfig(in_="pop", out="fade", wordStagger=0.04),
                    )
                )
            return assign_layout(events, video_duration=video_duration)

        # 2. Custom Multi-Style Selection (2+ styles picked)
        if len(custom_styles) > 1:
            events: list[TimelineEvent] = []
            if style_pacing == "sentence":
                groups = group_phrases_into_sentences(phrases)
            else:
                groups = [[p] for p in phrases]

            # If user selected a small custom subset (2-7 styles), rotate directly between them.
            # If broad pool (>= 8 styles or all styles), constrain to professional editorial quintet and 3-sentence anchoring.
            if len(custom_styles) >= 8:
                from backend.pipeline.plan_llm import CREATOR_VARIETY_STYLES
                pool = CREATOR_VARIETY_STYLES
                use_anchoring = True
            else:
                pool = custom_styles
                use_anchoring = False

            current_style = pool[0]
            for g_idx, group in enumerate(groups):
                if use_anchoring:
                    is_question = group[-1].text.strip().endswith("?") if group else False
                    should_transition = is_question or (g_idx > 0 and g_idx % 3 == 0)
                    if should_transition:
                        candidates = [s for s in pool if s != current_style]
                        current_style = candidates[(g_idx // 3) % len(candidates)] if candidates else pool[0]
                    group_style = current_style
                else:
                    group_style = pool[g_idx % len(pool)]

                sentence_id = f"sent_{g_idx}"
                for p in group:
                    if not p.word_indices:
                        continue
                    s = round(p.start, 2)
                    e = max(round(p.end, 2), round(s + 0.35, 2))
                    if video_duration > 0 and e > video_duration:
                        e = round(video_duration, 2)
                        s = max(0.0, round(e - 0.35, 2))

                    highlights = detect_highlights(p.words)
                    graphic = detect_graphic_for_text(p.text) if auto_emojis else None
                    events.append(
                        TimelineEvent(
                            id=f"evt_{p.id}",
                            style=group_style,
                            start=s,
                            end=e,
                            zone="free" if subtitle_y is not None else "lower",
                            x=0.5 if subtitle_y is not None else None,
                            y=round(subtitle_y, 2) if subtitle_y is not None else None,
                            layer=1,
                            wordRange=[p.word_indices[0], p.word_indices[-1]],
                            text=p.text,
                            highlights=highlights if highlights else None,
                            graphic=graphic,
                            captionSize=caption_size,
                            backgroundStyle=background_style,
                            highlightColor=highlight_color,
                            animation=AnimationConfig(in_="pop", out="fade", wordStagger=0.04),
                            sentenceId=sentence_id,
                        )
                    )
            return events

        # Default multi-style mode (no custom filter selected)
        events: list[TimelineEvent] = []
        total_phrases = len(phrases)

        # Base track: every phrase gets a pill_word event in lower zone
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
                    zone="free" if subtitle_y is not None else "lower",
                    x=0.5 if subtitle_y is not None else None,
                    y=round(subtitle_y, 2) if subtitle_y is not None else None,
                    layer=1,
                    wordRange=[p.word_indices[0], p.word_indices[-1]],
                    text=p.text,
                    captionSize=caption_size,
                    backgroundStyle=background_style,
                    highlightColor=highlight_color,
                )
            )

        if self.preset == "minimal_pill":
            return events

        # Master pool of feature styles including trending new styles
        all_feature_styles = [
            "hormozi_bold",
            "title3d",
            "neon_glow",
            "retro_vaporwave",
            "karaoke_bounce",
            "fire_burn",
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
            "beast_impact",
            "highlighter_marker",
            "cinematic_minimal",
            "cyber_hud",
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
        window_size = 5

        # Group by sentence if style_pacing == "sentence", else group by individual phrase
        if style_pacing == "sentence":
            phrase_groups = group_phrases_into_sentences(phrases)
        else:
            phrase_groups = [[p] for p in phrases]

        total_groups = len(phrase_groups)

        # 2. Add impact feature events across sentence groups ensuring rich distinct styles
        for g_idx, group in enumerate(phrase_groups):
            if not group:
                continue

            group_text = " ".join(p.text for p in group)
            text_lower = group_text.lower()
            all_words_in_group = [w.text.lower().strip(".,!?:;\"'") for p in group for w in p.words]

            feature_style: Optional[str] = None
            feature_zone = "free"
            feature_x: Optional[float] = 0.50
            feature_y: Optional[float] = 0.68
            feature_variant: Optional[str] = None
            feature_palette = "monochrome" if self.preset == "calm_serif" else "sunset"
            feature_decorations: list[str] = []
            feature_graphic: Optional[Graphic] = None

            # Determine semantic candidate style for this sentence
            if any(w in ORDINAL_WORDS for w in all_words_in_group) and any(
                kw in text_lower for kw in ["step", "number", "point", "having", "way"]
            ):
                feature_style = "numbered_point"
                feature_decorations = ["ellipse"]

            elif g_idx == 0:
                feature_style = "serif_title" if self.preset == "calm_serif" else "title3d"
                feature_zone = "free"
                feature_x = 0.50
                feature_y = 0.68
                feature_decorations = ["sparkles"]

            elif any(w in text_lower for w in ["code", "system", "logic", "terminal", "dollar", "percent", "data"]):
                feature_style = "typewriter_terminal"
                feature_zone = "upper"
                feature_x = 0.50
                feature_y = 0.18

            elif any(w in text_lower for w in ["fast", "electric", "power", "money", "future", "online", "crypto"]):
                feature_style = "neon_glow"
                feature_zone = "free"
                feature_x = 0.50
                feature_y = 0.68

            elif any(w in text_lower for w in ["quote", "remember", "said", "truth", "life", "why"]):
                feature_style = "quote_editorial"
                feature_zone = "upper"
                feature_x = 0.50
                feature_y = 0.18

            elif "?" in group_text or "!" in group_text or any(w in text_lower for w in ["wow", "crazy", "secret", "shout", "boom"]):
                feature_style = "comic_bubble"
                feature_zone = "free"
                feature_x = 0.50
                feature_y = 0.68

            elif any(w in text_lower for w in ["stop", "tip", "note", "rule", "warning", "advice"]):
                feature_style = "paper_cutout"
                feature_zone = "upper"
                feature_x = 0.50
                feature_y = 0.18

            elif any(w in text_lower for w in ["suddenly", "break", "glitch", "crash", "wrong", "shock", "never"]):
                feature_style = "glitch_kinetic"
                feature_zone = "free"
                feature_x = 0.50
                feature_y = 0.68

            elif any(w in text_lower for w in ["key", "grow", "core", "focus", "goal", "scale"]):
                feature_style = "minimal_underline"
                feature_zone = "upper"
                feature_x = 0.50
                feature_y = 0.18

            elif any(w in text_lower for w in ["how to", "plan", "start", "action"]):
                feature_style = "serif_title"
                feature_zone = "upper"
                feature_x = 0.50
                feature_y = 0.18
                feature_decorations = ["ellipse"]

            elif any(w in text_lower for w in ["everything", "basically", "definition", "concept"]):
                feature_style = "blob_card"
                feature_variant = "frosted" if self.preset == "calm_serif" else "glow"
                feature_zone = "free"
                feature_x = 0.50
                feature_y = 0.68
                feature_decorations = ["sparkles"]

            elif any(w in text_lower for w in ["rather than", "luck", "maybe", "whisper", "honestly"]):
                feature_style = "handwritten"
                feature_zone = "upper"
                feature_x = 0.50
                feature_y = 0.18

            elif len(all_words_in_group) in (2, 3) and all(len(w) <= 4 for w in all_words_in_group):
                feature_style = "arc_letters"
                feature_zone = "free"
                feature_x = 0.50
                feature_y = 0.68

            else:
                detected_graphic = detect_graphic_for_text(group_text) if self.preset != "calm_serif" else None
                if detected_graphic:
                    feature_style = "sticker"
                    feature_graphic = detected_graphic
                    feature_zone = "free"
                    feature_x = 0.50
                    feature_y = 0.68
                elif total_groups >= 4 and (g_idx % 3 == 0):
                    # Rotate in fresh unused styles on ~35% of non-keyword sentences
                    unused = [s for s in all_feature_styles if s not in used_styles]
                    if unused:
                        feature_style = unused[0]
                    else:
                        available = [s for s in all_feature_styles if s not in recent_styles]
                        feature_style = available[0] if available else all_feature_styles[g_idx % len(all_feature_styles)]
                    feature_zone = "free"
                    feature_x = 0.50
                    feature_y = 0.68

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

            # Generate feature events for each phrase within this sentence group
            sentence_id = f"sent_{g_idx}"
            for p in group:
                if not p.word_indices:
                    continue

                event_highlights = detect_highlights(p.words)
                if highlight_color and event_highlights:
                    for h in event_highlights:
                        if h.kind == "color":
                            h.value = highlight_color

                graphic_item = (feature_graphic or detect_graphic_for_text(p.text)) if auto_emojis else None

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
                        x=feature_x,
                        y=feature_y,
                        layer=2,
                        wordRange=[p.word_indices[0], p.word_indices[-1]],
                        text=p.text,
                        highlights=event_highlights if event_highlights else None,
                        palette=feature_palette,
                        variant=feature_variant,
                        decorations=feature_decorations if feature_decorations else None,
                        graphic=graphic_item,
                        animation=AnimationConfig(in_="pop", out="fade", wordStagger=0.04),
                        captionSize=caption_size,
                        backgroundStyle=background_style,
                        highlightColor=highlight_color,
                        sentenceId=sentence_id,
                    )
                )

        return events
