"""AI Viral Clip Extractor for Reels, TikToks, and Shorts.

Analyzes long videos and podcasts using LLM (Mistral / Gemini / Anthropic)
or rule-based heuristics to discover high-impact, standalone viral clips
(15s, 30s, 60s) with auto-assigned viral headline hooks.
"""
import json
import logging
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, List, Optional
from pydantic import BaseModel, Field
from backend.schemas.timeline import Timeline

logger = logging.getLogger("viral_clips")


class SocialPost(BaseModel):
    """Generated social media copy ready to paste into TikTok, Reels, or Shorts."""
    hook: str = Field(default="", description="Opening viral hook line")
    caption: str = Field(default="", description="Engaging caption paragraph with call-to-action")
    hashtags: List[str] = Field(default_factory=list, description="Targeted trending hashtags")


class ViralClip(BaseModel):
    """A self-contained viral reel or clip candidate."""
    id: str = Field(..., description="Unique clip identifier, e.g. 'clip_1'")
    start: float = Field(..., description="Clip start timestamp in seconds (snapped to phrase start)")
    end: float = Field(..., description="Clip end timestamp in seconds (snapped to phrase end)")
    duration: float = Field(..., description="Clip duration in seconds")
    headline: str = Field(..., description="Viral hook title assigned by AI")
    summary: str = Field(default="", description="1-sentence explanation of why this moment is engaging")
    virality_score: float = Field(default=8.5, description="Predicted virality potential score (1.0 to 10.0)")
    target_length: str = Field(default="30s", description="Target length category: 15s, 30s, 60s")
    keywords: List[str] = Field(default_factory=list, description="Top keywords in this clip")
    social_post: Optional[SocialPost] = Field(default=None, description="Pre-generated viral social media post")


TARGET_DURATIONS = {
    "15s": {"target": 15.0, "min": 8.0, "max": 20.0, "label": "15s Hook Reel"},
    "30s": {"target": 30.0, "min": 20.0, "max": 40.0, "label": "30s Story Highlight"},
    "60s": {"target": 60.0, "min": 45.0, "max": 75.0, "label": "60s Deep Discussion"},
}


def _snap_to_phrases(start_sec: float, end_sec: float, phrases: list) -> tuple[float, float]:
    """Snap timestamps to nearest phrase boundaries so sentences aren't cut mid-word."""
    if not phrases:
        return start_sec, end_sec

    # Find phrase closest to start_sec
    best_start = phrases[0]["start"] if isinstance(phrases[0], dict) else phrases[0].start
    min_dist_start = float("inf")
    for p in phrases:
        p_start = p["start"] if isinstance(p, dict) else p.start
        dist = abs(p_start - start_sec)
        if dist < min_dist_start:
            min_dist_start = dist
            best_start = p_start

    # Find phrase closest to end_sec (snapped to end of phrase)
    best_end = phrases[-1]["end"] if isinstance(phrases[-1], dict) else phrases[-1].end
    min_dist_end = float("inf")
    for p in phrases:
        p_end = p["end"] if isinstance(p, dict) else p.end
        dist = abs(p_end - end_sec)
        if dist < min_dist_end:
            min_dist_end = dist
            best_end = p_end

    if best_end <= best_start:
        best_end = best_start + 10.0

    return round(best_start, 2), round(best_end, 2)


HIGH_IMPACT_CATEGORIES = {
    "tech": ({"ai", "tech", "model", "system", "code", "livekit", "pipecap", "software", "api", "data", "compute", "algorithm", "python", "javascript", "developer", "automation"}, "🤖"),
    "money": ({"money", "million", "billion", "market", "scale", "cost", "revenue", "dollar", "price", "business", "profit", "sales", "client", "invest", "crypto"}, "💰"),
    "insight": ({"secret", "rule", "key", "lesson", "strategy", "truth", "problem", "solution", "hack", "skills", "mindset", "principle", "advice", "remember", "formula"}, "💡"),
    "warning": ({"mistake", "never", "stop", "danger", "fail", "failure", "wrong", "bottleneck", "risk", "warning", "trap", "avoid", "terrible"}, "🚨"),
    "growth": ({"future", "power", "growth", "success", "scale", "build", "expand", "opportunity", "win", "breakthrough", "transform", "achieve", "elevate"}, "🚀"),
    "curiosity": ({"why", "how", "what", "if", "insane", "crazy", "shocking", "nobody", "everyone", "unbelievable", "secret", "weird"}, "🔥"),
}

FILLER_PREFIXES = [
    r"^(so\s*,?\s*)+",
    r"^(and\s*,?\s*)+",
    r"^(but\s*,?\s*)+",
    r"^(well\s*,?\s*)+",
    r"^(you know\s*,?\s*)+",
    r"^(in my opinion\s*,?\s*)+",
    r"^(basically\s*,?\s*)+",
    r"^(i mean\s*,?\s*)+",
    r"^(actually\s*,?\s*)+",
    r"^(like\s*,?\s*)+",
    r"^(the thing is\s*,?\s*)+",
    r"^(right\s*,?\s*)+",
    r"^(yeah\s*,?\s*)+",
    r"^(now\s*,?\s*)+",
    r"^(look\s*,?\s*)+",
]


def _clean_hook_text(text: str) -> str:
    """Strip colloquial fillers, stuttering, and conversational fluff from hook candidate."""
    cleaned = text.strip()
    for pattern in FILLER_PREFIXES:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE).strip()
    return cleaned


