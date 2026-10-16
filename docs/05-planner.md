# 05 — Planner (the "AI" that styles the captions)

Input: `phrases.json` (+ optional `words.json`) and options (preset, language).
Output: `plan.json` = list of events matching docs/03 (before layout adjusts zones/layers).

## Always-on base track
Every phrase gets a `pill_word` event (lower zone) so there is a readable caption at all times.
On top of that, the planner adds "feature" events on ~25-40% of phrases.

## Feature-event rules (also the rule-based fallback)
- First sentence of the video / strong claim / question / short punchy statement (<= 8 words) -> `title3d` or
  `serif_title`. Use `title3d` at most once per ~12 seconds.
- Statements with ordinal markers ("first", "number one", "step two", "1.", "2.") -> `numbered_point`
  with the numeral extracted.
- Emphasis words (negations: not/never/no, superlatives, numbers, money, strong verbs, words after "but",
  "actually", "really") -> `highlights` (colour or italic or pill).
- Quotes, asides, or lower-energy lines -> `handwritten` or `blob_card` (frosted).
- Key concept sentences (definition, takeaway, "everything that is X can be Y") -> `blob_card` (glow).
- Spelled letters / lists of single tokens -> `arc_letters`.
- Concrete nouns with a clear emoji/icon (doctor, money, brain, fire, car, heart...) -> `graphic` (sticker).
- Never use more than 2 consecutive events with the same feature style. Leave breathing room: a feature event
  needs >= 1.0 s of gap from the previous feature event of the same style.
- Respect the preset: `bold_creator` (more title3d, more emoji), `calm_serif` (serif_title, blob_card,
  fewer graphics), `minimal_pill` (pill_word only with colour highlights).

## LLM planner
Provider interface: `plan(phrases, options) -> list[Event]` with implementations `GeminiPlanner`,
`AnthropicPlanner`, and `RulePlanner`. Select via `LLM_PROVIDER`.

Use structured/JSON output where the SDK supports it. Always validate with pydantic; on failure retry up to 2
times with the validation error appended; then fall back to `RulePlanner`.
Send phrases in batches (~40 phrases per call) with a short rolling summary of the previous batch to keep
styles varied.

### System prompt (use verbatim as a starting point)
```
You are an expert short-form video editor who designs dynamic animated captions for vertical videos
(Reels/Shorts/TikTok). You receive a list of timed phrases from a transcript. For each phrase, decide how it
should appear on screen.

Return ONLY valid JSON matching the provided schema. No prose, no markdown fences.

Available styles: title3d, serif_title, blob_card (variant: glow|frosted), pill_word, numbered_point,
handwritten, arc_letters, sticker. A readable pill_word base caption is added automatically for every phrase,
so only add feature events where they add impact.

Guidelines:
- Add feature events to roughly 30% of phrases; prefer moments that are claims, hooks, takeaways, numbered
  points, or emotionally strong.
- Vary styles; never repeat the same feature style more than twice in a row.
- Choose 0-2 emphasis words per feature event (highlights) - words that carry the meaning.
- Attach an emoji/icon graphic only when a concrete, recognizable object or concept is mentioned.
- Keep text exactly as spoken (you may fix capitalization/punctuation but never change words).
- Respect the preset: {preset}.
Phrase list (JSON): {phrases_json}
```

## Quality checks after planning
- Text of each event must equal the concatenation of its `wordRange` words (modulo case/punctuation).
- Reject events whose time range does not match their words (tolerance 0.15 s).
- Log style histogram and feature-density; warn if outside 20-45%.
