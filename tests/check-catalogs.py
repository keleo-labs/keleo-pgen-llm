#!/usr/bin/env python3
"""Regression checks for local source and practice catalogs."""

import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from zipfile import ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "utils"))
import catalog  # noqa: E402


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.workspace = self.root / "sources"

    def source(self, text="# Guide\n\n## Discovery\nFind the need."):
        path = self.root / "guide.md"
        path.write_text(text)
        return path

    def practice(self, name):
        directory = self.root / name
        directory.mkdir()
        path = directory / "practice.json"
        path.write_text(json.dumps({"kind": "practice", "name": name, "version": "1.0.0",
                                    "citations": [{"name": "Guide"}],
                                    "alphas": [{"name": "Discovery", "description": "Find the need."}]}))
        return path

    def test_two_practices_share_source_section(self):
        source = catalog.add_source(str(self.source()), self.workspace)
        section = json.loads(source.read_text())["sections"][1]["id"]
        (self.root / "practices").mkdir()
        for name in ("first", "second"):
            practice = self.practice(f"practices/{name}")
            links = practice.parent / "links.json"
            links.write_text(json.dumps({"/alphas/0": [section]}))
            output = catalog.build_practice(practice, self.workspace, links)
            self.assertEqual(json.loads(output.read_text())["elements"][1]["sourceSections"], [section])
            self.assertEqual(json.loads(practice.read_text())["citations"], [{"name": "Guide"}])
        with patch.object(catalog, "ROOT", self.root):
            self.assertEqual(len(catalog.search_practices("Discovery")), 2)

    def test_changed_and_unavailable_source_retains_snapshot(self):
        path = self.source()
        first = catalog.add_source(str(path), self.workspace)
        path.write_text("# Guide\n\n## Changed\nNew text.")
        self.assertEqual(list(catalog.source_catalogs(self.workspace, latest_only=True))[0][1]["status"], "stale")
        second = catalog.add_source(str(path), self.workspace)
        self.assertNotEqual(first, second)
        self.assertTrue(first.exists())
        with patch.object(catalog, "source_text", side_effect=OSError("unavailable")):
            self.assertEqual(catalog.add_source(str(path), self.workspace), second)
        latest = json.loads((second.parent / "latest.json").read_text())
        self.assertEqual(latest["status"], "stale")

    def test_changed_practice_and_missing_section_fail(self):
        self.source()
        catalog.add_source(str(self.root / "guide.md"), self.workspace)
        practice = self.practice("first")
        links = practice.parent / "links.json"
        links.write_text(json.dumps({"/alphas/0": ["missing"]}))
        with self.assertRaisesRegex(ValueError, "Missing source sections"):
            catalog.build_practice(practice, self.workspace, links)
        output = catalog.build_practice(practice, self.workspace)
        practice.write_text(practice.read_text() + "\n")
        self.assertNotEqual(json.loads(output.read_text())["practice"]["sha256"],
                            catalog.digest(practice.read_bytes()))

    def test_language_validator_checks_schema_links_and_freshness(self):
        source = catalog.add_source(str(self.source()), self.workspace)
        section = json.loads(source.read_text())["sections"][1]["id"]
        practice = self.practice("first")
        links = practice.parent / "links.json"
        links.write_text(json.dumps({"/alphas/0": [section]}))
        output = catalog.build_practice(practice, self.workspace, links)
        validator = catalog.ROOT.parent / "keleo-language/validate/validate-catalog.py"
        command = [sys.executable, str(validator), str(output), "--practice", str(practice),
                   "--source-workspace", str(self.workspace), "--require-fresh"]
        self.assertEqual(subprocess.run(command, capture_output=True).returncode, 0)
        practice.write_text(practice.read_text() + "\n")
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertIn("Practice changed", result.stderr)
        catalog.add_source(str(self.root / "guide.md"), self.workspace)
        with patch.object(catalog, "source_text", side_effect=OSError("unavailable")):
            catalog.add_source(str(self.root / "guide.md"), self.workspace)
        practice.write_text(practice.read_text().rstrip())
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertIn("Stale source section", result.stderr)

    def test_catalog_cannot_be_packaged(self):
        source = catalog.add_source(str(self.source()), self.workspace)
        command = [sys.executable, str(catalog.ROOT / "utils/package-keleo.py"),
                   "--documents", str(source), "--name", "test", "--version", "1.0.0",
                   "-o", str(self.root / "test.keleo")]
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("cannot be packaged", result.stderr)
        self.assertFalse((self.root / "test.keleo").exists())

    def test_powerpoint_uses_slide_notes_relationship(self):
        path = self.root / "slides.pptx"
        with ZipFile(path, "w") as archive:
            archive.writestr("ppt/slides/slide1.xml", "<p xmlns:a='http://schemas.openxmlformats.org/drawingml/2006/main'><a:p><a:r><a:t>Slide text</a:t></a:r></a:p></p>")
            archive.writestr("ppt/slides/_rels/slide1.xml.rels", "<Relationships><Relationship Type='http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesSlide' Target='../notesSlides/notesSlide9.xml'/></Relationships>")
            archive.writestr("ppt/notesSlides/notesSlide9.xml", "<p xmlns:a='http://schemas.openxmlformats.org/drawingml/2006/main'><a:p><a:r><a:t>Speaker note</a:t></a:r></a:p></p>")
        self.assertIn("Speaker note", catalog.source_text(str(path)))


if __name__ == "__main__":
    unittest.main()
