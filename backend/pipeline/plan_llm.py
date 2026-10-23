"""LLM and Rule-based planner implementations for Dynamic Captions Studio.

Supports:
- RulePlanner (deterministic fallback, zero-dependency)
- GeminiPlanner (using google-genai)
- AnthropicPlanner (using anthropic)
- MistralPlanner (using mistralai — free tier supported)

Never crashes on LLM failure: validates schema, retries up to 2 times, and falls back to RulePlanner.

Enhanced with scene-aware intelligence:
- Topic segments → headings get feature styles, regular speech gets consistent base
- Existing burned-in captions → skip those time ranges
- Mood/energy → style selection adapts to scene energy
- Speaker info → caption positioning respects speaker layout
"""
import os
import re
import json
import logging
from abc import ABC, abstractmethod
from typing import Optional

from backend.pipeline.chunk import Phrase
from backend.pipeline.plan_rules import RulePlanner as RuleBasedPlannerCore, group_phrases_into_sentences
from backend.pipeline.layout import assign_layout
from backend.schemas.timeline import TimelineEvent, Highlight, Graphic, AnimationConfig, VALID_STYLES

logger = logging.getLogger("captions_planner")

# ── Shared Prompt Template ───────────────────────────────────────────────────

SYSTEM_PROMPT_TEMPLATE = """You are an expert short-form video editor who designs dynamic animated captions for vertical videos (Reels/Shorts/TikTok) in the style of Ali Abdaal and Alex Hormozi. You receive a list of timed phrases from a transcript. For each phrase, decide how it should appear on screen.

Return ONLY valid JSON matching the following schema: a JSON array of event objects.
Each event object has:
- "id": string (e.g. "feat_p1")
- "style": one of ["title3d", "serif_title", "blob_card", "numbered_point", "handwritten", "arc_letters", "sticker", "neon_glow", "typewriter_terminal", "paper_cutout", "glitch_kinetic", "quote_editorial", "comic_bubble", "gradient_outline", "minimal_underline", "hormozi_bold", "retro_vaporwave", "karaoke_bounce", "fire_burn", "beast_impact", "highlighter_marker", "cinematic_minimal", "cyber_hud"]
- "start": float (seconds)
- "end": float (seconds)
- "zone": "callout_stack", "left", "right", or "lower"
- "wordRange": [firstWordIndex, lastWordIndex] (inclusive integers)
- "text": string (must match words in phrase)
- "variant": optional string (e.g. "glow" or "frosted" for blob_card)
- "palette": optional string (e.g. "sunset", "ocean", "candy", "mono")
- "decorations": optional array of strings ["sparkles", "ellipse", "underline_scribble"]
- "highlights": optional array of {{"wordIndex": int, "kind": "color"|"italic"|"pill", "value": "#HEX"}}
- "graphic": optional {{"kind": "emoji"|"icon", "value": "🔥", "position": "above"}}

CRITICAL PLACEMENT & ANTI-COLLISION RULES:
1. NEVER cover the speaker's face: in vertical video, the face is at y: 0.30 to 0.55. NEVER use center y: 0.50!
2. NEVER place text behind the top headline hook / headmarker: NEVER use "upper" (y < 0.28).
3. Place main points in "callout_stack" (y: 0.68, right above the lower subtitle line) or on margins ("left" x: 0.26, "right" x: 0.74).
4. Continuous speech captions belong in "lower" (y: 0.79).

Guidelines:
- A readable pill_word base caption is added automatically for every phrase in the lower zone, so ONLY return feature impact events.
- Add feature events to roughly 30% of phrases; prefer moments that are claims, hooks, takeaways, numbered points, or emotionally strong.
- Vary styles; never repeat the same feature style more than twice in a row.
- Choose 0-2 emphasis words per feature event (highlights).
- Attach an emoji/icon graphic only when a concrete, recognizable object or concept is mentioned.
- Keep text exactly as spoken.
- Respect the preset: {preset}.

Phrase list (JSON):
{phrases_json}
"""

# ── Scene-Aware Enhanced Prompt ──────────────────────────────────────────────

