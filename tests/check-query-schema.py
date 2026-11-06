#!/usr/bin/env python3
"""Check modular schema discovery and compatibility schema queries."""

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
QUERY = ROOT / "utils/query-schema.py"


class QuerySchemaTests(unittest.TestCase):
    def query(self, *args):
        return subprocess.run([sys.executable, str(QUERY), *args],
                              cwd=ROOT, capture_output=True, text=True, check=True).stdout

    def test_modular_definitions_and_cross_module_inheritance(self):
        listing = self.query("--list")
        self.assertIn("Alpha ", listing)
        self.assertIn("PackageManifest ", listing)
        alpha = self.query("Alpha")
        self.assertIn("Extends: PracticeElement", alpha)
        self.assertIn("* name: string", alpha)
        self.assertIn("* focusName: string", alpha)
        practice = self.query("Practice")
        self.assertIn("* name: string", practice)
        self.assertIn("kind: enum(", practice)
        self.assertIn("alphas: [Alpha]", practice)

    def test_compatibility_schema_remains_queryable(self):
        legacy = self.query("Alpha", "--schema", "deps/language.schema.json")
        self.assertIn("* name: string", legacy)


if __name__ == "__main__":
    unittest.main()
