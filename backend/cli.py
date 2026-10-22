"""Command-line interface for Dynamic Captions Studio."""
import argparse
import json
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from backend.pipeline.probe import probe_video
from backend.pipeline.transcribe import transcribe
from backend.pipeline.chunk import chunk_words, PhrasesDocument
from backend.pipeline.plan_llm import get_planner
from backend.pipeline.render import render, prepare_video_asset
from backend.schemas.timeline import Timeline, TimelineVideo, TimelineWord


def main():
    parser = argparse.ArgumentParser(
        prog="dynamic-captions",
        description="Render dynamic, multi-style, animated captions onto vertical video.",
    )
    parser.add_argument("input", type=str, help="Path to input video file (e.g. samples/input.mp4)")
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="out/final.mp4",
        help="Path for rendered output video (default: out/final.mp4)",
    )
    parser.add_argument(
        "--preset",
        "--style-preset",
        dest="preset",
        type=str,
        choices=["bold_creator", "calm_serif", "minimal_pill"],
        default="bold_creator",
        help="Style preset (default: bold_creator)",
    )
    parser.add_argument(
        "--llm",
        type=str,
        choices=["none", "gemini", "anthropic"],
        default=None,
        help="LLM provider for caption styling (default: from LLM_PROVIDER or 'none')",
    )
    parser.add_argument(
        "--language",
        type=str,
        default="en",
        help="Spoken language code (default: en)",
    )
    parser.add_argument(
        "--whisper-model",
        type=str,
        default="small",
        help="faster-whisper model size (default: small, options: tiny, base, small, medium)",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=None,
        help="Remotion render concurrency worker count",
    )
    parser.add_argument(
        "--draft",
        action="store_true",
        help="Render draft preview at half resolution (scale 0.5) for fast turnaround",
    )
    parser.add_argument(
        "--start",
        type=float,
        default=None,
        help="Start time in seconds to render a clip segment",
    )
    parser.add_argument(
        "--end",
        type=float,
        default=None,
        help="End time in seconds to render a clip segment",
    )
    parser.add_argument(
        "--frames",
        type=str,
        default=None,
        help="Remotion frame range (e.g. '0-150')",
    )
    parser.add_argument(
        "--timeline-out",
        type=str,
        default=None,
        help="Optional path to save generated timeline.json",
    )

    args = parser.parse_args()
    input_path = Path(args.input).resolve()
    output_path = Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not input_path.exists():
        print(f"Error: Input video not found at {input_path}", file=sys.stderr)
        sys.exit(1)

    llm_provider = args.llm or os.getenv("LLM_PROVIDER", "none")

    print("=" * 60)
    print("🎬  DYNAMIC CAPTIONS STUDIO")
    print(f"Input:    {input_path}")
    print(f"Output:   {output_path}")
    print(f"Preset:   {args.preset}")
    print(f"Planner:  {llm_provider}")
    print("=" * 60)

    start_time = time.time()

    # Step 1: Probe video
    print("\n[1/5] Probing video container...")
    probe = probe_video(input_path)
    print(f"  ✓ {probe.width}x{probe.height} @ {probe.fps:.1f} fps, {probe.duration:.2f}s (audio: {probe.has_audio})")
    if probe.duration > 300:
        print(f"  ⚠️ Warning: Video duration is {probe.duration:.1f}s (> 300s). Rendering high-res video may take substantial time.")

    # Step 2: Transcribe
    print("\n[2/5] Transcribing speech with word-level alignment...")
    transcript = transcribe(
        path=input_path,
        model=args.whisper_model,
        language=args.language if args.language != "auto" else None,
    )
    print(f"  ✓ Transcribed {len(transcript.words)} words (language: {transcript.language})")

    # Step 3: Chunk words into phrases
    print("\n[3/5] Chunking phrases with natural cadence...")
    phrases = chunk_words(
        words=transcript.words,
        duration=probe.duration,
    )
    phrases_doc = PhrasesDocument(
        language=transcript.language or args.language,
        duration=probe.duration,
        phrases=phrases,
    )
    print(f"  ✓ Created {len(phrases_doc.phrases)} natural phrasing units")

    # Step 4: Plan caption styles & layout
    print("\n[4/5] Planning dynamic caption events & collision-free layout...")
    planner = get_planner(provider=llm_provider, preset=args.preset)
    events = planner.plan(
        phrases=phrases_doc.phrases,
        video_duration=probe.duration,
        preset=args.preset,
        language=transcript.language or args.language,
    )

    styles_used = sorted(set(e.style for e in events))
    print(f"  ✓ Generated {len(events)} events using {len(styles_used)} styles: {', '.join(styles_used)}")

    # Prepare video in Remotion public directory
    job_id = f"cli_{output_path.stem}"
    public_rel = prepare_video_asset(input_path, job_id=job_id)

    tl_video = TimelineVideo(
        src=public_rel,
        width=probe.width,
        height=probe.height,
        fps=round(probe.fps),
        durationSec=round(probe.duration, 2),
    )
    tl_words = [
        TimelineWord(i=w.i, text=w.text, start=round(w.start, 2), end=round(w.end, 2))
        for w in transcript.words
    ]
    timeline = Timeline(
        version=1,
        video=tl_video,
        language=transcript.language or args.language,
        words=tl_words,
        events=events,
    )

    if args.timeline_out:
        tl_out = Path(args.timeline_out)
        tl_out.parent.mkdir(parents=True, exist_ok=True)
        tl_out.write_text(json.dumps(timeline.model_dump(by_alias=True, exclude_none=True), indent=2), encoding="utf-8")
        print(f"  ✓ Saved timeline to {tl_out}")

    # Determine frame range if start/end specified
    frames_range = args.frames
    if not frames_range and (args.start is not None or args.end is not None):
        start_sec = args.start if args.start is not None else 0.0
        end_sec = args.end if args.end is not None else probe.duration
        start_f = max(0, int(start_sec * probe.fps))
        end_f = min(int(probe.duration * probe.fps), int(end_sec * probe.fps))
        frames_range = f"{start_f}-{end_f}"
        print(f"  ℹ️ Rendering clip frame range: {frames_range} ({start_sec:.2f}s - {end_sec:.2f}s)")

    # Step 5: Render final video with Remotion
    print("\n[5/5] Rendering final animated video composition via Remotion...")
    if args.draft:
        print("  ⚡ Draft mode enabled (rendering at scale 0.5)")

    def on_progress(pct: float):
        percent = int(pct * 100)
        bar_len = 30
        filled = int(bar_len * pct)
        bar = "█" * filled + "░" * (bar_len - filled)
        sys.stdout.write(f"\r  Render progress: [{bar}] {percent}%")
        sys.stdout.flush()

    render(
        timeline_input=timeline,
        output_path=output_path,
        frames=frames_range,
        concurrency=args.concurrency,
        draft=args.draft,
        progress_callback=on_progress,
    )
    print(f"\n  ✓ Render complete -> {output_path}")

    elapsed = time.time() - start_time
    print("=" * 60)
    print(f"✨ DONE in {elapsed:.1f}s! Final video saved to: {output_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
