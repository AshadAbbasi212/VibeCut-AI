# Dynamic Captions Studio — Agent Starter Kit

Goal: upload a video -> get back the same video with **dynamic, multi-style, animated, overlapping captions**
(3D gradient titles, blob cards, word-by-word pills, doodles, emoji/stickers) like the reference screenshots in
`docs/reference-screenshots/`.

This kit contains **no finished app**. It contains everything an AI coding agent (Google Antigravity, or any
agentic IDE) needs to build the app end to end: architecture, phased plan with acceptance tests, style specs,
schemas, prompts, repos/models to use, and a few working seed scripts.

## How to use (3 steps)
1. Unzip and open this folder as a workspace in Antigravity.
2. Make sure prerequisites exist (see `docs/01-prerequisites.md`): Python 3.10+, Node 20+, ffmpeg, git.
   Optional but recommended: drop a 30-60s vertical talking video at `samples/input.mp4`.
   (If you don't, the agent will synthesize a test clip.)
3. Open the agent panel and paste the contents of **`KICKOFF_PROMPT.md`**.

The agent will work through `docs/02-build-plan.md` phase by phase, verifying each phase before moving on,
and tracking progress in `PROGRESS.md`.

## Key idea
There is **no pretrained "dynamic caption" model** and you do not need to train one. The pipeline is:

    video -> Whisper (word timestamps) -> chunking -> planner (LLM + rules assigns styles/emphasis/graphics)
          -> timeline.json -> Remotion (React) renders styled, animated captions over the video -> output.mp4

## Folder map
- `AGENTS.md` / `GEMINI.md` / `.agent/rules/` : standing rules for the agent
- `KICKOFF_PROMPT.md` : the prompt you paste to start
- `docs/` : the full spec (read in numeric order)
- `docs/reference-screenshots/` : visual targets for each caption style
- `scripts/check_env.py`, `scripts/transcribe.py` : working seed scripts
- `backend/`, `remotion/`, `frontend/`, `samples/` : empty; the agent fills them
