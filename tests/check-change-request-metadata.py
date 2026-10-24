#!/usr/bin/env python3
"""Verify that composition changes survive change-request generation."""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location(
    "generate_change_request", ROOT / "utils/generate-change-request.py"
)
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)


def main():
    for kind, member_field in (
        ("method", "practiceNames"),
        ("practice", "practiceDependencyNames"),
        ("practiceBaseline", "baselinePracticeNames"),
    ):
        old = {
            "kind": kind, "name": "Old name", "version": "1.0.0",
            member_field: ["Old dependency"],
            "dependencyVersions": [{"documentName": "Old dependency", "versionRange": "^1.0.0"}],
            "updatedAt": "2026-01-01", "keywords": ["obsolete"],
            "_cache": "old", "narratives": [],
        }
        new = {
            **old, "name": "New name", "version": "2.0.0",
            member_field: ["New dependency"],
            "dependencyVersions": [{"documentName": "New dependency", "versionRange": "^1.0.0"}],
            "updatedAt": "2026-10-23", "_cache": "new",
            "narratives": [{"name": "Transition", "description": "One shared plan."}],
        }
        del new["keywords"]
        change = generator.generate_change_request(
            old, new, "Test", "draft", "", ROOT / "deps/language.schema.json"
        )
        root = next(op for op in change["operations"] if op["operation"] == "modify")
        expected = {key: new.get(key) for key in (
            "name", "version", member_field, "dependencyVersions", "updatedAt", "keywords"
        )}
        assert root["modifications"] == expected, (kind, root["modifications"])
        assert sum(op["elementType"] == "Narrative" for op in change["operations"]) == 1
        unchanged = generator.generate_change_request(
            new, new, "Test", "draft", "", ROOT / "deps/language.schema.json"
        )
        assert unchanged["operations"] == []
    print("PASS: method, practice and baseline metadata, removals, named sections and no-op diffs")


if __name__ == "__main__":
    main()
