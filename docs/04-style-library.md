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

### `neon_glow`
Electric neon-cyan text with multi-layered glow filter on a dark translucent frosted pill. Words pop with spring
scaling and a subtle luminous flicker pulse, ideal for tech, high-energy, or nightlife punchlines.

### `typewriter_terminal`
Retro monospace terminal aesthetic (Roboto Mono / Courier) featuring a cyan `> ` command prompt and blinking
accent cursor. Words type out letter-by-letter with a mechanical digital cadence.

### `paper_cutout`
Angled kraft-paper style torn-card caption with a realistic translucent washi tape overlay at the top edge.
Features slight natural tilt (-2.5 deg) and deep drop-shadow, perfect for storytelling or casual vlogs.

### `glitch_kinetic`
High-impact cybernetic glitch effect with split RGB cyan and magenta chromatic aberration layers, staggered
subtle horizontal jitter, and aggressive bold condensed typography.

### `quote_editorial`
Magazine editorial quote design with an oversized warm amber quotation mark mark `“`, elegant italic Fraunces
serif typography, and a subtle champagne glass background.

### `comic_bubble`
Playful pop-art comic book speech bubble with high-contrast 3.5px black border, solid white fill, bold comic
sans lettering (Montserrat/Bangers feel), and a bottom-left directional pointer tail notch.

### `gradient_outline`
Modern sleek transparent pill with an iridescent pink-to-purple gradient border (`border: 2px solid`, gradient
box-shadow glow), and gradient-masked headline text.

### `minimal_underline`
Swiss modernist minimalist typography with an energetic animated horizontal underline bar that draws in
from left to right beneath the text using gradient accents.

### `hormozi_bold`
Ultra-punchy Alex Hormozi signature short-form typography: heavy condensed uppercase sans-serif with
aggressive black borders, radioactive neon yellow keyword pop, and rapid phrase flashing.

### `retro_vaporwave`
80s synthwave / aesthetic video styling: chrome gradient typography, soft neon magenta-to-cyan backdrop
haze, and a retro perspective grid glow.

### `karaoke_bounce`
Dynamic karaoke rhythm caption: active spoken words are highlighted with a glowing golden bouncing dot
following exact word timings with spring physics.

### `fire_burn`
High-octane fiery energy captions: blazing amber-to-crimson animated gradient with flickering ambient
glow and burning heat distortion aesthetics.

### `beast_impact`
MrBeast viral retention styling: dynamic -2° tilt, multi-layer 3D extruded black drop-shadow, explosive
spring pop scaling, and high-visibility lime & cyber-yellow keyword punch.

### `highlighter_marker`
Ali Abdaal / Vox video essay aesthetic: clean editorial typography with an animated pastel highlighter
stroke sweep that draws dynamically behind key spoken words.

### `cinematic_minimal`
A24 / Netflix widescreen subtitle aesthetic: clean letterbox typography with warm amber letter-spacing,
subtle dark frosted glass backing pill, and gentle fade cadence.

### `cyber_hud`
Sci-fi HUD telemetry display: monospace tech font with bracket telemetry `[ ]`, scanline overlay,
and pulsing electric cyan holographic glow.

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