SCENE_AWARE_PROMPT_TEMPLATE = """You are an elite video editor and creative director designing dynamic, multi-style animated captions — think Ali Abdaal, MrBeast, and Alex Hormozi-level production quality.

You receive a transcript (timed phrases) and a scene analysis of the video. Your job is to be the CREATIVE DIRECTOR: decide which caption style goes where, with professional editorial judgment.

## Your Responsibilities:

### 1. MAIN POINTS & KEY TAKEAWAYS (Ali Abdaal Editorial Technique)
Identify pivotal moments in the video: key claims, counter-intuitive rules, core takeaways, or mind-blowing insights.
For these moments, elevate the SPOKEN WORDS into FEATURE HIGHLIGHTS:
- Educational / Explanations / Core Rules → "highlighter_marker" (marker stroke over key words), "minimal_underline", "pill_word".
- High Impact / Viral Hooks / Punchlines → "beast_impact" (explosive text pop), "hormozi_bold" (high-contrast active word glow), "fire_burn".
- Deep Insights / Reflections → "cinematic_minimal" (clean tracking), "neon_glow", "karaoke_bounce".
- Tech / Data / Numbers → "typewriter_terminal", "cyber_hud".
Use word-level highlights on the punch words (e.g. highlights: [{{"wordIndex": 2, "kind": "color", "value": "#F59E0B"}}]) and contextual graphics/emojis.

CRITICAL RULE — 100% VERBATIM SPOKEN WORDS ONLY (ABSOLUTELY NO HALLUCINATIONS):
- You MUST ONLY use the EXACT words spoken by the speaker in the transcript.
- NEVER invent, summarize, or generate text that the speaker did not speak (e.g. NEVER generate fake textbook titles like "Collaborative AI development...", "[01] Chapter 1", "Why World Models Matter").
- The "text" field MUST be the EXACT verbatim words from the phrase within "wordRange".
- In Ali Abdaal's editing style, captions are 100% authentic spoken speech, never artificial summary cards.

### 2. STRICT PLACEMENT & ANTI-COLLISION RULES (MANDATORY)
- Continuous Speech Subtitles: always in the lower third safe zone ("lower", y: 0.79).
- Main Points & Editorial Callouts:
  * "callout_stack" (y: 0.68): elevated cleanly just above the dialogue subtitle, safely between the speaker's chest and the bottom captions.
  * "left" (x: 0.26, y: 0.70): professional callout in the left margin.
  * "right" (x: 0.74, y: 0.70): professional callout in the right margin.
- CRITICAL PROHIBITIONS:
  * NEVER use "upper" (y < 0.28): text will be hidden behind or collide with the top headmarker / headline hook card!
  * NEVER use "center" (y: 0.40 - 0.55): text will appear directly in front of the speaker's face!
  * All main points must appear cleanly in "callout_stack", "left", "right", or "lower".

### 3. STYLE VARIETY & REPETITION RULES
- **Headings/Main Points**: Use 2-3 recurring "heading styles" like highlighter_marker, beast_impact, or blob_card. These REPEAT throughout to feel cohesive.
- **Key Moments**: Use one-time special styles for hooks (beast_impact), conclusions (cinematic_minimal), technical terms (typewriter_terminal).
- **NEVER repeat the same style more than 3 times in a row.**
- **Use at least 4-5 different styles across the video.**

### 4. SKIP EXISTING CAPTIONS
{existing_captions_instruction}

### 5. ENERGY MATCHING
Match style energy to scene energy:
- High energy → beast_impact, fire_burn, glitch_kinetic, neon_glow
- Medium energy → hormozi_bold, highlighter_marker, gradient_outline, numbered_point
- Low/calm energy → cinematic_minimal, handwritten, minimal_underline, serif_title, quote_editorial
- Educational → highlighter_marker, numbered_point, blob_card, typewriter_terminal

## Available Styles:
["title3d", "serif_title", "blob_card", "numbered_point", "handwritten", "arc_letters", "sticker", "neon_glow", "typewriter_terminal", "paper_cutout", "glitch_kinetic", "quote_editorial", "comic_bubble", "gradient_outline", "minimal_underline", "hormozi_bold", "retro_vaporwave", "karaoke_bounce", "fire_burn", "beast_impact", "highlighter_marker", "cinematic_minimal", "cyber_hud"]

## Scene Analysis:
Video type: {video_type}
Dominant mood: {dominant_mood}
Number of speakers: {num_speakers}

Topic segments:
{topic_segments_json}

## Return Format:
Return ONLY valid JSON — an array of feature event objects:
```json
[
  {{
    "id": "feat_p1",
    "style": "highlighter_marker",
    "start": 0.5,
    "end": 2.3,
    "zone": "callout_stack",
    "wordRange": [0, 5],
    "text": "The three secrets to success",
    "highlights": [{{"wordIndex": 2, "kind": "color", "value": "#FBBF24"}}],
    "graphic": {{"kind": "emoji", "value": "🔥", "position": "above"}},
    "palette": "sunset",
    "decorations": ["sparkles"]
  }}
]
```

Preset: {preset}

Phrase list (JSON):
{phrases_json}
"""


