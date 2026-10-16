# 01 — Prerequisites

The agent should run `python scripts/check_env.py` first and install/fix what is missing.

| Tool | Version | Notes |
|---|---|---|
| Python | 3.10+ | use a venv in `.venv/` |
| Node.js | 20+ (LTS) | needed by Remotion |
| npm | bundled with Node | |
| ffmpeg + ffprobe | any recent | must be on PATH |
| git | any | |
| Chrome/Chromium | auto | Remotion downloads its own headless browser on first render |
| GPU (optional) | NVIDIA + CUDA | speeds up Whisper; CPU works with `small` model + int8 |

## Install hints
- macOS: `brew install ffmpeg node python git`
- Ubuntu/Debian: `sudo apt install ffmpeg git python3-venv` and install Node 20+ via nvm or NodeSource
- Windows: `winget install Gyan.FFmpeg OpenJS.NodeJS.LTS Python.Python.3.12 Git.Git` (restart the terminal)

## Accounts / keys (all optional)
- Gemini API key or Anthropic API key for the LLM planner. Without one, use `LLM_PROVIDER=none` (rule-based).
- Hugging Face account NOT required for faster-whisper models (they download automatically).

## Disk/time expectations
- Whisper model download: `small` ~0.5 GB, `medium` ~1.5 GB, `large-v3` ~3 GB (first run only).
- Remotion first render downloads a browser (~100-200 MB) and is slow; later renders are faster.
- Rendering is CPU-heavy: expect roughly real-time or slower for a 1080x1920 30 fps clip with heavy effects.
