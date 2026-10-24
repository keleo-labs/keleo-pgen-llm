#!/usr/bin/env python3
"""Given colliding names, a rebuild preserves document kind and entry point."""
import importlib.util
import json
import subprocess
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(__file__).resolve().parents[1] / "utils" / "audit-bundle-freshness.py"
spec = importlib.util.spec_from_file_location("audit_bundle_freshness", MODULE_PATH)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def write_bundle(path, entries):
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("manifest.json", json.dumps({
            "package": {"name": "Example collection", "version": "1.0.0"},
            "documents": entries,
        }))
        for entry in entries:
            kind = entry.get("documentType", "method")
            archive.writestr(entry["path"], json.dumps({
                "kind": kind, "name": "Shared title", "version": "1.0.0",
                **({"practiceNames": []} if kind == "method" else {}),
            }))


with tempfile.TemporaryDirectory() as temp:
    root = Path(temp)
    source = root / "practices" / "example"
    source.mkdir(parents=True)
    for kind, version in [("method", "1.1.0"), ("practice", "2.0.0")]:
        (source / f"{kind}.json").write_text(json.dumps({
            "kind": kind, "name": "Shared title", "version": version,
            **({"practiceNames": []} if kind == "method" else {}),
        }))
    index = audit.build_source_index(root)
    assert len(index) == 2
    entries = [
        {"documentName": "Shared title", "documentType": kind,
         "path": f"documents/{kind}.json", "entryPoint": kind == "method"}
        for kind in ("practice", "method")
    ]
    bundle = root / "example.keleo"
    write_bundle(bundle, entries)
    findings = audit.audit_bundle(bundle, index, root)
    assert {d["kind"]: d["sourceVersion"] for d in findings["documents"]} == {
        "method": "1.1.0", "practice": "2.0.0",
    }
    outcome = audit.rebuild_bundle(bundle, index, root, "patch", True)
    assert outcome["status"] == "rebuilt", outcome
    manifest = audit.read_manifest(bundle)
    assert [(e["documentName"], e["documentType"]) for e in manifest["documents"]
            if e["entryPoint"]] == [("Shared title", "method")]
    documents, error = audit.load_all_from_keleo(bundle)
    assert not error
    assert {d["kind"]: d["version"] for d in documents} == {
        "method": "1.1.0", "practice": "2.0.0",
    }

    # Packaging must not replace the original if its result changes the entry point.
    original = bundle.read_bytes()

    def wrong_entry_point(command, **kwargs):
        output = Path(command[command.index("-o") + 1])
        write_bundle(output, [entries[0]])
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    with patch.object(audit.subprocess, "run", side_effect=wrong_entry_point):
        outcome = audit.rebuild_bundle(bundle, index, root, "patch", True)
    assert outcome["status"] == "error" and "entry-point" in outcome["message"]
    assert bundle.read_bytes() == original

    # A missing manifest kind must not choose whichever source is newer.
    del entries[1]["documentType"]
    write_bundle(bundle, entries)
    original = bundle.read_bytes()
    outcome = audit.rebuild_bundle(bundle, index, root, "patch", True)
    assert outcome["status"] == "error" and "ambiguous" in outcome["message"]
    assert bundle.read_bytes() == original

    # A bundle-only method survives even if a same-name practice exists on disk.
    entries[1]["documentType"] = "method"
    write_bundle(bundle, entries)
    del index[("Shared title", "method")]
    outcome = audit.rebuild_bundle(bundle, index, root, "patch", True)
    assert outcome["status"] == "rebuilt", outcome
    documents, _ = audit.load_all_from_keleo(bundle)
    assert {d["kind"]: d["version"] for d in documents} == {
        "method": "1.0.0", "practice": "2.0.0",
    }

    # Reclosure still follows newly added dependencies transitively.
    (source / "method.json").write_text(json.dumps({
        "kind": "method", "name": "Shared title", "version": "1.1.0",
        "practiceNames": ["Dependent"],
    }))
    (source / "dependent.json").write_text(json.dumps({
        "kind": "practice", "name": "Dependent", "version": "1.0.0",
        "baselinePracticeName": "Foundation",
    }))
    (source / "foundation.json").write_text(json.dumps({
        "kind": "practiceBaseline", "name": "Foundation", "version": "1.0.0",
    }))
    index = audit.build_source_index(root)
    write_bundle(bundle, [entries[1]])
    outcome = audit.rebuild_bundle(bundle, index, root, "patch", True, reclose=True)
    assert outcome["status"] == "rebuilt", outcome
    assert outcome["addedDependencies"] == ["Dependent", "Foundation"]
    assert [e["documentType"] for e in audit.read_manifest(bundle)["documents"]
            if e["entryPoint"]] == ["method"]

    # An ambiguous untyped dependency is refused before any archive mutation.
    (source / "dependent-method.json").write_text(json.dumps({
        "kind": "method", "name": "Dependent", "version": "3.0.0",
    }))
    write_bundle(bundle, [entries[1]])
    original = bundle.read_bytes()
    outcome = audit.rebuild_bundle(bundle, audit.build_source_index(root), root,
                                   "patch", True, reclose=True)
    assert outcome["status"] == "error" and "ambiguous" in outcome["message"]
    assert bundle.read_bytes() == original

print("PASS: document kinds, entry point, missing-kind refusal, carryover and transitive reclosure")
