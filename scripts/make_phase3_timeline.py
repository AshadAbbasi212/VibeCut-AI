"""Generate a timeline.json with pill_word events for Phase 3 baseline testing."""
import json
import shutil
from pathlib import Path
from backend.pipeline.probe import probe_video
from backend.pipeline.render import prepare_video_asset
from backend.schemas.timeline import (
    Timeline,
    TimelineVideo,
    TimelineWord,
    TimelineEvent,
)


def create_phase3_timeline(
    video_path="samples/synthetic.mp4",
    words_path="out/words.json",
    phrases_path="out/phrases.json",
    out_timeline="out/test_timeline_phase3.json",
):
    video = Path(video_path)
    probe = probe_video(video)

    public_src = prepare_video_asset(video, job_id="test_phase3")

    words_data = json.loads(Path(words_path).read_text(encoding="utf-8"))
    phrases_data = json.loads(Path(phrases_path).read_text(encoding="utf-8"))

    timeline_words = [
        TimelineWord(
            i=w["i"],
            text=w["text"],
            start=w["start"],
            end=w["end"],
        )
        for w in words_data["words"]
    ]

    events = []
    for idx, p in enumerate(phrases_data["phrases"]):
        word_indices = p["word_indices"]
        events.append(
            TimelineEvent(
                id=f"e{idx}",
                style="pill_word",
                start=p["start"],
                end=p["end"],
                zone="lower",
                layer=1,
                wordRange=[word_indices[0], word_indices[-1]],
                text=p["text"],
            )
        )

    timeline = Timeline(
        version=1,
        video=TimelineVideo(
            src=public_src,
            width=probe.width,
            height=probe.height,
            fps=probe.fps,
            durationSec=probe.duration,
        ),
        language=words_data.get("language", "en"),
        words=timeline_words,
        events=events,
    )

    out_file = Path(out_timeline)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(timeline.model_dump_json(indent=2), encoding="utf-8")
    print(f"Generated {out_file} with {len(events)} pill_word events.")
    return timeline


if __name__ == "__main__":
    create_phase3_timeline()
