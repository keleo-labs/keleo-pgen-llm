#!/usr/bin/env python3
"""Checks for private content repository mounts and lossless imports."""

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


PROJECT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("content_repos", PROJECT / "utils/content-repos.py")
content_repos = importlib.util.module_from_spec(spec)
spec.loader.exec_module(content_repos)
sys.path.insert(0, str(PROJECT / "utils"))
import importlib  # noqa: E402
discover = importlib.import_module("discover-dependencies")  # noqa: E402
team_meeting = importlib.import_module("team-meeting")  # noqa: E402


class ContentRepoTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.project = self.base / "project"
        self.project.mkdir()
        for kind in content_repos.KINDS:
            (self.project / kind).mkdir()
        (self.project / "config").mkdir()
        self.config = self.project / "config/content-repos.json"
        self.patches = [patch.object(content_repos, "ROOT", self.project),
                        patch.object(content_repos, "CONFIG", self.config)]
        for item in self.patches:
            item.start()
            self.addCleanup(item.stop)

    def repo(self, name, items=None):
        path = self.base / name
        path.mkdir()
        subprocess.run(["git", "init", "-q", str(path)], check=True)
        return {"name": name, "path": f"../{name}",
                "items": items or {kind: [] for kind in content_repos.KINDS}}

    def configure(self, *repos):
        self.config.write_text(json.dumps({"version": "1.0.0", "repositories": repos}))
        return content_repos.load_config()

    def test_selected_items_mount_and_reach_their_own_git_repo(self):
        first = self.repo("first", {"practices": ["alpha"], "baselines": [], "reports": []})
        second = self.repo("second", {"practices": [], "baselines": ["base"], "reports": ["brief"]})
        for repo, kind, slug in ((first, "practices", "alpha"), (second, "baselines", "base"),
                                 (second, "reports", "brief")):
            (self.base / repo["name"] / kind / slug).mkdir(parents=True)
        (self.base / "first/practices/other").mkdir()
        data = self.configure(first, second)
        with self.assertRaisesRegex(ValueError, "Not mounted"):
            content_repos.mount(data, False, True)
        content_repos.mount(data, True)
        content_repos.mount(data, False, True)
        self.assertFalse((self.project / "practices/other").exists())
        (self.project / "practices/alpha/alpha.json").write_text("{}")
        (self.project / "reports/brief/brief.md").write_text("## Brief\n\nA short report.\n")
        lint = subprocess.run([sys.executable, str(PROJECT / "utils/lint-report.py"),
                               str(self.project / "reports/brief/brief.md"),
                               "--checks", "structure", "--json"], capture_output=True, text=True)
        self.assertEqual(lint.returncode, 0, lint.stderr or lint.stdout)
        (self.project / "reports/brief/series.json").write_text(
            json.dumps({"calendars": [{"title": "Brief"}]}))
        with patch.object(team_meeting, "validate"):
            registry = team_meeting.sync_registry(self.project)
        self.assertEqual(registry["meetings"][0]["seriesPath"], "reports/brief/series.json")
        status = subprocess.run(["git", "-C", str(self.base / "first"), "status", "--short"],
                                capture_output=True, text=True, check=True).stdout
        self.assertIn("practices/", status)

    def test_import_preserves_original_and_discovery_finds_copy(self):
        repo = self.repo("first")
        data = self.configure(repo)
        local = self.project / "practices/alpha"
        local.mkdir()
        payload = {"kind": "practice", "name": "Alpha", "version": "1.0.0"}
        (local / "alpha.json").write_text(json.dumps(payload))
        content_repos.add(data, "first", "practices", "alpha", True)
        self.assertTrue(local.is_symlink())
        backups = list((self.project / "content-import-backups/practices").iterdir())
        self.assertEqual(len(backups), 1)
        self.assertTrue(content_repos.same_tree(backups[0], local.resolve()))
        index, skipped = discover.build_index([str(self.project / "practices")])
        self.assertEqual(skipped, [])
        self.assertEqual(index["Alpha"][0]["path"], str(local / "alpha.json"))
        self.assertEqual(content_repos.load_config()["repositories"][0]["items"]["practices"], ["alpha"])
        content_repos.unmount(content_repos.load_config(), "practices", "alpha", True)
        self.assertFalse(local.exists())
        self.assertTrue((self.base / "first/practices/alpha/alpha.json").exists())

    def test_method_tiers_resolve_members_from_other_mounted_items(self):
        repo = self.repo("first", {"practices": ["method", "member"],
                                   "baselines": [], "reports": []})
        method_dir = self.base / "first/practices/method"
        member_dir = self.base / "first/practices/member"
        method_dir.mkdir(parents=True)
        member_dir.mkdir(parents=True)
        method_file = method_dir / "method.json"
        method_file.write_text(json.dumps({"kind": "method", "name": "Method",
                                           "practiceNames": ["Member"]}))
        (member_dir / "member.json").write_text(json.dumps({"kind": "practice", "name": "Member"}))
        content_repos.mount(self.configure(repo), True)
        result = discover.cmd_tiers(self.project / "practices/method/method.json",
                                    [self.project / "practices"])
        self.assertEqual(result["tier1"], ["Member"])
        self.assertIsNone(result["notFound"])

    def test_invalid_config_and_occupied_path_do_not_overwrite(self):
        first = self.repo("first", {"practices": ["alpha"], "baselines": [], "reports": []})
        second = self.repo("second", {"practices": ["alpha"], "baselines": [], "reports": []})
        with self.assertRaisesRegex(ValueError, "Duplicate owner"):
            self.configure(first, second)
        first["items"]["practices"] = ["../escape"]
        with self.assertRaisesRegex(ValueError, "Invalid practices item"):
            self.configure(first)
        first["items"]["practices"] = ["alpha"]
        (self.base / "first/practices/alpha").mkdir(parents=True)
        local = self.project / "practices/alpha"
        local.mkdir()
        (local / "keep.txt").write_text("untouched")
        data = self.configure(first)
        with self.assertRaisesRegex(ValueError, "Path occupied"):
            content_repos.mount(data, True)
        self.assertEqual((local / "keep.txt").read_text(), "untouched")
        first["path"] = "../missing"
        with self.assertRaisesRegex(ValueError, "Missing repository"):
            self.configure(first)

    def test_content_directory_cannot_escape_repository(self):
        repo = self.repo("first", {"practices": ["alpha"], "baselines": [], "reports": []})
        (self.base / "first/practices").mkdir()
        (self.base / "first/practices/alpha").symlink_to(self.project / "reports")
        data = self.configure(repo)
        with self.assertRaisesRegex(ValueError, "escapes repository"):
            content_repos.mount(data, True)
        self.assertFalse((self.project / "practices/alpha").exists())


if __name__ == "__main__":
    unittest.main()
