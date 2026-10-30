#!/usr/bin/env python3
"""Regression checks for shared skills and portable prompt-history hooks."""
import argparse
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]

def module(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / file)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result

history = module("history", "utils/prompt-history.py")
vendors = module("vendors", "utils/vendor-skills.py")

class Portability(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.history_file = self.root / history.HISTORY_FILENAME
        self.history_file.write_text("## Interaction Log\n\n## Decisions\n")
        self.pointer = self.root / "active.json"
        self.pointer.write_text(json.dumps({"directory": str(self.root)}))
        self.override = patch.object(history, "POINTER_PATH", str(self.pointer))
        self.override.start()
        self.addCleanup(self.override.stop)

    def hook(self, kind, payload):
        with patch("sys.stdin", io.StringIO(json.dumps(payload))), patch("sys.stdout", new_callable=io.StringIO) as output:
            history.cmd_hook(argparse.Namespace(hook=kind))
            self.assertEqual(output.getvalue(), "")

    def test_prompt_duplicate_and_session_isolation(self):
        payload = json.loads((ROOT / "tests/fixtures/hooks/cursor-prompt.json").read_text())
        self.hook("user-prompt", payload)
        self.hook("user-prompt", {"session_id": "session-a", "prompt": payload["prompt"]})
        self.hook("user-prompt", {"session_id": "session-b", "prompt": "Unrelated"})
        content = self.history_file.read_text()
        self.assertEqual(content.count(payload["prompt"]), 1)
        self.assertNotIn("Unrelated", content)

    def test_question_exchange(self):
        self.hook("tool", json.loads((ROOT / "tests/fixtures/hooks/claude-question.json").read_text()))
        content = self.history_file.read_text()
        self.assertIn("Which baseline?", content)
        self.assertIn("Platform", content)

    def test_codex_question_exchange(self):
        self.hook("tool", {
            "session_id": "codex-session", "tool_name": "functions.request_user_input",
            "tool_input": {"questions": [{"id": "baseline", "question": "Choose a baseline"}]},
            "tool_response": {"answers": {"baseline": {"answers": ["Platform"]}}},
        })
        content = self.history_file.read_text()
        self.assertIn("Choose a baseline", content)
        self.assertIn("Platform", content)

    def test_unidentified_and_malformed_events_are_ignored(self):
        before = self.history_file.read_text()
        self.hook("user-prompt", {"prompt": "No identity"})
        self.hook("user-prompt", [])
        self.assertEqual(self.history_file.read_text(), before)

    def test_wrapper_overlay_survives_regeneration(self):
        canonical = self.root / "skills/example"
        canonical.mkdir(parents=True)
        (canonical / "SKILL.md").write_text("---\nname: example\ndescription: Example\n---\nBody\n")
        adapter = self.root / ".test/skills/example/adapter.md"
        adapter.parent.mkdir(parents=True)
        adapter.write_text("Runtime mapping\n")
        with patch.object(vendors, "ROOT", self.root), patch.object(vendors, "CANONICAL", self.root / "skills"):
            vendors.sync(".test/skills", True)
            self.assertEqual(vendors.sync(".test/skills", False), [])
            self.assertIn("adapter.md", (adapter.parent / "SKILL.md").read_text())
            self.assertEqual(adapter.read_text(), "Runtime mapping\n")
            with self.assertRaises(ValueError):
                vendors.sync("../outside", True)

if __name__ == "__main__":
    unittest.main()