def generate_smart_headline(window_phrases: list[dict], full_text: str) -> tuple[str, str, list[str]]:
    """Synthesize a high-retention viral headline, contextual 2-sentence summary, and tags."""
    if not window_phrases:
        return "🔥 WATCH THIS HIGHLIGHT", "Key moment from the video", ["#viral", "#reels"]

    words_lower = set(re.findall(r"\b\w+\b", full_text.lower()))

    # Determine matched categories and hashtags
    hashtags = ["#podcast", "#viral", "#reels", "#shorts"]
    for cat, (cat_words, _) in HIGH_IMPACT_CATEGORIES.items():
        if words_lower.intersection(cat_words):
            hashtags.append(f"#{cat}")

    # 1. Search for a direct compelling question in the dialogue
    candidate_hooks = []
    q_matches = re.findall(r"([^.!?\n]+\?)", full_text)
    for q in q_matches:
        q_clean = _clean_hook_text(q).strip(" ?.,!")
        if len(q_clean.split()) >= 3 and len(q_clean) >= 12:
            candidate_hooks.append((q_clean + "?", 3.5))

    # 2. Extract best phrases across the window
    for idx, p in enumerate(window_phrases[:8]):
        raw_t = p["text"].strip()
        cleaned_t = _clean_hook_text(raw_t).strip(" .,!?:;")
        words = cleaned_t.split()
        if len(words) >= 3 and len(cleaned_t) >= 10:
            # Earlier phrases get a slight position advantage
            score = max(0.5, 2.5 - (idx * 0.25))
            # Bonus for high impact keywords in this phrase
            matching_impact = 0
            for _, (cat_words, _) in HIGH_IMPACT_CATEGORIES.items():
                matching_impact += len(set(w.lower() for w in words).intersection(cat_words))
            score += min(matching_impact * 0.8, 2.4)
            candidate_hooks.append((cleaned_t, score))

    # Pick the highest scoring hook or fall back to the first phrase
    if candidate_hooks:
        candidate_hooks.sort(key=lambda x: x[1], reverse=True)
        hook_raw = candidate_hooks[0][0]
    else:
        hook_raw = _clean_hook_text(window_phrases[0]["text"]).strip(" .,!?:;")

    # Strip dangling trailing prepositions, articles, and auxiliary words
    DANGLING_TAILS = r"\s+(WITH|THEIR|THE|A|AN|OF|AND|OR|TO|IN|FOR|ON|AT|IS|ARE|WAS|BE|BY|THAT|THIS|IT|SO)\s*$"
    for _ in range(2):
        hook_raw = re.sub(DANGLING_TAILS, "", hook_raw, flags=re.IGNORECASE).strip()

    # Format headline: ALL CAPS, snappy length <= 42 chars
    hook_upper = hook_raw.strip().upper()
    if len(hook_upper) > 40:
        truncated = hook_upper[:38].rsplit(" ", 1)[0]
        truncated = re.sub(DANGLING_TAILS, "", truncated, flags=re.IGNORECASE).strip()
        hook_upper = (truncated if len(truncated) >= 8 else hook_upper[:37]) + "..."

    headline = f"🔥 {hook_upper}" if not hook_upper.startswith("🔥") else hook_upper

    # 3. Contextual 2-sentence summary
    raw_sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", full_text) if len(s.strip()) > 12]
    if len(raw_sentences) >= 2:
        summary = f"{raw_sentences[0]} {raw_sentences[1]}"
    elif raw_sentences:
        summary = raw_sentences[0]
    else:
        summary = full_text[:140]

    if len(summary) > 165:
        summary = summary[:162].rsplit(" ", 1)[0] + "..."

    return headline, summary, hashtags[:7]


def _rule_based_clip_finder(
    phrases: list,
    video_duration: float,
    target_length: str = "30s",
) -> list[ViralClip]:
    """Content-aware rule-based finder discovering high-impact, standalone viral clips."""
    config = TARGET_DURATIONS.get(target_length, TARGET_DURATIONS["30s"])
    target_sec = config["target"]
    min_sec = config["min"]
    max_sec = config["max"]

    # Convert phrases to standard dicts
    clean_phrases = []
    for p in phrases:
        clean_phrases.append({
            "start": round(p["start"] if isinstance(p, dict) else p.start, 2),
            "end": round(p["end"] if isinstance(p, dict) else p.end, 2),
            "text": (p["text"] if isinstance(p, dict) else p.text).strip(),
        })

    # If no phrases provided, return empty list (never return a fake dummy clip!)
    if not clean_phrases:
        return []

    # Adaptive duration scaling: if the available speech span is shorter than min_sec,
    # scale thresholds dynamically so clips are ALWAYS discovered on trimmed clips or short videos!
    available_span = max(clean_phrases[-1]["end"] - clean_phrases[0]["start"], 1.0)
    effective_min_sec = min_sec
    effective_target_sec = target_sec
    effective_max_sec = max_sec

    if available_span < min_sec:
        effective_min_sec = max(3.0, available_span * 0.35)
        effective_target_sec = min(available_span, target_sec)
        effective_max_sec = available_span + 1.0

    HIGH_IMPACT_WORDS = {
        "secret", "never", "always", "stop", "mistake", "why", "how", "insane",
        "crazy", "money", "million", "success", "fail", "future", "truth",
        "power", "rule", "key", "first", "nobody", "everyone", "shocking",
        "ai", "agent", "system", "code", "tech", "growth", "build", "strategy"
    }

    candidates = []
    n = len(clean_phrases)

    for i in range(n):
        p_i = clean_phrases[i]
        start_time = p_i["start"]

        for j in range(i, n):
            p_j = clean_phrases[j]
            end_time = p_j["end"]
            dur = end_time - start_time

            if dur < effective_min_sec:
                continue
            if dur > effective_max_sec:
                break

            # Evaluate this speech window
            window_phrases = clean_phrases[i:j + 1]
            full_text = " ".join(p["text"] for p in window_phrases)
            words = full_text.lower().split()

            # Base score
            score = 6.2

            # Closeness to ideal target duration
            diff_from_target = abs(dur - effective_target_sec)
            score += max(0.0, (4.5 - (diff_from_target * 0.25)))

            # Speech density & cadence: reward full, rich sentences over silence
            wps = len(words) / max(dur, 1.0)
            if 1.8 <= wps <= 3.8:
                score += 1.0

            # Bonus for questions (curiosity gap) or exclamations
            if "?" in full_text:
                score += 1.4
            if "!" in full_text:
                score += 0.8

            # Bonus for high-impact keywords
            matching_keywords = [w.strip(".,!?") for w in words if w.strip(".,!?") in HIGH_IMPACT_WORDS]
            score += min(len(matching_keywords) * 0.4, 2.2)

            # Bonus if opening phrase has a strong hook trigger
            first_words = [w.lower() for w in window_phrases[0]["text"].split()[:4]]
            if any(w in {"why", "how", "what", "if", "you", "so", "the", "this", "here"} for w in first_words):
                score += 0.6

            # Synthesize smart headline, summary, and hashtags from speech content
            headline, summary, hashtags = generate_smart_headline(window_phrases, full_text)

            candidates.append({
                "start": start_time,
                "end": end_time,
                "duration": round(dur, 2),
                "headline": headline,
                "summary": summary,
                "score": round(min(score, 9.8), 1),
                "keywords": list(set(matching_keywords))[:5],
                "hashtags": hashtags,
            })

    # Sort candidates by score descending
    candidates.sort(key=lambda c: c["score"], reverse=True)

    # Filter out heavily overlapping candidates (>45% mutual overlap or duplicate headlines)
    selected = []
    seen_headlines = set()
    # Curate high-impact moments: At least 10 clips, up to 18-20 for long videos
    max_rule_clips = 20 if video_duration >= 1800 else (12 if video_duration >= 600 else 8)
    for cand in candidates:
        if len(selected) >= max_rule_clips:
            break
        # Avoid redundant duplicate titles
        if cand["headline"] in seen_headlines:
            continue
        overlap = False
        for s in selected:
            ov_start = max(cand["start"], s["start"])
            ov_end = min(cand["end"], s["end"])
            if ov_end > ov_start:
                ov_dur = ov_end - ov_start
                # Check overlap against the smaller clip so one does not engulf another
                if ov_dur > (min(cand["duration"], s["duration"]) * 0.45):
                    overlap = True
                    break
        if not overlap:
            selected.append(cand)
            seen_headlines.add(cand["headline"])

    # If no candidates met criteria, synthesize a clip directly from available phrases only if text exists
    if not selected:
        if clean_phrases and any(p["text"] for p in clean_phrases):
            dur = round(min(video_duration, target_sec), 2)
            full_text = " ".join(p["text"] for p in clean_phrases)
            headline, summary, hashtags = generate_smart_headline(clean_phrases, full_text)
            selected.append({
                "start": clean_phrases[0]["start"],
                "end": clean_phrases[-1]["end"] if (clean_phrases[-1]["end"] - clean_phrases[0]["start"]) <= effective_max_sec else round(clean_phrases[0]["start"] + dur, 2),
                "duration": dur,
                "headline": headline,
                "summary": summary,
                "score": 8.0,
                "keywords": ["highlight"],
                "hashtags": hashtags,
            })
        else:
            return []

    result = []
    for idx, c in enumerate(selected, 1):
        clean_headline = c["headline"].replace("🔥 ", "").title()
        social_post = SocialPost(
            hook=f"Wait till you hear this... {clean_headline} 🤯",
            caption=f"Key takeaway from this moment: \"{c.get('summary', '')}\"... Watch till the end and drop your thoughts below! 👇",
            hashtags=c.get("hashtags", ["#podcast", "#viral", "#reels", "#shorts", "#mindset", "#success", "#growth"])
        )
        result.append(
            ViralClip(
                id=f"clip_{idx}",
                start=c["start"],
                end=c["end"],
                duration=c["duration"],
                headline=c["headline"],
                summary=c["summary"],
                virality_score=c["score"],
                target_length=target_length,
                keywords=c.get("keywords", []),
                social_post=social_post,
            )
        )
    return result


