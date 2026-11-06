#!/usr/bin/env python3
"""Check all six Keleo diagram routes with a small practice and Studio fixture."""

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DERIVE = ROOT / "utils/derive-diagram.py"
RENDER = ROOT / "utils/render-diagram.py"
STUDIO = ROOT / "skills/diagram-foundation/scripts/keleo"


class KeleoDiagrams(unittest.TestCase):
    def test_native_views_render_and_preserve_relations(self):
        doc = {
            "name": "Sample", "kind": "practice", "practiceDependencyNames": ["Base"],
            "alphas": [
                {"name": "Goal", "focusName": "Value", "relatesTo": [
                    {"alphaName": "Work", "direction": "mutual", "relationship": "aligns with"}]},
                {"name": "Work", "focusName": "Endeavor", "contributesTo": "Goal"},
            ],
            "activitySpaces": [{"name": "Delivery", "focusName": "Endeavor",
                                "activities": [{"name": "Plan"}]}],
        }
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            source = work / "practice.json"
            source.write_text(json.dumps(doc), encoding="utf-8")
            dependency = work / "base.json"
            dependency.write_text(json.dumps({"name": "Base", "kind": "practiceBaseline",
                                              "baselinePracticeNames": ["Grand"]}),
                                  encoding="utf-8")
            for view, extra in (
                ("practice-dependency", ["--dependency-doc", str(dependency)]),
                ("concern-overview", []),
                ("activity-overview", []),
                ("alpha-relationship", ["--seed", "Goal"]),
            ):
                spec_path = work / f"{view}.json"
                subprocess.run(["python3", str(DERIVE), str(source), "--view", view,
                                *extra, "-o", str(spec_path)], check=True,
                               capture_output=True, text=True, cwd=ROOT)
                spec = json.loads(spec_path.read_text(encoding="utf-8"))
                if view == "practice-dependency":
                    self.assertEqual({n["label"] for n in spec["nodes"]},
                                     {"Sample", "Base", "Grand"})
                    self.assertEqual(len(spec["edges"]), 2)
                if view == "activity-overview":
                    self.assertEqual({n["label"] for n in spec["nodes"]},
                                     {"Delivery", "Plan"})
                if view == "alpha-relationship":
                    self.assertEqual(spec["satellites"][0]["direction"], "mutual")
                svg_path = work / f"{view}.svg"
                subprocess.run(["python3", str(RENDER), str(spec_path), "-o",
                                str(svg_path)], check=True, capture_output=True,
                               text=True, cwd=ROOT)
                self.assertIn("<svg", svg_path.read_text(encoding="utf-8"))
            self.assertIn("marker-start", (work / "alpha-relationship.svg").read_text())

    def test_copied_studio_renderers(self):
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            orchestration = work / "orchestration.svg"
            subprocess.run(["node", str(STUDIO / "render-orchestration-diagram.mjs"),
                            str(ROOT / "tests/fixtures/keleo-orchestration.json"),
                            "--out", str(orchestration)], check=True,
                           capture_output=True, text=True, cwd=ROOT)
            self.assertIn("<svg", orchestration.read_text(encoding="utf-8"))
            state = work / "state.svg"
            result = subprocess.run(
                ["node", str(STUDIO / "render-state-flow-diagram.mjs"),
                 str(ROOT / "tests/fixtures/merge-constructs/baseline.json"),
                 "Platform", "--out", str(state)], check=True,
                capture_output=True, text=True, cwd=ROOT)
            self.assertIn("cycles", result.stdout)
            self.assertIn("Capacity growth", state.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
