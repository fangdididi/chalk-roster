---
name: chalk-roster
description: Before mass-generating stick-figure, line-art, or chalk-style animated shorts, freeze a cast & style roster and a timed beat sheet, then gate continuity (markers, props, hook, VO density) to SHIP / FIX / HOLD. Use when planning faceless YouTube stick episodes, multi-scene line explainers, or any chalk cast that must not drift between shots.
---

# chalk-roster

Stick and chalk shorts fall apart when the beanie changes color mid-episode, a prop teleports, or the hook arrives at second twelve. **chalk-roster** is a pre-render continuity gate: lock the cast and style once, write timed beats, run the checker, and only then spend generation budget.

## When to use

- Faceless / stick / line-art / chalk animated shorts with a recurring cast
- Multi-scene explainers where the same silhouette must stay recognisable
- Series work where style must fingerprint across episodes
- Any plan that would otherwise jump straight into per-shot prompts

Do **not** use this for live-action edit timing, music-locked cuts, sound mix teardown, human photo pose blocking, or chat sticker packs — those are different jobs.

## Core idea

1. **Roster card** (frozen): channel + style lock + cast members with fixed markers and forbid lists.
2. **Beat sheet**: ordered shots with duration, cast present, action (no idle), props map, optional transfers, VO word counts, hook flag.
3. **Gate**: `chalkroster.py check` → **SHIP** / **FIX** / **HOLD**.

### Verdicts

| Verdict | Meaning | Generate clips? |
| --- | --- | --- |
| `SHIP` | Continuity clean | Yes |
| `FIX` | Soft issues (VO density, travel dir, forbid wording) | Patch beats, then re-check |
| `HOLD` | Hard breaks (unknown cast, prop jump, no hook, incomplete style) | Do not generate |

## Steps

1. Copy `templates/roster.json` → `roster.json`. Fill `style` (aspect, line weight, head fill, limb rule, bg rule, accent cap) and `cast` (id, markers ≥1, forbid).
2. Copy `templates/beats.json` → `beats.json`. One shot per row; mark the early hook; list prop holders; record every hand-off under `transfers` with `transfer: true`.
3. Lint: `python3 scripts/chalkroster.py lint roster.json beats.json`
4. Gate: `python3 scripts/chalkroster.py check roster.json beats.json`
5. Only on `SHIP`: expand each shot into your generator prompts, repeating the **frozen markers** verbatim for every cast member who appears.
6. If `FIX` / `HOLD`: repair the listed issues; never “approximate” a marker change without a transfer event.

## Roster shape

```json
{
  "channel": {"name": "chalk-bytes", "lock_style_across_episodes": true},
  "vo_lang": "en",
  "style": {
    "aspect_ratio": "9:16",
    "line_weight": "medium",
    "head_fill": "hollow",
    "limb_rule": "two-arms-two-legs",
    "bg_rule": "flat-black",
    "max_accent_colors": 3,
    "accent_colors": ["vivid red", "electric blue", "warm gold"],
    "fingerprint": "hollow-head/medium-line/flat-black/3-accent"
  },
  "cast": [
    {
      "id": "guide",
      "role": "narrator-avatar",
      "silhouette": "tall-thin",
      "markers": ["red beanie", "yellow shirt"],
      "forbid": ["photoreal face", "extra arms"]
    }
  ]
}
```

## Beat shape

Each shot needs `duration_s`, `action`, and usually `cast`. Props are a map `prop → holder_id|null`. Changing a holder or a marker requires an explicit transfer.

VO density bands (words/second): English `1.8–2.9`, Chinese `3.2–5.2`. Hook must land by `hook_deadline_s` (default 5).

## Examples

- Clean 30s episode: `examples/cache-lie-roster.json` + `examples/cache-lie-beats.json` → `SHIP`.
- Prop teleport: `examples/broken-prop-jump-beats.json` against the same roster → `HOLD` until a transfer is recorded.
- Built-in: `python3 scripts/chalkroster.py demo`

## Tips

- Markers are **plain words** (“red beanie”), not hex codes or anatomy recipes.
- One silhouette change = new cast id, not a quiet marker edit.
- Keep accent colors ≤ `max_accent_colors`; name them with ordinary language.
- Series mode: set `channel.lock_style_across_episodes` and keep `style.fingerprint` identical across episodes.
- Idle chalk figures fail the gate — every shot needs a concrete `action`.
