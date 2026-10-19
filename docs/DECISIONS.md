# Architectural and Technical Decisions

## 2026-10-16: Use Python 3.11 for venv instead of Python 3.14
- **Decision**: Target Python 3.11.9 (`py -3.11 -m venv .venv`).
- **Why**: Python 3.14 lacks prebuilt binary wheels for key dependencies including `ctranslate2` and `faster-whisper`. Python 3.11 has full binary wheel support across Windows, macOS, and Linux.

## 2026-10-16: Subprocess resolution for Windows npm/npx
- **Decision**: Explicitly check for `npx.cmd` and `npm.cmd` on Windows when invoking subprocess commands or resolve executable paths with `shutil.which()`.
- **Why**: On Windows, executing `.cmd` or `.bat` binaries via `subprocess.run(["npx", ...])` without `shell=True` causes `WinError 2: The system cannot find the file specified`.

## 2026-10-16: Remotion Licensing and Version Pinning
- **Decision**: Pin exact versions of `remotion` and `@remotion/*` packages (no caret `^`). Follow Remotion licence terms (free for individual / small team use, commercial licence for enterprise).
- **Why**: Pinning versions guarantees reproducible renders without breaking API changes across Remotion submodules.

## 2026-10-16: Video Preprocessing and Deterministic Timing (from talking-head-reel & opencut)
- **Decision**: Pre-transcode or normalize input video to standard 1080x1920 @ 30 fps if needed before rendering; pass exact durationSec and fps to Remotion composition calculateMetadata.
- **Why**: Remotion frame extraction is drastically faster and seeks without drift when the video stream matches the composition framerate and orientation.

## 2026-10-16: Font Loading with delayRender (from template-tiktok)
- **Decision**: Ensure web fonts are awaited using `delayRender()` / `continueRender()` or `@remotion/google-fonts` before frame rendering.
- **Why**: Prevents frame glitches and text jumping/shifting caused by asynchronous font loading during headless rendering.

## 2026-10-16: Resilient Whisper device auto-selection and CPU fallback
- **Decision**: When `device="auto"` or CUDA is requested, dynamically detect compute types and wrap initial model execution in a try/except that automatically falls back to `device="cpu", compute_type="int8"` if CUDA runtime libraries (such as `cublas64_12.dll`) are missing or incompatible.
- **Why**: Prevents pipeline crashes on machines with NVIDIA GPUs where CUDA drivers exist but specific cuBLAS or cuDNN runtime DLLs are absent.

## 2026-10-16: Resilient Planner architecture and post-layout pacing
- **Decision**: Architected planner with pluggable LLM backends (Gemini via google-genai, Claude via anthropic) and a zero-dependency deterministic RulePlanner fallback. Added 2x retry on validation failure and a deterministic layout engine that guarantees max 3 concurrent events, zero same-zone collisions, safe margins, and <= 2 consecutive identical styles.
- **Why**: LLM APIs can occasionally produce malformed JSON, rate limit, or experience network drops. The pipeline must never crash a job because of an LLM failure, and vertical video layouts must strictly avoid visual overlap or illegible clutter.

## 2026-10-16: Lucide icons and SVG path draw-on doodles
- **Decision**: Used `lucide-react` for clean, open-licence vector icons with PascalCase normalization and dynamic component rendering, alongside system/Noto emoji and custom SVG animated path doodles (`strokeDasharray`/`strokeDashoffset` interpolation).
- **Why**: Vector SVG icons and doodles scale losslessly to 1080x1920 without pixelation or heavy image asset downloads, keeping renders crisp, fast, and self-contained.

## 2026-10-16: ThreadPool-backed background runner and Windows console encoding
- **Decision**: Used `concurrent.futures.ThreadPoolExecutor(max_workers=1)` for the job runner with disk-persisted `job.json` state and Remotion stdout progress parsing. Reconfigured Windows CLI stdout/stderr to UTF-8 with automatic character replacement fallback.
- **Why**: Ensures sequential, resource-safe video rendering on single-GPU/CPU machines without race conditions or memory exhaustion, while eliminating Windows cp1252 UnicodeEncodeErrors in CLI pipelines.

