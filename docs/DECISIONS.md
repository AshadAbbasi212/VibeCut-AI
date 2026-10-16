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


