#!/usr/bin/env python3
"""Seed script: word-level transcription with faster-whisper.

Usage:
  python scripts/transcribe.py INPUT_VIDEO -o out/words.json [--model small] [--device auto]
                               [--compute-type int8] [--language en]

Output JSON:
  {"language": "en", "duration": 31.4, "words": [{"i": 0, "text": "Hello", "start": 0.12, "end": 0.40, "prob": 0.98}]}

Phase 1 turns this into backend/pipeline/transcribe.py (importable function + pydantic model + caching).
Verify the faster-whisper API against its current README before relying on this.
"""
import argparse
import json
from pathlib import Path


def transcribe(path, model="small", device="auto", compute_type="int8", language=None):
    from faster_whisper import WhisperModel

    wm = WhisperModel(model, device=device, compute_type=compute_type)
    segments, info = wm.transcribe(
        str(path),
        word_timestamps=True,
        vad_filter=True,
        language=language,
    )
    words = []
    for seg in segments:
        for w in seg.words or []:
            text = w.word.strip()
            if not text:
                continue
            words.append({
                "i": len(words),
                "text": text,
                "start": round(float(w.start), 3),
                "end": round(float(w.end), 3),
                "prob": round(float(getattr(w, "probability", 1.0)), 3),
            })
    return {"language": info.language, "duration": round(float(info.duration), 3), "words": words}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("-o", "--output", default="out/words.json")
    ap.add_argument("--model", default="small")
    ap.add_argument("--device", default="auto")
    ap.add_argument("--compute-type", default="int8")
    ap.add_argument("--language", default=None)
    args = ap.parse_args()

    result = transcribe(args.input, args.model, args.device, args.compute_type, args.language)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(result['words'])} words -> {out}")


if __name__ == "__main__":
    main()
