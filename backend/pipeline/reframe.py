"""
Active Speaker Tracking & Auto-Reframe Engine
Computes camera cut timelines with broadcast pacing rules, spatial speaker mapping,
minimum shot duration hysteresis, and cross-talk / split-screen fallback.
"""
from typing import Optional
from backend.pipeline.chunk import Phrase
from backend.schemas.timeline import CameraCut


def build_active_speaker_cuts(
    phrases: list[Phrase],
    video_duration: float,
    num_speakers: int = 2,
    min_shot_duration: float = 1.8,
    hold_buffer: float = 0.6,
) -> list[CameraCut]:
    """
    Generate broadcast-quality dynamic camera cuts tracking the active speaker.
    
    Args:
        phrases: Timed spoken phrases
        video_duration: Total video length in seconds
        num_speakers: 2 (duo interview) or 3 (trio panel)
        min_shot_duration: Minimum duration (seconds) before switching cameras (hysteresis)
        hold_buffer: Extra time (seconds) to hold camera on speaker after phrase ends
    
    Returns:
        List of non-overlapping CameraCut objects covering [0.0, video_duration]
    """
    if not phrases or video_duration <= 0.1:
        # Default full center or duo split
        return [
            CameraCut(
                start=0.0,
                end=max(0.1, video_duration),
                focusX=0.5,
                speakerId="speaker_0",
                layout="split_duo" if num_speakers == 2 else "solo",
            )
        ]

    # 1. Assign speaker turns to phrases
    # Speaker seat spatial mapping:
    # 2 speakers: Left (0.15) and Right (0.85)
    # 3 speakers: Left (0.15), Center (0.50), Right (0.85)
    seat_positions = {
        0: 0.15,
        1: 0.85 if num_speakers == 2 else 0.50,
        2: 0.85,
    }

    raw_cuts: list[dict] = []
    current_speaker = 0

    for i, p in enumerate(phrases):
        p_start = max(0.0, p.start)
        p_end = min(video_duration, max(p_start + 0.1, p.end))

        # Check for speaker turn indicators:
        # - Long pause between phrases (> 0.65s)
        # - Conversational question mark ending previous phrase
        # - Alternating question/answer turn
        prev_phrase = phrases[i - 1] if i > 0 else None
        has_pause = prev_phrase and (p_start - prev_phrase.end >= 0.65)
        prev_question = prev_phrase and prev_phrase.text.strip().endswith("?")

        # Check for cross-talk / interruption (current start is before previous end)
        is_cross_talk = prev_phrase and (p_start < prev_phrase.end)

        if is_cross_talk:
            # Overlapping speech -> cut to Split Stack
            raw_cuts.append({
                "start": p_start,
                "end": max(p_end, prev_phrase.end) + hold_buffer,
                "focusX": 0.5,
                "speaker": -1, # Cross-talk
                "layout": "split_duo" if num_speakers == 2 else "split_trio",
            })
            continue

        if has_pause or prev_question:
            current_speaker = (current_speaker + 1) % num_speakers

        focus_x = seat_positions.get(current_speaker, 0.5)
        raw_cuts.append({
            "start": p_start,
            "end": p_end + hold_buffer,
            "focusX": focus_x,
            "speaker": current_speaker,
            "layout": "solo",
        })

    if not raw_cuts:
        return [
            CameraCut(
                start=0.0,
                end=video_duration,
                focusX=0.15,
                speakerId="speaker_0",
                layout="split_duo",
            )
        ]

    # 2. Merge cuts and enforce Broadcast Pacing Rules (Minimum Shot Duration)
    # Never cut away in under min_shot_duration seconds (prevents camera whip-lash)
    merged_cuts: list[dict] = []
    
    for c in raw_cuts:
        if not merged_cuts:
            merged_cuts.append(dict(c))
            continue

        last = merged_cuts[-1]
        
        # If same speaker or layout, extend duration
        if last["speaker"] == c["speaker"] and last["layout"] == c["layout"]:
            last["end"] = max(last["end"], c["end"])
            continue

        # If previous cut hasn't satisfied minimum shot duration, keep holding camera on it
        last_dur = last["end"] - last["start"]
        if last_dur < min_shot_duration:
            # Extend previous shot to absorb or defer cut
            gap = min_shot_duration - last_dur
            if c["start"] < last["end"] + gap:
                # Merge into previous to preserve visual stability
                last["end"] = max(last["end"], c["end"])
                continue

        # Connect seamless transitions
        if c["start"] > last["end"]:
            # Brief lull/pause between sentences: hold previous camera angle
            last["end"] = c["start"]
        elif c["start"] < last["end"]:
            c["start"] = last["end"]

        if c["end"] > c["start"]:
            merged_cuts.append(dict(c))

    # 3. Final normalization & boundaries
    final_cuts: list[CameraCut] = []
    
    # Ensure start at 0.0
    if merged_cuts and merged_cuts[0]["start"] > 0.0:
        merged_cuts[0]["start"] = 0.0

    for i, c in enumerate(merged_cuts):
        # Clip to video duration
        c_start = round(max(0.0, c["start"]), 2)
        c_end = round(min(video_duration, c["end"]), 2)

        if i < len(merged_cuts) - 1:
            next_start = round(merged_cuts[i + 1]["start"], 2)
            c_end = max(c_start + 0.1, next_start)
        else:
            c_end = max(c_start + 0.1, round(video_duration, 2))

        speaker_id = f"speaker_{c['speaker']}" if c["speaker"] >= 0 else "cross_talk"
        final_cuts.append(
            CameraCut(
                start=c_start,
                end=c_end,
                focusX=c["focusX"],
                speakerId=speaker_id,
                layout=c.get("layout", "solo"),
            )
        )

    # Ensure last cut reaches video_duration exactly
    if final_cuts:
        final_cuts[-1].end = round(video_duration, 2)

    return final_cuts
