# 06 — Resources: models, repos, docs, commands

## Models (pretrained; do not train)
| Purpose | Model / library | Notes |
|---|---|---|
| Speech-to-text, word timestamps | `faster-whisper` (SYSTRAN/faster-whisper) | `pip install faster-whisper`. Models download automatically on first use. CPU dev: `small`, `compute_type=int8`. GPU: `large-v3`, `float16`. |
| Better word alignment (optional) | `whisperX` (m-bain/whisperX) | forced alignment via wav2vec2; heavier install; optional flag |
| Planner LLM (optional) | Gemini (`google-genai` SDK) or Anthropic (`anthropic` SDK) | API keys in `.env`; fallback is rule-based |
| Emoji art | Noto Emoji (Google) | check `@remotion/noto-emoji` or bundle SVG/PNG assets (OFL/Apache) |
| Face avoidance (stretch) | MediaPipe face detection | optional |

## Reference repos (clone into `vendor/` for READING; check licences before reusing code)
```
mkdir -p vendor && cd vendor
git clone https://github.com/remotion-dev/template-tiktok.git
git clone https://github.com/buildingopen/opencut.git
git clone https://github.com/floomhq/opencut.git floomhq-opencut
git clone https://github.com/mariagorskikh/talking-head-reel.git
git clone https://github.com/DojoCodingLabs/remotion-superpowers.git
git clone https://github.com/SYSTRAN/faster-whisper.git
```
What to take from each (concepts, not blind copying):
- `template-tiktok` (official Remotion): Whisper -> captions JSON -> TikTok-style paged captions, how
  captions are grouped into pages with word-level highlighting, project structure.
- `opencut` (two forks): Whisper word timestamps + Remotion subtitle overlay, keyword overlays, timeline-driven
  composition pattern.
- `talking-head-reel`: vertical reel pipeline with captions and animated overlays; prep (transcode to
  1080x1920 @ 30 fps for cheap seeking) is a good idea to copy conceptually.
- `remotion-superpowers`: ideas for caption commands/skills.
Remotion's company-licence terms apply to some organisations; read https://www.remotion.dev/docs/license
and note the outcome in `docs/DECISIONS.md`.

## Docs to consult (always prefer current docs over memory)
- Remotion: https://www.remotion.dev/docs  (captions, `@remotion/captions`, `@remotion/google-fonts`,
  `@remotion/paths`, `@remotion/layout-utils`, `calculateMetadata`, `OffthreadVideo`, rendering via CLI /
  `@remotion/renderer`, `--props`, `--concurrency`)
- faster-whisper README (word_timestamps, vad_filter, compute types)
- FastAPI: https://fastapi.tiangolo.com
- Gemini API: https://ai.google.dev/gemini-api/docs  |  Anthropic API: https://docs.anthropic.com
- Google Fonts: https://fonts.google.com

## Key commands
```
# env
python scripts/check_env.py
python -m venv .venv && source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# remotion (inside remotion/)
npm init -y            # or follow the Remotion scaffold, then pin versions exactly
npx remotion studio
npx remotion render CaptionedVideo out/test.mp4 --props=../jobs/<id>/timeline.json
npx remotion still StyleGallery out/gallery.png --frame=0

# useful ffmpeg
ffprobe -v error -show_streams -of json input.mp4
ffmpeg -ss 2 -i out.mp4 -frames:v 1 frame.png            # grab a frame to inspect
ffmpeg -i input.mp4 -vf "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,fps=30" -c:a aac prepped.mp4
```
