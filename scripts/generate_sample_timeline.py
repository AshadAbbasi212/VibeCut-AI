"""Generate out/timeline.json for samples/synthetic.mp4 using the planner and layout engine."""
import json
from pathlib import Path
from backend.pipeline.probe import probe_video
from backend.pipeline.chunk import PhrasesDocument
from backend.pipeline.transcribe import Transcript
from backend.pipeline.plan_llm import get_planner
from backend.schemas.timeline import Timeline, TimelineVideo, TimelineWord


def main():
    video_path = Path("samples/synthetic.mp4")
    phrases_path = Path("out/phrases.json")
    words_path = Path("out/words.json")
    output_path = Path("out/timeline.json")

    if not video_path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")
    if not phrases_path.exists():
        raise FileNotFoundError(f"Phrases document not found: {phrases_path}")
    if not words_path.exists():
        raise FileNotFoundError(f"Words document not found: {words_path}")

    # 1. Probe video
    probe = probe_video(video_path)
    print(f"Video probed: {probe.width}x{probe.height}, {probe.fps} fps, duration={probe.duration:.2f}s")

    # 2. Load phrases and words
    with open(phrases_path, "r", encoding="utf-8") as f:
        phrases_doc = PhrasesDocument(**json.load(f))

    with open(words_path, "r", encoding="utf-8") as f:
        trans_res = Transcript(**json.load(f))

    # 3. Plan events
    planner = get_planner(preset="bold_creator")
    events = planner.plan(
        phrases=phrases_doc.phrases,
        video_duration=probe.duration,
        preset="bold_creator",
        language=phrases_doc.language,
    )

    # 4. Construct Timeline
    tl_video = TimelineVideo(
        src=str(video_path).replace("\\", "/"),
        width=probe.width,
        height=probe.height,
        fps=round(probe.fps),
        durationSec=round(probe.duration, 2),
    )

    tl_words = [
        TimelineWord(i=w.i, text=w.text, start=round(w.start, 2), end=round(w.end, 2))
        for w in trans_res.words
    ]

    timeline = Timeline(
        version=1,
        video=tl_video,
        language=phrases_doc.language,
        words=tl_words,
        events=events,
    )

    # 5. Check DoD requirements: >= 4 styles, >= 1 moment with 2 overlapping events
    styles_used = set(e.style for e in timeline.events)
    print(f"Styles used ({len(styles_used)}): {sorted(styles_used)}")
    if len(styles_used) < 4:
        raise ValueError(f"Expected at least 4 styles, got {len(styles_used)}: {styles_used}")

    # Check overlaps
    overlapping_moments = []
    time_samples = [0.05 * i for i in range(int(probe.duration * 20))]
    for t in time_samples:
        active = [e for e in timeline.events if e.start <= t < e.end]
        if len(active) >= 2:
            overlapping_moments.append((t, [e.id for e in active], [e.style for e in active]))

    print(f"Number of overlapping moments sampled: {len(overlapping_moments)}")
    if not overlapping_moments:
        raise ValueError("Expected at least one moment with 2 overlapping events, found 0!")

    sample_overlap = overlapping_moments[len(overlapping_moments) // 2]
    print(f"Sample overlapping moment at t={sample_overlap[0]:.2f}s: events={sample_overlap[1]}, styles={sample_overlap[2]}")

    # 6. Save timeline.json
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(timeline.model_dump(by_alias=True, exclude_none=True), f, indent=2)

    print(f"Successfully generated and validated {output_path} ({len(timeline.events)} events)")


if __name__ == "__main__":
    main()
