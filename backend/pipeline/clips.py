"""AI Viral Clip Extractor for Reels, TikToks, and Shorts.

Analyzes long videos and podcasts using LLM (Mistral / Gemini / Anthropic)
or rule-based heuristics to discover high-impact, standalone viral clips
(15s, 30s, 60s) with auto-assigned viral headline hooks.
"""
import json
import logging
import os
import re
from typing import Any, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("viral_clips")


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


def _rule_based_clip_finder(
    phrases: list,
    video_duration: float,
    target_length: str = "30s",
) -> list[ViralClip]:
    """Fallback rule-based finder using speech energy, question marks, and cadence."""
    config = TARGET_DURATIONS.get(target_length, TARGET_DURATIONS["30s"])
    target_sec = config["target"]
    min_sec = config["min"]
    max_sec = config["max"]

    if not phrases:
        # Generate at least one clip spanning the video
        dur = min(video_duration, target_sec)
        return [
            ViralClip(
                id="clip_1",
                start=0.0,
                end=dur,
                duration=dur,
                headline="🔥 WATCH THIS HIGHLIGHT",
                summary="Key moment from the video",
                virality_score=8.5,
                target_length=target_length,
                keywords=["viral", "highlight"],
            )
        ]

    # Convert phrases to standard dicts
    clean_phrases = []
    for p in phrases:
        clean_phrases.append({
            "start": p["start"] if isinstance(p, dict) else p.start,
            "end": p["end"] if isinstance(p, dict) else p.end,
            "text": (p["text"] if isinstance(p, dict) else p.text).strip(),
        })

    # Hook / impact word triggers
    HIGH_IMPACT_WORDS = {
        "secret", "never", "always", "stop", "mistake", "why", "how", "insane",
        "crazy", "money", "million", "success", "fail", "future", "truth",
        "power", "rule", "key", "first", "nobody", "everyone", "shocking"
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

            if dur < min_sec:
                continue
            if dur > max_sec:
                break

            # Evaluate this window
            window_phrases = clean_phrases[i:j + 1]
            full_text = " ".join(p["text"] for p in window_phrases)
            words = full_text.lower().split()

            score = 6.0

            # Bonus for starting near ideal target duration
            diff_from_target = abs(dur - target_sec)
            score += max(0.0, (5.0 - (diff_from_target * 0.3)))

            # Bonus for questions or exclamation marks
            if "?" in full_text:
                score += 1.2
            if "!" in full_text:
                score += 0.8

            # Bonus for high-impact keywords
            matching_keywords = [w.strip(".,!?") for w in words if w.strip(".,!?") in HIGH_IMPACT_WORDS]
            score += min(len(matching_keywords) * 0.4, 2.0)

            # Bonus if starting with a strong hook
            first_words = [w.lower() for w in window_phrases[0]["text"].split()[:4]]
            if any(w in {"why", "how", "what", "if", "you", "so", "the", "this"} for w in first_words):
                score += 0.7

            # Generate headline
            headline = "🔥 " + window_phrases[0]["text"].upper()
            if len(headline) > 42:
                headline = headline[:39] + "..."

            candidates.append({
                "start": start_time,
                "end": end_time,
                "duration": round(dur, 2),
                "headline": headline,
                "summary": f"Discussion covering: {full_text[:80]}...",
                "score": round(min(score, 9.8), 1),
                "keywords": list(set(matching_keywords))[:5],
            })

    # Sort candidates by score descending
    candidates.sort(key=lambda c: c["score"], reverse=True)

    # Filter out heavily overlapping candidates (must be at least 50% non-overlapping)
    selected = []
    for cand in candidates:
        overlap = False
        for s in selected:
            # Overlap duration
            ov_start = max(cand["start"], s["start"])
            ov_end = min(cand["end"], s["end"])
            if ov_end > ov_start:
                ov_dur = ov_end - ov_start
                if ov_dur > (cand["duration"] * 0.5):
                    overlap = True
                    break
        if not overlap:
            selected.append(cand)
            if len(selected) >= 8:  # Return up to 8 top clips
                break

    # If no candidates met the strict length, take a sliding slice
    if not selected:
        dur = min(video_duration, target_sec)
        selected.append({
            "start": 0.0,
            "end": dur,
            "duration": dur,
            "headline": "🔥 WATCH THIS HIGHLIGHT",
            "summary": "Key excerpt from the video",
            "score": 8.0,
            "keywords": ["highlight"],
        })

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
                virality_score=c["score"],
                target_length=target_length,
                keywords=c.get("keywords", []),
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
        if resolved_provider == "mistral":
            return _find_clips_with_mistral(
                clean_phrases, video_duration, target_length, target_sec, min_sec, max_sec, resolved_key, topic_segments
            )
        elif resolved_provider == "gemini":
            return _find_clips_with_gemini(
                clean_phrases, video_duration, target_length, target_sec, min_sec, max_sec, resolved_key, topic_segments
            )
        else:
            return _rule_based_clip_finder(clean_phrases, video_duration, target_length)
    except Exception as e:
        logger.warning(f"LLM clip extraction failed ({e}); falling back to rule-based finder.")
        return _rule_based_clip_finder(clean_phrases, video_duration, target_length)


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
    """Call Mistral to extract viral clips from transcript."""
    try:
        from mistralai.client import Mistral
    except ImportError:
        from mistralai import Mistral

    client = Mistral(api_key=api_key)

    # Format transcript with timestamps
    transcript_lines = []
    for p in phrases:
        transcript_lines.append(f"[{p['start']:.1f}s - {p['end']:.1f}s]: {p['text']}")
    transcript_text = "\n".join(transcript_lines)

    topics_summary = ""
    if topic_segments:
        topics_summary = "\nKnown Video Topics:\n" + "\n".join(
            f"- [{t.get('start', 0):.1f}s-{t.get('end', 0):.1f}s] {t.get('title', '')} ({t.get('importance', '')})"
            for t in topic_segments[:10]
        )

    system_prompt = (
        "You are an elite short-form video producer and viral podcast editor. "
        "Your task is to analyze the full video transcript and find ALL standalone viral clips / highlights "
        f"that fit a target length of {target_length} (between {min_sec:.0f}s and {max_sec:.0f}s). "
        "Each clip must be a complete, coherent thought, debate, mind-blowing insight, or punchy story. "
        "Do NOT cut off mid-sentence. Snap start and end times to the provided phrase timestamps.\n\n"
        "Assign an attention-grabbing, viral HEADLINE for each clip (include 1 relevant emoji, ALL-CAPS punch words, "
        "e.g. '🔥 THE BIGGEST MISTAKE YOU MAKE', '🤯 WHY 99% OF PEOPLE FAIL', '⚡ SECRET TO 10X OUTPUT'). "
        "Also assign a virality_score between 1.0 and 10.0.\n\n"
        "Return ONLY a valid JSON object matching this schema:\n"
        "{\n"
        '  "clips": [\n'
        "    {\n"
        '      "id": "clip_1",\n'
        '      "start": 12.4,\n'
        '      "end": 42.1,\n'
        '      "headline": "🔥 THE #1 REASON PEOPLE QUIT",\n'
        '      "summary": "Breakdown of the psychology behind giving up too early.",\n'
        '      "virality_score": 9.4,\n'
        '      "keywords": ["discipline", "quitting", "success"]\n'
        "    }\n"
        "  ]\n"
        "}"
    )

    user_prompt = (
        f"Video Duration: {video_duration:.1f} seconds.\n"
        f"Target Length: {target_length} (approx {target_sec} seconds, between {min_sec}s and {max_sec}s).\n"
        f"{topics_summary}\n\n"
        f"Full Transcript:\n{transcript_text[:12000]}\n\n"
        "Find the best viral clips now. Return valid JSON only."
    )

    # Use open-mistral-7b for free tier reliability with fallback to mistral-small-latest
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
            )
            response_text = resp.choices[0].message.content
            if response_text:
                break
        except Exception as e:
            logger.warning(f"Mistral clip model {model_name} error: {e}")

    if not response_text:
        return _rule_based_clip_finder(phrases, video_duration, target_length)

    # Parse JSON
    try:
        data = json.loads(response_text)
        raw_clips = data.get("clips", [])
        if not raw_clips:
            return _rule_based_clip_finder(phrases, video_duration, target_length)

        clips = []
        for idx, rc in enumerate(raw_clips, 1):
            raw_start = float(rc.get("start", 0.0))
            raw_end = float(rc.get("end", min(raw_start + target_sec, video_duration)))

            # Snap to phrase boundaries
            snapped_start, snapped_end = _snap_to_phrases(raw_start, raw_end, phrases)
            dur = round(snapped_end - snapped_start, 2)

            headline = rc.get("headline", "").strip() or f"🔥 HIGHLIGHT #{idx}"
            summary = rc.get("summary", "").strip()
            score = float(rc.get("virality_score", 8.5))
            keywords = rc.get("keywords", [])

            clips.append(
                ViralClip(
                    id=f"clip_{idx}",
                    start=snapped_start,
                    end=snapped_end,
                    duration=dur,
                    headline=headline,
                    summary=summary,
                    virality_score=score,
                    target_length=target_length,
                    keywords=keywords if isinstance(keywords, list) else [],
                )
            )

        # Sort clips by virality_score descending
        clips.sort(key=lambda c: c.virality_score, reverse=True)
        return clips if clips else _rule_based_clip_finder(phrases, video_duration, target_length)

    except Exception as parse_err:
        logger.warning(f"Failed to parse Mistral clip JSON: {parse_err}. Response was: {response_text[:300]}")
        return _rule_based_clip_finder(phrases, video_duration, target_length)


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
    """Call Google Gemini to extract viral clips from transcript."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)

    transcript_lines = [f"[{p['start']:.1f}s - {p['end']:.1f}s]: {p['text']}" for p in phrases]
    transcript_text = "\n".join(transcript_lines)

    prompt = (
        f"You are an elite short-form video editor. Analyze this podcast/video transcript ({video_duration:.1f}s) "
        f"and find ALL viral {target_length} highlights (between {min_sec:.0f}s and {max_sec:.0f}s). "
        "Each clip must be a complete self-contained thought. Snap start/end times to phrase timestamps.\n"
        "Return ONLY a JSON object: {'clips': [{'id': 'clip_1', 'start': float, 'end': float, 'headline': '🔥 ...', 'summary': '...', 'virality_score': 9.2, 'keywords': [...]}]}.\n\n"
        f"Transcript:\n{transcript_text[:12000]}"
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[prompt],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.3,
        ),
    )

    text = response.text or ""
    data = json.loads(text)
    raw_clips = data.get("clips", [])
    clips = []
    for idx, rc in enumerate(raw_clips, 1):
        snapped_start, snapped_end = _snap_to_phrases(float(rc["start"]), float(rc["end"]), phrases)
        clips.append(
            ViralClip(
                id=f"clip_{idx}",
                start=snapped_start,
                end=snapped_end,
                duration=round(snapped_end - snapped_start, 2),
                headline=rc.get("headline", f"🔥 HIGHLIGHT #{idx}"),
                summary=rc.get("summary", ""),
                virality_score=float(rc.get("virality_score", 8.5)),
                target_length=target_length,
                keywords=rc.get("keywords", []),
            )
        )
    clips.sort(key=lambda c: c.virality_score, reverse=True)
    return clips
