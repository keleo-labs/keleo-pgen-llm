#!/usr/bin/env python3
"""
Apply ChangeRequest nameChanges to downstream practice/baseline/method JSON files.

Usage:
    # Dry-run: see what would change
    python3 utils/apply-change-request.py cr.json target1.json target2.json

    # Apply in-place
    python3 utils/apply-change-request.py cr.json target1.json target2.json --fix

    # Only apply ActivitySpace renames
    python3 utils/apply-change-request.py cr.json target.json --element-types ActivitySpace

    # Write patched files to a directory instead of in-place
    python3 utils/apply-change-request.py cr.json target.json --fix -o patched/
"""
import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _shared import load_json, detect_kind


def _check_field(obj, field, rename_map, changes, path):
    val = obj.get(field)
    if val is not None and val in rename_map:
        old = val
        obj[field] = rename_map[old]
        changes.append({"path": path, "field": field, "old": old, "new": rename_map[old]})


def _check_string_array(arr, rename_map, changes, path):
    for i, val in enumerate(arr):
        if val in rename_map:
            old = val
            arr[i] = rename_map[old]
            changes.append({
                "path": f"{path}[{i}]", "field": "(string item)",
                "old": old, "new": rename_map[old],
            })


def _rename_activity_space(data, rename_map, prefix, changes):
    for i, item in enumerate(data.get("activitySpaces", [])):
        p = f"{prefix}activitySpaces[{item.get('name', i)}]"
        _check_field(item, "name", rename_map, changes, p)
        for j, act in enumerate(item.get("activities", [])):
            _check_field(act, "activitySpaceName", rename_map, changes,
                         f"{p}.activities[{act.get('name', j)}]")
    for i, act in enumerate(data.get("activities", [])):
        _check_field(act, "activitySpaceName", rename_map, changes,
                     f"{prefix}activities[{act.get('name', i)}]")


def _rename_alpha(data, rename_map, prefix, changes):
    for i, alpha in enumerate(data.get("alphas", [])):
        p = f"{prefix}alphas[{alpha.get('name', i)}]"
        _check_field(alpha, "name", rename_map, changes, p)
        _check_field(alpha, "contributesTo", rename_map, changes, p)
        for j, rel in enumerate(alpha.get("relatesTo", [])):
            _check_field(rel, "alphaName", rename_map, changes, f"{p}.relatesTo[{j}]")

    for coll in ("activitySpaces", "activities"):
        for i, item in enumerate(data.get(coll, [])):
            ip = f"{prefix}{coll}[{item.get('name', i)}]"
            for j, contrib in enumerate(item.get("contributesTo", [])):
                if isinstance(contrib, dict):
                    _check_field(contrib, "alphaName", rename_map, changes,
                                 f"{ip}.contributesTo[{j}]")

    for i, wp in enumerate(data.get("workProducts", [])):
        wp_p = f"{prefix}workProducts[{wp.get('name', i)}]"
        for j, lod in enumerate(wp.get("levelsOfDetail", [])):
            for k, contrib in enumerate(lod.get("contributesTo", [])):
                if isinstance(contrib, dict):
                    _check_field(contrib, "alphaName", rename_map, changes,
                                 f"{wp_p}.levelsOfDetail[{j}].contributesTo[{k}]")

    for i, pat in enumerate(data.get("patterns", [])):
        pat_p = f"{prefix}patterns[{pat.get('name', i)}]"
        for j, view in enumerate(pat.get("patternViews", [])):
            for k, astate in enumerate(view.get("alphaStates", [])):
                if isinstance(astate, dict):
                    _check_field(astate, "alphaName", rename_map, changes,
                                 f"{pat_p}.patternViews[{j}].alphaStates[{k}]")


def _rename_competency(data, rename_map, prefix, changes):
    for i, comp in enumerate(data.get("competencies", [])):
        _check_field(comp, "name", rename_map, changes,
                     f"{prefix}competencies[{comp.get('name', i)}]")

    for coll in ("activitySpaces", "activities"):
        for i, item in enumerate(data.get(coll, [])):
            ip = f"{prefix}{coll}[{item.get('name', i)}]"
            rc = item.get("requiredCompetencies")
            if isinstance(rc, list):
                _check_string_array(rc, rename_map, changes,
                                    f"{ip}.requiredCompetencies")
            for j, clr in enumerate(item.get("recommendedCompetencyLevels", [])):
                _check_field(clr, "competencyName", rename_map, changes,
                             f"{ip}.recommendedCompetencyLevels[{j}]")

    for i, persona in enumerate(data.get("personas", [])):
        pp = f"{prefix}personas[{persona.get('name', i)}]"
        for j, comp_ref in enumerate(persona.get("competencies", [])):
            _check_field(comp_ref, "competencyName", rename_map, changes, f"{pp}.competencies[{j}]")