## 2026-10-16: Zero-bundle FastAPI static SPA architecture
- **Decision**: Implemented the frontend as a self-contained, dependency-free vanilla HTML5/CSS3/ES6 single-page app served directly by FastAPI via `StaticFiles(directory='frontend', html=True)`.
- **Why**: Eliminates Node/Vite build steps and dev server port conflicts in production/Docker, loads instantly with native modern browser APIs (Drag and Drop, FormData, Fetch, Video), and presents a dark-mode glassmorphic interface matching modern creator tools.

## 2026-10-19: Subtitle Sizing Optimization and Single-Caption Screen Clearance
- **Decision**: Scaled down font sizes across all styles by ~40-50% (30-44px instead of 88px, padding 10-20px instead of 40-76px). In Remotion, suppressed `base_` pill caption rendering during intervals where a concurrent `feat_` caption is active for the same phrase. Adjusted safe zone centers to: upper=18%, center=50%, lower=79%.
- **Why**: 88px titles combined with simultaneous base pills covered over half the screen on 9:16 vertical shorts, blocking the speaker's face. Suppressing duplicate base pills and optimizing font scale keeps typography legible, crisp, and compact while keeping the speaker unobstructed.

## 2026-10-19: 16-Style Library Expansion and 10-15 Style Variety Planner
- **Decision**: Expanded available subtitle styles from 8 to 16 by adding `neon_glow`, `typewriter_terminal`, `paper_cutout`, `glitch_kinetic`, `quote_editorial`, `comic_bubble`, `gradient_outline`, and `minimal_underline`. In `RulePlanner`, implemented a rolling anti-repetition queue (size 6) and multi-style round-robin pool ensuring videos with multiple phrases draw across 10 to 15 distinct styles without consecutive repeats.
- **Why**: Creators need high visual retention in short-form content. Ensuring a rich palette of 10-15 distinct styles per video keeps viewer engagement high while avoiding repetitive visual fatigue.

## 2026-10-19: Professional Creator Studio Frontend & Fast Re-render Pipeline
- **Decision**: Redesigned the frontend into a full-featured creator studio with a 4-tab control dock (`1. Video & Trim`, `2. Style Engine`, `3. Edit Captions`, `4. Exports`), a synchronized 9:16 vertical video player, an interactive live style sandbox for all 16 styles, and exposed `GET /api/styles` and `POST /api/jobs/{id}/rerender` endpoints.
- **Why**: Creators need a seamless, desktop-class editing experience where they can review videos, adjust word-level timing, change per-phrase styles, and re-render in seconds directly from the timeline without re-running transcription or chunking.

## 2026-10-19: Development No-Cache Middleware & HTTP HEAD Video Support
- **Decision**: Added FastAPI HTTP middleware setting `Cache-Control: no-cache, no-store, must-revalidate` for static files, and registered both `GET` and `HEAD` routes on `/api/jobs/{id}/output` and `/api/sample`. Upgraded aspect ratio toggle styling to high-contrast cyan accent and set video canvas preview to `object-fit: contain`.
- **Why**: Prevents browsers from silently serving stale `app.js` and `index.html` after UI modifications during development. Resolves browser media player failures when querying video metadata with standard HTTP `HEAD` pre-requests. Ensures instant, unambiguous visual feedback for active aspect ratios without video clipping.

## 2026-10-19: Sentence-Level Style Pacing, Transparent Backdrop & Studio Customization
- **Decision**: Grouped spoken phrases into sentence units (`group_phrases_into_sentences`) so caption styles remain rock-solid and consistent throughout an entire sentence, changing style only when a complete sentence/thought concludes. Adjusted default font sizing to the 52px "sweet spot" (with configurable small 38px, medium 52px, large 68px scale via `getCaptionFontSize`). Replaced the solid white rectangular background box with a transparent default backdrop featuring high-contrast drop shadows and electric glowing word highlights, plus optional `glass` and `solid` modes. Added creator studio UI controls for Caption Size, Backdrop, Style Pacing, and Highlight Color in Card 3 ("3. Options").
- **Why**: Switching visual styles mid-sentence (every 1-2s) created visual fatigue and distraction. Transparent backdrops prevent clunky bounding boxes and text clipping on dark/coding videos, while giving creators direct control over typography, pacing, and color schemes.




