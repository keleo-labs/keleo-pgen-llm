#!/usr/bin/env python3
"""Check exact-value prose edits and all-file preflight."""

import importlib.util
import json
import tempfile
from pathlib import Path


script = Path(__file__).resolve().parents[1] / "utils/apply-prose-edits.py"
spec = importlib.util.spec_from_file_location("apply_prose_edits", script)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    first = root / "first.json"
    second = root / "second.json"
    first.write_text('{"description":"old"}\n', encoding="utf-8")
    second.write_text('{"narratives":[{"context":"other"}]}\n', encoding="utf-8")
    valid = [{"file": "first.json", "edits": [{"path": ["description"], "before": "old", "after": "new"}]}]
    assert len(module.apply_edits(valid, root, False)) == 1
    assert json.loads(first.read_text())["description"] == "old"
    stale = valid + [{"file": "second.json", "edits": [{"path": ["narratives", 0, "context"], "before": "wrong", "after": "new"}]}]
    try:
        module.apply_edits(stale, root, True)
    except ValueError:
        pass
    else:
        raise AssertionError("stale edit accepted")
    assert json.loads(first.read_text())["description"] == "old"
    module.apply_edits(valid, root, True)
    assert json.loads(first.read_text())["description"] == "new"
    nested = [{"file": "second.json", "edits": [{"path": ["narratives", 0, "context"], "before": "other", "after": "clear"}]}]
    module.apply_edits(nested, root, True)
    assert json.loads(second.read_text())["narratives"][0]["context"] == "clear"