def _rename_narrative_type(data, rename_map, prefix, changes):
    for i, nt in enumerate(data.get("narrativeTypes", [])):
        _check_field(nt, "name", rename_map, changes,
                     f"{prefix}narrativeTypes[{nt.get('name', i)}]")

    for i, narr in enumerate(data.get("narratives", [])):
        _check_field(narr, "narrativeTypeName", rename_map, changes,
                     f"{prefix}narratives[{narr.get('name', i)}]")

    for coll in ("alphas", "activitySpaces", "competencies", "activities", "workProducts"):
        for i, item in enumerate(data.get(coll, [])):
            ip = f"{prefix}{coll}[{item.get('name', i)}]"
            for j, narr in enumerate(item.get("narratives", [])):
                _check_field(narr, "narrativeTypeName", rename_map, changes,
                             f"{ip}.narratives[{narr.get('name', j)}]")


def _rename_state(data, rename_map, prefix, changes):
    for i, alpha in enumerate(data.get("alphas", [])):
        ap = f"{prefix}alphas[{alpha.get('name', i)}]"
        for j, state in enumerate(alpha.get("states", [])):
            sp = f"{ap}.states[{state.get('name', j)}]"
            _check_field(state, "name", rename_map, changes, sp)
            _check_field(state, "contributesToState", rename_map, changes, sp)

    for coll in ("activitySpaces", "activities"):
        for i, item in enumerate(data.get(coll, [])):
            ip = f"{prefix}{coll}[{item.get('name', i)}]"
            for j, contrib in enumerate(item.get("contributesTo", [])):
                if isinstance(contrib, dict):
                    _check_field(contrib, "stateName", rename_map, changes,
                                 f"{ip}.contributesTo[{j}]")

    for i, wp in enumerate(data.get("workProducts", [])):
        wp_p = f"{prefix}workProducts[{wp.get('name', i)}]"
        for j, lod in enumerate(wp.get("levelsOfDetail", [])):
            for k, contrib in enumerate(lod.get("contributesTo", [])):
                if isinstance(contrib, dict):
                    _check_field(contrib, "stateName", rename_map, changes,
                                 f"{wp_p}.levelsOfDetail[{j}].contributesTo[{k}]")

    for i, pat in enumerate(data.get("patterns", [])):
        pat_p = f"{prefix}patterns[{pat.get('name', i)}]"
        for j, view in enumerate(pat.get("patternViews", [])):
            for k, astate in enumerate(view.get("alphaStates", [])):
                if isinstance(astate, dict):
                    _check_field(astate, "stateName", rename_map, changes,
                                 f"{pat_p}.patternViews[{j}].alphaStates[{k}]")


def _rename_focus(data, rename_map, prefix, changes):
    for i, focus in enumerate(data.get("focuses", [])):
        _check_field(focus, "name", rename_map, changes,
                     f"{prefix}focuses[{focus.get('name', i)}]")
    for coll in ("alphas", "activitySpaces", "activities"):
        for i, item in enumerate(data.get(coll, [])):
            _check_field(item, "focusName", rename_map, changes,
                         f"{prefix}{coll}[{item.get('name', i)}]")


def _rename_work_product(data, rename_map, prefix, changes):
    for i, wp in enumerate(data.get("workProducts", [])):
        _check_field(wp, "name", rename_map, changes,
                     f"{prefix}workProducts[{wp.get('name', i)}]")
    for i, act in enumerate(data.get("activities", [])):
        ap = f"{prefix}activities[{act.get('name', i)}]"
        for j, wo in enumerate(act.get("worksOn", [])):
            _check_field(wo, "workProductName", rename_map, changes, f"{ap}.worksOn[{j}]")


def _rename_aliases(data, element_type, rename_map, prefix, changes):
    for i, alias in enumerate(data.get("practiceElementAliases", [])):
        if alias.get("practiceElementType") == element_type:
            _check_field(alias, "practiceElementName", rename_map, changes,
                         f"{prefix}practiceElementAliases[{i}]")


_RENAME_DISPATCH = {
    "ActivitySpace": _rename_activity_space,
    "Alpha": _rename_alpha,
    "Competency": _rename_competency,
    "NarrativeType": _rename_narrative_type,
    "State": _rename_state,
    "Focus": _rename_focus,
    "WorkProduct": _rename_work_product,
}


