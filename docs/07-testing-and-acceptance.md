# 07 — Testing & Final Acceptance

## Automated
- `pytest` (backend): chunking, schema validation, layout invariants, planner fallback, cache, API upload.
- Remotion smoke render: 2-second render of each style through the CLI succeeds.
- Schema sync test: a sample `timeline.json` validates in Python and type-checks in TypeScript (`tsc --noEmit`).

## Visual (agent must LOOK at frames, not just check exit codes)
For the final video, extract frames at several timestamps and inspect them:
```
ffmpeg -i out/final.mp4 -vf "fps=1/3" out/frames/f_%03d.png
```
Check each against docs/04: correct fonts/colours, text inside safe areas, no overlap collisions, highlight
matches the spoken word, emoji/doodles visible, captions not covering the speaker's face for long.

## Final acceptance checklist
- [ ] `python -m backend.cli samples/<clip> -o out/final.mp4` works from a clean venv
- [ ] Web UI: upload -> progress -> preview -> download works
- [ ] >= 5 distinct styles appear in the final video; >= 1 moment with 2+ overlapping captions
- [ ] Word highlighting within ~100 ms of speech
- [ ] Emoji/sticker and at least one doodle (ellipse/underline/sparkles) render
- [ ] Works with `LLM_PROVIDER=none`; works with an LLM key if provided; falls back gracefully on LLM failure
- [ ] Audio intact in output; duration equals input
- [ ] README quickstart verified; `THIRD_PARTY.md` and `docs/DECISIONS.md` complete
