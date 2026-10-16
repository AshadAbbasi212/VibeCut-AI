# 03 — timeline.json schema (contract between Python and Remotion)

All times are in **seconds** in JSON; Remotion converts to frames with `Math.round(t * fps)`.

```json
{
  "version": 1,
  "video": {
    "src": "jobs/abc123/input.mp4",
    "width": 1080,
    "height": 1920,
    "fps": 30,
    "durationSec": 31.4
  },
  "language": "en",
  "words": [
    { "i": 0, "text": "Making", "start": 0.12, "end": 0.40 }
  ],
  "events": [
    {
      "id": "e1",
      "style": "title3d",
      "start": 0.12,
      "end": 2.60,
      "zone": "upper",
      "layer": 2,
      "wordRange": [0, 7],
      "text": "Making money is basically a skills problem",
      "lines": ["Making money", "is basically a", "skills problem"],
      "highlights": [
        { "wordIndex": 4, "kind": "color", "value": "#FFD166" }
      ],
      "palette": "sunset",
      "decorations": ["sparkles"],
      "graphic": null,
      "animation": { "in": "pop", "out": "fade", "wordStagger": 0.04 }
    },
    {
      "id": "e2",
      "style": "pill_word",
      "start": 0.12,
      "end": 2.60,
      "zone": "lower",
      "layer": 1,
      "wordRange": [0, 7],
      "text": "Making money is basically a skills problem"
    }
  ]
}
```

## Field rules
- `style` is one of the ids in docs/04. Unknown ids must fail validation (Python) and render a safe fallback
  (`pill_word`) in Remotion with a console warning.
- `zone`: `upper` | `center` | `lower` | `free` (free uses explicit `x`,`y` fractions 0-1).
- `layer`: integer z-order; higher on top. Max 3 events overlap in time.
- `wordRange`: inclusive `[firstWordIndex, lastWordIndex]` into `words`; drives word-synced animation.
- `highlights[].kind`: `color` | `italic` | `pill` | `underline` | `scale`; `value` is a CSS colour or style token.
- `palette`: named palette defined in the style (e.g. `sunset`, `ocean`, `candy`, `mono`).
- `decorations`: any of `sparkles`, `ellipse`, `underline_scribble`, `arrow`, `none`.
- `graphic`: `null` or `{ "kind": "emoji"|"icon"|"image", "value": "🩺", "position": "above"|"below"|"left"|"right" }`.
- `animation.in`: `pop` | `slide_up` | `fade` | `typewriter` | `none`; `animation.out`: `fade` | `pop` | `none`.

## Invariants (test them)
- `0 <= start < end <= video.durationSec`
- words sorted by time; `wordRange` valid
- at no instant are more than 3 events active; no two events share a zone while overlapping in time,
  except `pill_word` (lower) may coexist with an upper/center event
- every event has duration >= 0.5 s
