#!/usr/bin/env python3
"""Check batch removals leave a valid target and reject ambiguous edits atomically."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATCHER = ROOT / "utils" / "patch-practice-json.py"


def run(target, spec, *options):
    return subprocess.run(
        [sys.executable, str(PATCHER), str(target), "--batch-file", str(spec), *options],
        capture_output=True, text=True, cwd=ROOT,
    )


with tempfile.TemporaryDirectory() as tmp:
    directory = Path(tmp)
    target = directory / "practice.json"
    spec = directory / "batch.json"
    original = {
        "alphas": [
            {"name": "One", "seq": 1, "legacy": "remove me"},
            {"name": "Two", "seq": 2},
            {"name": "Three", "seq": 3},
        ]
    }
    target.write_text(json.dumps(original))
    spec.write_text(json.dumps([
        {"path": "alphas", "removeNamed": "Two"},
        {"path": "alphas[One].legacy", "removeField": True},
    ]))

    preview = run(target, spec, "--dry-run")
    assert preview.returncode == 0, preview.stderr
    assert json.loads(target.read_text()) == original

    result = run(target, spec)
    assert result.returncode == 0, result.stderr
    changed = json.loads(target.read_text())
    assert [item["name"] for item in changed["alphas"]] == ["One", "Three"]
    assert [item["seq"] for item in changed["alphas"]] == [1, 2]
    assert "legacy" not in changed["alphas"][0]

    before_invalid = target.read_bytes()
    spec.write_text(json.dumps([
        {"path": "alphas[One]", "merge": {"description": "must not be written"}},
        {"path": "alphas", "removeNamed": "Missing"},
    ]))
    invalid = run(target, spec)
    assert invalid.returncode != 0 and "not written" in invalid.stderr
    assert target.read_bytes() == before_invalid

    changed["alphas"].append({"name": "Three", "seq": 3})
    target.write_text(json.dumps(changed))
    before_ambiguous = target.read_bytes()
    spec.write_text(json.dumps([{"path": "alphas", "removeNamed": "Three"}]))
    ambiguous = run(target, spec)
    assert ambiguous.returncode != 0 and "found 2" in ambiguous.stderr
    assert target.read_bytes() == before_ambiguous

print("Batch patch removals: 4 scenarios passed")
