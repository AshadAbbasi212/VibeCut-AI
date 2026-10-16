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
