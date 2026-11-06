#!/usr/bin/env python3
"""Redeclare contributesTo parents and gate their states with child states.

Missing child-side mappings are supplied by reviewed JSON mapping files. Later
files override earlier entries; a file value of "*" applies to every practice
that has the named alpha and state. The utility makes no semantic choice about
which parent state a child advances.
"""

import argparse
import copy
import json
import subprocess
import sys
from pathlib import Path


VERSION = "1.0.0"


def load(path):
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def primary_documents(root):
    for path in sorted((root / "practices").glob("*/*.json")):
        if path.name.startswith("_") or path.name.endswith(".changerequest.json"):
            continue
        try:
            document = load(path)
        except (OSError, json.JSONDecodeError):
            continue
        if document.get("kind") == "practice":
            yield path, document


def baseline_documents(root):
    for path in sorted((root / "baselines").glob("*/*.json")):
        if path.name.startswith("_") or path.name.endswith(".changerequest.json"):
            continue
        try:
            document = load(path)
        except (OSError, json.JSONDecodeError):
            continue
        if document.get("kind") == "practiceBaseline" and document.get("name"):
            yield document["name"], document


def mappings_by_key(entries):
    result = {}
    for entry in entries:
        key = (entry["file"], entry["alpha"], entry["state"])
        result[key] = entry["parentState"]
    return result


def parent_alpha(name, document, baseline, documents, baselines):
    for alpha in document.get("alphas", []):
        if alpha.get("name") == name:
            return alpha
    for alpha in baseline.get("alphas", []):
        if alpha.get("name") == name:
            return alpha
    for other_baseline in baselines.values():
        for alpha in other_baseline.get("alphas", []):
            if alpha.get("name") == name:
                return alpha
    dependencies = set(document.get("practiceDependencyNames", []))
    matches = [(path, alpha) for path, other in documents
               if other.get("name") in dependencies
               for alpha in other.get("alphas", []) if alpha.get("name") == name]
    if matches:
        matches.sort(key=lambda item: (item[0].parent.name != item[0].stem, str(item[0])))
        return matches[0][1]
    return None


def redeclaration(alpha):
    result = {key: copy.deepcopy(alpha[key]) for key in
              ("kind", "name", "description", "focusName") if key in alpha}
    result["states"] = []
    for state in alpha.get("states", []):
        copy_state = {key: copy.deepcopy(value) for key, value in state.items()
                      if key != "checklist"}
        copy_state["checklist"] = []
        result["states"].append(copy_state)
    return result


def merge_inherited_backgrounds(local_parent, inherited_parent):
    """Restore original prerequisites while keeping authored additions."""
    changed = 0
    inherited_states = {state["name"]: state for state in inherited_parent.get("states", [])}
    for state in local_parent.get("states", []):
        original = inherited_states.get(state["name"])
        if original is None:
            continue
        for field, values in original.get("background", {}).items():
            target = state.setdefault("background", {}).setdefault(field, [])
            for value in values:
                if value not in target:
                    target.append(copy.deepcopy(value))
                    changed += 1
    return changed