# ── Base Planner Class ───────────────────────────────────────────────────────

class BasePlanner(ABC):
    """Abstract base class for caption planners."""

    @abstractmethod
    def plan(
        self,
        phrases: list[Phrase],
        video_duration: float,
        preset: str = "bold_creator",
        language: str = "en",
        style_pacing: str = "sentence",
        caption_size: str = "medium",
        background_style: str = "transparent",
        highlight_color: str = "#38BDF8",
        selected_styles: Optional[list[str]] = None,
        subtitle_y: Optional[float] = None,
        auto_emojis: bool = True,
        scene_analysis: Optional[dict] = None,
        **kwargs,
    ) -> list[TimelineEvent]:
        """Generate a list of TimelineEvents for the given phrases."""
        pass


class RulePlanner(BasePlanner):
    """Deterministic rule-based planner implementing styling heuristics."""

    def __init__(self, preset: str = "bold_creator"):
        self.preset = preset
        self.core = RuleBasedPlannerCore(preset=preset)

    def plan(
        self,
        phrases: list[Phrase],
        video_duration: float,
        preset: str = "bold_creator",
        language: str = "en",
        style_pacing: str = "sentence",
        caption_size: str = "medium",
        background_style: str = "transparent",
        highlight_color: str = "#38BDF8",
        selected_styles: Optional[list[str]] = None,
        subtitle_y: Optional[float] = None,
        auto_emojis: bool = True,
        scene_analysis: Optional[dict] = None,
        **kwargs,
    ) -> list[TimelineEvent]:
        raw_events = self.core.plan(
            phrases,
            video_duration,
            language=language,
            style_pacing=style_pacing,
            caption_size=caption_size,
            background_style=background_style,
            highlight_color=highlight_color,
            selected_styles=selected_styles,
            subtitle_y=subtitle_y,
            auto_emojis=auto_emojis,
        )
        return assign_layout(raw_events, video_duration=video_duration)


# ── JSON Validation ──────────────────────────────────────────────────────────

