"""Layout engine: enforces zone assignment, layer order, concurrency limits, safe areas,
and style pacing according to docs/03, docs/04, and docs/05.
"""
from typing import Optional
from backend.schemas.timeline import TimelineEvent


STYLE_ALTERNATIVES = {
    "title3d": "serif_title",
    "serif_title": "blob_card",
    "blob_card": "serif_title",
    "numbered_point": "serif_title",
    "handwritten": "blob_card",
    "arc_letters": "blob_card",
    "sticker": "serif_title",
    "pill_word": "serif_title",
}


def split_lines_balanced(text: str, max_chars_per_line: int = 22, max_lines: int = 3) -> list[str]:
    """Split text into balanced visual lines for 9:16 vertical video layout."""
    words = text.strip().split()
    if not words:
        return [text]
    if len(words) <= 3:
        return [text]

    lines: list[str] = []
    current_line: list[str] = []
    current_len = 0

    for w in words:
        add_len = len(w) + (1 if current_line else 0)
        if current_len + add_len > max_chars_per_line and current_line and len(lines) < max_lines - 1:
            lines.append(" ".join(current_line))
            current_line = [w]
            current_len = len(w)
        else:
            current_line.append(w)
            current_len += add_len

    if current_line:
        lines.append(" ".join(current_line))

    return lines


def _overlaps(s1: float, e1: float, s2: float, e2: float) -> bool:
    """Return True if two half-open intervals [s1, e1) and [s2, e2) overlap."""
    return max(s1, s2) < min(e1, e2)