def apply_renames(data, element_type, rename_map, prefix=""):
    changes = []
    fn = _RENAME_DISPATCH.get(element_type)
    if fn:
        fn(data, rename_map, prefix, changes)
    _rename_aliases(data, element_type, rename_map, prefix, changes)
    return changes


def _remove_alpha_refs(data, alpha_name, prefix, changes):
    """Remove all references and definitions of a removed baseline alpha."""
    alphas = data.get("alphas", [])
    removed_defs = [a for a in alphas if a.get("name") == alpha_name]
    for a in removed_defs:
        changes.append({"path": f"{prefix}alphas", "field": "alphaName",
                        "old": alpha_name, "new": "(definition removed)"})
        alphas.remove(a)

    for i, alpha in enumerate(data.get("alphas", [])):
        ap = f"{prefix}alphas[{alpha.get('name', i)}]"
        if alpha.get("contributesTo") == alpha_name:
            changes.append({"path": ap, "field": "contributesTo",
                            "old": alpha_name, "new": "(removed)"})
            del alpha["contributesTo"]
        rels = alpha.get("relatesTo", [])
        removed_rels = [r for r in rels if r.get("alphaName") == alpha_name]
        for r in removed_rels:
            changes.append({"path": f"{ap}.relatesTo", "field": "alphaName",
                            "old": alpha_name, "new": "(removed)"})
            rels.remove(r)

    for coll in ("activitySpaces", "activities"):
        for i, item in enumerate(data.get(coll, [])):
            ip = f"{prefix}{coll}[{item.get('name', i)}]"
            contribs = item.get("contributesTo", [])
            removed = [c for c in contribs if isinstance(c, dict)
                       and c.get("alphaName") == alpha_name]
            for c in removed:
                changes.append({"path": f"{ip}.contributesTo", "field": "alphaName",
                                "old": alpha_name, "new": "(removed)"})
                contribs.remove(c)

    for i, wp in enumerate(data.get("workProducts", [])):
        wp_p = f"{prefix}workProducts[{wp.get('name', i)}]"
        for j, lod in enumerate(wp.get("levelsOfDetail", [])):
            contribs = lod.get("contributesTo", [])
            removed = [c for c in contribs if isinstance(c, dict)
                       and c.get("alphaName") == alpha_name]
            for c in removed:
                changes.append({
                    "path": f"{wp_p}.levelsOfDetail[{j}].contributesTo",
                    "field": "alphaName", "old": alpha_name, "new": "(removed)"})
                contribs.remove(c)

    for i, pat in enumerate(data.get("patterns", [])):
        pat_p = f"{prefix}patterns[{pat.get('name', i)}]"
        for j, view in enumerate(pat.get("patternViews", [])):
            astates = view.get("alphaStates", [])
            removed = [a for a in astates if isinstance(a, dict)
                       and a.get("alphaName") == alpha_name]
            for a in removed:
                changes.append({
                    "path": f"{pat_p}.patternViews[{j}].alphaStates",
                    "field": "alphaName", "old": alpha_name, "new": "(removed)"})
                astates.remove(a)


def _remove_activity_space_refs(data, space_name, prefix, changes):
    """Remove definitions and references to a removed baseline activitySpace."""
    spaces = data.get("activitySpaces", [])
    removed_defs = [s for s in spaces if s.get("name") == space_name]
    for s in removed_defs:
        changes.append({"path": f"{prefix}activitySpaces", "field": "activitySpaceName",
                        "old": space_name, "new": "(definition removed)"})
        spaces.remove(s)

    for i, act in enumerate(data.get("activities", [])):
        if act.get("activitySpaceName") == space_name:
            ap = f"{prefix}activities[{act.get('name', i)}]"
            changes.append({"path": ap, "field": "activitySpaceName",
                            "old": space_name, "new": "(removed)"})
            del act["activitySpaceName"]


def _remove_asset_refs(data, asset_name, prefix, changes):
    """Remove definitions and references to a removed asset."""
    assets = data.get("assets", [])
    removed_defs = [a for a in assets if a.get("name") == asset_name]
    for a in removed_defs:
        changes.append({"path": f"{prefix}assets", "field": "assetName",
                        "old": asset_name, "new": "(definition removed)"})
        assets.remove(a)

    for coll in ("alphas", "activitySpaces", "activities", "workProducts",
                 "competencies", "patterns", "personas"):
        for i, item in enumerate(data.get(coll, [])):
            ip = f"{prefix}{coll}[{item.get('name', i)}]"
            anames = item.get("assetNames", [])
            removed = [a for a in anames if isinstance(a, dict)
                       and a.get("assetName") == asset_name]
            for a in removed:
                changes.append({"path": f"{ip}.assetNames", "field": "assetName",
                                "old": asset_name, "new": "(removed)"})
                anames.remove(a)


