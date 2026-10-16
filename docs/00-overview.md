# 00 — Overview & Architecture

## Product
Upload a video (vertical talking-head by default) -> receive an MP4 with dynamic captions: multiple visual
styles within one video, animated per word, emphasized keywords, decorative doodles, emoji/stickers, and
several captions on screen at once (e.g. a title card up top and a word-by-word pill at the bottom).

## Pipeline

    input.mp4
      |  ffprobe (size, fps, duration)
      v
    [1 Transcribe]  faster-whisper -> words.json  (text, start, end per word)
      v
    [2 Chunk]       group words into phrases (1-6 words) -> phrases.json
      v
    [3 Plan]        assign style/emphasis/graphics per phrase
                    (LLM with strict JSON schema, or rule-based fallback) -> plan.json
      v
    [4 Layout]      zones, layers, collision avoidance, safe areas -> timeline.json
      v
    [5 Render]      Remotion composition reads timeline.json + video -> output.mp4

## Components
- `backend/` (Python, FastAPI): pipeline steps 1-4, job runner, REST API, CLI. Calls Remotion via subprocess.
- `remotion/` (TypeScript/React): `CaptionedVideo` composition + style components + `StyleGallery`.
- `frontend/`: minimal web UI (upload, progress, preview, download). Served by FastAPI as static files.
- `jobs/<job_id>/`: input.mp4, words.json, phrases.json, plan.json, timeline.json, output.mp4, log.txt.

## Data contract
Python and Remotion communicate ONLY through `timeline.json` (schema in `docs/03-timeline-schema.md`).
Keep the JSON schema as the single source of truth: pydantic model in Python, matching TypeScript types in
Remotion (generate or hand-sync, and add a test that a sample timeline validates on both sides).

## Why this design
- No custom model training: Whisper handles speech, an LLM (or rules) handles "taste", Remotion handles motion.
- Styles are code (React components), so adding a new look = adding a component + registering its id.
- The JSON timeline makes the system debuggable and makes a future in-browser editor straightforward.
