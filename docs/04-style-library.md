# 04 — Style Library (match `docs/reference-screenshots/`)

Open each referenced screenshot while implementing. Fonts below are suggestions from Google Fonts (OFL):
verify availability in `@remotion/google-fonts` and pick the closest feel.

## Frame, zones, safe areas (1080x1920)
- Safe margins: left/right 6% (right 14% near the bottom, where Shorts UI sits), top 10%, bottom 16%.
- Zones: `upper` ~ y 14-38%, `center` ~ y 38-62%, `lower` ~ y 66-80%.
- In the references, titles sit roughly mid-frame over the speaker's torso, the pill sits at ~72-76% height.

## Style ids

### `title3d`  (ref 01)
Big uppercase condensed heavy sans (try Anton, Bebas Neue, or Alfa Slab One), 2-4 centered lines.
- Each LINE has its own vertical gradient fill (e.g. peach->orange, lavender->purple, light-blue->orange).
- A solid dark extruded "3D" shadow offset down-right ~8-14px with a darker same-hue colour.
- Thin white/cream outer outline.
- Flanking sparkle emoji/shapes that twinkle.
- Implementation hint: `background-clip:text` gradients do NOT combine with `text-shadow` extrusion in one
  element. Use TWO stacked copies of the text: bottom copy = stacked `text-shadow` (many 1px steps) or
  `-webkit-text-stroke` + extrusion in the dark colour; top copy = gradient fill via `background-clip:text`.
- Animation: words pop in with spring overshoot, slight rotation wobble, 40 ms stagger.
- Palettes: `sunset`, `ocean`, `candy`, `mono`.

### `blob_card`  (ref 02, ref 07)
Organic rounded "blob" background (SVG path, irregular rounded rectangle) behind 2-3 lines of bold serif text
(try Fraunces, Playfair Display, DM Serif Display).
- Variant `glow` (ref 02): deep blue->purple radial gradient, soft outer glow, white text, ✨ flanking.
- Variant `frosted` (ref 07): translucent whitish blob with backdrop-blur feel, white text; emphasized words in
  crimson/rose (e.g. NOT in caps bold, key phrase bold).
- Blob subtly morphs/breathes (animate path control points slightly).
- Animation: blob scales in with spring, text fades up per line.

### `pill_word`  (refs 03, 05, 06)
The workhorse. Rounded-rect pill (light translucent/off-white, ~85% opacity) in the lower zone containing the
CURRENT 1-4 words in a bold geometric sans (Poppins, Montserrat).
- Words already spoken: near-black, bold. Not-yet-spoken words in the same pill: mid-grey.
  Study screenshots 03, 05, 06 to confirm the exact behaviour and mimic it.
- Pill width hugs text; short pop/scale on each phrase change.

### `serif_title`  (ref 05)
White serif display (Fraunces, DM Serif Display) 2-3 lines, with emphasis treatments inside the text:
- `pill` highlight: key words in a white rounded highlight with red text (e.g. "STOP PLANNING")
- `color` highlight: a keyword in warm yellow (e.g. "TAKE ACTION")
- decoration `ellipse`: thin white hand-drawn ellipse outline that draws on and overlaps the text.

### `numbered_point`  (ref 06)
Italic serif numeral (e.g. "1") with a small hand-drawn ellipse doodle around it, above 2-3 lines of white
serif text; one keyword in italic yellow (e.g. "monetise"). Used for list/step statements ("number one...").

### `handwritten`  (ref 04, small top line)
Small handwritten font (Caveat, Patrick Hand, Gochi Hand), white with soft dark shadow, typewriter or
word-fade animation; used for secondary or whispered/aside lines.

### `arc_letters`  (ref 04)
Letters/short words placed along an arc, each letter a different pastel colour (peach, yellow, mint, aqua)
with a soft glow/outline, gentle float animation. Use for spelled-out letters, acronyms, "A B C D" lists.

### `sticker`  (ref 04 avatar)
An emoji/icon/image with a coloured glow outline (drop-shadow stack, e.g. cyan) that pops in with a spring and
floats slightly. Positioned above a pill caption or beside a title. Triggered by `graphic` on an event or as a
standalone event.

### Doodles & decorations (shared)
- `ellipse`: SVG path stroke draw-on (stroke-dashoffset or `@remotion/paths` evolve-path), 2-3px white,
  slightly irregular, overlaps text.
- `underline_scribble`, `arrow`: same technique.
- `sparkles`: 4-point star shapes or ✨ emoji, scale/rotate twinkle loop.

## Shared animation helpers (build once, in `remotion/src/anim/`)
`popIn(frame, fps, delay)`, `staggerWords`, `fadeOut`, `drawOn(path, progress)`, `floatY`, `twinkle`.
Use Remotion `spring()` and `interpolate()` only (no CSS transitions/animations; they do not render
deterministically).

## Rendering rules
- Everything must be deterministic functions of the current frame.
- Measure text before layout (e.g. `@remotion/layout-utils` `fitText` / `measureText`) so lines fit inside
  the safe width; auto-reduce font size, never overflow.
- Keep a `StyleGallery` composition with sample text for every style/palette/variant.
