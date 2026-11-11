#!/usr/bin/env python3
"""Check additive batch patches preserve existing practice arrays."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile


tool = Path(__file__).resolve().parents[1] / "utils/patch-practice-json.py"
with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    practice = root / "practice.json"
    batch = root / "batch.json"
    practice.write_text(
        json.dumps({"alphas": [{"name": "Partner", "states": [{"name": "Ready", "checklist": [{"name": "Existing"}]}]}]}),
        encoding="utf-8",
    )
    batch.write_text(
        json.dumps([{"path": "alphas[Partner].states[Ready].checklist", "append": [{"name": "Added"}]}]),
        encoding="utf-8",
    )
    subprocess.run([sys.executable, str(tool), str(practice), "--batch-file", str(batch)], check=True, capture_output=True)
    checklist = json.loads(practice.read_text(encoding="utf-8"))["alphas"][0]["states"][0]["checklist"]
    assert [item["name"] for item in checklist] == ["Existing", "Added"]

print("Batch append check passed")
