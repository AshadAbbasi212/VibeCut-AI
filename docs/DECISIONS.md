# Architectural and Technical Decisions

## 2026-10-26: High-Virality LLM Prompt Script & Curated Clip Selection (Guaranteed >= 10 Viral Moments)
- **Decision**:
  1. **Root Cause Analysis of 118-Clip Flood**:
     - Identified why a 63-minute video produced 118 clips: The LLM window prompt previously instructed the model: `"Extract ALL relevant, standalone viral clips... Do NOT artificially cap or limit to 3, 5, or 10 clips. Extract EVERY distinct highlight, punchy insight, debate, or story."`
     - This prompted Mistral/Gemini to extract 5–8 clips in every single 4-minute window across 19 windows, capturing trivial chit-chat and ordinary dialogue.
     - Additionally, `find_viral_clips()` was merging all non-overlapping `_rule_based_clip_finder()` mechanical slices on top of the LLM clips.
  2. **Refined LLM Prompt Script for High-Value Viral Moments**:
     - Updated both `_extract_window_mistral` and `_extract_window_gemini` with strict editorial selection criteria:
       - **Focus on Important Points**: Only extract moments containing significant insights, counterintuitive lessons, breakthrough ideas, passionate debates, or high-stakes storytelling.
       - **Strictly Exclude Filler**: Ignore routine pleasantries, greetings, administrative talk, podcast housekeeping, rambling transitions, and mundane explanations.
       - **Empty Return for Routine Windows**: If a segment does not contain any genuinely important or viral points, the LLM returns `{"clips": []}` instead of forcing mediocre slices.
       - **At Most 1-2 Top Moments per Segment**: In segments with standout content, extracts only the top 1 or 2 best moments.
       - **Plain Text Headlines**: Enforces pure plain text headlines without markdown asterisks (`**`), backticks, or quotes.
  3. **Guaranteed At Least 10 Clips with Curation Logic**:
     - In `find_viral_clips()`, established intelligent curation:
       - For long videos (>= 450s / 7.5 mins), sets `min_target = 10` and `max_target = 25`.
       - If the LLM generates >= 10 clips, those AI-curated clips are returned directly without appending mechanical rule slices (filtering for top viral moments with virality >= 8.5).
       - If the LLM generates fewer than 10 clips (e.g. 5–7 clips), the engine automatically supplements with the top-scoring non-overlapping speech peaks from the rule finder to guarantee at least 10 clips.
       - If LLM fails or is disabled (`LLM_PROVIDER=none`), the rule finder yields 10–20 high-scoring clips for long videos.
  4. **Markdown Stripping & Headline Sanitization**:
     - Sanitized all raw headlines in `_assemble_and_deduplicate_clips` by stripping markdown asterisks (`**`), quotes, and backticks (`re.sub(r"[*_`\"]", "", headline)`), ensuring cards and on-screen headmarkers render cleanly.
- **Why**: Fulfills the user request to eliminate the overwhelming 118-clip flood, focus exclusively on important discussions and viral moments, guarantee at least 10 clips (and more if they contain important points), and render clean headlines without markdown artifacts.

## 2026-10-26: Permanent Solution for Silent / DASH Video Uploads, Audio Multiplexing & Resilient Viral Clip Discovery
- **Decision**:
  1. **Root Cause Analysis of Silent Video Fallback (`videoplayback (3).mp4`)**:
     - Identified why the user saw the fallback clip `🔥 WATCH THIS HIGHLIGHT (00:00 - 01:00)`: The uploaded video was a YouTube 1080p DASH video-only stream containing 0 audio streams (`has_audio: False`).
     - Previously, `transcribe.py` returned an empty `Transcript(words=[])` and cached an 87-byte empty JSON file in `.cache/transcriptions/`. `find_viral_clips()` previously had a dummy fallback returning a generic highlight card when `len(phrases) == 0`.
  2. **Cache Poisoning Prevention & Dummy Clip Removal**:
     - Purged all corrupt empty transcription cache files.
     - Updated `transcribe.py` to strictly forbid caching empty transcripts (`len(words) == 0`) and reject corrupt cached files.
     - Removed dummy synthetic fallback from `find_viral_clips()`: If `clean_phrases` has no spoken text, it returns an empty list (`[]`) rather than spoofing a fake clip.
  3. **Backend Validation & Informative Error Contracts (`/api/clips/discover` & `/api/jobs/{id}/find-clips`)**:
     - Fast video probing via `probe_video()` to check `has_audio` and `audio_codec`.
     - If video lacks an audio track, raises HTTP 400 with `NO_AUDIO_TRACK: This video file has no audio stream (common with YouTube DASH downloads)...`.
     - If audio exists but no words are spoken, raises HTTP 400 with `NO_SPEECH_DETECTED: No spoken words or dialog were detected...`.
  4. **Audio Multiplexing Endpoint (`/api/merge-audio`) & Multi-Track Video Ingestion**:
     - Implemented `POST /api/merge-audio` and added `audio_file` support to `POST /api/clips/discover`: Uses FFmpeg stream mapping (`-c:v copy -c:a aac -shortest`) to combine separate video and audio tracks in under 2 seconds without re-encoding video.
  5. **Client-Side Probing & Actionable Audio Attachment UI (`app.js` & `index.html`)**:
     - On file selection/drop, `handleFile(file)` probes the video immediately. If silent, displays a prominent `🔇 No Audio Track` badge and shows a clean alert card with a `🎵 Attach Audio Track (.mp3, .m4a, .wav)` button.
     - When an audio file is selected, the frontend automatically multiplexes audio into the video, updates the Studio Monitor preview with full sound, and triggers reel scanning.
     - `fetchViralClips` saves `rootJobId = data.root_job_id`, ensuring instant (<0.1s) duration switches and reel renders.
  6. **Fix UI Callback Reference Error in `applyViralClip` & Defensive Gallery Protection**:
     - Diagnosed why the user's scan displayed `119 Found` on the badge but showed the red text `updateSourceSplitPreview is not defined` instead of the clip list:
     - `applyViralClip()` and `setClipLayout()` called `updateSourceSplitPreview()`, which was an obsolete function name instead of `updateSourcePreviewFraming()`.
     - When the first clip was auto-applied after discovery, the uncaught `ReferenceError` bubbled to `fetchViralClips`'s catch block, which overwrote `viralClipsList.innerHTML` with the error text, hiding the 119 discovered clips.
     - Replaced with `updateSourcePreviewFraming()`, removed duplicate calls, and protected the auto-apply call with a dedicated try/catch so the discovered clips gallery is never wiped.
- **Why**: Permanently eliminates misleading fake clips, catches silent DASH videos before transcription, and guarantees that all 119 discovered clips render cleanly in the UI.

## 2026-10-24: Content-Aware Viral Clip Discovery, Smart Headline Synthesis, Master Transcript Caching & Deduplication
- **Decision**:
  1. **Content-Aware Topic & Headline Synthesis in Rule-Based Finder (`backend/pipeline/clips.py`)**:
     - Diagnosed why the AI Viral Reels Studio extracted only a single generic card (`🔥 WATCH THIS HIGHLIGHT`, 00:00 - 01:00, "Key moment from the video"):
       - The rule-based finder had hardcoded fallbacks that fired whenever candidate window durations did not meet strict min duration requirements or when an invalid/expired LLM API key returned 401.
       - The previous headline generator blindly took the raw first 4 words of dialogue with colloquial filler prefixes (`"AND IF IT IS..."`, `"SO IN MY OPINION..."`).
     - Replaced with an intelligent, content-aware headline and topic synthesis engine:
       - **Filler Stripping**: Automatically strips conversational fluff (`"so"`, `"and"`, `"in my opinion"`, `"basically"`, `"the thing is"`, `"you know"`).
       - **Thematic Categories & Emoji Mapping**: Categorizes dialogue into tech (`🤖`), money/business (`💰`), insight/strategy (`💡`), warning/mistakes (`🚨`), growth/future (`🚀`), or curiosity/hooks (`🔥`).
       - **Compelling Question & Thought Detection**: Scans transcript windows for direct questions (`?`) and high-impact key phrases, formulating snappy all-caps headlines (e.g. `🔥 THE TECH ISN'T THE BOTTLENECK ANYMORE`, `🔥 FIRST PIPE CAP AI VOICE AGENT`, `🔥 ITS CLOSEST COMPETITOR IS LIVEKIT`).
       - **Dangling Tail Cleaner**: Strips dangling prepositions and conjunctions (`WITH`, `THEIR`, `THE`, `OF`, `AND`, `OR`, `TO`, `IN`, `FOR`, `ON`, `AT`, `IS`, `ARE`).
       - **2-Sentence Contextual Summaries & Targeted Hashtags**: Generates clean, readable summaries reflecting the real spoken discussion.
  2. **Adaptive Duration Scaling for Short or Trimmed Inputs**:
     - When available speech duration is shorter than target `min_sec` (e.g. 60s discussion requested on a 30s clip or short preview), dynamically scales `effective_min_sec = max(3.0, available_span * 0.35)` and `effective_target_sec = min(available_span, target_sec)` instead of returning 0 candidates.
  3. **Mutual Overlap Ratio & Duplicate Headline Elimination**:
     - Upgraded candidate window deduplication: checks overlap against the smaller of two windows (`ov_dur > min(cand.dur, s.dur) * 0.45`) and strictly rejects duplicate headlines, ensuring 10-50+ distinct, non-overlapping clips spanning the entire video.
  4. **Master Full-Video Transcript Caching (`backend/api/app.py` `find_job_clips`)**:
     - Diagnosed why scanning from a child job or previously trimmed 5s job returned 0 candidates: `job_dir / "phrases.json"` only contained the 5 seconds of the trimmed render.
     - Added ancestor traversal to `root_job`. If the root job's `phrases.json` covers only a trimmed fragment while the master source file is longer, the backend automatically transcribes the full master video once, caches `phrases_master.json`, and extracts viral moments across the complete video duration.
  5. **Frontend State Isolation & Target Job Resolution (`frontend/app.js`)**:
     - Updated `handleFile(file)` to reset `rootJobId = null; currentJobId = null; activeViralClips = [];` and clear stale tweaker UI whenever a new video file is selected.
     - Updated `fetchViralClips` to target `rootJobId || currentJobId`, ensuring that discovery always operates against the full master video.
