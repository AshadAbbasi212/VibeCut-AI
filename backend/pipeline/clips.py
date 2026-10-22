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
        clean_headline = c["headline"].replace("🔥 ", "").title()
        social_post = SocialPost(
            hook=f"Wait till you hear this... {clean_headline} 🤯",
            caption=f"Key takeaway from this moment: \"{c.get('summary', '')}\"... Watch till the end and drop your thoughts below! 👇",
            hashtags=["#podcast", "#viral", "#reels", "#shorts", "#mindset", "#success", "#growth"]
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

        headline = rc.get("headline", "").strip() or "🔥 VIRAL HIGHLIGHT"
        summary = rc.get("summary", "").strip()
        try:
            score = float(rc.get("virality_score", 8.5))
        except (ValueError, TypeError):
            score = 8.5
        keywords = rc.get("keywords", [])
        if not isinstance(keywords, list):
            keywords = []

        sp = rc.get("social_post")
        if isinstance(sp, dict):
            social_post = SocialPost(
                hook=sp.get("hook", f"Wait till you hear this... {headline}"),
                caption=sp.get("caption", summary),
                hashtags=sp.get("hashtags", ["#podcast", "#viral", "#shorts", "#reels"]),
            )
        else:
            clean_h = headline.replace("🔥 ", "").title()
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

    # Filter out heavily overlapping clips (must be at least 50% non-overlapping)
    # Note: NO CAP on total clips - returns all valid moments across the entire video!
    selected = []
    for cand in candidates:
        overlap = False
        for s in selected:
            ov_start = max(cand["start"], s["start"])
            ov_end = min(cand["end"], s["end"])
            if ov_end > ov_start:
                ov_dur = ov_end - ov_start
                if ov_dur > (cand["duration"] * 0.5):
                    overlap = True
                    break
        if not overlap:
            selected.append(cand)

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
        "You are an elite short-form video producer and viral podcast editor. "
        f"Your task is to analyze this segment of video transcript ({win_start:.1f}s to {win_end:.1f}s) "
        f"and find ALL standalone viral clips / highlights that fit a target length of {target_length} "
        f"(between {min_sec:.0f}s and {max_sec:.0f}s).\n\n"
        "CRITICAL INSTRUCTIONS:\n"
        "1. Extract ALL relevant, standalone viral clips in this segment. Do NOT artificially cap or limit to 3, 5, or 10 clips. "
        "Extract EVERY distinct highlight, punchy insight, debate, or story.\n"
        "2. Each clip must be a complete, coherent thought. Do NOT cut off mid-sentence.\n"
        "3. Snap start and end times to the provided phrase timestamps within this segment.\n"
        "4. Assign an attention-grabbing, viral HEADLINE for each clip (include 1 relevant emoji, ALL-CAPS punch words, "
        "e.g. '🔥 THE BIGGEST MISTAKE YOU MAKE', '🤯 WHY 99% OF PEOPLE FAIL', '⚡ SECRET TO 10X OUTPUT').\n"
        "5. Assign a virality_score between 1.0 and 10.0.\n\n"
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
        f"Segment Time Window: {win_start:.1f}s - {win_end:.1f}s (Total Video Duration: {video_duration:.1f}s).\n"
        f"Target Length: {target_length} (approx {target_sec}s, range {min_sec}s - {max_sec}s).\n"
        f"{topics_summary}\n\n"
        f"Full Transcript for this segment:\n{transcript_text}\n\n"
        "Extract ALL viable viral clips in this segment now. Return valid JSON only."
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
        "You are an elite short-form video producer and viral podcast editor. "
        f"Analyze this segment of video transcript ({win_start:.1f}s to {win_end:.1f}s, total video {video_duration:.1f}s) "
        f"and find ALL viral {target_length} highlights (between {min_sec:.0f}s and {max_sec:.0f}s).\n\n"
        "CRITICAL INSTRUCTIONS:\n"
        "- Extract ALL relevant, standalone viral clips in this segment. Do NOT artificially cap or limit to 3, 5, or 10 clips.\n"
        "- Each clip must be a complete self-contained thought. Snap start/end times to phrase timestamps.\n"
        "- Return ONLY a JSON object: {'clips': [{'id': 'clip_1', 'start': float, 'end': float, 'headline': '🔥 ...', 'summary': '...', 'virality_score': 9.2, 'keywords': [...]}]}.\n\n"
        f"{topics_summary}\n\n"
        f"Transcript:\n{transcript_text}"
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
) -> Timeline:
    """Slice a Timeline to a specific clip window [clip_start, clip_end].
    
    Adjusts all events, words, camera cuts, and video duration to start at 0.0,
    and applies any tweaker overrides (headline, location, style, font size, boosters, layout, scene analysis).
    """
    clip_duration = round(clip_end - clip_start, 2)

    # 1. Determine layout
    chosen_layout = video_layout or timeline.video.layout or "split_podcast"

    # Slice video metadata
    new_video = timeline.video.model_copy(
        update={
            "durationSec": clip_duration,
            "src": trimmed_video_src or timeline.video.src,
            "layout": chosen_layout,
        }
    )

    # Determine styles to apply
    custom_styles = None
    if selected_styles and selected_styles.strip() and selected_styles != "ai_auto":
        custom_styles = [s.strip() for s in selected_styles.split(",") if s.strip()]
    elif selected_styles == "ai_auto":
        # Dynamic AI Creator Director styles based on clip duration / energy
        if clip_duration <= 20.0:
            custom_styles = ["beast_impact", "hormozi_bold"]
        elif clip_duration <= 45.0:
            custom_styles = ["highlighter_marker", "beast_impact", "hormozi_bold"]
        else:
            custom_styles = ["cinematic_minimal", "highlighter_marker"]

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
                if custom_styles:
                    updates["style"] = custom_styles[event_idx % len(custom_styles)]
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
        # Non-active_speaker layouts (split_podcast, blur_fit, fill, focus_left, focus_right)
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

    return timeline.model_copy(update=timeline_updates)


def batch_render_viral_clips(
    job_id: str,
    clips: List[ViralClip | dict],
    concurrency: Optional[int] = None,
    draft: bool = False,
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
