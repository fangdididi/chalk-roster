#!/usr/bin/env python3
"""chalk-roster: pre-render cast & style continuity gate for stick/line/chalk animated shorts.

Commands:
  lint   ROSTER.json [BEATS.json]   validate shape only
  check  ROSTER.json BEATS.json     full continuity gate → SHIP / FIX / HOLD
  demo                              print a tiny SHIP example

Standard library only. Exit codes: 0 SHIP, 2 FIX, 3 HOLD, 1 usage/IO error.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REQUIRED_STYLE = (
    "aspect_ratio",
    "line_weight",
    "head_fill",
    "limb_rule",
    "bg_rule",
    "max_accent_colors",
    "accent_colors",
)
ALLOWED_RATIOS = {"16:9", "9:16", "1:1", "4:5"}
ALLOWED_HEAD = {"hollow", "filled-white", "filled-flat", "dot"}
ALLOWED_LIMB = {"two-arms-two-legs", "stick-simple", "glove-hands"}
VO_BOUNDS = {
    "en": (1.8, 2.9),  # words / second
    "zh": (3.2, 5.2),
}
HOOK_DEFAULT_S = 5.0


def _load(path: str | Path) -> Any:
    p = Path(path)
    with p.open(encoding="utf-8") as f:
        return json.load(f)


def _issues() -> dict[str, list[str]]:
    return {"hold": [], "fix": []}


def lint_roster(roster: dict) -> dict[str, list[str]]:
    out = _issues()
    if not isinstance(roster, dict):
        out["hold"].append("roster must be a JSON object")
        return out
    style = roster.get("style")
    if not isinstance(style, dict):
        out["hold"].append("style lock missing")
        return out
    for k in REQUIRED_STYLE:
        if k not in style:
            out["hold"].append(f"style.{k} missing")
    ratio = style.get("aspect_ratio")
    if ratio is not None and ratio not in ALLOWED_RATIOS:
        out["hold"].append(f"aspect_ratio must be one of {sorted(ALLOWED_RATIOS)}")
    head = style.get("head_fill")
    if head is not None and head not in ALLOWED_HEAD:
        out["hold"].append(f"head_fill must be one of {sorted(ALLOWED_HEAD)}")
    limb = style.get("limb_rule")
    if limb is not None and limb not in ALLOWED_LIMB:
        out["hold"].append(f"limb_rule must be one of {sorted(ALLOWED_LIMB)}")
    max_acc = style.get("max_accent_colors")
    accents = style.get("accent_colors")
    if isinstance(max_acc, int) and isinstance(accents, list):
        if len(accents) > max_acc:
            out["hold"].append(f"accent_colors has {len(accents)} > max_accent_colors {max_acc}")
        if len(set(a.lower() for a in accents if isinstance(a, str))) != len(
            [a for a in accents if isinstance(a, str)]
        ):
            out["fix"].append("accent_colors has duplicates")
    elif accents is not None and not isinstance(accents, list):
        out["hold"].append("accent_colors must be a list of plain color words")

    cast = roster.get("cast")
    if not isinstance(cast, list) or not cast:
        out["hold"].append("cast must be a non-empty list")
        return out
    ids = []
    for i, member in enumerate(cast):
        if not isinstance(member, dict):
            out["hold"].append(f"cast[{i}] must be an object")
            continue
        cid = member.get("id")
        if not cid or not isinstance(cid, str):
            out["hold"].append(f"cast[{i}].id missing")
        else:
            ids.append(cid)
        markers = member.get("markers")
        if not isinstance(markers, list) or len(markers) < 1:
            out["hold"].append(f"cast[{cid or i}].markers need ≥1 fixed visual anchors")
        forbid = member.get("forbid", [])
        if forbid is not None and not isinstance(forbid, list):
            out["hold"].append(f"cast[{cid or i}].forbid must be a list")
        if "silhouette" not in member and "role" not in member:
            out["fix"].append(f"cast[{cid or i}] missing silhouette or role label")
    if len(ids) != len(set(ids)):
        out["hold"].append("cast ids must be unique")

    channel = roster.get("channel")
    if not isinstance(channel, dict) or not channel.get("name"):
        out["fix"].append("channel.name recommended for series continuity")
    return out


def lint_beats(beats: dict) -> dict[str, list[str]]:
    out = _issues()
    if not isinstance(beats, dict):
        out["hold"].append("beats must be a JSON object")
        return out
    if "title" not in beats:
        out["fix"].append("beats.title missing")
    shots = beats.get("shots")
    if not isinstance(shots, list) or not shots:
        out["hold"].append("shots must be a non-empty list")
        return out
    t = 0.0
    for i, shot in enumerate(shots):
        if not isinstance(shot, dict):
            out["hold"].append(f"shots[{i}] must be an object")
            continue
        dur = shot.get("duration_s")
        if not isinstance(dur, (int, float)) or dur <= 0:
            out["hold"].append(f"shots[{i}].duration_s must be > 0")
        else:
            t += float(dur)
        if "action" not in shot or not str(shot.get("action") or "").strip():
            out["hold"].append(f"shots[{i}].action required (no idle chalk figures)")
        if "cast" in shot and not isinstance(shot["cast"], list):
            out["hold"].append(f"shots[{i}].cast must be a list of cast ids")
        if "props" in shot and not isinstance(shot["props"], dict):
            out["hold"].append(f"shots[{i}].props must be a map prop→holder_id|null")
    beats_total = beats.get("target_duration_s")
    if isinstance(beats_total, (int, float)) and abs(t - float(beats_total)) > 0.51:
        out["fix"].append(f"sum(shot durations)={t:.1f}s ≠ target_duration_s={beats_total}")
    return out


def check(roster: dict, beats: dict) -> dict[str, Any]:
    issues = _issues()
    for src in (lint_roster(roster), lint_beats(beats)):
        issues["hold"].extend(src["hold"])
        issues["fix"].extend(src["fix"])

    cast_map = {
        m["id"]: m
        for m in (roster.get("cast") or [])
        if isinstance(m, dict) and isinstance(m.get("id"), str)
    }
    style = roster.get("style") or {}
    shots = beats.get("shots") or []
    lang = (beats.get("vo_lang") or roster.get("vo_lang") or "en").lower()
    if lang not in VO_BOUNDS:
        lang = "en"
    lo, hi = VO_BOUNDS[lang]
    hook_deadline = float(beats.get("hook_deadline_s") or HOOK_DEFAULT_S)

    # cast presence
    for i, shot in enumerate(shots):
        if not isinstance(shot, dict):
            continue
        for cid in shot.get("cast") or []:
            if cid not in cast_map:
                issues["hold"].append(f"shots[{i}] references unknown cast id '{cid}'")

    # marker continuity + prop ownership
    last_markers: dict[str, list] = {
        cid: list(m.get("markers") or []) for cid, m in cast_map.items()
    }
    last_props: dict[str, str | None] = {}  # prop → holder
    cursor = 0.0
    hook_ok = False
    for i, shot in enumerate(shots):
        if not isinstance(shot, dict):
            continue
        dur = float(shot.get("duration_s") or 0)
        # hook
        if cursor + dur <= hook_deadline + 1e-9:
            if shot.get("hook") is True or shot.get("kind") == "hook":
                hook_ok = True
        # marker overrides
        overrides = shot.get("marker_override") or {}
        if overrides and not isinstance(overrides, dict):
            issues["hold"].append(f"shots[{i}].marker_override must be an object")
        else:
            for cid, new_markers in (overrides or {}).items():
                if cid not in cast_map:
                    issues["hold"].append(f"shots[{i}] marker_override unknown cast '{cid}'")
                    continue
                if not shot.get("transfer"):
                    # silent marker change without transfer event
                    if list(new_markers) != list(last_markers.get(cid) or []):
                        issues["hold"].append(
                            f"shots[{i}] changes markers for '{cid}' without transfer=true"
                        )
                last_markers[cid] = list(new_markers)
        # implicit: cast appearing must keep markers unless override
        for cid in shot.get("cast") or []:
            if cid in overrides:
                continue
            # still fine — using last_markers
            _ = last_markers.get(cid)

        # props map: prop → holder id or null
        props = shot.get("props") or {}
        if isinstance(props, dict):
            for prop, holder in props.items():
                prev = last_props.get(prop)
                if prev is not None and holder != prev:
                    # need transfer note listing this prop
                    transfers = shot.get("transfers") or []
                    ok = False
                    if shot.get("transfer") is True:
                        ok = True
                    for tr in transfers:
                        if isinstance(tr, dict) and tr.get("prop") == prop:
                            if tr.get("from") == prev and tr.get("to") == holder:
                                ok = True
                    if not ok:
                        issues["hold"].append(
                            f"shots[{i}] prop '{prop}' jumps {prev}→{holder} without transfer record"
                        )
                if holder is not None and holder not in cast_map:
                    issues["hold"].append(
                        f"shots[{i}] prop '{prop}' held by unknown cast '{holder}'"
                    )
                last_props[prop] = holder

        # screen direction for travel
        if shot.get("travel"):
            if shot.get("screen_dir") not in ("L", "R", "U", "D", "in", "out"):
                issues["fix"].append(
                    f"shots[{i}] travel=true but screen_dir not in L/R/U/D/in/out"
                )

        # VO density per shot
        vo = shot.get("vo_words")
        if isinstance(vo, int) and dur > 0:
            rate = vo / dur
            if rate < lo or rate > hi:
                issues["fix"].append(
                    f"shots[{i}] vo density {rate:.2f} w/s outside {lang} band {lo}-{hi}"
                )

        # forbid check: action/vo text shouldn't include forbid tokens (soft)
        forbid_hits = []
        blob = " ".join(
            str(shot.get(k) or "") for k in ("action", "vo", "note")
        ).lower()
        for cid in shot.get("cast") or []:
            for tok in cast_map.get(cid, {}).get("forbid") or []:
                if isinstance(tok, str) and tok.lower() in blob:
                    forbid_hits.append(f"{cid}:{tok}")
        if forbid_hits:
            issues["fix"].append(f"shots[{i}] mentions forbid tokens {forbid_hits}")

        cursor += dur

    if shots and not hook_ok:
        issues["hold"].append(
            f"no hook shot ending by {hook_deadline}s (set hook=true or kind=hook on an early shot)"
        )

    # series: channel style fingerprint reminder
    if roster.get("channel", {}).get("lock_style_across_episodes") and not style.get(
        "fingerprint"
    ):
        issues["fix"].append(
            "channel.lock_style_across_episodes set but style.fingerprint missing"
        )

    # verdict
    if issues["hold"]:
        verdict = "HOLD"
    elif issues["fix"]:
        verdict = "FIX"
    else:
        verdict = "SHIP"

    return {
        "verdict": verdict,
        "hold": issues["hold"],
        "fix": issues["fix"],
        "stats": {
            "cast": len(cast_map),
            "shots": len(shots),
            "duration_s": round(cursor, 2),
            "vo_lang": lang,
        },
    }


DEMO_ROSTER = {
    "channel": {"name": "chalk-bytes", "lock_style_across_episodes": True},
    "vo_lang": "en",
    "style": {
        "aspect_ratio": "9:16",
        "line_weight": "medium",
        "head_fill": "hollow",
        "limb_rule": "two-arms-two-legs",
        "bg_rule": "flat-black",
        "max_accent_colors": 3,
        "accent_colors": ["vivid red", "electric blue", "warm gold"],
        "fingerprint": "hollow-head/medium-line/flat-black/3-accent",
    },
    "cast": [
        {
            "id": "guide",
            "role": "narrator-avatar",
            "silhouette": "tall-thin",
            "markers": ["red beanie", "yellow shirt"],
            "forbid": ["photoreal face", "extra arms"],
        },
        {
            "id": "rival",
            "role": "foil",
            "silhouette": "short-round",
            "markers": ["blue scarf"],
            "forbid": ["red beanie"],
        },
    ],
}

DEMO_BEATS = {
    "title": "Why caches lie",
    "target_duration_s": 30,
    "hook_deadline_s": 5,
    "vo_lang": "en",
    "shots": [
        {
            "id": "s1",
            "duration_s": 5,
            "kind": "hook",
            "hook": True,
            "cast": ["guide"],
            "action": "guide snaps fingers; cache meter flashes wrong",
            "vo_words": 12,
            "props": {"meter": "guide"},
        },
        {
            "id": "s2",
            "duration_s": 10,
            "cast": ["guide", "rival"],
            "action": "rival steals the meter; guide points at the jump",
            "vo_words": 22,
            "transfer": True,
            "transfers": [{"prop": "meter", "from": "guide", "to": "rival"}],
            "props": {"meter": "rival"},
            "travel": True,
            "screen_dir": "R",
        },
        {
            "id": "s3",
            "duration_s": 15,
            "cast": ["guide"],
            "action": "guide redraws the meter as a truthful timeline",
            "vo_words": 30,
            "props": {"meter": "guide"},
            "transfer": True,
            "transfers": [{"prop": "meter", "from": "rival", "to": "guide"}],
        },
    ],
}


def cmd_lint(args: argparse.Namespace) -> int:
    roster = _load(args.roster)
    issues = lint_roster(roster)
    if args.beats:
        b = lint_beats(_load(args.beats))
        issues["hold"].extend(b["hold"])
        issues["fix"].extend(b["fix"])
    ok = not issues["hold"] and not issues["fix"]
    print(json.dumps({"ok": ok, **issues}, indent=2, ensure_ascii=False))
    return 0 if ok else (3 if issues["hold"] else 2)


def cmd_check(args: argparse.Namespace) -> int:
    result = check(_load(args.roster), _load(args.beats))
    print(json.dumps(result, indent=2, ensure_ascii=False))
    v = result["verdict"]
    return {"SHIP": 0, "FIX": 2, "HOLD": 3}.get(v, 1)


def cmd_demo(_args: argparse.Namespace) -> int:
    result = check(DEMO_ROSTER, DEMO_BEATS)
    print(json.dumps({"roster": DEMO_ROSTER, "beats": DEMO_BEATS, "result": result}, indent=2))
    return 0 if result["verdict"] == "SHIP" else 3


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="chalkroster", description=__doc__)
    sp = p.add_subparsers(dest="cmd", required=True)

    p_lint = sp.add_parser("lint", help="shape-check roster and optional beats")
    p_lint.add_argument("roster")
    p_lint.add_argument("beats", nargs="?")
    p_lint.set_defaults(func=cmd_lint)

    p_check = sp.add_parser("check", help="full continuity gate")
    p_check.add_argument("roster")
    p_check.add_argument("beats")
    p_check.set_defaults(func=cmd_check)

    p_demo = sp.add_parser("demo", help="run built-in SHIP example")
    p_demo.set_defaults(func=cmd_demo)

    args = p.parse_args(argv)
    try:
        return args.func(args)
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"error: invalid JSON: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