def _validate_and_parse_llm_json(
    raw_text: str, phrases: list[Phrase], video_duration: float
) -> list[TimelineEvent]:
    """Parse JSON text from LLM and validate into TimelineEvent objects."""
    # Strip markdown code blocks if present
    cleaned = raw_text.strip()
    if "```" in cleaned:
        # Find opening and closing code fences or outer bracket
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned, re.IGNORECASE)
        if match:
            cleaned = match.group(1).strip()

    # Fallback to finding outermost [ ... ] or { ... }
    if not (cleaned.startswith("[") or cleaned.startswith("{")):
        start_bracket = cleaned.find("[")
        start_brace = cleaned.find("{")
        indices = [i for i in [start_bracket, start_brace] if i != -1]
        if indices:
            first_idx = min(indices)
            if cleaned[first_idx] == "[":
                last_idx = cleaned.rfind("]")
            else:
                last_idx = cleaned.rfind("}")
            if last_idx != -1 and last_idx > first_idx:
                cleaned = cleaned[first_idx : last_idx + 1]

    data = json.loads(cleaned)
    if isinstance(data, dict) and "events" in data:
        data = data["events"]

    if not isinstance(data, list):
        raise ValueError(f"Expected a JSON list of events, got {type(data)}")

    word_map = {}
    for p in phrases:
        for w in p.words:
            word_map[w.i] = w

    parsed_events: list[TimelineEvent] = []
    for item in data:
        # Basic field normalization
        if not isinstance(item, dict):
            continue

        # Check wordRange validity and enforce verbatim spoken dialogue
        wr = item.get("wordRange")
        sub_items: list[dict] = []
        if wr and len(wr) == 2 and wr[0] in word_map and wr[1] in word_map:
            word_span_len = wr[1] - wr[0] + 1
            if word_span_len > 6:
                # SUBDIVIDE long multi-phrase takes into synchronized 3-5 word chunks
                matching_phrases = [
                    p for p in phrases
                    if p.word_indices and max(p.word_indices[0], wr[0]) <= min(p.word_indices[-1], wr[1])
                ]
                if matching_phrases:
                    for s_idx, sp in enumerate(matching_phrases):
                        sub = dict(item)
                        sub["id"] = f"{item.get('id', 'feat')}_{sp.id}"
                        sub["start"] = sp.start
                        sub["end"] = sp.end
                        sub["wordRange"] = [sp.word_indices[0], sp.word_indices[-1]]
                        sub["text"] = sp.text
                        if s_idx > 0:
                            sub.pop("graphic", None)
                        sub_items.append(sub)
                else:
                    for c_start in range(wr[0], wr[1] + 1, 5):
                        c_end = min(wr[1], c_start + 4)
                        sub = dict(item)
                        sub["id"] = f"{item.get('id', 'feat')}_{c_start}"
                        sub["start"] = word_map[c_start].start
                        sub["end"] = word_map[c_end].end
                        sub["wordRange"] = [c_start, c_end]
                        sub["text"] = " ".join([word_map[i].text for i in range(c_start, c_end + 1) if i in word_map])
                        if c_start > wr[0]:
                            sub.pop("graphic", None)
                        sub_items.append(sub)
            else:
                w_start = word_map[wr[0]].start
                w_end = word_map[wr[1]].end
                item["start"] = max(0.0, min(float(item.get("start", w_start)), w_start + 0.15))
                item["end"] = min(video_duration, max(float(item.get("end", w_end)), w_end - 0.15))
                actual_words = [word_map[i].text for i in range(wr[0], wr[1] + 1) if i in word_map]
                if actual_words:
                    item["text"] = " ".join(actual_words)
                sub_items.append(item)
        else:
            # If wordRange is missing or invalid, verify that text was actually spoken
            ev_text = str(item.get("text", "")).strip()
            full_transcript_text = " ".join([w.text for w in word_map.values()]).lower()
            if not ev_text or ev_text.lower() not in full_transcript_text:
                logger.info(f"Dropping non-spoken / hallucinated event: '{ev_text}'")
                continue
            sub_items.append(item)

        for sub_ev in sub_items:
            # Prevent oversized card styles from dominating screen if paragraph-length text
            st = sub_ev.get("style", "")
            words_count = len(sub_ev.get("text", "").split())
            if st in ("blob_card", "numbered_point") and words_count > 10:
                sub_ev["style"] = "highlighter_marker"

            # Sanitize graphic field
            g = sub_ev.get("graphic")
            if isinstance(g, dict):
                valid_kinds = {"emoji", "icon", "image", "sticker3d"}
                if g.get("kind") not in valid_kinds:
                    val = str(g.get("value", ""))
                    # If value contains an emoji, normalize kind to emoji
                    if any(ord(c) > 1000 for c in val):
                        g["kind"] = "emoji"
                    else:
                        sub_ev.pop("graphic", None)
                if "graphic" in sub_ev and isinstance(sub_ev["graphic"], dict):
                    valid_positions = {"above", "below", "left", "right"}
                    if sub_ev["graphic"].get("position") not in valid_positions:
                        sub_ev["graphic"]["position"] = "above"

            # Sanitize highlights field
            hl_list = sub_ev.get("highlights")
            if isinstance(hl_list, list):
                valid_hl_kinds = {"color", "italic", "pill", "underline", "scale"}
                for hl in hl_list:
                    if isinstance(hl, dict) and hl.get("kind") not in valid_hl_kinds:
                        hl["kind"] = "color"

            ev_start = round(float(sub_ev.get("start", 0.0)), 2)
            ev_end = max(round(float(sub_ev.get("end", 0.0)), 2), round(ev_start + 0.35, 2))
            if video_duration > 0 and ev_end > video_duration:
                ev_end = round(video_duration, 2)
                ev_start = max(0.0, round(ev_end - 0.35, 2))
            sub_ev["start"] = ev_start
            # Zone sanitization: prevent hiding behind headmarker ("upper") or blocking speaker face ("center")
            z = sub_ev.get("zone", "lower")
            if z in ("upper", "center", "callout_stack"):
                sub_ev["zone"] = "free"
                sub_ev["x"] = 0.5
                sub_ev["y"] = 0.68
            elif z == "left":
                sub_ev["zone"] = "free"
                sub_ev["x"] = 0.26
                sub_ev["y"] = 0.70
            elif z == "right":
                sub_ev["zone"] = "free"
                sub_ev["x"] = 0.74
                sub_ev["y"] = 0.70
            elif z not in ("lower", "upper", "center", "free"):
                sub_ev["zone"] = "lower"

            ev = TimelineEvent(**sub_ev)
            parsed_events.append(ev)

    return parsed_events