def find_viral_clips(
    phrases: list,
    video_duration: float,
    target_length: str = "30s",
    provider: str = "mistral",
    api_key: Optional[str] = None,
    topic_segments: Optional[list] = None,
) -> list[ViralClip]:
    """Discover viral clips from transcript using LLM or rule-based fallback.

    Args:
        phrases: List of transcript phrases with start, end, text
        video_duration: Total video length in seconds
        target_length: Desired clip duration ('15s', '30s', '60s')
        provider: 'mistral', 'gemini', 'anthropic', or 'none'
        api_key: Optional API key override
        topic_segments: Optional pre-analyzed topic segments

    Returns:
        List of ViralClip objects with timestamps snapped to phrases and viral headlines.
    """
    if not phrases or video_duration <= 5.0:
        return _rule_based_clip_finder(phrases, video_duration, target_length)

    # Normalize phrases
    clean_phrases = []
    for p in phrases:
        clean_phrases.append({
            "start": round(p["start"] if isinstance(p, dict) else p.start, 2),
            "end": round(p["end"] if isinstance(p, dict) else p.end, 2),
            "text": (p["text"] if isinstance(p, dict) else p.text).strip(),
        })

    config = TARGET_DURATIONS.get(target_length, TARGET_DURATIONS["30s"])
    target_sec = config["target"]
    min_sec = config["min"]
    max_sec = config["max"]

    resolved_provider = provider.lower()
    if resolved_provider == "none":
        return _rule_based_clip_finder(clean_phrases, video_duration, target_length)

    # Resolve API Key
    resolved_key = api_key
    if not resolved_key:
        env_map = {
            "mistral": "MISTRAL_API_KEY",
            "gemini": "GEMINI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
        }
        env_var = env_map.get(resolved_provider)
        if env_var:
            resolved_key = os.getenv(env_var)

    if not resolved_key:
        logger.info(f"No API key found for provider {resolved_provider}; using rule-based finder.")
        return _rule_based_clip_finder(clean_phrases, video_duration, target_length)

    try:
        llm_clips = []
        if resolved_provider == "mistral":
            llm_clips = _find_clips_with_mistral(
                clean_phrases, video_duration, target_length, target_sec, min_sec, max_sec, resolved_key, topic_segments
            )
        elif resolved_provider == "gemini":
            llm_clips = _find_clips_with_gemini(
                clean_phrases, video_duration, target_length, target_sec, min_sec, max_sec, resolved_key, topic_segments
            )
        else:
            return _rule_based_clip_finder(clean_phrases, video_duration, target_length)

        min_target = 10 if video_duration >= 450 else max(1, int(video_duration // 35))
        max_target = 25 if video_duration >= 1800 else (18 if video_duration >= 600 else 12)

        if not llm_clips:
            return _rule_based_clip_finder(clean_phrases, video_duration, target_length)

        # Prioritize curated LLM viral moments
        # If the LLM discovered at least min_target clips, use them directly (do NOT blindly append 100 rule slices!)
        if len(llm_clips) >= min_target:
            # If there are many LLM clips, keep those with virality >= 8.5 (important points), up to max_target
            high_value_clips = [c for c in llm_clips if c.virality_score >= 8.5]
            if len(high_value_clips) >= min_target:
                final_clips = high_value_clips[:max_target]
            else:
                final_clips = llm_clips[:max_target]
        else:
            # If LLM generated fewer than min_target (e.g. 5-7), supplement with top non-overlapping rule clips until min_target
            final_clips = list(llm_clips)
            rule_clips = _rule_based_clip_finder(clean_phrases, video_duration, target_length)
            for rc in rule_clips:
                if len(final_clips) >= min_target:
                    break
                overlap = False
                for fc in final_clips:
                    ov_start = max(rc.start, fc.start)
                    ov_end = min(rc.end, fc.end)
                    if ov_end > ov_start:
                        ov_dur = ov_end - ov_start
                        if ov_dur > (min(rc.duration, fc.duration) * 0.45):
                            overlap = True
                            break
                if not overlap:
                    final_clips.append(rc)

        for idx, c in enumerate(final_clips, 1):
            c.id = f"clip_{idx}"

        return final_clips
    except Exception as e:
        logger.warning(f"LLM clip extraction failed ({e}); falling back to rule-based finder.")
        return _rule_based_clip_finder(clean_phrases, video_duration, target_length)


def _generate_time_windows(video_duration: float, window_size: float = 240.0, overlap: float = 45.0) -> list[tuple[float, float]]:
    """Generate time windows covering the full video duration so no portion is ever truncated."""
    if video_duration <= window_size:
        return [(0.0, video_duration)]

    windows = []
    start = 0.0
    step = max(window_size - overlap, 30.0)
    while start < video_duration:
        end = min(start + window_size, video_duration)
        windows.append((round(start, 2), round(end, 2)))
        if end >= video_duration:
            break
        start += step
    return windows


def _assemble_and_deduplicate_clips(
    raw_clips: list[dict],
    phrases: list[dict],
    video_duration: float,
    target_length: str,
    target_sec: float,
    min_sec: float,
    max_sec: float,
) -> list[ViralClip]:
    """Snap candidate clips to phrases, eliminate heavy overlap (>50%), sort by virality score, and return ALL clips without arbitrary caps."""
    if not raw_clips:
        return _rule_based_clip_finder(phrases, video_duration, target_length)

    candidates = []
    for rc in raw_clips:
        try:
            raw_start = float(rc.get("start", 0.0))
            raw_end = float(rc.get("end", min(raw_start + target_sec, video_duration)))
        except (ValueError, TypeError):
            continue

        # Snap to phrase boundaries
        snapped_start, snapped_end = _snap_to_phrases(raw_start, raw_end, phrases)
        dur = round(snapped_end - snapped_start, 2)
        if dur < (min_sec * 0.7) or dur > (max_sec * 1.5):
            continue

        headline = rc.get("headline", "").strip()
        summary = rc.get("summary", "").strip()

        # Clean any markdown formatting (asterisks, quotes, backticks, header hashes)
        headline = re.sub(r"[*_`\"]", "", headline).strip()
        headline = re.sub(r"^\s*#+\s*", "", headline).strip()
        summary = re.sub(r"[*_`\"]", "", summary).strip()

        # If headline or summary is generic or missing, synthesize from speech in window
        if not headline or headline in {"🔥 VIRAL HIGHLIGHT", "🔥 WATCH THIS HIGHLIGHT"} or not summary:
            win_phrases = [
                {"start": p["start"] if isinstance(p, dict) else p.start, "end": p["end"] if isinstance(p, dict) else p.end, "text": (p["text"] if isinstance(p, dict) else p.text).strip()}
                for p in phrases
                if (p["start"] if isinstance(p, dict) else p.start) >= (snapped_start - 0.5)
                and (p["end"] if isinstance(p, dict) else p.end) <= (snapped_end + 0.5)
            ]
            if win_phrases:
                full_t = " ".join(p["text"] for p in win_phrases)
                smart_h, smart_s, _ = generate_smart_headline(win_phrases, full_t)
                if not headline or headline in {"🔥 VIRAL HIGHLIGHT", "🔥 WATCH THIS HIGHLIGHT"}:
                    headline = smart_h
                if not summary:
                    summary = smart_s

        if not headline:
            headline = "🔥 VIRAL HIGHLIGHT"
        if not summary:
            summary = "Key discussion highlight"

        # Ensure single emoji prefix if missing
        if headline and not any(ord(char) > 0x1F000 for char in headline[:4]):
            headline = f"🔥 {headline}"

        try:
            score = float(rc.get("virality_score", 8.5))
        except (ValueError, TypeError):
            score = 8.5
        keywords = rc.get("keywords", [])
        if not isinstance(keywords, list):
            keywords = []

        clean_h = re.sub(r"^[^\w\s]+\s*", "", headline).title()
        sp = rc.get("social_post")
        if isinstance(sp, dict):
            social_post = SocialPost(
                hook=sp.get("hook", f"Wait till you hear this... {clean_h}"),
                caption=sp.get("caption", summary),
                hashtags=sp.get("hashtags", ["#podcast", "#viral", "#shorts", "#reels"]),
            )
        else:
            social_post = SocialPost(
                hook=f"Wait till you hear this... {clean_h} 🤯",
                caption=f"{summary} Watch till the end and share your thoughts! 👇",
                hashtags=["#podcast", "#viral", "#reels", "#shorts", "#trending"],
            )

        candidates.append({
            "start": snapped_start,
            "end": snapped_end,
            "duration": dur,
            "headline": headline,
            "summary": summary,
            "score": score,
            "keywords": keywords,
            "social_post": social_post,
        })

    if not candidates:
        return _rule_based_clip_finder(phrases, video_duration, target_length)

    # Sort candidates by virality score descending
    candidates.sort(key=lambda c: c["score"], reverse=True)

    # Filter out heavily overlapping clips (must be at least 50% non-overlapping) and duplicate headlines
    selected = []
    seen_headlines = set()
    for cand in candidates:
        norm_h = re.sub(r"^[^\w\s]+\s*", "", cand["headline"]).lower().strip()
        if norm_h in seen_headlines:
            continue
        overlap = False
        for s in selected:
            ov_start = max(cand["start"], s["start"])
            ov_end = min(cand["end"], s["end"])
            if ov_end > ov_start:
                ov_dur = ov_end - ov_start
                if ov_dur > (min(cand["duration"], s["duration"]) * 0.45):
                    overlap = True
                    break
        if not overlap:
            selected.append(cand)
            seen_headlines.add(norm_h)

    # Build final ViralClip list with ordered ids
    result = []
    for idx, c in enumerate(selected, 1):
        result.append(
            ViralClip(
                id=f"clip_{idx}",
                start=c["start"],
                end=c["end"],
                duration=c["duration"],
                headline=c["headline"],
                summary=c["summary"],
                virality_score=round(c["score"], 1),
                target_length=target_length,
                keywords=c["keywords"],
                social_post=c["social_post"],
            )
        )
    return result


def _extract_window_mistral(
    client: Any,
    window_phrases: list[dict],
    win_start: float,
    win_end: float,
    video_duration: float,
    target_length: str,
    target_sec: float,
    min_sec: float,
    max_sec: float,
    win_topics: list[dict],
) -> list[dict]:
    """Call Mistral on a single time window to extract all viral clips in that window without truncation."""
    transcript_lines = [f"[{p['start']:.1f}s - {p['end']:.1f}s]: {p['text']}" for p in window_phrases]
    transcript_text = "\n".join(transcript_lines)

    topics_summary = ""
    if win_topics:
        topics_summary = "\nTopics in this segment:\n" + "\n".join(
            f"- [{t.get('start', 0):.1f}s-{t.get('end', 0):.1f}s] {t.get('title', '')} ({t.get('importance', '')})"
            for t in win_topics
        )

    system_prompt = (
        "You are an elite short-form video editor and viral content strategist (producing for TikTok, Instagram Reels, and YouTube Shorts).\n"
        f"Your task is to analyze this segment of video transcript ({win_start:.1f}s to {win_end:.1f}s) "
        f"and identify standout viral moments and important discussions that fit a target length of {target_length} "
        f"(strictly between {min_sec:.0f}s and {max_sec:.0f}s).\n\n"
        "EDITORIAL SELECTION CRITERIA:\n"
        "1. FOCUS EXCLUSIVELY ON HIGH-VALUE, IMPORTANT POINTS: Only select moments that convey a significant insight, "
        "a counterintuitive lesson, a breakthrough idea, an eye-opening revelation, a heated debate, or high-stakes storytelling.\n"
        "2. STRICTLY EXCLUDE FILLER: Completely ignore routine pleasantries, greetings, administrative talk, podcast housekeeping, "
        "rambling transitions, and mundane explanations.\n"
        "3. BE HIGHLY SELECTIVE: Quality over quantity. If this segment contains NO genuinely important or viral points, "
        "return an empty list: {\"clips\": []}. Do NOT force clips from ordinary conversation.\n"
        "If there are strong moments, extract at most 1 or 2 top-tier highlights from this window.\n"
        "4. COMPLETE, COHERENT THOUGHTS: Each clip must have a hook opening, the core insight/story, and a satisfying punchline or resolution. "
        "Do NOT cut off mid-thought or mid-sentence. Snap start and end times to the provided phrase timestamps.\n"
        "5. VIRALITY SCORE: Rate honestly from 7.0 to 10.0 based on retention potential and shareability. "
        "Scores of 9.0+ must be reserved for mind-blowing insights, emotional peaks, or game-changing lessons.\n"
        "6. HEADLINE: Create a punchy, click-worthy ALL-CAPS headline preceded by 1 relevant emoji (e.g. '🔥 THE SECRET INSIGHT THAT BUILT NVIDIA'). "
        "CRITICAL: Output pure plain text ONLY. NEVER include markdown asterisks (**), quotes, or backticks in the headline.\n"
        "7. SUMMARY: A concise 1-2 sentence breakdown of the important point made.\n\n"
        "Return ONLY a valid JSON object matching this schema:\n"
        "{\n"
        '  "clips": [\n'
        "    {\n"
        '      "id": "clip_1",\n'
        '      "start": 12.4,\n'
        '      "end": 42.1,\n'
        '      "headline": "🔥 THE #1 REASON PEOPLE QUIT",\n'
        '      "summary": "Breakdown of the psychology behind giving up too early and how to push through.",\n'
        '      "virality_score": 9.4,\n'
        '      "keywords": ["discipline", "quitting", "success"]\n'
        "    }\n"
        "  ]\n"
        "}"
    )

    user_prompt = (
        f"Segment Time Window: {win_start:.1f}s - {win_end:.1f}s (Total Video Duration: {video_duration:.1f}s).\n"
        f"Target Length: {target_length} (approx {target_sec}s, range {min_sec}s - {max_sec}s).\n"
        f"{topics_summary}\n\n"
        f"Full Transcript for this segment:\n{transcript_text}\n\n"
        "Find ONLY the standout viral clips containing an important point or discussion in this segment. "
        "If none exist, return {\"clips\": []}. Return valid JSON only."
    )

    response_text = ""
    for model_name in ["open-mistral-7b", "mistral-small-latest"]:
        try:
            resp = client.chat.complete(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.4,
                response_format={"type": "json_object"},
                max_tokens=4096,
            )
            response_text = resp.choices[0].message.content
            if response_text:
                break
        except Exception as e:
            logger.warning(f"Mistral clip model {model_name} error on window [{win_start}-{win_end}]: {e}")

    if not response_text:
        return []

    try:
        data = json.loads(response_text)
        return data.get("clips", [])
    except Exception as e:
        logger.warning(f"Failed to parse Mistral clip JSON for window [{win_start}-{win_end}]: {e}")
        return []


def _find_clips_with_mistral(
    phrases: list[dict],
    video_duration: float,
    target_length: str,
    target_sec: float,
    min_sec: float,
    max_sec: float,
    api_key: str,
    topic_segments: Optional[list] = None,
) -> list[ViralClip]:
    """Call Mistral across time windows to extract all viral clips without arbitrary caps."""
    try:
        from mistralai.client import Mistral
    except ImportError:
        from mistralai import Mistral

    client = Mistral(api_key=api_key)

    windows = _generate_time_windows(video_duration, window_size=240.0, overlap=45.0)
    all_raw_clips = []

    def scan_win(win_start: float, win_end: float):
        win_phrases = [
            p for p in phrases
            if (p["start"] < win_end and p["end"] > win_start)
        ]
        if len(win_phrases) < 2:
            return []
        win_topics = []
        if topic_segments:
            win_topics = [
                t for t in topic_segments
                if t.get("start", 0) < win_end and t.get("end", 0) > win_start
            ]
        return _extract_window_mistral(
            client=client,
            window_phrases=win_phrases,
            win_start=win_start,
            win_end=win_end,
            video_duration=video_duration,
            target_length=target_length,
            target_sec=target_sec,
            min_sec=min_sec,
            max_sec=max_sec,
            win_topics=win_topics,
        )

    if len(windows) == 1:
        win_start, win_end = windows[0]
        raw = scan_win(win_start, win_end)
        all_raw_clips.extend(raw)
    else:
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(scan_win, ws, we) for ws, we in windows]
            for f in as_completed(futures):
                try:
                    res = f.result()
                    if res:
                        all_raw_clips.extend(res)
                except Exception as e:
                    logger.warning(f"Mistral window scanning error: {e}")

    return _assemble_and_deduplicate_clips(
        raw_clips=all_raw_clips,
        phrases=phrases,
        video_duration=video_duration,
        target_length=target_length,
        target_sec=target_sec,
        min_sec=min_sec,
        max_sec=max_sec,
    )


def _extract_window_gemini(
    client: Any,
    window_phrases: list[dict],
    win_start: float,
    win_end: float,
    video_duration: float,
    target_length: str,
    target_sec: float,
    min_sec: float,
    max_sec: float,
    win_topics: list[dict],
) -> list[dict]:
    """Call Google Gemini on a single time window to extract all viral clips in that window without truncation."""
    from google.genai import types

    transcript_lines = [f"[{p['start']:.1f}s - {p['end']:.1f}s]: {p['text']}" for p in window_phrases]
    transcript_text = "\n".join(transcript_lines)

    topics_summary = ""
    if win_topics:
        topics_summary = "\nTopics in this segment:\n" + "\n".join(
            f"- [{t.get('start', 0):.1f}s-{t.get('end', 0):.1f}s] {t.get('title', '')} ({t.get('importance', '')})"
            for t in win_topics
        )

    prompt = (
        "You are an elite short-form video editor and viral content strategist (producing for TikTok, Instagram Reels, and YouTube Shorts).\n"
        f"Analyze this segment of video transcript ({win_start:.1f}s to {win_end:.1f}s, total video {video_duration:.1f}s) "
        f"and extract standout viral moments / important discussions that fit a target length of {target_length} "
        f"(strictly between {min_sec:.0f}s and {max_sec:.0f}s).\n\n"
        "EDITORIAL SELECTION CRITERIA:\n"
        "1. FOCUS ON HIGH-VALUE, IMPORTANT POINTS: Only select moments that contain a significant insight, counterintuitive lesson, "
        "breakthrough idea, passionate debate, eye-opening revelation, or high-stakes storytelling.\n"
        "2. STRICTLY EXCLUDE FILLER: Ignore routine pleasantries, greetings, administrative talk, podcast housekeeping, rambling transitions, and mundane explanations.\n"
        "3. BE HIGHLY SELECTIVE: If this segment contains NO genuinely important points or viral moments, return: {\"clips\": []}. "
        "If there are strong moments, extract at most 1 or 2 top-tier highlights from this window.\n"
        "4. COMPLETE THOUGHTS: Each clip must be a complete, self-contained thought with hook, point, and punchline. Snap start/end times to phrase timestamps.\n"
        "5. VIRALITY SCORE: Rate honestly from 7.0 to 10.0 (9.0+ reserved for game-changing revelations).\n"
        "6. HEADLINE: Punchy ALL-CAPS headline with 1 leading emoji. Pure plain text ONLY (NO markdown asterisks **, NO quotes, NO backticks).\n\n"
        f"{topics_summary}\n\n"
        f"Transcript:\n{transcript_text}\n\n"
        "Return ONLY a JSON object: {\"clips\": [{\"id\": \"clip_1\", \"start\": float, \"end\": float, \"headline\": \"🔥 ...\", \"summary\": \"...\", \"virality_score\": 9.2, \"keywords\": [...]}]}"
    )

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.3,
                max_output_tokens=4096,
            ),
        )
        text = response.text or ""
        data = json.loads(text)
        return data.get("clips", [])
    except Exception as e:
        logger.warning(f"Gemini clip error on window [{win_start}-{win_end}]: {e}")
        return []


