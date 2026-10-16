# 02 — Build Plan (phases, steps, Definition of Done)

Copy the checklist at the bottom into `PROGRESS.md` in Phase 0.
After each phase: run its verification, then `git commit -m "phase N: <title>"`.

---
## Phase 0 — Environment & scaffolding
1. `python scripts/check_env.py`; install anything missing (docs/01).
2. `python -m venv .venv`, activate, `pip install -r requirements.txt`.
3. `git init`; create `.gitignore` check (already provided).
4. Create package structure: `backend/__init__.py`, `backend/pipeline/`, `backend/api/`, `backend/tests/`.
5. Clone reference repos into `vendor/` (see docs/06). Read them; note useful patterns in `docs/DECISIONS.md`.
6. Create `THIRD_PARTY.md` and `docs/DECISIONS.md`.

DoD: `check_env.py` reports all required tools OK; `pytest` runs (even if 0 tests); first commit exists.

## Phase 1 — Transcription
1. Move `scripts/transcribe.py` into `backend/pipeline/transcribe.py` as an importable function
   `transcribe(path, model, device, compute_type, language) -> Transcript` (pydantic) plus a CLI wrapper.
2. Add ffprobe helper `backend/pipeline/probe.py` returning width, height, fps, duration, has_audio.
3. Test input: use `samples/input.mp4` if present. Otherwise synthesize a speech clip: generate speech with
   `edge-tts` (or any available TTS), then combine with a solid/gradient 1080x1920 background using ffmpeg ->
   `samples/synthetic.mp4`. Use whichever exists for all later phases.
4. Cache by SHA-256 of the input file so repeat runs skip transcription.
5. Optional: WhisperX alignment behind a flag `--align` if installation succeeds.

DoD: `python -m backend.pipeline.transcribe samples/<clip> -o out/words.json` produces words with strictly
non-decreasing timestamps, every word has start<end, word count > 0. pytest test covers the
monotonic-timestamp invariant using a fixture JSON.

