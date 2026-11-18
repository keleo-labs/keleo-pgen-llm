#!/usr/bin/env python3
"""Check notebook exports against the Studio GAS resolver and package inputs."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures/notebook-sources"
EXPORTER = ROOT / "utils/export-notebook-sources.py"
STUDIO = ROOT.parent / "keleo-studio-gas"


class NotebookSourcesTest(unittest.TestCase):
    def setUp(self):
        work = tempfile.TemporaryDirectory()
        self.addCleanup(work.cleanup)
        self.work = Path(work.name)
        self.output = self.work / "sources"

    def cli(self, *inputs, output=None, check=True):
        return subprocess.run([sys.executable, str(EXPORTER), *map(str, inputs), "--output-dir",
                               str(output or self.output), "--studio-gas-dir", str(STUDIO)],
                              text=True, capture_output=True, check=check)

    def packaged(self):
        bundle = self.work / "trial.keleo"
        inventory = []
        with ZipFile(bundle, "w") as archive:
            for path in sorted(FIXTURES.glob("*.json")):
                body = json.loads(path.read_text())
                member = f"documents/{path.name}"
                inventory.append({"path": member, "documentType": body["kind"],
                                  "documentName": body["name"], "entryPoint": body["kind"] == "method"})
                archive.write(path, member)
            archive.writestr("manifest.json", json.dumps({
                "package": {"name": "lantern-trial", "version": "1.0.0"}, "documents": inventory
            }))
        return bundle

    def test_practice_uses_studio_closure_and_preserves_authored_fields(self):
        arguments = (FIXTURES / "lighting.json", "--dependency", FIXTURES / "kernel.json",
                     "--dependency", FIXTURES / "colour.json", "--dependency", FIXTURES / "colour-kernel.json")
        self.cli(*arguments)
        file = next(self.output.glob("*.md"))
        text = file.read_text()
        authored, view = text.split("## Studio practice view", 1)
        self.assertIn("Preserve the cobalt dial.", authored)
        self.assertIn("futureField", authored)
        self.assertIn("Authored lantern definition", authored)
        self.assertIn("Reference context — Colour Check / Verified", authored)
        self.assertIn("cobalt reflection on the third tile", authored)
        self.assertIn("Reference context — Colour Check / Verified in", authored)
        self.assertIn("Incomplete Studio view", view)
        self.assertIn("Weather Calibration", text)
        self.assertIn("practice-colour-verification-v1.0.0.md`, absent from this export", text)
        self.assertIn("https://example.invalid/colour-chart", text)
        control = subprocess.run(["node", str(STUDIO / "utils/merge-practice.mjs"),
                                  str(FIXTURES), "Lantern Lighting", "--json"],
                                 text=True, capture_output=True, check=True)
        expected = json.loads(control.stdout)
        for alpha in expected["alphas"]:
            self.assertIn(alpha["name"], view)
        self.assertNotIn("Spare Wicks", view)
        repeat = self.work / "repeat"
        self.cli(*arguments, output=repeat)
        self.assertEqual(file.read_bytes(), (repeat / file.name).read_bytes())
        retry = self.cli(*arguments, check=False)
        self.assertNotEqual(retry.returncode, 0)
        self.assertEqual(text, file.read_text())

    def test_bundle_exports_method_and_members_in_order(self):
        bundle = self.packaged()
        self.cli(bundle)
        self.assertEqual({p.name for p in self.output.glob("*.md")}, {
            "method-lantern-trial-v1.0.0.md", "practice-colour-verification-v1.0.0.md",
            "practice-lantern-lighting-v1.0.0.md",
        })
        text = (self.output / "method-lantern-trial-v1.0.0.md").read_text()
        self.assertLess(text.index("Colour Verification"), text.index("Lantern Lighting"))
        self.assertIn("alphaBindings", text)
        self.assertIn("Colour Check", text)
        self.assertIn("Reference context — Colour Check in Colour Trial Kernel", text)
        self.assertIn("Reference context — Colour Check / Projected in", text)
        self.assertIn("Reference context — Lantern / Ready in", text)
        self.assertNotIn("## Studio practice view", text)
        self.cli(f"{bundle}::documents/kernel.json", output=self.work / "baseline")
        self.assertTrue((self.work / "baseline/baseline-lantern-trial-kernel-v1.0.0.md").is_file())

    def test_embedded_method_and_explicit_list(self):
        method = json.loads((FIXTURES / "method.json").read_text())
        method.pop("practiceNames")
        method["practices"] = [json.loads((FIXTURES / name).read_text())
                               for name in ("colour.json", "lighting.json")]
        method["practices"][0].pop("kind")
        method["practices"][0].pop("version")
        source = self.work / "embedded.json"
        source.write_text(json.dumps(method))
        self.cli(source, "--dependency", FIXTURES / "kernel.json", "--dependency", FIXTURES / "colour-kernel.json")
        file = self.output / "practice-colour-verification-v1.0.0.md"
        self.assertIn("embedded Colour Verification", file.read_text())
        list_output = self.work / "list"
        self.cli(FIXTURES / "lighting.json", FIXTURES / "colour.json", "--dependency",
                 FIXTURES / "kernel.json", "--dependency", FIXTURES / "colour-kernel.json", output=list_output)
        self.assertEqual(len(list(list_output.glob("*.md"))), 2)

    def test_missing_member_stops_before_writing(self):
        result = self.cli(FIXTURES / "kernel.json", FIXTURES / "method.json", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("requires practice 'Colour Verification' missing", result.stderr)
        self.assertFalse(self.output.exists())

    def test_constraint_selects_exact_version_and_reports_cycle(self):
        lamp = json.loads((FIXTURES / "lighting.json").read_text())
        lamp["dependencyVersions"] = [{"documentName": "Colour Verification", "versionRange": "2.x || 3.x"}]
        root = self.work / "lamp.json"
        root.write_text(json.dumps(lamp))
        upgrade = json.loads((FIXTURES / "colour.json").read_text())
        upgrade.update(version="2.0.0", practiceDependencyNames=["Lantern Lighting"])
        extra = self.work / "upgrade.json"
        extra.write_text(json.dumps(upgrade))
        self.cli(root, "--dependency", FIXTURES / "kernel.json", "--dependency",
                 FIXTURES / "colour.json", "--dependency", extra, "--dependency", FIXTURES / "colour-kernel.json")
        output = next(self.output.glob("*.md")).read_text()
        self.assertIn("practice-colour-verification-v2.0.0.md", output)
        self.assertIn("dependency cycle", output)


def grade_export(directory):
    files = {path.name: path.read_text(encoding="utf-8") for path in directory.glob("*.md")}
    if directory.name == "practice":
        text = files.get("practice-lantern-lighting-v1.0.0.md", "")
        checks = {
            "one practice file": len(files) == 1 and bool(text),
            "authored field": "futureField" in text and "Preserve the cobalt dial." in text,
            "state criterion with context": "Reference context — Colour Check / Verified" in text
            and "cobalt reflection on the third tile" in text,
            "declared gap": "Incomplete Studio view" in text and "Weather Calibration" in text,
        }
    else:
        text = files.get("method-lantern-trial-v1.0.0.md", "")
        checks = {
            "method and member files": set(files) == {
                "method-lantern-trial-v1.0.0.md", "practice-colour-verification-v1.0.0.md",
                "practice-lantern-lighting-v1.0.0.md",
            },
            "authored member order": "Colour Verification" in text and "Lantern Lighting" in text
            and text.index("Colour Verification") < text.index("Lantern Lighting"),
            "cross-baseline binding": "alphaBindings" in text and "Colour Trial Kernel" in text
            and "Lantern Trial Kernel" in text and "Reference context — Colour Check in" in text,
        }
    rate = sum(checks.values()) / len(checks)
    return {"checks": checks, "summary": {"pass_rate": rate, "error_pass_rate": rate}}


if __name__ == "__main__":
    if len(sys.argv) == 2 and Path(sys.argv[1]).is_dir():
        print(json.dumps(grade_export(Path(sys.argv[1]))))
    else:
        unittest.main()