# ── Build Scene-Aware Prompt ─────────────────────────────────────────────────

def _is_ignorable_watermark(text: str, start: float, end: float) -> bool:
    """Check if an existing caption entry is a logo, persistent watermark, or teaser bug."""
    if end - start > 12.0:
        return True
    t = (text or "").lower()
    watermark_keywords = ["logo", "podcast", "coming up", "subscribe", "@", "channel", "watermark", "show", "corner"]
    return any(k in t for k in watermark_keywords)


def _build_scene_aware_prompt(
    phrases: list[Phrase],
    preset: str,
    scene_analysis: Optional[dict],
) -> Optional[str]:
    """Build the scene-aware prompt if analysis data is available."""
    if not scene_analysis:
        return None

    topic_segments = scene_analysis.get("topic_segments", [])
    existing_captions = scene_analysis.get("existing_captions", [])
    video_type = scene_analysis.get("video_type", "talking_head")
    dominant_mood = scene_analysis.get("dominant_mood", "neutral")
    num_speakers = scene_analysis.get("num_speakers", 1)
    has_burned_in = scene_analysis.get("has_burned_in_captions", False)

    # Build skip instruction (ignoring persistent channel logos / watermarks)
    existing_captions_instruction = "No existing captions detected — generate captions for the entire video."
    valid_existing = [
        ec for ec in existing_captions
        if not _is_ignorable_watermark(ec.get("text", ""), ec.get("start", 0), ec.get("end", 0))
    ]
    if has_burned_in and valid_existing:
        skip_ranges = "\n".join(
            f"  - {ec.get('start', 0):.1f}s to {ec.get('end', 0):.1f}s: \"{ec.get('text', '')}\""
            for ec in valid_existing
        )
        existing_captions_instruction = (
            f"The video already has burned-in captions/titles in these time ranges. "
            f"DO NOT generate feature events overlapping these:\n{skip_ranges}"
        )

    phrases_data = [
        {
            "id": p.id,
            "text": p.text,
            "start": round(p.start, 2),
            "end": round(p.end, 2),
            "wordRange": [p.word_indices[0], p.word_indices[-1]] if p.word_indices else [],
        }
        for p in phrases
    ]

    return SCENE_AWARE_PROMPT_TEMPLATE.format(
        preset=preset,
        phrases_json=json.dumps(phrases_data, indent=2),
        video_type=video_type,
        dominant_mood=dominant_mood,
        num_speakers=num_speakers,
        topic_segments_json=json.dumps(topic_segments, indent=2) if topic_segments else "No topic segments detected.",
        existing_captions_instruction=existing_captions_instruction,
    )


def _build_basic_prompt(phrases: list[Phrase], preset: str) -> str:
    """Build the basic (non-scene-aware) prompt."""
    phrases_data = [
        {
            "id": p.id,
            "text": p.text,
            "start": round(p.start, 2),
            "end": round(p.end, 2),
            "wordRange": [p.word_indices[0], p.word_indices[-1]] if p.word_indices else [],
        }
        for p in phrases
    ]
    return SYSTEM_PROMPT_TEMPLATE.format(
        preset=preset,
        phrases_json=json.dumps(phrases_data, indent=2),
    )


