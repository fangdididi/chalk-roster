# chalk-roster

[中文](README.zh-CN.md) | **English**

Pre-render **cast & style continuity gate** for stick-figure, line-art, and chalk-style animated shorts. Freeze a roster, write timed beats, run the checker, and only spend generation budget on a `SHIP` verdict.

## Features

- **Style lock** — aspect ratio, line weight, head fill, limb rule, background, accent-color cap + fingerprint
- **Cast roster** — each member has fixed markers and a forbid list
- **Beat sheet** — timed shots with action (no idle), cast presence, prop ownership, transfers, hook flag
- **Continuity gate** — unknown cast, prop teleport, silent marker drift, missing hook → `HOLD`; VO density / travel dir / forbid wording → `FIX`
- **Stdlib helper** — `scripts/chalkroster.py` (`lint` / `check` / `demo`) + unit tests

## Install

Clone this repo and point your agent at it, or copy the folder into your skills directory.

```bash
git clone https://github.com/fangdididi/chalk-roster.git
cd chalk-roster
```

### Claude Code / Codex / Cursor-style agents

- Place or symlink the repo where your agent loads skills from, **or**
- Open the folder and say: “Follow SKILL.md (chalk-roster) on this episode plan.”

No API keys. Helper is Python 3 stdlib only.

## Usage

```bash
# shape check
python3 scripts/chalkroster.py lint templates/roster.json templates/beats.json

# full gate
python3 scripts/chalkroster.py check templates/roster.json templates/beats.json

# built-in SHIP demo
python3 scripts/chalkroster.py demo

# tests
python3 -m unittest discover -s tests -v
```

Typical agent flow:

1. Fill `roster.json` (style + cast).
2. Fill `beats.json` (shots, hook, props, transfers).
3. Run `check`. Branch on `SHIP` / `FIX` / `HOLD`.
4. On `SHIP`, expand shots into generator prompts — repeat frozen markers verbatim.

## Examples

| Files | Expected |
| --- | --- |
| `examples/cache-lie-roster.json` + `examples/cache-lie-beats.json` | `SHIP` |
| same roster + `examples/broken-prop-jump-beats.json` | `HOLD` (prop jump) |

## File structure

```
chalk-roster/
├── SKILL.md              # English skill
├── SKILL.zh-CN.md        # 中文技能
├── README.md
├── README.zh-CN.md
├── LICENSE
├── scripts/chalkroster.py
├── tests/test_chalkroster.py
├── templates/roster.json
├── templates/beats.json
└── examples/
```

## Verdict cheat-sheet

| Verdict | Exit | Meaning |
| --- | --- | --- |
| SHIP | 0 | Continuity clean — generate |
| FIX | 2 | Soft issues — patch beats |
| HOLD | 3 | Hard break — do not generate |
