#!/usr/bin/env python3
"""Verify dependency versions select the newest copy in either scan order.

Given two copies of one dependency at different versions,
when the version index is built and dependency constraints are refreshed,
then the newer version wins regardless of directory traversal order.
"""
import importlib.util
import itertools
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("apply_versioning", ROOT / "utils/apply-versioning.py")
VERSIONING = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERSIONING)


class DependencyVersionTests(unittest.TestCase):
    def test_files_from_selects_exact_files(self):
        fixture = ROOT / "tests/fixtures/version-collision-new.json"
        with tempfile.TemporaryDirectory() as directory:
            listing = Path(directory) / "files.txt"
            listing.write_text(f"{fixture}\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(ROOT / "utils/apply-versioning.py"),
                 "--files-from", str(listing), "--show"],
                capture_output=True, text=True, check=True,
            )
            self.assertIn("Version Collision Probe", result.stdout)

    def test_newest_copy_wins_in_both_orders(self):
        fixtures = [ROOT / "tests/fixtures/version-collision-old.json",
                    ROOT / "tests/fixtures/version-collision-new.json"]
        for paths in itertools.permutations(fixtures):
            with self.subTest(order=[p.name for p in paths]):
                index = VERSIONING.build_version_index(paths)
                self.assertEqual(index["Version Collision Probe"], "1.1.0")
                self.assertEqual(VERSIONING.resolve_dependency_version("Version Collision Probe", index), "1.1.0")


if __name__ == "__main__":
    unittest.main()