def _find_clips_with_gemini(
    phrases: list[dict],
    video_duration: float,
    target_length: str,
    target_sec: float,
    min_sec: float,
    max_sec: float,
    api_key: str,
    topic_segments: Optional[list] = None,
) -> list[ViralClip]:
    """Call Google Gemini across time windows to extract all viral clips without arbitrary caps."""
    from google import genai

    client = genai.Client(api_key=api_key)

    windows = _generate_time_windows(video_duration, window_size=240.0, overlap=45.0)
    all_raw_clips = []

    def scan_win(win_start: float, win_end: float):
        win_phrases = [
            p for p in phrases
            if (p["start"] < win_end and p["end"] > win_start)
        ]
        if len(win_phrases) < 2:
            return []
        win_topics = []
        if topic_segments:
            win_topics = [
                t for t in topic_segments
                if t.get("start", 0) < win_end and t.get("end", 0) > win_start
            ]
        return _extract_window_gemini(
            client=client,
            window_phrases=win_phrases,
            win_start=win_start,
            win_end=win_end,
            video_duration=video_duration,
            target_length=target_length,
            target_sec=target_sec,
            min_sec=min_sec,
            max_sec=max_sec,
            win_topics=win_topics,
        )

    if len(windows) == 1:
        win_start, win_end = windows[0]
        raw = scan_win(win_start, win_end)
        all_raw_clips.extend(raw)
    else:
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(scan_win, ws, we) for ws, we in windows]
            for f in as_completed(futures):
                try:
                    res = f.result()
                    if res:
                        all_raw_clips.extend(res)
                except Exception as e:
                    logger.warning(f"Gemini window scanning error: {e}")

    return _assemble_and_deduplicate_clips(
        raw_clips=all_raw_clips,
        phrases=phrases,
        video_duration=video_duration,
        target_length=target_length,
        target_sec=target_sec,
        min_sec=min_sec,
        max_sec=max_sec,
    )


