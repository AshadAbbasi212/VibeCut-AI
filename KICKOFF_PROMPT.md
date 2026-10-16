You are building "Dynamic Captions Studio" in this workspace, fully autonomously.

1. Read `AGENTS.md`, then every file in `docs/` in numeric order. Open and study every image in
   `docs/reference-screenshots/`: they are the visual targets.
2. Create `PROGRESS.md` from the checklist in `docs/02-build-plan.md` and keep it updated.
3. Execute phases 0 through 9 of `docs/02-build-plan.md` in order. For each phase: implement, run the
   verification listed for that phase, fix failures, then `git commit` with message `phase N: <title>`.
   Do not start a phase until the previous phase's verification passes.
4. Install dependencies, download models, and clone reference repos yourself using the commands in
   `docs/06-resources.md`. Check every library API against its current official docs rather than memory
   (Remotion and the Gemini/Anthropic SDKs change often).
5. For visual work, render stills/frames and actually look at them next to the reference screenshots; iterate
   until the style is a close match. Save comparisons in `out/gallery/`.
6. Only stop to ask me if you are blocked by something you cannot resolve (missing API key, missing system
   dependency you cannot install, license problem). Otherwise make a reasonable decision, record it in
   `docs/DECISIONS.md`, and continue.
7. Finish with: a working `python -m backend.cli samples/input.mp4 -o out/final.mp4` command, a running web
   UI, and a short demo section in the top-level README.
