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
from backend.pipeline.plan_rules import RulePlanner as RuleBasedPlannerCore
from backend.pipeline.layout import assign_layout
from backend.schemas.timeline import TimelineEvent, Highlight, Graphic, AnimationConfig

logger = logging.getLogger("captions_planner")

# ── Shared Prompt Template ───────────────────────────────────────────────────

SYSTEM_PROMPT_TEMPLATE = """You are an expert short-form video editor who designs dynamic animated captions for vertical videos (Reels/Shorts/TikTok). You receive a list of timed phrases from a transcript. For each phrase, decide how it should appear on screen.

Return ONLY valid JSON matching the following schema: a JSON array of event objects.
Each event object has:
- "id": string (e.g. "feat_p1")
- "style": one of ["title3d", "serif_title", "blob_card", "numbered_point", "handwritten", "arc_letters", "sticker", "neon_glow", "typewriter_terminal", "paper_cutout", "glitch_kinetic", "quote_editorial", "comic_bubble", "gradient_outline", "minimal_underline", "hormozi_bold", "retro_vaporwave", "karaoke_bounce", "fire_burn", "beast_impact", "highlighter_marker", "cinematic_minimal", "cyber_hud"]
- "start": float (seconds)
- "end": float (seconds)
- "zone": "upper" or "center"
- "wordRange": [firstWordIndex, lastWordIndex] (inclusive integers)
- "text": string (must match words in phrase)
- "variant": optional string (e.g. "glow" or "frosted" for blob_card)
- "palette": optional string (e.g. "sunset", "ocean", "candy", "mono")
- "decorations": optional array of strings ["sparkles", "ellipse", "underline_scribble"]
- "highlights": optional array of {{"wordIndex": int, "kind": "color"|"italic"|"pill", "value": "#HEX"}}
- "graphic": optional {{"kind": "emoji"|"icon", "value": "🔥", "position": "above"}}

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

SCENE_AWARE_PROMPT_TEMPLATE = """You are a professional video editor and creative director designing dynamic, multi-style animated captions — think Ali Abdaal, MrBeast, or Hormozi-level production quality.

You receive a transcript (timed phrases) and a scene analysis of the video. Your job is to be the CREATIVE DIRECTOR: decide which caption style goes where, with professional editorial judgment.

## Your Responsibilities:

### 1. HEADINGS & MAIN POINTS → Feature Styles
When the speaker announces a topic, makes a key claim, lists a numbered point, or delivers a punchline:
- Use a DISTINCT feature style (title3d, serif_title, beast_impact, numbered_point, etc.)
- These appear in the "upper" or "center" zone OVERLAPPING with the base caption
- Headings/main points should feel like editorial callouts

### 2. REGULAR SPEECH → Consistent Base (auto-handled)
A pill_word base caption is auto-added for every phrase in the "lower" zone.
You do NOT need to generate these. Only return FEATURE events.

### 3. STYLE VARIETY & REPETITION RULES
- **Headings/Main Points**: Use 2-3 recurring "heading styles" like serif_title, beast_impact, or highlighter_marker. These REPEAT throughout to feel consistent.
- **Key Moments**: Use one-time special styles for hooks (title3d), conclusions (cinematic_minimal), funny moments (comic_bubble), technical terms (typewriter_terminal).
- **NEVER repeat the same style more than 3 times in a row.**
- **Use at least 5 different styles across the video.**

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
    "style": "serif_title",
    "start": 0.5,
    "end": 2.3,
    "zone": "upper",
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

        # Check wordRange validity
        wr = item.get("wordRange")
        if wr and len(wr) == 2 and wr[0] in word_map and wr[1] in word_map:
            w_start = word_map[wr[0]].start
            w_end = word_map[wr[1]].end
            # Allow tolerance if LLM's start/end drift
            item["start"] = max(0.0, min(float(item.get("start", w_start)), w_start + 0.15))
            item["end"] = min(video_duration, max(float(item.get("end", w_end)), w_end - 0.15))

        ev_start = round(float(item.get("start", 0.0)), 2)
        ev_end = max(round(float(item.get("end", 0.0)), 2), round(ev_start + 0.35, 2))
        if video_duration > 0 and ev_end > video_duration:
            ev_end = round(video_duration, 2)
            ev_start = max(0.0, round(ev_end - 0.35, 2))
        item["start"] = ev_start
        item["end"] = ev_end

        ev = TimelineEvent(**item)
        parsed_events.append(ev)

    return parsed_events


# ── Build Scene-Aware Prompt ─────────────────────────────────────────────────

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

    # Build skip instruction
    existing_captions_instruction = "No existing captions detected — generate captions for the entire video."
    if has_burned_in and existing_captions:
        skip_ranges = "\n".join(
            f"  - {ec.get('start', 0):.1f}s to {ec.get('end', 0):.1f}s: \"{ec.get('text', '')}\""
            for ec in existing_captions
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


def _build_base_events(phrases: list[Phrase], scene_analysis: Optional[dict] = None) -> list[TimelineEvent]:
    """Build base pill_word events for all phrases, skipping burned-in caption ranges."""
    skip_ranges = []
    if scene_analysis and scene_analysis.get("has_burned_in_captions"):
        for ec in scene_analysis.get("existing_captions", []):
            skip_ranges.append((ec.get("start", 0), ec.get("end", 0)))

    base_events = []
    for p in phrases:
        if not p.word_indices:
            continue

        # Check if this phrase overlaps with any burned-in caption
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
                style="pill_word",
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
        model: str = "mistral-small-latest",
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
            from mistralai import Mistral
        except ImportError:
            logger.warning("mistralai SDK not installed. Falling back to RulePlanner.")
            return self.rule_fallback.plan(phrases, video_duration, preset=preset, language=language, **kwargs)

        base_events = _build_base_events(phrases, scene_analysis)

        # Choose prompt: scene-aware if analysis available, else basic
        scene_prompt = _build_scene_aware_prompt(phrases, preset, scene_analysis)
        prompt = scene_prompt or _build_basic_prompt(phrases, preset)

        client = Mistral(api_key=self.api_key)
        feature_events: list[TimelineEvent] = []

        last_error = None
        for attempt in range(3):
            try:
                current_prompt = prompt
                if last_error:
                    current_prompt += f"\n\nPrevious attempt returned invalid output: {last_error}. Please fix and return ONLY valid JSON array."

                response = client.chat.complete(
                    model=self.model,
                    messages=[{"role": "user", "content": current_prompt}],
                    temperature=0.3,
                )
                text = response.choices[0].message.content or ""
                feature_events = _validate_and_parse_llm_json(text, phrases, video_duration)
                logger.info(f"MistralPlanner successfully generated {len(feature_events)} feature events on attempt {attempt + 1}")
                break
            except Exception as e:
                last_error = str(e)
                logger.warning(f"MistralPlanner attempt {attempt + 1} failed: {e}")

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

        base_events = _build_base_events(phrases, scene_analysis)

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

        base_events = _build_base_events(phrases, scene_analysis)

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