## Phase 2 — Chunking into phrases
Implement `backend/pipeline/chunk.py`: group words into phrases.
Rules (make constants configurable): max 6 words (title-type phrases up to 8), break on pause > 0.35 s, break
after sentence punctuation, avoid single-word orphans where possible, max ~28 characters per rendered line,
min phrase duration 0.6 s (extend end into following silence, never into the next phrase's speech).
Each phrase keeps `word_indices`.

DoD: pytest covers pause break, punctuation break, max words, orphan avoidance, and no overlap between phrase
speech ranges. Running on the Phase 1 output produces `phrases.json`.

## Phase 3 — Remotion baseline
1. Scaffold `remotion/` (study `vendor/template-tiktok`; Remotion's official docs on captions). TypeScript.
   Pin all remotion packages to one exact version.
2. Composition `CaptionedVideo`: props = `{ timeline }`. Uses `calculateMetadata` so duration/size/fps come
   from the timeline. Video via `OffthreadVideo`; the Python side copies the input into
   `remotion/public/jobs/<id>/input.mp4` or passes a served URL/`staticFile`.
3. Implement ONE style, `pill_word` (docs/04), driven by timeline events.
4. Write `backend/pipeline/render.py` that runs `npx remotion render` (or `@remotion/renderer` via a tiny Node
   script) with `--props=<timeline.json path>`, captures logs, returns the output path.
5. Audio must be preserved in the output.

DoD: render a 5-second range of the sample with `pill_word` captions; extract a frame with ffmpeg
(`ffmpeg -ss 2 -i out.mp4 -frames:v 1 frame.png`), view it, confirm captions are visible, positioned in the
lower third, and the highlighted word changes with speech. Output has audio.

## Phase 4 — Style library + gallery
Implement every style in `docs/04-style-library.md`, one at a time. For each:
- React component under `remotion/src/styles/<style_id>/`
- registered in `remotion/src/styles/registry.ts`
- appears in `StyleGallery` (a Remotion `Still`/Composition showing sample text for each style)
- rendered to `out/gallery/<style_id>.png` and compared against its reference screenshot; iterate until close
  in layout, colour, typography feel and effects (it does not need to be pixel-identical).
Also implement shared animation helpers: spring pop-in, per-word stagger, exit fade, path draw-on (doodles),
sparkle twinkle.

DoD: gallery PNG exists for every style; side-by-side comparison images saved in `out/gallery/compare/`;
a render test plays 2 s of each style without errors; no text overflows the 1080x1920 frame.

## Phase 5 — Planner & layout engine
1. `backend/schemas/timeline.py` (pydantic) per docs/03; JSON Schema export; TypeScript types in Remotion.
2. Rule-based planner `backend/pipeline/plan_rules.py` (docs/05 fallback rules).
3. LLM planner `backend/pipeline/plan_llm.py`: provider interface with Gemini and Anthropic
   implementations; prompt from docs/05; output validated against the schema; on invalid JSON retry up to 2
   times, then fall back to the rule planner. Never crash the job because of the LLM.
4. Layout engine `backend/pipeline/layout.py`: assigns zone/layer/anchor, enforces: max 3 concurrent events,
   no two events in the same zone overlapping in time, safe areas (docs/04), vary styles (no more than 2
   consecutive identical styles), title style used sparingly (see docs/05).
5. Optional stretch: face detection (e.g. MediaPipe) to keep captions off the face.

DoD: pytest covers schema validation (valid + invalid), layout invariants on randomized inputs
(property-style test), and planner fallback when `LLM_PROVIDER=none` or the LLM returns garbage. A full
`timeline.json` is produced for the sample clip and renders successfully with at least 4 different styles
and at least one moment with 2 overlapping events.

## Phase 6 — Graphics, emoji, doodles
1. Keyword -> graphic: planner may attach `graphic: {kind: "emoji"|"icon"|"image", value}` to an event.
2. Emoji: render using a bundled emoji set or `@remotion/noto-emoji` (verify availability in docs).
   Icons: Lucide or similar (licence-checked). Pop-in spring animation, outline glow (see style
   `sticker`).
3. Doodles: ellipse, underline scribble, arrows, sparkles drawn with SVG path draw-on animation.
4. Stretch (optional, behind a flag): generated stickers via an image-generation API, cached by keyword.

DoD: sample timeline with emoji, icon, ellipse doodle, sparkles renders; frames viewed and checked.

## Phase 7 — Backend API, job runner, CLI
1. FastAPI app: `POST /api/jobs` (multipart upload, optional style preset + options),
   `GET /api/jobs/{id}` (status, step, progress 0-1, error), `GET /api/jobs/{id}/output` (MP4),
   `GET /api/jobs/{id}/timeline` (JSON), `GET /api/health`.
2. Background job runner (simple thread/process pool or asyncio queue; one render at a time by default).
3. Progress: parse Remotion render progress from its stdout; map steps to progress ranges.
4. CLI: `python -m backend.cli INPUT -o OUTPUT [--style-preset NAME] [--llm none|gemini|anthropic]
   [--whisper-model small] [--start S --end E]`.
5. Validate uploads (extension, size limit, ffprobe succeeds), unique job dirs, cleanup policy for old jobs.

DoD: `python -m backend.cli samples/<clip> -o out/final.mp4` succeeds end to end; API integration test uploads
the sample via `httpx`/TestClient and gets an MP4 back (use a short clip or `--start/--end` for speed).

## Phase 8 — Frontend
Single-page UI (plain HTML/JS or small Vite app built into `frontend/dist`, served by FastAPI):
upload drag-and-drop, options (style preset, language, LLM on/off), live progress, inline video preview of
the result, download button, and "view timeline JSON".

DoD: start the server, upload the sample through the browser (use a browser tool if available), see progress
update, play the result.

## Phase 9 — Polish & hardening
- Performance: render concurrency flag, cached transcription, optional lower-res draft preview render.
- Robustness: clips with no speech, very long clips (warn/limit), non-vertical input (letterbox or adapt
  safe zones), missing audio, odd fps, rotated phone videos.
- Style presets: at least 3 (`bold_creator`, `calm_serif`, `minimal_pill`) that bias the planner.
- Docs: top-level README with setup, usage, architecture diagram, troubleshooting, demo GIF/MP4.
- Optional `Dockerfile` (ffmpeg + node + python) if time allows.
- Final full run on the sample; save `out/final.mp4`.

DoD: `pytest` green; final video shows >= 5 distinct styles, word-synced highlighting, overlapping captions,
emoji/doodles, audio intact; README quickstart verified from a clean clone.

## Phase 10 — Stretch (only if everything above is done)
In-browser timeline editor; multilingual and RTL support (font fallback, e.g. Arabic/Urdu/Devanagari);
sound-effect hits on emphasis; brand kits (custom fonts/colours); batch processing; Remotion Lambda or
cloud rendering.

---
## PROGRESS.md checklist (copy)
- [ ] Phase 0 Environment & scaffolding
- [ ] Phase 1 Transcription
- [ ] Phase 2 Chunking
- [ ] Phase 3 Remotion baseline
- [ ] Phase 4 Style library + gallery
- [ ] Phase 5 Planner & layout
- [ ] Phase 6 Graphics, emoji, doodles
- [ ] Phase 7 Backend API, runner, CLI
- [ ] Phase 8 Frontend
- [ ] Phase 9 Polish & hardening
- [ ] Phase 10 Stretch (optional)
