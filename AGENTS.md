# Agent Rules — Dynamic Captions Studio

## Mission
Build an app that takes an uploaded video and renders it with dynamic, multi-style, overlapping, animated
captions (see `docs/04-style-library.md` and `docs/reference-screenshots/`). Output must be a normal MP4.

## Working rules
- Follow `docs/02-build-plan.md` strictly in phase order. Each phase has a Definition of Done (DoD). Verify it
  with real commands and real output before committing. Never mark a phase done on assumption.
- No placeholder/stub code left in finished phases. No "TODO: implement" in committed code.
- Initialize git in Phase 0 and commit after every phase.
- Keep `PROGRESS.md` current (checkbox per phase + short notes + known issues).
- Record non-obvious decisions in `docs/DECISIONS.md` (one short entry each: decision, why, date).
- Verify library APIs against current official documentation before using them. Do not rely on memory for
  Remotion, faster-whisper, WhisperX, Gemini or Anthropic SDK signatures.

## Technical constraints
- Backend: Python 3.10+, FastAPI, pydantic v2. Cross-platform: use `pathlib`, `subprocess` with argument lists,
  and handle Windows (`npx.cmd`) as well as macOS/Linux.
- Renderer: Remotion (React + TypeScript). Pin ALL `remotion` and `@remotion/*` packages to the same exact
  version (no `^`). Default composition: 1080x1920, 30 fps, vertical.
- Transcription: faster-whisper (default) with word timestamps; WhisperX optional for better alignment.
- NO model training. Reuse pretrained models only (Whisper). Planner uses an LLM via API OR a rule-based
  fallback; the app must work end to end with `LLM_PROVIDER=none`.
- LLM provider is pluggable: `gemini`, `anthropic`, or `none` (see `.env.example`). Secrets only in `.env`
  (gitignored). Never print or commit keys.
- Fonts: only open-licence fonts (SIL OFL / Apache), loaded via `@remotion/google-fonts` or bundled locally.
- Third-party code: clone reference repos into `vendor/` (gitignored) for READING. Check each licence before
  copying any code; list anything reused in `THIRD_PARTY.md`. Prefer writing our own implementation.
- Do not commit videos, model weights, `node_modules`, `jobs/`, `vendor/`, `out/`, or `.env`.

## Quality bar
- Captions must be synced to speech (word start/end within ~100 ms of audio).
- Text must never leave the safe zones (docs/04) or collide with other simultaneous captions.
- Every style listed in docs/04 must exist, have a gallery still, and be used by the planner.
- Tests: pytest for backend logic (chunking, schema validation, layout, planner fallback). Remotion: a render
  smoke test.