_REMOVE_DISPATCH = {
    "Alpha": _remove_alpha_refs,
    "ActivitySpace": _remove_activity_space_refs,
    "Asset": _remove_asset_refs,
}


def apply_removals(data, operations, prefix=""):
    """Apply remove operations from a ChangeRequest to downstream data."""
    changes = []
    for op in operations:
        if op.get("operation") != "remove":
            continue
        et = op["elementType"]
        name = op["elementName"]
        fn = _REMOVE_DISPATCH.get(et)
        if fn:
            fn(data, name, prefix, changes)
    return changes


def process_target(data, kind, name_changes, type_filter=None, operations=None):
    by_type = defaultdict(dict)
    identity_count = 0
    for nc in name_changes:
        et = nc["elementType"]
        if type_filter and et not in type_filter:
            continue
        if nc["fromName"] == nc["toName"]:
            identity_count += 1
            continue
        by_type[et][nc["fromName"]] = nc["toName"]

    sources = [("", data)]
    if kind == "method":
        for i, practice in enumerate(data.get("practices", [])):
            pname = practice.get("name", f"practice[{i}]")
            sources.append((f"practices[{pname}].", practice))

    results = []
    for element_type, rename_map in by_type.items():
        type_changes = []
        for prefix, source_data in sources:
            type_changes.extend(apply_renames(source_data, element_type, rename_map, prefix))

        for from_name, to_name in rename_map.items():
            refs = [c for c in type_changes if c["old"] == from_name]
            if refs:
                results.append({
                    "elementType": element_type,
                    "fromName": from_name,
                    "toName": to_name,
                    "references": refs,
                })

    if operations:
        remove_ops = [op for op in operations if op.get("operation") == "remove"]
        if remove_ops:
            for prefix, source_data in sources:
                removal_changes = apply_removals(source_data, remove_ops, prefix)
                for rc in removal_changes:
                    results.append({
                        "elementType": rc["field"],
                        "fromName": rc["old"],
                        "toName": rc["new"],
                        "references": [rc],
                    })

    return results, identity_count


def main():
    parser = argparse.ArgumentParser(
        description="Apply ChangeRequest nameChanges to downstream JSON files"
    )
    parser.add_argument("change_request", help="ChangeRequest JSON file")
    parser.add_argument("targets", nargs="+", help="Target JSON files to patch")
    parser.add_argument("--fix", action="store_true",
                        help="Apply changes in-place (default: dry-run)")
    parser.add_argument("--element-types", nargs="*", metavar="TYPE",
                        help="Only apply changes for these element types")
    parser.add_argument("--output", "-o", metavar="DIR",
                        help="Write patched files to DIR instead of in-place")
    args = parser.parse_args()

    cr = load_json(args.change_request)
    name_changes = cr.get("nameChanges", [])
    operations = cr.get("operations", [])
    if not name_changes and not operations:
        print(json.dumps({"error": "No nameChanges or operations found in ChangeRequest"}))
        sys.exit(1)

    type_filter = set(args.element_types) if args.element_types else None

    if args.output:
        out_dir = Path(args.output)
        out_dir.mkdir(parents=True, exist_ok=True)

    target_reports = []
    for target_path in args.targets:
        import copy
        original = load_json(target_path)
        data = copy.deepcopy(original) if not args.fix else original

        kind = detect_kind(data)
        results, identity_count = process_target(
            data, kind, name_changes, type_filter, operations=operations
        )

        total = sum(len(r["references"]) for r in results)
        target_reports.append({
            "file": target_path,
            "kind": kind,
            "totalChanges": total,
            "nameChanges": results,
            "skippedIdentityMappings": identity_count,
        })

        if total > 0 and args.fix:
            if args.output:
                out_path = Path(args.output) / Path(target_path).name
            else:
                out_path = Path(target_path)
            with open(out_path, "w") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.write("\n")

    report = {
        "dryRun": not args.fix,
        "changeRequest": cr.get("changeId", "(unknown)"),
        "targets": target_reports,
        "summary": {
            "totalTargets": len(target_reports),
            "totalChanges": sum(t["totalChanges"] for t in target_reports),
            "targetsModified": sum(1 for t in target_reports if t["totalChanges"] > 0),
            "targetsUnchanged": sum(1 for t in target_reports if t["totalChanges"] == 0),
        },
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
