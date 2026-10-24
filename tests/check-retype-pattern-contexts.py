#!/usr/bin/env python3
"""Given typed pattern views, retyping changes every label and preserves prose."""
import importlib.util
from copy import deepcopy
from pathlib import Path


path = Path(__file__).resolve().parents[1] / "utils" / "retype-narratives.py"
spec = importlib.util.spec_from_file_location("retype_narratives", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

data = {
    "practices": [{
        "patterns": [{
            "name": "Journey", "narrativeTypeName": "Old",
            "patternViews": [
                {"narrativeContexts": [{"seq": 1, "narrativeElementName": "Start", "context": "First"}]},
                {"narrativeContexts": [{"seq": 1, "narrativeElementName": "Finish", "context": "Second"}]},
            ],
        }],
        "patternOrchestrations": [{
            "name": "Programme", "narrativeTypeName": "Old",
            "stages": [{"narrativeContexts": [
                {"seq": 1, "narrativeElementName": "Finish", "context": "Third"}
            ]}],
        }],
    }],
}
operation = [{"fromType": "Old", "toType": "New", "elementMap": {"Start": "Opening", "Finish": "Outcome"}}]
changed = deepcopy(data)
changes, errors = module.retype(changed, operation, {"New": ["Opening", "Outcome"]})
assert not errors and len(changes) == 2
pattern = changed["practices"][0]["patterns"][0]
assert pattern["narrativeTypeName"] == "New"
assert [(c["narrativeElementName"], c["context"]) for c in module.narrative_contexts(pattern)] == [("Opening", "First"), ("Outcome", "Second")]
orchestration = changed["practices"][0]["patternOrchestrations"][0]
assert module.narrative_contexts(orchestration)[0] == {"seq": 1, "narrativeElementName": "Outcome", "context": "Third"}
assert "narrativeContexts" not in pattern

# Given an invalid target label, reject the operation before changing that host.
invalid = deepcopy(operation)
invalid[0]["elementMap"]["Finish"] = "Undefined"
untouched = deepcopy(data)
_, errors = module.retype(untouched, invalid, {"New": ["Opening", "Outcome"]})
assert errors and untouched == data

# Local seq values cannot safely determine a cross-view positional mapping.
untouched = deepcopy(data)
_, errors = module.retype(untouched, [{"fromType": "Old", "toType": "New"}], {"New": ["Opening", "Outcome"]})
assert errors and untouched == data
print("PASS: embedded pattern/stage labels, prose preservation and invalid/ambiguous mapping rejection")

# Attached orchestration narratives follow the same route as other narrative hosts.
attached = {"patternOrchestrations": [{"name": "Programme", "narratives": [{
    "name": "Overview", "narrativeTypeName": "Old", "narrativeContexts": [
        {"seq": 1, "narrativeElementName": "Start", "context": "Keep this prose"}
    ]
}]}]}
changes, errors = module.retype(attached, operation, {"New": ["Opening", "Outcome"]})
assert not errors and len(changes) == 1
assert attached["patternOrchestrations"][0]["narratives"][0]["narrativeContexts"][0] == {
    "seq": 1, "narrativeElementName": "Opening", "context": "Keep this prose"}

# The canonical gate rejects legacy Essay, and explicit retyping clears it safely.
reconcile_path = path.parent / "reconcile-cross-references.py"
reconcile_spec = importlib.util.spec_from_file_location("reconcile_cross_references", reconcile_path)
reconcile = importlib.util.module_from_spec(reconcile_spec)
reconcile_spec.loader.exec_module(reconcile)
entries = reconcile.load_map(path.parents[1] / "references" / "narrative-type-canonical-names.json")
essay = {"narratives": [{"narrativeTypeName": "Essay", "narrativeContexts": [
    {"seq": 1, "narrativeElementName": "Body", "context": "Evidence already written"}
]}]}
preview = deepcopy(essay)
counts = reconcile.apply_map_to_properties(preview, entries, ["narrativeTypeName"])
assert counts["Essay"] == 1
changes, errors = module.retype(essay, [{"fromType": "Essay", "toType": "Essay Narrative",
    "elementMap": {"Body": "Presenting Evidence"}}],
    {"Essay Narrative": ["Introduction", "Defining Key Concepts", "Presenting Evidence", "Conclusion"]})
assert not errors
assert essay["narratives"][0]["narrativeContexts"] == [
    {"seq": 1, "narrativeElementName": "Presenting Evidence", "context": "Evidence already written"}]
assert not any(reconcile.apply_map_to_properties(essay, entries, ["narrativeTypeName"]).values())
for name in ("Hero's Journey", "Three-Act Structure"):
    unchanged = {"narrativeTypeName": name}
    assert not any(reconcile.apply_map_to_properties(unchanged, entries, ["narrativeTypeName"]).values())
    assert unchanged["narrativeTypeName"] == name
print("PASS: attached orchestration narratives and canonical essay migration")
