#!/usr/bin/env python3
"""Regression check for APA references and team-meeting integration, 1.0.1."""
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "utils"))
spec = importlib.util.spec_from_file_location("report_lint", ROOT / "utils/lint-report.py")
lint = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lint)


class ReferencesTests(unittest.TestCase):
    def test_bulleted_dated_and_undated_references(self):
        body = ["([Farley et al., 2026](https://example.org/article)); [NVIDIA, n.d.](https://example.org/docs)."]
        references = ["- Farley, P., Yasin, F., & Sahu, K. (2026, October 9). Article.",
                      "- NVIDIA. (n.d.). Documentation."]
        cites = lint.find_in_text_citations(body)
        refs = lint.find_reference_entries(references, 1)
        self.assertEqual(len(refs), 2)
        self.assertFalse(lint.check_citations(cites, refs, 0, 15))
        self.assertTrue(lint.check_citations(cites, {}, 0, 15))
        self.assertTrue(lint.check_citations({}, refs, 0, 15))
        wrong_year = lint.find_in_text_citations(["[Farley et al., 2025](https://example.org/article)"])
        self.assertTrue(lint.check_citations(wrong_year, refs, 0, 15))

    def test_link_destinations_are_not_terminology(self):
        self.assertFalse(lint.check_terminology(["[Useful method](/path/keleo/method.json)"], False))
        self.assertTrue(lint.check_terminology(["[Keleo method](/path/method.json)"], False))

    def test_both_reference_depths(self):
        for heading in ("## References", "### References"):
            lines = ["## Analysis", "Evidence (Example, 2026).", heading, "Example (2026). Source."]
            body, references = lint.parse_sections(lines)
            self.assertEqual(body, lines[:2])
            self.assertEqual(references, lines[3:])
            cites = lint.find_in_text_citations(body)
            refs = lint.find_reference_entries(references, len(body) + 1)
            self.assertFalse([f for f in lint.check_citations(cites, refs, 0, 15) if f["severity"] == "error"])

    def test_registered_type_and_contract(self):
        verifier = (ROOT / ".agents/skills/verification-foundation/verifiers/report.md").read_text()
        self.assertIn("| `team-meeting` |", verifier)
        contract = (ROOT / ".agents/skills/team-meeting/contract.feature").read_text()
        self.assertIn("Inherit and add signals", contract)
        self.assertIn("Keep all sections suitable for the team", contract)
        self.assertIn("Brief acknowledgements and reminders directly", contract)


if __name__ == "__main__":
    unittest.main()