def update(path, document, baseline, documents, baselines, mappings, removals, root):
    issues = []
    changed = 0
    relative = str(path.relative_to(root))
    for removal in removals:
        if removal["file"] != relative:
            continue
        child = next((alpha for alpha in document.get("alphas", [])
                      if alpha.get("name") == removal["alpha"]), None)
        state = next((item for item in child.get("states", [])
                      if item.get("name") == removal["state"]), None) if child else None
        if state is None:
            issues.append(f"{relative}: removal target not found: {removal['alpha']} / {removal['state']}")
            continue
        reference = {"alphaName": removal["alphaName"], "stateName": removal["stateName"]}
        references = state.get("background", {}).get("alphaStates", [])
        if reference in references:
            references.remove(reference)
            changed += 1
    for child in list(document.get("alphas", [])):
        target = child.get("contributesTo")
        if not target:
            continue
        parent = parent_alpha(target, document, baseline, documents, baselines)
        if parent is None:
            issues.append(f"{relative}: unresolved parent {target} for {child['name']}")
            continue
        parent_states = {state["name"] for state in parent.get("states", [])}
        desired = []
        for state in child.get("states", []):
            target_state = mappings.get(("*", child["name"], state["name"])) \
                or mappings.get((relative, child["name"], state["name"])) \
                or state.get("contributesToState")
            if target_state not in parent_states:
                issues.append(f"{relative}: unmapped {child['name']} / {state['name']} -> {target}")
                continue
            desired.append((state, target_state))
        if len(desired) != len(child.get("states", [])):
            continue
        local_parent = next((alpha for alpha in document["alphas"]
                             if alpha.get("name") == target), None)
        if local_parent is None:
            local_parent = redeclaration(parent)
            document["alphas"].append(local_parent)
            changed += 1
        else:
            inherited = parent_alpha(target, {
                "alphas": [],
                "practiceDependencyNames": document.get("practiceDependencyNames", []),
            }, baseline, documents, baselines)
            if inherited is not None and inherited is not local_parent:
                changed += merge_inherited_backgrounds(local_parent, inherited)
        local_states = {state["name"]: state for state in local_parent["states"]}
        for state, target_state in desired:
            if state.get("contributesToState") != target_state:
                state["contributesToState"] = target_state
                changed += 1
                reference = {"alphaName": child["name"], "stateName": state["name"]}
                for other_state in local_parent["states"]:
                    if other_state["name"] == target_state:
                        continue
                    old_refs = other_state.get("background", {}).get("alphaStates", [])
                    if reference in old_refs:
                        old_refs.remove(reference)
                        changed += 1
            target_entry = local_states.get(target_state)
            if target_entry is None:
                issues.append(f"{relative}: redeclared parent lacks {target} / {target_state}")
                continue
            prerequisites = target_entry.setdefault("background", {}).setdefault("alphaStates", [])
            reference = {"alphaName": child["name"], "stateName": state["name"]}
            if reference not in prerequisites:
                prerequisites.append(reference)
                changed += 1
    return changed, issues


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", action="version", version=VERSION)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--baseline-name", action="append", default=[],
                        help="Restrict updates to practices using this baseline; repeatable")
    parser.add_argument("--mapping", type=Path, action="append", default=[],
                        help="Reviewed JSON array of file/alpha/state/parentState entries; repeatable")
    parser.add_argument("--remove-prerequisites", type=Path,
                        help="Reviewed JSON array of child Background references to remove")
    parser.add_argument("--fix", action="store_true", help="Write fully resolved documents")
    args = parser.parse_args()
    root = args.root.resolve()
    mappings = mappings_by_key([entry for path in args.mapping for entry in load(path)])
    removals = load(args.remove_prerequisites) if args.remove_prerequisites else []
    documents = list(primary_documents(root))
    baselines = dict(baseline_documents(root))
    total_changed = total_issues = 0
    pending = []
    for path, original in documents:
        baseline_name = original.get("baselinePracticeName")
        if baseline_name not in baselines or (args.baseline_name and
                                            baseline_name not in args.baseline_name):
            continue
        document = copy.deepcopy(original)
        changed, issues = update(path, document,
                                 baselines[baseline_name],
                                 documents, baselines, mappings, removals, root)
        total_changed += changed
        total_issues += len(issues)
        for issue in issues:
            print("ISSUE", issue)
        if changed:
            print(f"{'WRITE' if args.fix and not issues else 'PLAN'} {path.relative_to(root)}: {changed} changes")
        if changed and not issues:
            pending.append((path, document))
    if args.fix and not total_issues and pending:
        backup = root / "utils" / "backup-practice.py"
        directories = sorted({path.parent for path, _ in pending})
        subprocess.run([sys.executable, str(backup), *(str(path) for path in directories)],
                       check=True)
        for path, document in pending:
            with path.open("w", encoding="utf-8") as stream:
                json.dump(document, stream, ensure_ascii=False, indent=2)
                stream.write("\n")
    print(f"Total changes: {total_changed}; issues: {total_issues}")
    if total_issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