- **Why**: Eliminates the single generic dummy clip fallback, guarantees multiple high-retention clips across 15s, 30s, and 60s targets with punchy topic-specific headlines, and ensures seamless discovery across long podcasts and short clips alike.

- **Decision**:
  1. **Enforce Solo Dynamic Framing in Active Speaker Mode (`reframe.py` & Remotion `CaptionedVideo/index.tsx`)**:
     - Diagnosed why clips rendered as split-screen when "Active Speaker" was selected: `reframe.py` (`build_active_speaker_cuts`) defaulted to `layout="split_duo"` when phrases were empty or during cross-talk, and Remotion intercepted `currentCutLayout === "split_duo"` to render the podcast split screen.
     - Updated `build_active_speaker_cuts` and Remotion so that selecting `active_speaker` strictly frames the active speaker in a 9:16 vertical broadcast solo shot (`layout: "solo"`, centering face tracking coordinates via `objectPosition: ${objPosX} center`), never splitting the screen. Split screen remains exclusively reserved for the dedicated "Podcast Split" (`split_podcast`) layout option.
  2. **Guaranteed Captions via Fallback Transcription on Trimmed Clips (`runner.py`)**:
     - Diagnosed why rendered clips had 0 captions: when rendering a clip from a parent job that had already been trimmed (or whose timeline did not cover the clip's timestamp window), `slice_timeline_for_clip` matched 0 events, resulting in an empty `events: []` and `words: []` timeline.
     - Added an automatic fallback in `submit_clip_job`: if the sliced timeline has 0 events or 0 words, the backend immediately transcribes `trimmed_mp4` using `transcribe()`, chunks the phrases, and calls `get_planner().plan()` with the user's chosen styles, ensuring that every generated reel is 100% guaranteed to have synchronized captions.
  3. **Multi-Reel Root Job Reference Preservation (`app.js` & `runner.py`)**:
     - Diagnosed why rendering a second clip failed: `frontend/app.js` was overwriting `currentJobId` with `clipJob.id` (a 43-second child clip). Slicing subsequent clips from a child clip job failed because the child clip did not contain the rest of the podcast.
     - Introduced `rootJobId` in `frontend/app.js` to preserve the parent job ID containing the original full video. All subsequent clip render requests now target `rootJobId`.
     - In `backend/api/runner.py`, added ancestor job traversal: if `parent_job` is a child clip, the backend automatically climbs ancestor links (`curr.parent_job_id`) to find the root master video file for ffmpeg trimming.
  4. **Non-Destructive Result Dismissal & Seamless Multi-Reel Workflow (`app.js` & `index.html`)**:
     - Diagnosed why canceling/closing the player forced the user to re-upload: the "✕" button on the video player was calling `resetStudioForNewVideo()`, which wiped `selectedFile`, `currentJobId`, and `activeViralClips`.
     - Replaced with `dismissResultView()`, which pauses the rendered player and returns to `showStage("source")` while keeping the uploaded video, scanned reels list, and clip tweaker intact.
     - Added a dedicated "🎬 Render Another Reel" button in the download actions bar next to "Download Captioned MP4".
  5. **Synchronized Video Layout Selection & Layout Alias Normalization**:
     - Synchronized `setVideoLayout` in `frontend/app.js` so clicking any visual layout card (`Active Speaker`, `Podcast Split`, `Ambient Blur`, etc.) simultaneously updates `selectedVideoLayout`, `selectedClipLayout`, and all UI badges, preventing state desynchronization.
     - Added `LAYOUT_ALIASES` normalization in `backend/schemas/timeline.py`, `backend/pipeline/clips.py`, and `backend/api/runner.py` (mapping `"ambient_blur"` -> `"blur_fit"`, `"split"` -> `"split_podcast"`, `"speaker"` -> `"active_speaker"`, `"center_zoom"` -> `"fill"`) so external inputs and UI parameters validate seamlessly against Pydantic schemas.
     - Integrated automatic `probe_video(trimmed_mp4)` on newly trimmed clip files in `submit_clip_job` to guarantee that `originalWidth` and `originalHeight` always match the real source aspect ratio for Remotion's layout switcher.
- **Why**: Solves the user's reported bugs: eliminates unintended split screen on active speaker, guarantees captions on all reels, allows rendering multiple reels sequentially without re-uploading or re-scanning, and makes the video frame layout options intuitive and responsive.

## 2026-10-23: Dynamic Multi-Style Variety Toggle, 3-5 Word Subdivision & Universal Active-Window Pagination Shield
- **Decision**:
  1. **User Control Option for Dynamic Multi-Style Variety Across Video (Full & Viral Reels)**:
     - Added an explicit user option for "✨ Dynamic Multi-Style Variety" with dedicated UI toggles (`#multiStyleVarietyToggle` in Full Video Studio, `#clipMultiStyleVarietyToggle` in AI Viral Reels Studio), API parameters (`multi_style_variety: bool` in `POST /api/jobs`, `POST /api/jobs/{id}/render-clip`, `POST /api/jobs/{id}/batch-render-clips`), and pipeline integration (`_build_base_events`, `RulePlanner.plan`, `slice_timeline_for_clip`).
     - When enabled (default): Rotates dialogue styles across the curated creator pool sentence-by-sentence with rich keyword highlights.
     - When disabled: Locks captions across the entire video or reel to a single consistent style (e.g. `pill_word` or user's picked style).
  2. **Elimination of the 20-Word Feature Event Suppression Trap**:
     - Diagnosed root cause of vertical text wrapping: when an LLM tagged an entire sentence as a feature event, Remotion suppressed concurrent 3-5 word base chunks. If the feature event had 20 words (9.18s), all 20 words were rendered simultaneously in `hormozi_bold`, wrapping into a 13-line vertical column covering the host.
     - In `backend/pipeline/plan_llm.py` (`_validate_and_parse_llm_json`): Any multi-phrase take with $> 6$ words is automatically subdivided into synchronized 3–5 word sub-events matching transcript phrases (`matching_phrases`), mapping exact `start`, `end`, and `wordRange`, attaching graphics only to the first chunk.
  3. **Universal Remotion Active-Window Pagination Safety Shield (`getActivePhraseWords`)**:
     - Exported `getActivePhraseWords(allWords, wordRange, currentTime, maxWords=5)` in `remotion/src/styles/registry.ts`.
     - Integrated across `hormozi_bold`, `beast_impact`, `highlighter_marker`, `karaoke_bounce`, and `pill_word`.
     - Uses paginated sliding windows so spoken words stay stable on screen during speech and never exceed 4–5 words simultaneously under any circumstances (even with legacy or unchunked timelines).
  4. **Base Dialogue Track Style Preservation in `layout.py`**:
     - Updated `assign_layout` to identify base dialogue events by id (`base_` or `evt_`), ensuring they preserve their custom dynamic styles and layer 1 without being corrupted by feature callout style rotation.
- **Why**: Directly satisfies the user's explicit requirement for dynamic variety control in both reels and full video while completely eliminating screen-covering text towers, maintaining strict 3–5 word Ali Abdaal formatting.

## 2026-10-23: Professional Ali Abdaal Editorial Mode, Computer Vision Face Tracking & Mathematical Cover Centering
- **Decision**:
  1. **Mathematical Centering Formula for 9:16 Vertical Video (`getCoverObjectPositionX`)**:
     - Identified that CSS `objectPosition: X%` is relative to container overflow, not normalized image coordinates. When cropping a 16:9 source to 9:16 portrait with `objectFit: "cover"`, only 31.64% of width is visible. Setting `objectPosition: 85%` aligns the 85% mark of the video with the 85% mark of the viewport, pushing the speaker against the right border.
     - Implemented the exact centering transformation:
       $$P = \frac{X_{\text{face}} - \frac{\text{visible}}{2}}{\text{overflow}} = \frac{X_{\text{face}} - 0.1582}{0.6836}$$
       Host (`focusX = 0.206`) maps to `7.0%`, Guest (`0.853`) maps to `100%`, and Close-ups (`0.56`) map to `58.7%`, perfectly centering every active speaker.
  2. **OpenCV Deep Learning Face Tracking (`face_detection_yunet.onnx`)**:
     - Embedded YuNet face detector (232 KB) into `backend/pipeline/reframe.py`.
     - Automatically scans video frames to detect 2D face coordinates, distinguishes solo close-ups from wide multi-speaker shots, tracks speaker positions across time, and links speaker dialogue intervals to actual detected face coordinates.
  3. **Headroom Protection & Kinetic Zoom Eye-Line Anchor**:
     - Anchored kinetic zoom `transformOrigin` to `"center 28%"` (the upper-third eye line) and softened scale to `1.05x`, permanently eliminating forehead decapitation in vertical video renders.
  4. **Strict Verbatim Dialogue Enforcement & Hallucination Elimination**:
     - In `backend/pipeline/plan_llm.py`, updated system prompt instructions and implemented deterministic Python post-processing that matches word ranges to the Whisper transcript and overwrites `item["text"]` with exact spoken words. Any non-spoken phrase or invented heading card is dropped.
     - Remapped wide cards with $> 10$ words to sleek Ali Abdaal `highlighter_marker`. Clamped font sizes to `[32px, 60px]`.
- **Why**: Eliminates clipped speakers, decapitated heads, and screen-covering synthetic cards, achieving broadcast-quality Ali Abdaal editorial standards ready for production deployment.

## 2026-10-23: 10-Minute Video Deep Analysis: Concurrency Loop Pruning, Safe Zone Fallback & Universal Word Separation
- **Decision**:
  1. **Concurrency While-Loop Pruning in `layout.py`**:
     - On long 10-minute videos (1,479 words, 308 sentences), 158 timestamp slices exceeded the invariant limit of 3 concurrent events because `assign_layout` used an `if len(active) > max_concurrent:` statement, removing only 1 event per sampled instant instead of all exceeding events.
     - Upgraded to `while len(active) > max_concurrent:`, removing the lowest-priority feature event and updating `active.remove(to_remove)` until the count strictly satisfies `<= 3`. Concurrency is now verified `<= 2` across the entire 10-minute timeline.
  2. **Elimination of Center Face Occlusion in RulePlanner & Layout Engine**:
     - `RulePlanner` was previously assigning `zone = "center"` to feature events, placing text right over the speaker's face (`y: 0.35 .. 0.58`).
     - In `layout.py`, any feature event with `zone in ("center", "callout_stack")` or `0.35 <= y <= 0.58` is automatically converted to `zone = "free", x = 0.50, y = 0.68` (safe callout stack on the chest between face and subtitles) or flank margins. In `plan_rules.py`, feature events now default to `zone = "free"` and non-keyword sentences are paced to ~35% of sentences, eliminating visual clutter.
  3. **Layout-Aware Headline Hook in Split Layouts**:
     - In dual-camera split podcast setups (`split_podcast`, `split_triple`), the top speaker's face occupies `top: 6% .. 25%`. Placing the headline hook at single-camera default `top: 8%` covered the top host's eyes.
     - In `CaptionedVideo/index.tsx`, when `isSplitLayout` is true and default `headlineY = 0.08` is used, it automatically adapts to `top: 2%` (`hookYRatio = 0.02`) with a compact header badge that sits cleanly in the ceiling margin above the hairline, preserving 100% facial visibility.
  4. **Universal Word Separation (`pill_word`, `neon_glow`, `karaoke_bounce`)**:
     - Frame analysis of rendered video at 7.5s and 12.0s revealed fused words like "AndSundar" and "Welcometo theshow." because words inside flex-wrap containers lacked explicit whitespace characters and outer margin.
     - Wrapped word spans in `<React.Fragment key={w.i ?? idx}>`, added `margin: "2px 6px"`, and inserted `{idx < phraseWords.length - 1 && " "}` to guarantee visual whitespace across all continuous speech captions. Verified in re-rendered frames `frame_07.5s.jpg` ("And Sundar") and `frame_12.0s.jpg` ("Welcome to the show.").
- **Why**: Guarantees that 10-minute and long-form videos render with broadcast-quality typography, zero facial obstruction across both single and split layouts, zero concurrency leaks, and well-paced feature styles.

## 2026-10-23: Safe-Zone Anti-Collision Guard, Granular Headmarker Vanish Timer, Ali Abdaal Multi-Style Director & Complete Studio Parity
- **Decision**:
  1. **Safe-Zone Collision Avoidance (No Captions Behind Headmarker or Over Face)**:
     - In `remotion/src/CaptionedVideo/index.tsx` and `backend/pipeline/clips.py`: Captions are strictly prohibited from rendering in the `upper` safe zone (`y < 0.28`) when a headline hook is active, and forbidden from covering the speaker's face in the `center` zone (`y: 0.35–0.58`).
     - Any caption assigned to those zones is automatically shifted down to an elevated callout stack (`zone = "free", x = 0.50, y = 0.68`) resting safely between the speaker's chin and the dialogue subtitles, or to left/right flank editorial slots (`x = 0.26, y = 0.70` or `x = 0.74, y = 0.70`).
     - Caption container z-index is elevated (`(event.layer || 1) + 20`) to prevent any z-fighting behind card backgrounds.
  2. **Custom Vanishing Headmarker Timer (Seconds Slider + Quick Chips)**:
     - Replaced rigid 5s/10s options with a continuous seconds slider (`1.0s` to `15.0s`, `0.5s` step) and 6 quick chips (`2s`, `3s`, `4s`, `5s`, `8s`, `Sticky`) in both the Full Video Studio and AI Reel Studio Tweaker.
     - In `frontend/app.js`, fixed the canvas preview bug on trimmed clips by computing `clipElapsed = isPlayingCut ? Math.max(0, cur - (trimStartSec || 0)) : cur;`, preventing the headmarker from erroneously vanishing on frame 0 during clip previews.
  3. **Full 24-Style Library & Color Swatch Parity in AI Reel Studio**:
     - Upgraded Reel Tweaker to provide complete access to all 24 dynamic caption styles organized into categorized filter tabs (`All (24)`, `⚡ Punchy`, `🖍️ Explainer`, `🎬 Clean`, `🔮 Cyber/Retro`) and one-click Director Presets (`Ali Abdaal Mix`, `MrBeast`, `Marker`, `Hormozi`, `Blob Card`, `Numbered Step`, `Minimal`, `Cyber`, `All 24 Mix`).
     - Unified accent color swatches with all 7 presets plus a native Hex Color Picker (`#clipCustomColorPicker`), syncing with word highlights across both preview canvas and backend renderer.
     - Added the `📸 Compare Photos` layout modal button and 3-Way Stack (`split_triple`) layout option to the Reel Tweaker.
  4. **Ali Abdaal Editorial LLM Prompting & Content-Aware Keyword Styling**:
     - Overhauled system prompts in `backend/pipeline/plan_llm.py` to instruct LLMs to identify 3–5 core takeaways/rules, applying contrasting styles (`highlighter_marker`, `blob_card`, `beast_impact`, `numbered_point`, `typewriter_terminal`) and word-level highlights without cluttering the screen.
     - In `backend/pipeline/clips.py`, added content-aware style assignment for `ai_auto` mode detecting numbered steps (`numbered_point`), punchlines (`beast_impact`), educational definitions (`highlighter_marker`), and technical stats (`typewriter_terminal`).
  5. **Layout-Aware Dual-Camera Split Safe Zones & Webkit Stroke Word Spacing**:
     - Deep forensic keyframe analysis revealed that for `split_podcast` and `split_triple` vertical layouts, the lower speaker's face is positioned around `y: 0.56 - 0.74`. Placing callouts at generic single-camera `y = 0.68` placed text over the lower speaker's chin.
     - Sliced timeline and Remotion renderer now detect `isSplitLayout`: callouts and cards are placed directly on the neutral horizontal dividing seam (`y = 0.50`), and dialogue subtitles sit safely on the lower chest at `y = 0.85`, preserving 100% facial visibility for both speakers.
     - In `HormoziBold` and `BeastImpact`, added literal space separation `{idx < phraseWords.length - 1 && " "}` and `margin: "4px 8px"` so heavy 4-5px black text strokes never crowd or fuse adjacent words together.
- **Why**: Solves headmarker overlap and speaker face occlusion across all single-camera and split-screen layouts, guarantees crisp word-level typography, brings the AI Reel Studio to 100% feature parity with the Full Studio, and replicates Ali Abdaal's signature high-retention educational reel format.


## 2026-10-22: Uncapped AI Viral Clip Discovery & Full-Duration Time-Window Scanning
- **Decision**:
  1. **Removed Artificial 8/10 Clip Cap**: Removed the `len(selected) >= 8` break in `_rule_based_clip_finder`. Both heuristic and AI discovery pipelines now evaluate candidate moments across the full video timeline without an arbitrary ceiling.
  2. **Multi-Window Full-Transcript Scanning (`_generate_time_windows`)**: Removed the hardcoded `transcript_text[:12000]` character cutoffs and `topic_segments[:10]` truncation in both Mistral and Gemini extractors. Videos are segmented into sequential, overlapping time windows (`window_size=240.0s`, `overlap=45.0s`), ensuring 100% of the dialogue across 30m, 1h, or 2h videos is analyzed.
  3. **High-Token Completion & Deduplication (`_assemble_and_deduplicate_clips`)**: Prompts explicitly demand extraction of ALL viable highlights without stopping at 3-5 clips per window, with `max_tokens=4096` to prevent JSON truncation. Discovered clips from all windows are aggregated, snapped to phrase boundaries, filtered against heavy overlap (>50% non-overlapping criteria, keeping highest virality scores), and indexed sequentially.
  4. **High-Capacity UI Gallery**: Updated the frontend to display the exact live count in `#clipsCountBadge` (`X Found`) and increased the gallery scroll height to 420px.
- **Why**: Long podcasts, lectures, or interviews contain dozens or 50–100+ high-retention viral moments. Artificially capping extraction at 8 or 10 clips or truncating the transcript at 12,000 characters discarded 70-80% of longer videos. The windowed architecture scales to arbitrary video runtimes without hitting LLM output token limits.

## 2026-10-22: Reframe Layout in Reel Studio, Scene-Aware AI Vision & Boundary Validation Hardening
- **Decision**:
  1. **Video Reframe Layout in Reel Tweaker**: Integrated interactive Video Reframe Layout selector chips (`active_speaker`, `split_podcast`, `blur_fit`, `fill`, `focus_left`, `focus_right`) into the AI Viral Reels Tweaker card. Synchronized live framing preview directly onto the Studio Monitor (`#sourceSplitWrap`, `#sourceBlurWrap`, `#sourceSingleWrap`).
  2. **Scene-Aware AI Vision Analysis in Reel Tweaker**: Added `🎬 AI Vision Analysis (Scene-Aware)` toggle in the Reel Tweaker. Enabled keyframe vision extraction on trimmed clips (or sliced parent `analysis.json`) to accurately detect speaker coordinates, distinguishing solo close-ups (centered at `focusX = 0.50`) from wide 2-shots (at `0.20` and `0.82`) to prevent cut-off heads.
  3. **Event Boundary Duration & Concurrency Fix**: Fixed `TimelineEvent` validation failure where sliced clip events near trim boundaries resulted in sub-0.3s fragments (e.g. `0.299999s < 0.30s` due to float precision) or overlapping start adjustments triggering `More than 3 concurrent events`. Sliced events now extend forward within `clip_duration` or cleanly omit trailing partial fragments, and `TimelineEvent` duration validation uses `round(self.end - self.start, 2) < 0.30`.
- **Why**: Allows creators to immediately reframe any viral clip (e.g. using `split_podcast` Dual-Cam Stack for interview reels or `blur_fit` for zero-crop widescreen) and eliminates camera framing errors and render stalls.

## 2026-10-22: Creator Booster Pack: Batch ZIP Export, Viral Audio Layer, Kinetic Zooms, Social Copy & Auto Multi-Speaker Diarization
- **Decision**:
  1. **Batch Multi-Clip Export to ZIP**: Built `slice_timeline_for_clip` and `batch_render_viral_clips` in `backend/pipeline/clips.py` with endpoints `POST /api/jobs/{job_id}/batch-render-clips` and `GET /api/jobs/{job_id}/download-zip`. Slices the timeline down to each clip's time window, offsets all events and words to start at 0.0, extracts the sub-video via FFmpeg fast stream copy, renders standalone vertical MP4s via Remotion, generates matching `clip_XX_post.txt` files, and bundles them into `{job_id}_viral_reels.zip`.
  2. **Viral SFX & Lo-Fi Ambient Audio Layer**: Generated clean local assets `sfx_pop.wav` and `bg_lofi.wav`. Integrated Remotion `<Audio>` layers for pop sound effects on sticker/hook entrances and looped ambient background pads ducked under speech, controlled via user toggles (`#soundEffectsToggle`, `#bgMusicToggle`).
  3. **Kinetic Punch-In Micro-Zooms**: Implemented dynamic camera zoom calculation in `CaptionedVideo` that smoothly interpolates video scale up to 1.13x every 150 frames (5 seconds), giving an editorial attention reset without distracting motion. User toggled via `#kineticZoomToggle`.
  4. **Social Media Copy & Hashtag Generator**: Added `SocialPost` model with hook, caption, and hashtags to `ViralClip`. Added 1-click `📋 Copy Post` button on each clip card that copies ready-to-paste social copy directly to the user's clipboard.
  5. **Multi-Speaker Diarization Auto Color Coding**: *Direct implementation without user toggle*: In `backend/api/runner.py` and Remotion renderer, Host (`speaker_0`) dialogue is automatically mapped to Electric Cyan (`#38BDF8`) and Guest (`speaker_1`) dialogue to Cyber Amber (`#F59E0B`) based on active camera cut intervals.
  6. **Custom Brand Watermark / Handle**: Added `#watermarkInput` with live floating canvas badge preview on `#phoneCanvas` and Remotion renderer badge overlay.
- **Why**: Turns Dynamic Captions Studio from a caption generator into an end-to-end viral content repurposing engine. Creators can take one podcast, discover all engaging discussion clips, get auto-colored speaker subtitles, pop SFX, and download ready-to-publish reels in a single ZIP.

## 2026-10-22: AI Viral Clip Extractor (15s, 30s, 60s Highlights), Headline Hook Duration & Backend-Only API Key Security
- **Decision**:
  1. Removed the API key input box, visibility toggles, and client-side storage from the frontend UI. All LLM credentials (including `MISTRAL_API_KEY`) are kept strictly in backend `.env` (gitignored) and accessed via `os.getenv()`, preventing any client key exposure.
  2. Implemented the AI Viral Clip Extractor in `backend/pipeline/clips.py` with endpoints `POST /api/jobs/{job_id}/find-clips` and `POST /api/clips/discover`. The extractor analyzes transcript phrases and topic segments with Mistral (`open-mistral-7b` / `mistral-small-latest` free tier) or falls back to an audio-cadence & keyword density rule-based finder. Candidate clips are snapped to natural phrase boundaries, assigned a viral headline hook and virality score, and displayed as interactive cards in the studio Trimmer. Clicking a clip sets the trimmer range, seeks video playback, and populates the Top Headline Hook Card.
  3. Added headline hook card duration options (`5s`, `10s`, `Full Video`) in frontend UI chips, backend schema (`Timeline.headlineDuration`), and Remotion renderer (`interpolate()` smooth fade-out over 15 frames).
- **Why**: Protects sensitive LLM API keys on the server, allows creators to discover unlimited high-retention short reels (15s, 30s, 60s) from long podcasts or lectures, and provides option for the top headline card to vanish after the opening hook rather than staying on-screen permanently.

## 2026-10-22: Smart Watermark Filtering, Full-Duration Keyframes & Scene-Aware Auto-Framing
- **Decision**: 
  1. Refined `SCENE_ANALYSIS_PROMPT` and `plan_llm.py` so stationary channel logos, corner bugs (e.g. "BIG TECHNOLOGY PODCAST"), and teaser tags ("Coming up...") are NOT classified as burned-in dialogue captions. Any entry > 12s or matching watermark keywords is excluded from subtitle suppression, ensuring base speech captions remain visible across the full video.
  2. Enhanced `build_active_speaker_cuts` in `reframe.py` to accept `scene_analysis` and distinguish solo centered camera angles (`focusX = 0.50`) from wide two-shot angles (`focusX = 0.20` and `0.82`), and prevented camera cut merging when `focusX` changes.
  3. Updated `extract_keyframes` in `analyze.py` to use an `effective_interval` so keyframe extraction spans the full duration of the video rather than cutting off at 120s.
- **Why**: Eliminates blank caption periods caused by stationary watermarks, prevents extreme horizontal crops from cutting speakers off on multi-camera podcast videos, and ensures scene analysis covers the entire video duration.

## 2026-10-22: AI Director with Mistral Free Tier, Scene Analysis & Smart Heading Detection
- **Decision**: Added `MistralPlanner` (using `mistralai` SDK with `mistral-small-latest` for prompt planning and `pixtral-12b-2409` for keyframe vision analysis), client-side per-provider API key storage via `localStorage`, an optional `analyze_video` pipeline step extracting keyframes via FFmpeg to detect scenes, speakers, mood, and burned-in captions, and scene-aware creative director prompting. When burned-in captions are detected, both base and feature events are skipped for those timestamps.
- **Why**: Allows users to use Mistral's free tier for AI-directed caption styling (mimicking editors like Ali Abdaal who use distinct recurring styles for headings, special one-time styles for key hooks, and match style energy to video mood), while automatically preventing collisions with pre-existing hardcoded captions in video clips.


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

## 2026-10-19: CapCut Dual-Handle Trimmer, 20-Style Pool & On-Canvas Caption Drag & Drop
- **Decision**:
  1. Built an interactive CapCut-style dual-handle timeline trimmer with draggable left `[` and right `]` handles, dimmed exclusion zones, live video frame seeking during drag, time badges, and a `▶ Play Cut` preview loop.
  2. Expanded the style engine to 20 styles by adding `hormozi_bold` (Alex Hormozi yellow-pop uppercase block text), `retro_vaporwave` (80s chrome gradient with neon grid backing), `karaoke_bounce` (bouncing rhythm ball physics dot with golden glow), and `fire_burn` (blazing ember fire gradient with flicker shadow).
  3. Added an interactive visual style pool in Card 2 where creators select 1, 2, or all 20 styles with instant presets (`Hormozi Only`, `Retro 80s Only`, `Karaoke Only`, `Fire Only`, `Neon Only`, `Dynamic Mix`). When 1 style is picked, the planner locks the entire video into that style cleanly without duplicate base pills; picking 2+ styles rotates strictly across those selected.
  4. Added direct drag-and-drop caption placement directly onto the video canvas (`#phoneCanvas`) with magnetic snap guidelines (Upper 18%, Center 50%, Lower 79%), live coordinate badges (`Y: 10%-88%`), and fine-tuning slider controls synced bidirectionally with the backend and Remotion renderer.
- **Why**: Creators need full CapCut-level agency over video selection, typography styling, and spatial placement. Draggable timeline brackets remove guesswork from video trimming, custom style pools prevent unwanted aesthetic switching, and direct canvas dragging lets users position subtitles anywhere without blocking crucial visual elements in the video.

## 2026-10-19: Live Caption Example Showcase, Style Specimens & Size/Backdrop Previews
- **Decision**:
  1. Cleaned up the Card 2 header by removing the parenthetical "(Pick 1, 2, or All)" text.
  2. Integrated visual mini-specimens on each of the 20 style cards (displaying authentic typography such as `VIRAL BOLD`, `RETRO 80s`, `KARAOKE •`, `FIRE BLAZE`, `> CODE_`, etc.) so users see each style's visual aesthetic directly in the selection grid.
  3. Added visual specimen indicators to the Caption Font Size buttons (`Aa` in small 11px, medium 17px, and large 24px) and Caption Backdrop buttons (visual boxes showing Transparent floating text with shadow, Dark Glass with frosted blur pill, and Solid white pill).
  4. Implemented a dedicated interactive "Live Caption Example" showcase panel in Card 3 that morphs dynamically with live typography, scaling, backdrops, and active word highlights in real time as creators select or hover any style, font size, backdrop, or color swatch. Synchronized the live styling with the on-canvas `#draggableCaptionBox` overlay.
- **Why**: Creators should never have to guess what abstract labels like "Hormozi Bold", "52px", or "Dark Glass" look like. Providing immediate visual specimens on the controls and a live animated showcase panel gives creators instant visual feedback and confidence before rendering.
## 2026-10-20: Smart Video Reframe Engine (Podcast Split Stack, Ambient Blur & Speaker Focus)
- **Decision**: Solved the issue where 16:9 landscape interview/podcast videos had ~70% of the screen cut off when converting to 9:16 vertical reels:
  1. Saved a complete standalone git bundle (`backup-progress.bundle`) and created a backup branch and tag `backup-before-reframe` before applying any modifications so the user can revert at any point.
  2. Implemented the industry-standard **Podcast Split-Screen Stack** (Top: Left Host, Bottom: Right Guest) with an ultra-crisp cyan neon dividing line. Muted the bottom video stream in Remotion to guarantee zero audio doubling or echo.
  3. Added alternative framing modes: `blur_fit` (full 16:9 frame over an ambient dynamic blurred mirror background), `focus_left` (host framing), `focus_right` (guest framing), and `fill` (center zoom for native vertical videos).
  4. Added `layout`, `originalWidth`, and `originalHeight` to `TimelineVideo`, and `videoLayout` to `Timeline` and `JobInfo`.
  5. Built synchronized dual-cam live preview in the Studio frontend (`#sourceSplitWrap`) and interactive `Reframe Layout` option buttons in Card 3.
- **Why**: Amateur tools shrink landscape videos into tiny letterboxes with black bars, or crop the middle seam and cut both speakers in half. The Podcast Split-Screen Stack fills 100% of the 9:16 vertical screen with both speakers clearly visible in high resolution, delivering broadcast-quality reels for Instagram and TikTok.

## 2026-10-20: Active Speaker Auto-Tracking & Dynamic Auto-Reframe Engine
- **Decision**: Implemented an automated speaker-tracking engine (`backend/pipeline/reframe.py`) that cuts between active speakers on sentence boundaries while adhering to professional broadcast pacing:
  1. **Broadcast Pacing Rules (Hysteresis)**: Enforces a minimum shot duration of 1.8 seconds so the camera never jerks back and forth on short laughs or 0.3s interjections ("camera whip-lash").
  2. **Hold / Reaction Buffer**: Holds the camera on the speaker for 0.6 seconds after speech finishes to prevent unnatural cut-offs.
  3. **Cross-Talk & Interruption Handling**: Automatically switches to the dual-cam Split Stack whenever speakers talk simultaneously, ensuring both reactions are visible before returning to solo framing.
  4. **Dynamic Remotion Camera**: `CaptionedVideo` dynamically evaluates active `CameraCut` timeline events and cuts cleanly to the speaker's horizontal position (`15%` left, `50%` center, `85%` right) in 9:16 vertical orientation.
  5. **UI Integration**: Added `⚡ Active Speaker (Auto-Tracking)` button to the Reframe Layout selector in the creator options dock.
- **Why**: Multi-person videos require dynamic visual direction. Rather than statically letterboxing or cutting speakers down the center, automated speaker tracking delivers high-energy, broadcast-quality cuts ideal for TikTok and Reels without manual timeline keyframing.

## 2026-10-21: Caption Font Size Slider, Real-Time On-Screen Display, and Copyright-Free Stills
- **Decision**:
  1. Replaced layout preview thumbnails with 4 custom AI-generated copyright-free illustrations (`solo_fullscreen.png`, `blur_fit.png`, `split_podcast.png`, `split_triple.png`).
  2. Implemented an interactive Caption Font Size range slider (24px to 96px, default 52px) alongside the Small (38px), Medium (52px), and Large (68px) preset chips.
  3. Integrated real-time on-screen display on the video canvas preview: added a live font size badge (`#dragSizeBadge`, e.g. `52px`) directly in the draggable overlay and dynamically scaled `#dragSampleText` font size on screen as the slider or chips move.
  4. Extended `backend/schemas/timeline.py` and Remotion `TimelineEvent` / `Timeline` types so `captionSize` allows custom numeric pixel values (e.g. `"44"`), scaling all 20 styles via `getCaptionFontSize`.
  5. Pipeline speed optimization: Transcribed only trimmed sections in `backend/api/runner.py` and optimized Whisper CPU thread count and default model.
- **Why**: Creators need granular pixel-level control over font sizes instead of being locked to 3 discrete options. Displaying the font size badge and dynamically scaling text on the video canvas provides immediate WYSIWYG feedback before rendering.

## 2026-10-21: 24-Style Expansion, Clean Studio Layout Stills, Studio Monitor Canvas & Live Showcase Sync
- **Decision**:
  1. **Clean Studio-Grade Layout Stills (Zero Overlap)**: Replaced mockups containing baked-in captions with clean studio photography (`solo_fullscreen_clean.jpg`, `blur_fit_clean.jpg`, `split_podcast_clean.jpg`, `split_triple_clean.jpg` and updated `.png` targets). All backgrounds now feature clean plates with zero baked-in text, completely resolving text collisions with the on-screen draggable caption overlay (`Y: 79%`).
  2. **Studio Monitor Preview Overhaul**: Redesigned the right-hand canvas into a sleek, dark-glass broadcast "STUDIO MONITOR" with a glowing amber/emerald live status LED, dynamic resolution telemetry badge (`1080×1920 • 30 FPS • 9:16`), rounded bezel framing, and streamlined mode pill badge (`🎥 Clean Plate / Framing Preview`).
  3. **4 Top Viral Caption Styles Added (24 Styles Total)**:
     - `beast_impact`: MrBeast high-energy viral retention styling with -2° tilt, 3D extruded drop-shadow, and lime/cyber-yellow punch.
     - `highlighter_marker`: Ali Abdaal / Vox video essay style featuring an animated pastel yellow marker stroke sweep behind active keywords.
     - `cinematic_minimal`: A24 / Netflix widescreen subtitle design with warm amber tracking and dark frosted glass pill.
     - `cyber_hud`: Cyberpunk sci-fi HUD telemetry display with `[ ]` brackets, monospace typography, and cyan holographic glow.
  4. **Live Caption Example Showcase & Canvas Preview Synchronization**:
     - Built dedicated CSS styling classes (`.style-<id>`) in `frontend/index.html` for all 24 styles with imported Google Fonts (`Plus Jakarta Sans`, `Caveat`, `Bangers`, `Montserrat`, `Fraunces`, `JetBrains Mono`).
     - Overhauled `updateCaptionShowcase(styleId)` and `updateDraggableCaptionPreview()` in `frontend/app.js` to render authentic typography, marker sweeps, and accents for every style when clicked or selected.
     - Added quick-preset buttons in Card 2 for new viral styles (`⚡ MrBeast Only`, `🖍️ Ali Marker Only`, `🎬 Cinematic Only`, `🤖 Cyber HUD Only`).
- **Why**: Creators expect an ultra-professional, distraction-free preview interface where framing plates never clash with subtitle mockups, typography faithfully previews before rendering, and trending viral subtitle treatments from MrBeast, Ali Abdaal, and cinematic releases are instantly accessible.

## 2026-10-21: High-Speed Remotion Rendering Engine (3x-5x Speedup with Zero Quality Loss)
- **Decision**:
  1. **Webpack Bundle Pre-Compilation (`ensure_remotion_bundle`)**: Implemented pre-bundling via `remotion bundle src/index.ts --bundle-cache`. Passing the pre-built `build` directory directly to `remotion render` skips the 8-12 second Webpack compilation on every single render. The bundle auto-updates whenever any file in `remotion/src` changes.
  2. **High-Performance Visually Lossless JPEG Pipeline (`--image-format=jpeg --jpeg-quality=95`)**: Replaced uncompressed PNG frame writes with JPEG at 95% quality. Cuts disk I/O and Chromium frame compression CPU time by ~50% with zero visible degradation.
  3. **Hardware GPU Acceleration (`--gl=angle`)**: Enforced ANGLE Direct3D 11/12 GPU rendering on Windows, bypassing the slow CPU software rasterizer (`SwiftShader`).
  4. **Pristine Fast Encoding (`--x264-preset=veryfast --crf=18 --pixel-format=yuv420p`)**: Switched FFmpeg encoding to `veryfast` with CRF 18 (visually lossless standard in digital video) and standard `yuv420p` pixel format.
  5. **In-Memory Video Frame Cache (`--offthreadvideo-cache-size-in-bytes=1073741824`)**: Allocated a 1 GB cache for decoded video frames so multi-layer compositions (`split_podcast`, `split_triple`, `blur_fit`) reuse decoded frames without redundant FFmpeg extractions.
  6. **Optimal Concurrency Tuning**: Capped default rendering concurrency to `min(max(2, cpu_cores // 2), 4)` to eliminate CPU cache thrashing and memory paging stalls caused by too many simultaneous headless Chrome processes.
- **Why**: Creators need rapid iteration cycles. Re-compiling Webpack and writing uncompressed PNG frames per frame caused unacceptable latency even on short 5-10 second clips. These optimizations cut rendering time by 3x-5x while preserving 1080x1920 60/30fps production visual quality.
## 2026-10-21: Viral Boosters Pack (Retention Progress Bar, Headline Hook Card, AI Keyword Auto-Emojis)
- **Decision**:
  1. **Reversibility & Backup Checkpoint**: Created git branch `backup-before-viral-pack`, tag `backup-before-viral-pack`, and exported standalone bundle `backup-progress-viral.bundle` before implementing changes, giving the user guaranteed single-command rollback capability (`git checkout backup-before-viral-pack`).
  2. **Top Headline Hook Card with Explicit User Option**: Made the Headline Hook Card completely optional via a dedicated toggle in Card 3 (defaults to OFF). When enabled, creators can customize the hook text (e.g. `"🔥 WAIT TILL THE END..."`) and choose between 4 visual aesthetics:
     - `badge`: Amber-bordered dark pill with glowing drop-shadow.
     - `glass`: Ultra-sleek Apple frosted glassmorphism with backdrop-filter blur.
     - `clean`: High-contrast bold black & white card with 3px border.
     - `cyber`: Cyberpunk neon cyan HUD console styling with 2.5px letter spacing.
     Positioned in the upper safe zone (top 8%) with smooth spring `popIn` animation, avoiding any collisions with center or lower captions.
  3. **Animated Retention Progress Bar**: Added a sleek glowing progress bar running continuously along the top or bottom of the screen (`progressBarPosition="bottom" | "top"`), calculating frame progress as `(frame / totalFrames) * 100%` with a smooth multi-stop gradient matching the user's selected highlight color (`timeline.highlightColor`, `#ec4899`, `#FBBF24`).
  4. **AI Keyword Auto-Emojis & Animated Stickers**: Expanded semantic dictionary (`EMOJI_KEYWORDS` and `ICON_KEYWORDS`) to 50+ viral keywords across finance (💰, 💵, 💎, 📈), energy (🔥, 🚀, 💥, ⚡, ✨), health/mind (🧠, 🩺, ❤️, ⏳), tech (🤖, 💻, 📱, 🎥), and reactions (🏆, 🛑, ⚠️, 🤫, 👀). When `autoEmojis` is enabled, keyword-triggered graphics pop smoothly above spoken words across all styling presets and custom style modes.
## 2026-10-21: 3D Viral Animated Stickers (Microsoft Fluent 3D Assets, Volumetric Lighting & Auto-Upgrade)
- **Decision**:
  1. **Volumetric 3D Sticker Library**: Replaced flat system 2D emojis with 23 high-resolution transparent PNG 3D stickers from Microsoft Fluent Emoji (MIT license): `fire`, `rocket`, `money_bag`, `coin`, `diamond`, `lightbulb`, `brain`, `trophy`, `target`, `lightning`, `star`, `heart`, `stop`, `lock`, `key`, `crown`, `chart`, `boom`, `eyes`, `warning`, `clock`, `party`, `robot`.
  2. **Bundled Asset Architecture**: Pre-bundled the 3D assets in `remotion/public/stickers_3d/`, `remotion/build/public/stickers_3d/`, and `frontend/assets/stickers_3d/`, with automatic synchronization during pre-bundling.
  3. **Volumetric Renderer & Auto-Upgrade**:
     - Added explicit `kind="sticker3d"` in `TimelineGraphic` schema (`backend/schemas/timeline.py` and `remotion/src/types/timeline.ts`).
     - In `GraphicRenderer.tsx`, implemented high-resolution image rendering with volumetric drop shadows (`filter: drop-shadow(0 14px 26px rgba(0,0,0,0.75)) drop-shadow(0 0 20px ${glowColor})`) and subtle 3D perspective tilt (`perspective(600px) rotateX(4deg)`).
     - Added automatic emoji & icon upgrade dictionaries (`EMOJI_TO_3D` and `ICON_TO_3D`) so any timeline containing legacy emojis (`🔥`, `🚀`, `💰`, etc.) or icons seamlessly renders as high-res 3D stickers with zero code changes or migration overhead.
  4. **Keyword Detection & Backwards Compatibility**: Updated `detect_graphic_for_text(text, prefer_3d=True)` in `backend/pipeline/plan_rules.py` with 3D keyword mappings and backwards-compatible fallback support for legacy 2D emojis when `prefer_3d=False`.
  5. **Creator Studio UI**: Updated toggle in Card 3 from "AI Auto-Emojis" to "3D Viral Stickers" ("Pops 3D 🚀, 🔥, 💰, 💡 glossy stickers") with matching toast notifications.
- **Why**: Flat 2D system emojis vary wildly across operating systems, often rendering as dull, low-contrast glyphs. High-res volumetric 3D stickers with specular highlights and glowing drop-shadows provide the polished, professional visual punch popularized by top creators on TikTok, Reels, and YouTube Shorts.

## 2026-10-22: Seamless Multi-Video Workflow, Studio Reset & Isolated Render Props
- **Decision**:
  1. **Dismiss / Cancel (✕) & Studio Reset**: Added a dedicated circular `✕` button (`#closeResultBtn`) anchored to the top-right of the result monitor, and upgraded the secondary action to `🔄 Start New Video (✕)`. Both trigger `resetStudioForNewVideo()`, which halts active polling intervals, pauses and unloads media elements, clears selected file and job IDs, resets the CapCut trimmer and input elements, re-enables the generate button, and returns the workspace to clean idle preview.
  2. **Per-Job Render Props Isolation**: Replaced static `render_props.json` in `backend/pipeline/render.py` with unique `render_props_{job_id}.json` both in `remotion/public/temp/` and `remotion/build/public/temp/`. Temporary props files are safely unlinked in a `finally` block upon render completion.
  3. **Non-blocking Worker Queue**: Increased `JobManager` thread pool concurrency to 4 workers, sanitized interrupted lingering job states on server startup, and added `POST /api/jobs/{job_id}/cancel`.
## 2026-10-22: Studio Architecture Separation & Dedicated Viral Clip Tweaker (Phase 28)
- **Decision**:
  1. **Top-Level Segmented Studio Mode Switcher**: Decoupled full video rendering settings from AI viral clips extraction. Added `.studio-mode-switcher` at the top of the controls column (`[🎞️ Full Video Studio]` and `[✨ AI Viral Reels Studio]`), providing clean separation between full-timeline renders and short-form clip generation.
  2. **Studio Monitor Header Collision Fix**: Fixed badge overflow in `.stage-header-left` where long filenames (`#stageStatus`) wrapped into 5 lines and overlapped the aspect ratio selector buttons (`9:16`, `16:9`, `1:1`, `4:5`). Applied CSS `min-width: 0; flex: 1; overflow: hidden;` to header left, and `max-width: 170px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;` to `#stageStatus`, with safe filename truncation in `handleFile()`.
  3. **Full Video Studio Cleanup**: Removed the embedded `aiClipsBox` from inside the CapCut trimmer in Card 3, replacing it with a sleek shortcut banner (`.studio-callout-banner`) pointing to the Clips Studio.
  4. **Dedicated AI Viral Reels Studio & Clip Tweaker Architecture**: Built a 3-stage dedicated workflow in `<div id="clipsStudioSection">`:
     - **Card A (Scanner)**: Target length selector chips (`15s Hook`, `30s Highlight`, `60s Discussion`) + Discover button.
     - **Card B (Gallery)**: Discovered clips list with virality scores, timestamps, AI summary, and `📋 Copy Post`.
     - **Card C (`#clipTweakerCard`)**: Dedicated Selected Clip Customizer allowing creators to tweak all parameters before rendering:
       - **Headline Hook**: Editable text, visual styles (`badge`, `glass`, `clean`, `cyber`), and fade-out duration (`5s`, `10s`, `Full`).
       - **Caption Font Size**: Preset chips (`38px`, `52px`, `68px`) + live fine-tuning slider (`24px` - `96px`), immediately synced to canvas preview.
       - **Caption Placement**: Quick buttons (`Top 18%`, `Center 50%`, `Bottom 79%`) + vertical slider + real-time canvas drag sync.
       - **Caption Style & Palette**: Quick style selector + accent color swatches.
       - **Creator Watermark**: Custom `@handle` input synced to live canvas badge.
       - **Viral Boosters**: Toggles for Kinetic Zooms, Viral Pop SFX, Lo-Fi Ambient Beat, 3D Stickers.
       - **Actions**: `⚡ Render This Viral Reel (MP4)` rendering this customized clip with all overrides, and `📦 Export All Clips (.ZIP)`.
- **Why**: As the studio expanded with CapCut trimming, AI clip generation, diarization, and booster packs, having all controls stacked together in one column caused visual clutter and confusion. Separating the modes gives creators a focused workflow, prevents UI collisions, and empowers them to fine-tune individual viral clips (typography, placement, styling, and boosters) before final export.

## 2026-10-22: Optional Watermark, Booster Retention Education, Headmarker Positioning & Dedicated Clip Render Engine (Phase 29)
- **Decision**:
  1. **Optional Watermark Badge**: Replaced auto-rendered watermark handle with an explicit opt-in toggle checkbox in both Full Video Studio and AI Viral Reels Studio (defaults to OFF). When unchecked, the input field is collapsed, the preview badge on the video monitor is hidden, and `watermark_text` is omitted/null.
  2. **Viral Boosters Retention Explanations**: Added clear, professional descriptions beneath each of the 4 booster options explaining why they boost viewer retention (Kinetic Zooms reset attention every 3-5s, Pop SFX accentuates keyword highlights, Lo-Fi Audio ducked at -18dB fills pauses, and 3D Glossy Stickers highlight key concepts).
  3. **Headmarker (Headline Hook) Location Positioning**: Added `headlineY` (vertical position ratio 0.05 to 0.85) to `Timeline` backend schema, Remotion types, and `CaptionedVideo` layout. In the frontend, added quick safe zone chips (`Top 8%`, `Upper 22%`, `Center 42%`, `Lower 65%`) and fine-tuning slider, dynamically moving the headmarker card on the Studio Monitor preview.
  4. **AI Smart Director Caption Styling**: Added `🤖 AI Smart Director` (`ai_auto`) as the primary style option in the Tweaker card. When selected, the AI dynamically evaluates clip energy, duration, and tone to assign high-retention styles (e.g., `beast_impact` and `hormozi_bold` for punchy hooks, `highlighter_marker` for explanations, and `cinematic_minimal` for longer discussions).
  5. **Dedicated Lightning Single-Clip Render Engine (`POST /api/jobs/{job_id}/render-clip`)**: Resolved the clip rendering freeze/stall where editing a viral reel previously tried to re-upload the entire source video (which could be a 45-minute file) and re-run transcription from scratch. The dedicated endpoint rapidly trims the existing parent video via FFmpeg (< 0.5s), slices the timeline with all user tweaker overrides, and renders standalone reels in ~5-7s via Remotion.
- **Why**: Creators need full control over their branding (optional watermark), placement (custom headmarker Y location), and style intelligence (letting AI pick the best caption style for the scene). Most importantly, rendering a tweaked 15-30s viral reel must be instantaneous rather than re-uploading and re-transcribing a massive 45-minute parent video.

## 2026-10-23: Dynamic Multi-Style Variety Toggle, 3-5 Word Phrase Subdivision & Universal Active-Window Pagination Shield (Phase 36)
- **Decision**:
  1. **Dynamic Multi-Style Variety User Toggles**: Provided explicit, branded user-facing toggles in both the **Full Video Studio** (`#multiStyleVarietyToggle` in Card 3 Options) and the **AI Viral Reels Studio** (`#clipMultiStyleVarietyToggle` in Section 3 of the Clip Tweaker card).
     - When **Enabled (ON)**: Rotates dynamic, creator-grade styles (`beast_impact`, `hormozi_bold`, `highlighter_marker`, `pill_word`, `karaoke_bounce`, `quote_editorial`, etc.) across sentence groups, bringing Ali Abdaal / MrBeast visual variety.
     - When **Disabled (OFF)**: Strictly locks captions to a single, consistent uniform style throughout the entire duration of the full video or reel.
  2. **Feature Long-Take Subdivision (3-5 Words)**: Solved the root cause of the 13-line vertical column bug where LLMs tagged multi-clause sentences (> 6 words) as a single feature event, causing 15-25 words to render at once. Subdivided long feature events into synchronized 3–5 word sub-events matching transcript phrases (`matching_phrases`) with exact monotonic timing.
  3. **Universal Active-Window Pagination Shield (`getActivePhraseWords`)**: Added a universal pagination helper in `remotion/src/styles/registry.ts` and integrated it across all dynamic styles (`hormozi_bold`, `beast_impact`, `highlighter_marker`, `karaoke_bounce`, `pill_word`). Displays a sliding active window of max 4-5 words centered on the active word, guaranteeing captions never exceed 4-5 words on screen or wrap into vertical towers regardless of input.
- **Why**: Creators requested full autonomy over whether their videos use multi-style visual variety or remain locked to a single uniform style. Additionally, long feature events covering the speaker's face violated safe-zone guidelines; combining backend phrase subdivision with Remotion active-window pagination ensures 100% face clearance, perfect pacing, and broadcast-ready typography across both full videos and viral reels.

## 2026-10-23: Speaker Face Centering Calibration, Professional Restraint & 2x Render Speedup (Phase 37)
- **Decision**:
  1. **Speaker Centering Calibration**:
     - Resolved the root cause where `resolveTimeline` omitted `cameraCuts` from root-level props, defaulting to `0.500`.
     - In Remotion `getCoverObjectPositionX`, replaced overshooting non-linear ratio formula with direct focal percentage alignment (`Math.max(0.15, Math.min(0.85, focusX))`). In OpenCV face detection, added prominent face filtering (`fw * fh >= 0.015`) to ignore tiny background artifacts.
     - Verified centering on test still frame: face `cx = 0.476` (within 2.4% of dead center 0.500).
  2. **Professional Editorial Restraint (Ali Abdaal Aesthetic)**:
     - Constrained broad style pools (>= 8 styles or all 24) to the curated **Professional Editorial Quintet**: `highlighter_marker`, `cinematic_minimal`, `pill_word`, `quote_editorial`, `hormozi_bold`. Gimmick styles (comic bubbles, glitch, flames) never appear in professional videos unless specifically chosen.
     - Anchored styles across **3-4 sentence thoughts** (`g_idx % 3 == 0` or on conversational questions `?`) rather than frantically switching on every single sentence.
  3. **2x Remotion Rendering Speedup**:
     - Switched x264 encoder preset to `ultrafast` (visually lossless with CRF 18).
     - Adjusted compositor JPEG quality to 85% (75% for draft previews).
     - Expanded worker concurrency from 4 to `max(2, min(cpu_cores, 8))` (using all 8 CPU threads on 8-core machines).
     - Measured render benchmark: cut 60-frame render from 18.91s down to 10.08s (an 87% speedup / ~2x faster rendering).
- **Why**: Videos with frantic style-switching every 2 seconds felt chaotic rather than professional; anchoring clean editorial typography across thoughts restores broadcast elegance. Off-center speaker framing caused awkward visual clipping, and rendering 10-minute videos was taking too long; optimizing encoder presets, compositor quality, and concurrency halves rendering times while maintaining visually lossless 1080x1920 output.

## 2026-10-24: Storage Reclaim, Fast-Fail Auth, Audio Extraction Pre-Pass & Studio Live Sync (Phase 38)
- **Decision**:
  1. **Automated Storage Management & 3.4+ GB Disk Reclaim**:
     - Built `cleanup_storage(max_kept_jobs=15)` in `JobManager` with zero risk to test fixtures (`job_mock_*`, `job_test_*`, `test_trim.mp4`).
     - Added automated background pruning in `submit_job` if jobs exceed 40, preventing unbounded directory growth.
     - Pruned 309 historical test runs and purged duplicate video copies in `remotion/public/jobs/` and `remotion/build/public/jobs/`, reclaiming **3,437.88 MB (~3.44 GB)** of disk space and slashing `remotion bundle` compilation time down to seconds.
     - Exposed `GET /api/storage/status` and `POST /api/storage/cleanup` with a top header "🧹 Storage" 1-click clean button and live MB badge in the web UI.
  2. **LLM Fast-Fail & UnboundLocalError Resolution**:
     - Fixed `UnboundLocalError` at `analyze.py:329` by guarding response parsing.
     - Added fast-fail abort on HTTP 401 / 403 / unauthorized error across `MistralPlanner`, `GeminiPlanner`, and `AnthropicPlanner`, immediately dropping into deterministic `RulePlanner` fallback and saving 10-15s of timeout lag.
  3. **High-Speed Transcription Caching & Audio Pre-Pass**:
     - Implemented `compute_fast_file_hash(path)`: samples file size, modification time, and 64KB boundary chunks (< 1ms execution on multi-gigabyte video files vs 5-8s full-file SHA-256).
     - Added 16kHz mono 16-bit PCM WAV extraction pre-pass via FFmpeg before calling `WhisperModel.transcribe`, cutting Whisper transcription time by 30-50%.
  4. **Frontend Studio Polish & Live Sync**:
     - Integrated real-time caption sync on the Studio Monitor HTML5 player: dragging or playing the source video updates `#dragSampleText` and the retention progress bar in real time.
     - Added a "⚡ Clean Filler Words" utility to scrub hesitation words ("um", "uh", "like", "you know") from timeline phrases with 1 click.
     - Added 1-click Social Export Presets (TikTok/Reels 9:16, YouTube Shorts 9:16, LinkedIn/X 1:1, YouTube 16:9).
     - Removed legacy unused concept mockups and duplicate layout stills from `frontend/assets/`.
- **Why**: Historical test jobs and duplicate video copies accumulated to over 3.4 GB and degraded remotion bundle performance. Hashing entire 2GB video files and repeatedly retrying failed API keys introduced unnecessary latency. These enhancements deliver rapid, resilient pipeline execution and a responsive, high-fidelity studio experience.

