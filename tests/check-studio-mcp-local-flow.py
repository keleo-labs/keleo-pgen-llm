#!/usr/bin/env python3
"""Check that MCP materialized documents work without mounted content folders."""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_utility(name):
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), ROOT / "utils" / name)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class StudioLocalFlowTest(unittest.TestCase):
    def test_transitive_resolution_uses_only_mcp_cache(self):
        discover = load_utility("discover-dependencies.py")
        with tempfile.TemporaryDirectory() as temporary:
            cache = Path(temporary) / ".studio-documents"
            documents = (
                ("root", {"kind": "practiceBaseline", "name": "Root", "version": "1.0.0"}),
                ("child", {"kind": "practiceBaseline", "name": "Child", "version": "1.0.0", "baselinePracticeNames": ["Root"]}),
                ("practice", {"kind": "practice", "name": "Practice", "version": "1.0.0", "baselinePracticeName": "Child"}),
            )
            for slug, data in documents:
                folder = cache / slug
                folder.mkdir(parents=True)
                (folder / "document.json").write_text(json.dumps(data), encoding="utf-8")
            index, skipped = discover.build_index([str(cache)])
            result = discover.cmd_resolve_from(str(cache / "practice" / "document.json"), index, transitive=True)
            self.assertFalse(skipped)
            self.assertEqual(result["unresolved"], [])
            self.assertEqual({item["name"] for item in result["dependencies"]}, {"Root", "Child"})

    def test_attribution_encodes_verified_names(self):
        links = load_utility("studio-links.py")
        self.assertIn("?doc=Platform%20Operations", links.attribution("https://studio.example/exec", ["Platform Operations"]))

    def test_materialization_converts_baseline_without_touching_local_draft(self):
        materializer = load_utility("materialize-studio-document.py")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            local = root / "baselines" / "example.json"
            local.parent.mkdir()
            local.write_text('{"name":"Local draft"}', encoding="utf-8")
            raw = root / "response.json"
            raw.write_text(json.dumps({
                "kind": "baseline", "name": "Example", "version": "1.0.0",
                "bundleSlug": "example-1-0-0", "documentPath": "documents/example.json",
                "id": "bundle:example-1-0-0/documents/example.json",
                "documentPath": "documents/wrong-name.json",
                "baselineDependencyNames": ["Root"], "validationWarnings": [],
            }), encoding="utf-8")
            result = materializer.materialize(raw, root / "cache")
            data = json.loads(result.read_text(encoding="utf-8"))
            self.assertEqual(data["kind"], "practiceBaseline")
            self.assertEqual(data["baselinePracticeNames"], ["Root"])
            self.assertNotIn("bundleSlug", data)
            self.assertEqual(result.name, "example.json")
            self.assertEqual(local.read_text(encoding="utf-8"), '{"name":"Local draft"}')


if __name__ == "__main__":
    unittest.main()