def slice_timeline_for_clip(
    timeline: Timeline,
    clip_start: float,
    clip_end: float,
    clip_headline: Optional[str] = None,
    trimmed_video_src: Optional[str] = None,
    clip_headline_style: Optional[str] = None,
    clip_headline_duration: Optional[float] = None,
    clip_headline_y: Optional[float] = None,
    caption_size: Optional[str] = None,
    subtitle_y: Optional[float] = None,
    selected_styles: Optional[str] = None,
    watermark_text: Optional[str] = None,
    video_layout: Optional[str] = None,
    ai_enhance: Optional[bool] = False,
    scene_analysis: Optional[dict] = None,
    kinetic_zoom: Optional[bool] = None,
    sound_effects: Optional[bool] = None,
    bg_music: Optional[str] = None,
    progress_bar: Optional[bool] = None,
    auto_emojis: Optional[bool] = None,
    highlight_color: Optional[str] = None,
    multi_style_variety: Optional[bool] = True,
) -> Timeline:
    """Slice a Timeline to a specific clip window [clip_start, clip_end].
    
    Adjusts all events, words, camera cuts, and video duration to start at 0.0,
    and applies any tweaker overrides (headline, location, style, font size, boosters, layout, scene analysis, accent color).
    Guarantees strict safe-zone collision avoidance: captions never render behind the headmarker or over the speaker's face.
    """
    clip_duration = round(clip_end - clip_start, 2)

    # 1. Determine layout
    from backend.schemas.timeline import LAYOUT_ALIASES
    chosen_layout = video_layout or timeline.video.layout or "split_podcast"
    chosen_layout = LAYOUT_ALIASES.get(chosen_layout, chosen_layout)

    # Slice video metadata
    new_video = timeline.video.model_copy(
        update={
            "durationSec": clip_duration,
            "src": trimmed_video_src or timeline.video.src,
            "layout": chosen_layout,
        }
    )

    # Determine styles to apply (Ali Abdaal multi-style editorial director)
    custom_styles = None
    is_ai_director = False
    if multi_style_variety is False:
        # Lock to single consistent style
        first_st = selected_styles.split(",")[0].strip() if selected_styles and selected_styles != "ai_auto" else "pill_word"
        custom_styles = [first_st]
    elif selected_styles and selected_styles.strip() and selected_styles != "ai_auto":
        custom_styles = [s.strip() for s in selected_styles.split(",") if s.strip()]
    elif selected_styles == "ai_auto" or not selected_styles:
        is_ai_director = True
        custom_styles = [
            "highlighter_marker",
            "beast_impact",
            "numbered_point",
            "blob_card",
            "typewriter_terminal",
            "hormozi_bold",
        ]
        if clip_duration > 45.0:
            custom_styles.extend(["cinematic_minimal", "quote_editorial"])

    has_headmarker = bool(
        (clip_headline is not None and clip_headline.strip())
        or (timeline.headlineHook and timeline.headlineHook.strip())
    )
    resolved_hl = highlight_color or timeline.highlightColor

    # 2. Slice events
    new_events = []
    event_idx = 0
    for ev in timeline.events:
        if ev.end > clip_start and ev.start < clip_end:
            shifted_start = max(0.0, round(ev.start - clip_start, 2))
            shifted_end = min(clip_duration, round(ev.end - clip_start, 2))
            dur = round(shifted_end - shifted_start, 2)
            if dur < 0.30:
                # If event is cut off near boundary to < 0.3s, extend end if within clip_duration
                if round(shifted_start + 0.30, 2) <= clip_duration:
                    shifted_end = round(shifted_start + 0.30, 2)
                    dur = round(shifted_end - shifted_start, 2)
                else:
                    # Trailing sub-0.3s fragment at the end of the clip — omit to avoid concurrency collisions
                    continue

            if dur >= 0.30:
                updates = {"start": shifted_start, "end": shifted_end}
                if caption_size:
                    updates["captionSize"] = caption_size
                if subtitle_y is not None:
                    updates["subtitleY"] = subtitle_y

                # Style assignment
                if custom_styles:
                    if is_ai_director:
                        text_lower = (ev.text or "").lower()
                        # Numbered step detection (e.g. "step 1", "number one", "first", "rule")
                        if any(k in text_lower for k in ["rule", "step", "number", "first", "second", "third", "01", "02", "1.", "2."]):
                            assigned_style = "numbered_point" if "numbered_point" in custom_styles else custom_styles[event_idx % len(custom_styles)]
                        # High-impact punchlines & viral moments
                        elif any(k in text_lower for k in ["viral", "moment", "never", "always", "insane", "million", "secret", "biggest", "shocking", "fail", "win", "stop"]):
                            assigned_style = "beast_impact" if (event_idx % 2 == 0) else "hormozi_bold"
                            if assigned_style not in custom_styles:
                                assigned_style = custom_styles[event_idx % len(custom_styles)]
                        # Key educational takeaway / advice / definition
                        elif any(k in text_lower for k in ["because", "means", "remember", "reason", "key", "lesson", "concept", "focus", "how to"]):
                            assigned_style = "highlighter_marker" if "highlighter_marker" in custom_styles else custom_styles[event_idx % len(custom_styles)]
                        # Numbers / stats / tech
                        elif any(ch.isdigit() for ch in ev.text or "") or any(k in text_lower for k in ["system", "code", "ai", "percent", "%", "data"]):
                            assigned_style = "typewriter_terminal" if "typewriter_terminal" in custom_styles else custom_styles[event_idx % len(custom_styles)]
                        # Deep reflection
                        elif len(ev.text or "") > 45:
                            assigned_style = "cinematic_minimal" if "cinematic_minimal" in custom_styles else custom_styles[event_idx % len(custom_styles)]
                        else:
                            assigned_style = custom_styles[event_idx % len(custom_styles)]
                        updates["style"] = assigned_style
                    else:
                        updates["style"] = custom_styles[event_idx % len(custom_styles)]

                # Collision avoidance & Safe zone enforcement:
                # Captions must NEVER render behind the top headmarker ("upper") or across any speaker's face.
                cur_zone = ev.zone or "lower"
                is_split = chosen_layout in ("split_podcast", "split_triple")
                safe_callout_y = 0.50 if is_split else 0.68
                safe_flank_y = 0.50 if is_split else 0.70

                if (has_headmarker and cur_zone == "upper") or cur_zone == "center" or cur_zone == "callout_stack":
                    updates["zone"] = "free"
                    updates["x"] = 0.5
                    updates["y"] = safe_callout_y
                elif cur_zone == "left":
                    updates["zone"] = "free"
                    updates["x"] = 0.26
                    updates["y"] = safe_flank_y
                elif cur_zone == "right":
                    updates["zone"] = "free"
                    updates["x"] = 0.74
                    updates["y"] = safe_flank_y
                elif cur_zone not in ("lower", "upper", "center", "free"):
                    updates["zone"] = "lower"

                # Editorial cards stay stacked safely between speakers or above dialogue subtitles
                assigned_st = updates.get("style", ev.style)
                if assigned_st in ("blob_card", "numbered_point") and updates.get("zone") != "free":
                    updates["zone"] = "free"
                    updates["x"] = 0.5
                    updates["y"] = safe_callout_y

                # Word Highlight & Accent Color
                if resolved_hl:
                    updates["highlightColor"] = resolved_hl
                    if ev.highlights:
                        new_hls = []
                        for hl in ev.highlights:
                            new_hls.append(hl.model_copy(update={"value": resolved_hl}))
                        updates["highlights"] = new_hls

                ev_copy = ev.model_copy(update=updates)
                new_events.append(ev_copy)
                event_idx += 1

    # 3. Slice words
    new_words = []
    for w in timeline.words:
        if w.end > clip_start and w.start < clip_end:
            shifted_start = max(0.0, round(w.start - clip_start, 2))
            shifted_end = min(clip_duration, round(w.end - clip_start, 2))
            if shifted_end > shifted_start:
                new_words.append(w.model_copy(update={"start": shifted_start, "end": shifted_end}))

    # 4. Handle camera cuts for chosen layout
    new_cuts = None
    if chosen_layout == "active_speaker":
        from backend.pipeline.chunk import Phrase
        from backend.pipeline.reframe import build_active_speaker_cuts
        clip_phrases = [
            Phrase(
                id=ev.id,
                text=ev.text,
                start=ev.start,
                end=ev.end,
                speech_start=ev.start,
                speech_end=ev.end,
                word_indices=ev.wordRange or [],
                words=[],
            )
            for ev in new_events
        ]
        num_spk = (scene_analysis or {}).get("num_speakers", 2)
        new_cuts = build_active_speaker_cuts(
            phrases=clip_phrases,
            video_duration=clip_duration,
            num_speakers=num_spk,
            scene_analysis=scene_analysis,
        )
    else:
        # Non-active_speaker layouts (split_podcast, blur_fit, fill, focus_left, focus_right, split_triple)
        # do not require dynamic cuts
        new_cuts = None

    # 5. Build sub-timeline with overrides
    timeline_updates = {
        "video": new_video,
        "videoLayout": chosen_layout,
        "events": new_events,
        "words": new_words,
        "cameraCuts": new_cuts,
        "headlineHook": clip_headline if clip_headline is not None else timeline.headlineHook,
    }
    if clip_headline_style is not None:
        timeline_updates["headlineStyle"] = clip_headline_style
    if clip_headline_duration is not None:
        timeline_updates["headlineDuration"] = clip_headline_duration
    if clip_headline_y is not None:
        timeline_updates["headlineY"] = clip_headline_y
    if watermark_text is not None:
        timeline_updates["watermarkText"] = watermark_text.strip() if watermark_text.strip() else None
    if kinetic_zoom is not None:
        timeline_updates["kineticZoom"] = kinetic_zoom
    if sound_effects is not None:
        timeline_updates["soundEffects"] = sound_effects
    if bg_music is not None:
        timeline_updates["bgMusic"] = bg_music.strip() if bg_music.strip() else None
    if progress_bar is not None:
        timeline_updates["progressBar"] = progress_bar
    if auto_emojis is not None:
        timeline_updates["autoEmojis"] = auto_emojis
    if resolved_hl is not None:
        timeline_updates["highlightColor"] = resolved_hl

    return timeline.model_copy(update=timeline_updates)


