#!/usr/bin/env python3
"""Check the README writer's content selection and preservation rules."""

import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "utils/write-workspace-readmes.py"
SPEC = importlib.util.spec_from_file_location("workspace_readmes", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class WorkspaceReadmeTest(unittest.TestCase):
    def test_model_workspace_links_actual_files_in_phase_order(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary) / "baselines/example"
            folder.mkdir(parents=True)
            (folder / "example.json").write_text(json.dumps({"kind": "practiceBaseline", "name": "Example", "description": "An example baseline.", "version": "1.2.0", "schemaVersion": "3.0.0"}))
            for name in ("00-prompt-history.md", "01-analysis-report.md", "01.5-distilled-essentials.md",
                         "02-mapping-guide.md", "example.changerequest.json"):
                (folder / name).write_text("")
            result = MODULE.readme_for(folder)
            self.assertIn("[example.json](example.json) is the baseline model (version 1.2.0; schema 3.0.0)", result)
            self.assertLess(result.index("01-analysis-report.md"), result.index("01.5-distilled-essentials.md"))
            self.assertLess(result.index("02-mapping-guide.md"), result.index("00-prompt-history.md"))
            self.assertIn("[example.changerequest.json](example.changerequest.json) — Change request", result)

    def test_report_workspace_uses_report_as_main_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary) / "reports/example"
            folder.mkdir(parents=True)
            (folder / "example.md").write_text("## Example\n")
            (folder / "example.pdf").write_bytes(b"pdf")
            result = MODULE.readme_for(folder)
            self.assertIn("[example.md](example.md) is the report", result)
            self.assertIn("[example.pdf](example.pdf) — Export", result)

    def test_baseline_and_practice_dependencies_link_to_folders(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            baseline = root / "baselines/base"
            dependency = root / "practices/shared"
            folder = root / "practices/example"
            for path in (baseline, dependency, folder):
                path.mkdir(parents=True)
            (folder / "example.json").write_text(json.dumps({
                "kind": "practice", "name": "Example", "baselinePracticeName": "Base",
                "practiceDependencyNames": ["Shared"],
            }))
            result = MODULE.readme_for(folder, {"Base": baseline, "Shared": dependency})
            self.assertIn("### Dependencies", result)
            self.assertIn("[Base](../../baselines/base/) — version not recorded; schema not recorded", result)
            self.assertIn("[Shared](../shared/) — version not recorded; schema not recorded", result)

    def test_cross_repository_dependency_uses_remote_folder_url(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source/practices/example"
            target = root / "target/baselines/base"
            source.mkdir(parents=True)
            target.mkdir(parents=True)
            for repo in (root / "source", root / "target"):
                subprocess.run(["git", "init", "-q", str(repo)], check=True)
            subprocess.run(["git", "-C", str(root / "target"), "remote", "add", "origin",
                            "git@gitlab.example.invalid:team/content.git"], check=True)
            self.assertEqual(MODULE.dependency_url(source, target),
                             "https://gitlab.example.invalid/team/content/-/tree/main/baselines/base")
            subprocess.run(["git", "-C", str(root / "target"), "remote", "remove", "origin"], check=True)
            (source / "example.json").write_text(json.dumps({
                "kind": "practice", "name": "Example", "baselinePracticeName": "Base",
            }))
            self.assertIn("local checkout only; target has no remote",
                          MODULE.readme_for(source, {"Base": target}))

    def test_multiple_practices_are_listed_before_dependencies(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            folder = root / "practices/example"
            baseline = root / "baselines/base"
            folder.mkdir(parents=True)
            baseline.mkdir(parents=True)
            (folder / "example.json").write_text(json.dumps({
                "kind": "practice", "name": "Example", "baselinePracticeName": "Base",
            }))
            for name in ("First", "Second"):
                (folder / f"{name.lower()}.json").write_text(json.dumps({"kind": "practice", "name": name}))
            result = MODULE.readme_for(folder, {"Base": baseline})
            self.assertLess(result.index("### Practices"), result.index("### Dependencies"))
            self.assertIn("[First](first.json)", result)
            self.assertIn("[Second](second.json)", result)
            self.assertNotIn("[first.json](first.json) — Related model", result)

    def test_method_lists_external_practices_and_inherited_baselines(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            method = root / "practices/method"
            practice = root / "practices/external"
            child = root / "baselines/child"
            parent = root / "baselines/parent"
            for folder in (method, practice, child, parent):
                folder.mkdir(parents=True)
            (method / "method.json").write_text(json.dumps({
                "kind": "method", "name": "Method", "practiceNames": ["External"],
                "baselinePracticeName": "Child", "version": "2.0.0", "schemaVersion": "4.0.0",
            }))
            (practice / "external.json").write_text(json.dumps({
                "kind": "practice", "name": "External", "baselinePracticeName": "Child",
                "version": "1.1.0", "schemaVersion": "4.0.0",
            }))
            (child / "child.json").write_text(json.dumps({
                "kind": "practiceBaseline", "name": "Child", "baselinePracticeNames": ["Parent"],
                "version": "3.0.0", "schemaVersion": "4.0.0",
            }))
            (parent / "parent.json").write_text(json.dumps({"kind": "practiceBaseline", "name": "Parent"}))
            result = MODULE.readme_for(method, {"External": practice, "Child": child, "Parent": parent})
            self.assertIn("[method.json](method.json) is the method model (version 2.0.0; schema 4.0.0)", result)
            self.assertIn("[External](../external/) — version 1.1.0; schema 4.0.0", result)
            self.assertIn("[Child](../../baselines/child/) — version 3.0.0; schema 4.0.0", result)
            self.assertIn("[Parent](../../baselines/parent/)", result)
            self.assertLess(result.index("### Practices"), result.index("### Baselines"))


if __name__ == "__main__":
    unittest.main()
