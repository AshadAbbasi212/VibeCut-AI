import os
import logging
from typing import Optional
from backend.pipeline.chunk import Phrase
from backend.schemas.timeline import CameraCut

logger = logging.getLogger("reframe_engine")


def detect_faces_timeline(
    video_path: str,
    model_path: str = "models/face_detection_yunet.onnx",
    step_sec: float = 1.5,
) -> list[dict]:
    """Sample video frames at step_sec intervals and detect face bounding boxes."""
    if not video_path or not os.path.exists(video_path) or not os.path.exists(model_path):
        return []
    try:
        import cv2
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        ret, sample = cap.read()
        if not ret:
            cap.release()
            return []
        h, w = sample.shape[:2]
        detector = cv2.FaceDetectorYN.create(model_path, "", (w, h), score_threshold=0.7)
        step_frames = max(1, int(fps * step_sec))
        timeline_faces = []

        for f_idx in range(0, total_frames, step_frames):
            cap.set(cv2.CAP_PROP_POS_FRAMES, f_idx)
            ret, frame = cap.read()
            if not ret:
                break
            t = f_idx / fps
            detector.setInputSize((w, h))
            _, faces = detector.detect(frame)
            detected = []
            if faces is not None:
                for f in faces:
                    x, y, fw, fh = f[:4]
                    detected.append({
                        "cx": round(float((x + fw / 2) / w), 3),
                        "cy": round(float((y + fh / 2) / h), 3),
                        "fw": round(float(fw / w), 3),
                        "fh": round(float(fh / h), 3),
                    })
            detected.sort(key=lambda d: d["cx"])
            timeline_faces.append({"t": round(t, 2), "faces": detected})
        cap.release()
        return timeline_faces
    except Exception as e:
        logger.warning(f"Face tracking failed or cv2 not available: {e}")
        return []


def _get_scene_for_time(scenes: list[dict], t: float) -> Optional[dict]:
    """Find the scene keyframe analysis corresponding to timestamp t."""
    if not scenes:
        return None
    matched = None
    for s in scenes:
        if s.get("timestamp", 0) <= t:
            matched = s
        else:
            break
    return matched


def _get_nearest_faces(face_samples: list[dict], t: float) -> list[dict]:
    """Find the nearest face detection sample for timestamp t."""
    if not face_samples:
        return []
    best = face_samples[0]
    best_diff = abs(face_samples[0]["t"] - t)
    for s in face_samples:
        diff = abs(s["t"] - t)
        if diff < best_diff:
            best_diff = diff
            best = s
        elif s["t"] > t and diff > best_diff:
            break
    return best.get("faces", [])


def build_active_speaker_cuts(
    phrases: list[Phrase],
    video_duration: float,
    num_speakers: int = 2,
    min_shot_duration: float = 1.8,
    hold_buffer: float = 0.6,
    scene_analysis: Optional[dict] = None,
    video_path: Optional[str] = None,
) -> list[CameraCut]:
    """
    Generate broadcast-quality dynamic camera cuts tracking the active speaker.
    
    Args:
        phrases: Timed spoken phrases
        video_duration: Total video length in seconds
        num_speakers: 2 (duo interview) or 3 (trio panel)
        min_shot_duration: Minimum duration (seconds) before switching cameras (hysteresis)
        hold_buffer: Extra time (seconds) to hold camera on speaker after phrase ends
        scene_analysis: Optional AI scene analysis with keyframe speaker positions
        video_path: Optional path to source video for real-time face tracking
    
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

    # Run computer vision face tracking if video_path is provided
    face_samples = detect_faces_timeline(video_path) if video_path else []

    scenes = (scene_analysis or {}).get("scenes", [])

    # Default seat positions for wide 2-shot or 3-shot fallback:
    # 2 speakers: Left (0.20) and Right (0.82)
    # 3 speakers: Left (0.20), Center (0.50), Right (0.82)
    # 1 speaker: Center (0.50)
    seat_positions = {
        0: 0.20 if num_speakers > 1 else 0.50,
        1: 0.82 if num_speakers == 2 else 0.50,
        2: 0.82,
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

        if has_pause or prev_question:
            current_speaker = (current_speaker + 1) % max(1, num_speakers)

        # Determine camera focus and layout: prioritize real-time computer vision face tracking
        matched_faces = _get_nearest_faces(face_samples, p_start) if face_samples else []
        if matched_faces:
            if len(matched_faces) == 1:
                # Solo close-up camera angle: lock directly on speaker's face horizontal center
                focus_x = matched_faces[0]["cx"]
                layout = "solo"
            else:
                # Wide angle / interview with 2+ speakers in frame
                left_face = matched_faces[0]
                right_face = matched_faces[-1]
                if is_cross_talk:
                    focus_x = 0.50
                    layout = "split_duo" if num_speakers == 2 else "split_trio"
                elif current_speaker == 0:
                    focus_x = left_face["cx"]
                    layout = "solo"
                else:
                    focus_x = right_face["cx"]
                    layout = "solo"
        elif scenes:
            # Fallback to AI scene analysis keyframes
            matched_scene = _get_scene_for_time(scenes, p_start)
            if matched_scene:
                spk_list = matched_scene.get("speakers", [])
                positions = [
                    sp.get("position") if isinstance(sp, dict) else str(sp)
                    for sp in spk_list
                    if sp
                ]
                if not positions or all(pos == "center" for pos in positions) or (len(positions) == 1 and positions[0] == "center"):
                    focus_x = 0.50
                    layout = "solo"
                elif "left" in positions and "right" in positions:
                    if is_cross_talk:
                        focus_x = 0.50
                        layout = "split_duo" if num_speakers == 2 else "split_trio"
                    else:
                        focus_x = 0.20 if current_speaker == 0 else 0.82
                        layout = "solo"
                elif "left" in positions and "right" not in positions:
                    focus_x = 0.20
                    layout = "solo"
                elif "right" in positions and "left" not in positions:
                    focus_x = 0.82
                    layout = "solo"
                else:
                    focus_x = 0.50
                    layout = "solo"
            else:
                focus_x = seat_positions.get(current_speaker, 0.50)
                layout = "solo"
        else:
            if is_cross_talk:
                focus_x = 0.50
                layout = "split_duo" if num_speakers == 2 else "split_trio"
            else:
                focus_x = seat_positions.get(current_speaker, 0.50)
                layout = "solo"

        raw_cuts.append({
            "start": p_start,
            "end": p_end + hold_buffer,
            "focusX": focus_x,
            "speaker": -1 if (is_cross_talk and layout != "solo") else current_speaker,
            "layout": layout,
        })

    if not raw_cuts:
        return [
            CameraCut(
                start=0.0,
                end=video_duration,
                focusX=0.50,
                speakerId="speaker_0",
                layout="split_duo" if num_speakers == 2 else "solo",
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
        
        # If same speaker, layout, and camera framing, extend duration
        if (
            last["speaker"] == c["speaker"]
            and last["layout"] == c["layout"]
            and abs(last["focusX"] - c["focusX"]) < 0.05
        ):
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