def batch_render_viral_clips(
    job_id: str,
    clips: List[ViralClip | dict],
    concurrency: Optional[int] = None,
    draft: bool = False,
    multi_style_variety: Optional[bool] = True,
) -> Path:
    """Batch render a list of viral clips into individual MP4s and bundle into a ZIP archive."""
    import zipfile
    import subprocess
    from pathlib import Path
    from backend.api.runner import get_job_manager
    from backend.pipeline.render import render, prepare_video_asset

    manager = get_job_manager()
    job = manager.get_job(job_id)
    if not job or not job.timeline_file or not Path(job.timeline_file).exists():
        raise ValueError(f"Job {job_id} or timeline not found")

    tl_data = json.loads(Path(job.timeline_file).read_text(encoding="utf-8"))
    base_timeline = Timeline.model_validate(tl_data)

    job_dir = Path("jobs").resolve() / job_id
    batch_dir = job_dir / "batch_clips"
    batch_dir.mkdir(parents=True, exist_ok=True)

    source_video = Path(job.input_file).resolve()
    rendered_files = []

    for idx, raw_clip in enumerate(clips, 1):
        clip = raw_clip if isinstance(raw_clip, ViralClip) else ViralClip.model_validate(raw_clip)

        # Clean title for file name
        safe_headline = re.sub(r'[^\w\s-]', '', clip.headline).strip().replace(" ", "_")[:35]
        clip_name = f"clip_{idx:02d}_{safe_headline}"
        clip_mp4 = batch_dir / f"{clip_name}.mp4"

        # Trim input video for this clip using ffmpeg
        trimmed_video = batch_dir / f"{clip_name}_raw.mp4"
        trim_cmd = [
            "ffmpeg", "-y",
            "-ss", str(clip.start),
            "-to", str(clip.end),
            "-i", str(source_video),
            "-c:v", "libx264", "-c:a", "aac",
            "-avoid_negative_ts", "make_zero",
            str(trimmed_video)
        ]
        subprocess.run(trim_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Prepare asset in remotion public folder
        rel_src = prepare_video_asset(trimmed_video, job_id=f"{job_id}_batch_{idx}")

        # Slice timeline
        sub_timeline = slice_timeline_for_clip(
            timeline=base_timeline,
            clip_start=clip.start,
            clip_end=clip.end,
            clip_headline=clip.headline,
            trimmed_video_src=rel_src,
            multi_style_variety=multi_style_variety,
        )

        # Render with Remotion
        render(
            timeline_input=sub_timeline,
            output_path=clip_mp4,
            concurrency=concurrency,
            draft=draft,
        )
        rendered_files.append((clip_mp4, f"{clip_name}.mp4"))

        # Write social post copy file
        if clip.social_post:
            post_txt = (
                f"=== SOCIAL MEDIA POST ===\n\n"
                f"HOOK:\n{clip.social_post.hook}\n\n"
                f"CAPTION:\n{clip.social_post.caption}\n\n"
                f"HASHTAGS:\n{' '.join(clip.social_post.hashtags)}\n\n"
                f"VIRALITY SCORE: {clip.virality_score}/10\n"
                f"DURATION: {clip.duration}s ({clip.start:.1f}s - {clip.end:.1f}s)\n"
            )
            post_file = batch_dir / f"{clip_name}_post.txt"
            post_file.write_text(post_txt, encoding="utf-8")
            rendered_files.append((post_file, f"{clip_name}_post.txt"))

    # Create ZIP archive
    zip_path = job_dir / f"{job_id}_viral_reels.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for fpath, arcname in rendered_files:
            zf.write(fpath, arcname=arcname)

    return zip_path