CREATOR_VARIETY_STYLES = [
    "highlighter_marker",
    "cinematic_minimal",
    "pill_word",
    "quote_editorial",
    "hormozi_bold",
]


def _build_base_events(
    phrases: list[Phrase],
    scene_analysis: Optional[dict] = None,
    multi_style_variety: bool = True,
    selected_styles: Optional[list[str]] = None,
    style_pacing: str = "sentence",
) -> list[TimelineEvent]:
    """Build base dialogue events with optional professional editorial style variety."""
    skip_ranges = []
    if scene_analysis and scene_analysis.get("has_burned_in_captions"):
        for ec in scene_analysis.get("existing_captions", []):
            start = ec.get("start", 0)
            end = ec.get("end", 0)
            text = ec.get("text", "")
            if _is_ignorable_watermark(text, start, end):
                continue
            skip_ranges.append((start, end))

    # Resolve style pool from user selection or curated professional editorial pool
    custom_pool = [s for s in selected_styles if s in VALID_STYLES] if selected_styles else []
    if not custom_pool or len(custom_pool) >= 8:
        custom_pool = CREATOR_VARIETY_STYLES
        use_anchoring = True
    else:
        use_anchoring = False

    sentence_groups = group_phrases_into_sentences(phrases) if style_pacing == "sentence" else [[p] for p in phrases]
    base_events = []
    current_style = custom_pool[0]

    for g_idx, group in enumerate(sentence_groups):
        if multi_style_variety and len(custom_pool) > 1:
            if use_anchoring:
                # Professional pacing: anchor style across 3-4 sentences (topic thought).
                # Transition on questions or every 3 sentences for calm, cohesive visual flow.
                is_question = group[-1].text.strip().endswith("?") if group else False
                should_transition = is_question or (g_idx > 0 and g_idx % 3 == 0)
                if should_transition:
                    candidates = [s for s in custom_pool if s != current_style]
                    current_style = candidates[(g_idx // 3) % len(candidates)] if candidates else custom_pool[0]
                group_style = current_style
            else:
                group_style = custom_pool[g_idx % len(custom_pool)]
        else:
            group_style = custom_pool[0] if custom_pool else "pill_word"

        for p in group:
            if not p.word_indices:
                continue

            # Check if this phrase overlaps with any confirmed burned-in dialogue
            if skip_ranges:
                should_skip = any(
                    p.start < ec_end and p.end > ec_start
                    for ec_start, ec_end in skip_ranges
                )
                if should_skip:
                    continue

            base_events.append(
                TimelineEvent(
                    id=f"base_{p.id}",
                    style=group_style,
                    start=p.start,
                    end=p.end,
                    zone="lower",
                    layer=1,
                    wordRange=[p.word_indices[0], p.word_indices[-1]],
                    text=p.text,
                )
            )

    return base_events


# ── Mistral Planner ──────────────────────────────────────────────────────────

class MistralPlanner(BasePlanner):
    """Mistral-powered planner (free tier: mistral-small-latest)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "open-mistral-7b",
        preset: str = "bold_creator",
    ):
        self.api_key = api_key or os.getenv("MISTRAL_API_KEY")
        self.model = os.getenv("MISTRAL_MODEL", model)
        self.preset = preset
        self.rule_fallback = RulePlanner(preset=preset)

    def plan(
        self,
        phrases: list[Phrase],
        video_duration: float,
        preset: str = "bold_creator",
        language: str = "en",
        scene_analysis: Optional[dict] = None,
        **kwargs,
    ) -> list[TimelineEvent]:
        if not self.api_key:
            logger.warning("MISTRAL_API_KEY not set. Falling back to RulePlanner.")
            return self.rule_fallback.plan(phrases, video_duration, preset=preset, language=language, **kwargs)

        try:
            from mistralai.client import Mistral
        except ImportError:
            try:
                from mistralai import Mistral
            except ImportError:
                logger.warning("mistralai SDK not installed. Falling back to RulePlanner.")
                return self.rule_fallback.plan(phrases, video_duration, preset=preset, language=language, **kwargs)

        multi_style_variety = kwargs.get("multi_style_variety", True)
        selected_styles = kwargs.get("selected_styles")
        style_pacing = kwargs.get("style_pacing", "sentence")

        base_events = _build_base_events(
            phrases,
            scene_analysis,
            multi_style_variety=multi_style_variety,
            selected_styles=selected_styles,
            style_pacing=style_pacing,
        )

        # Choose prompt: scene-aware if analysis available, else basic
        scene_prompt = _build_scene_aware_prompt(phrases, preset, scene_analysis)
        prompt = scene_prompt or _build_basic_prompt(phrases, preset)

        client = Mistral(api_key=self.api_key)
        feature_events: list[TimelineEvent] = []

        # Candidate models prioritizing free-tier accessible models
        models_to_try = [self.model]
        for fallback_m in ["open-mistral-7b", "pixtral-12b-2409", "mistral-small-latest"]:
            if fallback_m not in models_to_try:
                models_to_try.append(fallback_m)

        last_error = None
        for attempt, target_model in enumerate(models_to_try):
            try:
                current_prompt = prompt
                if last_error:
                    current_prompt += f"\n\nPrevious attempt returned invalid output: {last_error}. Please fix and return ONLY valid JSON array."

                logger.info(f"MistralPlanner calling model {target_model} (attempt {attempt + 1}/{len(models_to_try)})")
                response = client.chat.complete(
                    model=target_model,
                    messages=[{"role": "user", "content": current_prompt}],
                    temperature=0.3,
                )
                text = response.choices[0].message.content or ""
                feature_events = _validate_and_parse_llm_json(text, phrases, video_duration)
                logger.info(f"MistralPlanner successfully generated {len(feature_events)} feature events with model {target_model}")
                break
            except Exception as e:
                last_error = str(e)
                logger.warning(f"MistralPlanner model {target_model} attempt {attempt + 1} failed: {e}")

        if not feature_events:
            logger.warning("MistralPlanner failed after retries. Falling back to RulePlanner.")
            return self.rule_fallback.plan(phrases, video_duration, preset=preset, language=language)

        all_events = base_events + feature_events
        return assign_layout(all_events, video_duration=video_duration)


# ── Gemini Planner ───────────────────────────────────────────────────────────

class GeminiPlanner(BasePlanner):
    """Gemini-powered planner using the official google-genai SDK."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.5-flash", preset: str = "bold_creator"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model = os.getenv("GEMINI_MODEL", model)
        self.preset = preset
        self.rule_fallback = RulePlanner(preset=preset)

    def plan(
        self,
        phrases: list[Phrase],
        video_duration: float,
        preset: str = "bold_creator",
        language: str = "en",
        scene_analysis: Optional[dict] = None,
        **kwargs,
    ) -> list[TimelineEvent]:
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not set. Falling back to RulePlanner.")
            return self.rule_fallback.plan(phrases, video_duration, preset=preset, language=language, **kwargs)

        try:
            from google import genai
            from google.genai import types
        except ImportError:
            logger.warning("google-genai SDK not installed. Falling back to RulePlanner.")
            return self.rule_fallback.plan(phrases, video_duration, preset=preset, language=language, **kwargs)

        multi_style_variety = kwargs.get("multi_style_variety", True)
        selected_styles = kwargs.get("selected_styles")
        style_pacing = kwargs.get("style_pacing", "sentence")

        base_events = _build_base_events(
            phrases,
            scene_analysis,
            multi_style_variety=multi_style_variety,
            selected_styles=selected_styles,
            style_pacing=style_pacing,
        )

        # Choose prompt: scene-aware if analysis available, else basic
        scene_prompt = _build_scene_aware_prompt(phrases, preset, scene_analysis)
        prompt = scene_prompt or _build_basic_prompt(phrases, preset)

        client = genai.Client(api_key=self.api_key)
        feature_events: list[TimelineEvent] = []

        # Retry loop for validation up to 2 times
        last_error = None
        for attempt in range(3):
            try:
                current_prompt = prompt
                if last_error:
                    current_prompt += f"\n\nPrevious attempt returned invalid output: {last_error}. Please fix and return valid JSON."

                response = client.models.generate_content(
                    model=self.model,
                    contents=current_prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.3,
                    ),
                )
                text = response.text or ""
                feature_events = _validate_and_parse_llm_json(text, phrases, video_duration)
                logger.info(f"GeminiPlanner successfully generated {len(feature_events)} feature events on attempt {attempt + 1}")
                break
            except Exception as e:
                last_error = str(e)
                logger.warning(f"GeminiPlanner attempt {attempt + 1} failed: {e}")

        if not feature_events:
            logger.warning("GeminiPlanner failed after retries. Falling back to RulePlanner.")
            return self.rule_fallback.plan(phrases, video_duration, preset=preset, language=language)

        # Merge base events with feature events and apply layout engine
        all_events = base_events + feature_events
        return assign_layout(all_events, video_duration=video_duration)


# ── Anthropic Planner ────────────────────────────────────────────────────────

class AnthropicPlanner(BasePlanner):
    """Anthropic Claude-powered planner."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-3-5-haiku-20241022",
        preset: str = "bold_creator",
    ):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = os.getenv("ANTHROPIC_MODEL", model)
        self.preset = preset
        self.rule_fallback = RulePlanner(preset=preset)

    def plan(
        self,
        phrases: list[Phrase],
        video_duration: float,
        preset: str = "bold_creator",
        language: str = "en",
        scene_analysis: Optional[dict] = None,
        **kwargs,
    ) -> list[TimelineEvent]:
        if not self.api_key:
            logger.warning("ANTHROPIC_API_KEY not set. Falling back to RulePlanner.")
            return self.rule_fallback.plan(phrases, video_duration, preset=preset, language=language, **kwargs)

        try:
            import anthropic
        except ImportError:
            logger.warning("anthropic SDK not installed. Falling back to RulePlanner.")
            return self.rule_fallback.plan(phrases, video_duration, preset=preset, language=language, **kwargs)

        multi_style_variety = kwargs.get("multi_style_variety", True)
        selected_styles = kwargs.get("selected_styles")
        style_pacing = kwargs.get("style_pacing", "sentence")

        base_events = _build_base_events(
            phrases,
            scene_analysis,
            multi_style_variety=multi_style_variety,
            selected_styles=selected_styles,
            style_pacing=style_pacing,
        )

        # Choose prompt: scene-aware if analysis available, else basic
        scene_prompt = _build_scene_aware_prompt(phrases, preset, scene_analysis)
        prompt = scene_prompt or _build_basic_prompt(phrases, preset)

        client = anthropic.Anthropic(api_key=self.api_key)
        feature_events: list[TimelineEvent] = []

        last_error = None
        for attempt in range(3):
            try:
                msg_content = prompt
                if last_error:
                    msg_content += f"\n\nPrevious attempt returned invalid output: {last_error}. Please fix and return ONLY valid JSON array."

                response = client.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    messages=[{"role": "user", "content": msg_content}],
                )
                text = response.content[0].text if response.content else ""
                feature_events = _validate_and_parse_llm_json(text, phrases, video_duration)
                logger.info(f"AnthropicPlanner successfully generated {len(feature_events)} feature events on attempt {attempt + 1}")
                break
            except Exception as e:
                last_error = str(e)
                logger.warning(f"AnthropicPlanner attempt {attempt + 1} failed: {e}")

        if not feature_events:
            logger.warning("AnthropicPlanner failed after retries. Falling back to RulePlanner.")
            return self.rule_fallback.plan(phrases, video_duration, preset=preset, language=language)

        all_events = base_events + feature_events
        return assign_layout(all_events, video_duration=video_duration)


# ── Planner Factory ──────────────────────────────────────────────────────────

def get_planner(
    provider: Optional[str] = None,
    preset: str = "bold_creator",
    api_key: Optional[str] = None,
) -> BasePlanner:
    """Factory returning the configured planner instance."""
    prov = (provider or os.getenv("LLM_PROVIDER", "none")).lower().strip()
    if prov == "gemini":
        return GeminiPlanner(api_key=api_key, preset=preset)
    elif prov == "anthropic":
        return AnthropicPlanner(api_key=api_key, preset=preset)
    elif prov == "mistral":
        return MistralPlanner(api_key=api_key, preset=preset)
    else:
        return RulePlanner(preset=preset)
