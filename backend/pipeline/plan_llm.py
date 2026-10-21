"""LLM and Rule-based planner implementations for Dynamic Captions Studio.

Supports:
- RulePlanner (deterministic fallback, zero-dependency)
- GeminiPlanner (using google-genai)
- AnthropicPlanner (using anthropic)

Never crashes on LLM failure: validates schema, retries up to 2 times, and falls back to RulePlanner.
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

SYSTEM_PROMPT_TEMPLATE = """You are an expert short-form video editor who designs dynamic animated captions for vertical videos (Reels/Shorts/TikTok). You receive a list of timed phrases from a transcript. For each phrase, decide how it should appear on screen.

Return ONLY valid JSON matching the following schema: a JSON array of event objects.
Each event object has:
- "id": string (e.g. "feat_p1")
- "style": one of ["title3d", "serif_title", "blob_card", "numbered_point", "handwritten", "arc_letters", "sticker"]
- "start": float (seconds)
- "end": float (seconds)
- "zone": "upper" or "center"
- "wordRange": [firstWordIndex, lastWordIndex] (inclusive integers)
- "text": string (must match words in phrase)
- "variant": optional string (e.g. "glow" or "frosted" for blob_card)
- "palette": optional string (e.g. "sunset", "ocean", "candy", "mono")
- "decorations": optional array of strings ["sparkles", "ellipse", "underline_scribble"]
- "highlights": optional array of {"wordIndex": int, "kind": "color"|"italic"|"pill", "value": "#HEX"}
- "graphic": optional {"kind": "emoji"|"icon", "value": "🔥", "position": "above"}

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

        # Prepare base pill captions
        base_events = [
            TimelineEvent(
                id=f"base_{p.id}",
                style="pill_word",
                start=p.start,
                end=p.end,
                zone="lower",
                layer=1,
                wordRange=[p.word_indices[0], p.word_indices[-1]] if p.word_indices else [],
                text=p.text,
            )
            for p in phrases
            if p.word_indices
        ]

        # Prepare phrases summary for LLM
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

        prompt = SYSTEM_PROMPT_TEMPLATE.format(
            preset=preset,
            phrases_json=json.dumps(phrases_data, indent=2),
        )

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

        base_events = [
            TimelineEvent(
                id=f"base_{p.id}",
                style="pill_word",
                start=p.start,
                end=p.end,
                zone="lower",
                layer=1,
                wordRange=[p.word_indices[0], p.word_indices[-1]] if p.word_indices else [],
                text=p.text,
            )
            for p in phrases
            if p.word_indices
        ]

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

        prompt = SYSTEM_PROMPT_TEMPLATE.format(
            preset=preset,
            phrases_json=json.dumps(phrases_data, indent=2),
        )

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


def get_planner(provider: Optional[str] = None, preset: str = "bold_creator") -> BasePlanner:
    """Factory returning the configured planner instance."""
    prov = (provider or os.getenv("LLM_PROVIDER", "none")).lower().strip()
    if prov == "gemini":
        return GeminiPlanner(preset=preset)
    elif prov == "anthropic":
        return AnthropicPlanner(preset=preset)
    else:
        return RulePlanner(preset=preset)