def assign_layout(
    events: list[TimelineEvent],
    video_duration: float,
    max_concurrent: int = 3,
    min_event_duration: float = 0.35,
) -> list[TimelineEvent]:
    """Adjusts event zones, layers, timings, and style variety to strictly satisfy invariants.

    Invariants enforced:
    1. 0 <= start < end <= video_duration (duration >= min_event_duration).
    2. No more than max_concurrent (3) events active simultaneously at any instant.
    3. No two events in the same zone ('upper', 'center', 'lower') overlap in time.
    4. Base pill_word captions are locked to 'lower' zone and layer 1.
    5. Feature captions are routed to 'upper' or 'center' (never 'lower').
    6. No more than 2 consecutive feature events with the identical style.
    7. 'title3d' used sparingly (at most once per ~10 seconds).
    8. Layers assigned deterministically (layer 1 for base, 2 and 3 for features).
    """
    if not events:
        return []

    # 1. Clamp bounds and ensure minimum duration
    bounded_events: list[TimelineEvent] = []
    for ev in events:
        s = max(0.0, round(ev.start, 2))
        e = min(video_duration, round(ev.end, 2))
        if e - s < min_event_duration:
            e = min(video_duration, round(s + min_event_duration, 2))
            if e - s < min_event_duration:
                s = max(0.0, round(e - min_event_duration, 2))

        if e <= s or (e - s) < 0.30:
            continue

        ev_copy = ev.model_copy(update={"start": s, "end": e})
        bounded_events.append(ev_copy)

    # 2. Separate base track (pill_word in lower) from feature events
    base_events = [e for e in bounded_events if e.style == "pill_word" and e.id.startswith("base_")]
    feature_events = [e for e in bounded_events if not (e.style == "pill_word" and e.id.startswith("base_"))]

    # Clean base events: ensure zone is 'lower' and layer is 1, and no overlapping base events
    base_events.sort(key=lambda x: (x.start, x.end))
    cleaned_base: list[TimelineEvent] = []
    for b in base_events:
        b_up = b.model_copy(update={"zone": "lower", "layer": 1})
        if cleaned_base:
            prev = cleaned_base[-1]
            if b_up.start < prev.end:
                # Resolve slight overlap in base captions by trimming previous
                prev_dur = b_up.start - prev.start
                if prev_dur >= min_event_duration:
                    cleaned_base[-1] = prev.model_copy(update={"end": b_up.start})
                else:
                    # Adjust b_up start and preserve min duration
                    new_start = prev.end
                    new_end = max(b_up.end, round(new_start + min_event_duration, 2))
                    if video_duration > 0 and new_end > video_duration:
                        new_end = round(video_duration, 2)
                    b_up = b_up.model_copy(update={"start": new_start, "end": new_end})
                    if b_up.end - b_up.start < 0.30:
                        continue
        cleaned_base.append(b_up)

    # 3. Process feature events: enforce style variety, zone collisions, and pacing
    feature_events.sort(key=lambda x: (x.start, x.end))
    resolved_features: list[TimelineEvent] = []

    last_feature_style: Optional[str] = None
    consecutive_style_count = 0
    last_title3d_time = -100.0

    for feat in feature_events:
        style = feat.style
        # Enforce title3d frequency limit (at most once every 10s)
        if style == "title3d":
            if feat.start - last_title3d_time < 10.0:
                style = "serif_title"
            else:
                last_title3d_time = feat.start

        # Enforce max 2 consecutive identical styles
        if style == last_feature_style:
            if consecutive_style_count >= 2:
                style = STYLE_ALTERNATIVES.get(style, "serif_title")
                consecutive_style_count = 1
            else:
                consecutive_style_count += 1
        else:
            consecutive_style_count = 1
        last_feature_style = style

        # Safe line splitting
        lines = feat.lines
        if not lines and style in {"title3d", "serif_title", "blob_card", "numbered_point"}:
            lines = split_lines_balanced(feat.text)

        # Zone assignment: feature events must NOT be 'lower'
        target_zone = feat.zone if feat.zone in {"upper", "center", "free"} else "center"

        # Check if target_zone collides with existing placed features
        colliding = [
            placed for placed in resolved_features
            if placed.zone == target_zone and _overlaps(placed.start, placed.end, feat.start, feat.end)
        ]

        if colliding:
            # Try alternate zone
            alt_zone = "upper" if target_zone == "center" else "center"
            alt_colliding = [
                placed for placed in resolved_features
                if placed.zone == alt_zone and _overlaps(placed.start, placed.end, feat.start, feat.end)
            ]
            if not alt_colliding:
                target_zone = alt_zone
            else:
                # Both center and upper are occupied during this window.
                # If overlap can be resolved by shifting start or end, try that:
                latest_end = max(c.end for c in colliding)
                if feat.end - latest_end >= min_event_duration:
                    feat = feat.model_copy(update={"start": latest_end})
                else:
                    # Cannot fit without collision; drop this feature event
                    continue

        # Add resolved feature
        updated_feat = feat.model_copy(
            update={
                "style": style,
                "zone": target_zone,
                "lines": lines,
            }
        )
        resolved_features.append(updated_feat)

    # 4. Merge base and feature events, enforce max concurrency <= max_concurrent
    all_events = sorted(cleaned_base + resolved_features, key=lambda x: (x.start, x.end))

    # Concurrency check across all time slices
    # Sample critical timestamps
    timestamps = set()
    for e in all_events:
        timestamps.add(e.start + 0.005)
        timestamps.add(max(0.0, e.end - 0.005))
        timestamps.add((e.start + e.end) / 2.0)

    final_events: list[TimelineEvent] = list(all_events)
    for t in sorted(timestamps):
        active = [e for e in final_events if e.start <= t < e.end]
        if len(active) > max_concurrent:
            # Too many active events: drop the lowest-priority feature event
            # Base pill_word has high priority for readability; drop newest or shortest feature event
            features_active = [e for e in active if not (e.style == "pill_word" and e.id.startswith("base_"))]
            if features_active:
                features_active.sort(key=lambda x: (x.end - x.start, x.start))
                to_remove = features_active[0]
                final_events = [e for e in final_events if e.id != to_remove.id]

    # 4b. Pacing check on surviving feature events
    final_events.sort(key=lambda x: (x.start, x.end))
    consec_count = 0
    last_style: Optional[str] = None
    pacing_checked_events: list[TimelineEvent] = []

    for ev in final_events:
        if ev.style == "pill_word" and ev.id.startswith("base_"):
            pacing_checked_events.append(ev)
            continue
        st = ev.style
        if st == "pill_word":
            st = "serif_title"
        if st == last_style:
            consec_count += 1
            if consec_count > 2:
                st = STYLE_ALTERNATIVES.get(st, "blob_card")
                if st == last_style:
                    st = "serif_title" if last_style != "serif_title" else "blob_card"
                consec_count = 1
        else:
            consec_count = 1
        last_style = st
        pacing_checked_events.append(ev.model_copy(update={"style": st}))

    final_events = pacing_checked_events

    # 5. Layer assignment: base is layer 1; concurrent upper/center features get layers 2 and 3
    final_events.sort(key=lambda x: (x.start, x.end))
    layered_events: list[TimelineEvent] = []

    for ev in final_events:
        if ev.style == "pill_word" and ev.id.startswith("base_"):
            layered_events.append(ev.model_copy(update={"layer": 1}))
        else:
            # Check what layers are occupied at ev.start
            overlapping_features = [
                placed for placed in layered_events
                if placed.layer > 1 and _overlaps(placed.start, placed.end, ev.start, ev.end)
            ]
            assigned_layer = 2 if not overlapping_features else 3
            layered_events.append(ev.model_copy(update={"layer": assigned_layer}))

    return layered_events
