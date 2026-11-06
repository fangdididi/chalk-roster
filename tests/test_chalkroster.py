#!/usr/bin/env python3
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import chalkroster as cr  # noqa: E402


class ChalkRosterTests(unittest.TestCase):
    def setUp(self):
        self.roster = copy.deepcopy(cr.DEMO_ROSTER)
        self.beats = copy.deepcopy(cr.DEMO_BEATS)

    def test_demo_ships(self):
        r = cr.check(self.roster, self.beats)
        self.assertEqual(r["verdict"], "SHIP")
        self.assertEqual(r["stats"]["shots"], 3)

    def test_missing_style_holds(self):
        del self.roster["style"]["line_weight"]
        r = cr.check(self.roster, self.beats)
        self.assertEqual(r["verdict"], "HOLD")
        self.assertTrue(any("line_weight" in h for h in r["hold"]))

    def test_unknown_cast_holds(self):
        self.beats["shots"][0]["cast"] = ["ghost"]
        r = cr.check(self.roster, self.beats)
        self.assertEqual(r["verdict"], "HOLD")
        self.assertTrue(any("unknown cast" in h for h in r["hold"]))

    def test_prop_jump_without_transfer_holds(self):
        # remove transfer on shot 2
        self.beats["shots"][1].pop("transfer", None)
        self.beats["shots"][1].pop("transfers", None)
        r = cr.check(self.roster, self.beats)
        self.assertEqual(r["verdict"], "HOLD")
        self.assertTrue(any("prop 'meter'" in h for h in r["hold"]))

    def test_marker_override_needs_transfer(self):
        self.beats["shots"][1]["marker_override"] = {
            "guide": ["green beanie", "yellow shirt"]
        }
        self.beats["shots"][1].pop("transfer", None)
        r = cr.check(self.roster, self.beats)
        self.assertEqual(r["verdict"], "HOLD")
        self.assertTrue(any("without transfer" in h for h in r["hold"]))

    def test_no_hook_holds(self):
        self.beats["shots"][0]["hook"] = False
        self.beats["shots"][0]["kind"] = "setup"
        r = cr.check(self.roster, self.beats)
        self.assertEqual(r["verdict"], "HOLD")
        self.assertTrue(any("no hook" in h for h in r["hold"]))

    def test_vo_density_fix(self):
        self.beats["shots"][0]["vo_words"] = 40  # 8 w/s on 5s shot
        r = cr.check(self.roster, self.beats)
        self.assertEqual(r["verdict"], "FIX")
        self.assertTrue(any("vo density" in f for f in r["fix"]))

    def test_accent_overflow_holds(self):
        self.roster["style"]["accent_colors"] = ["a", "b", "c", "d"]
        r = cr.check(self.roster, self.beats)
        self.assertEqual(r["verdict"], "HOLD")

    def test_idle_shot_holds(self):
        self.beats["shots"][2]["action"] = "   "
        r = cr.check(self.roster, self.beats)
        self.assertEqual(r["verdict"], "HOLD")
        self.assertTrue(any("action required" in h for h in r["hold"]))

    def test_duplicate_cast_ids(self):
        self.roster["cast"].append(copy.deepcopy(self.roster["cast"][0]))
        issues = cr.lint_roster(self.roster)
        self.assertTrue(any("unique" in h for h in issues["hold"]))

    def test_travel_without_dir_fix(self):
        self.beats["shots"][1]["screen_dir"] = "sideways"
        r = cr.check(self.roster, self.beats)
        self.assertEqual(r["verdict"], "FIX")

    def test_forbid_token_fix(self):
        self.beats["shots"][0]["action"] = "guide grows extra arms and waves"
        r = cr.check(self.roster, self.beats)
        self.assertEqual(r["verdict"], "FIX")
        self.assertTrue(any("forbid" in f for f in r["fix"]))

    def test_cli_demo_exit(self):
        self.assertEqual(cr.main(["demo"]), 0)

    def test_templates_roundtrip(self):
        tdir = ROOT / "templates"
        roster = json.loads((tdir / "roster.json").read_text())
        beats = json.loads((tdir / "beats.json").read_text())
        r = cr.check(roster, beats)
        self.assertIn(r["verdict"], ("SHIP", "FIX"))  # template should at least not HOLD hard shape


if __name__ == "__main__":
    unittest.main()
