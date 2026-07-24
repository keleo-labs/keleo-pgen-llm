#!/usr/bin/env python3
"""Cross-practice reference auditing within a method.

Checks that all symbolic references (alphaName, stateName, personaGroupName,
personaNames) resolve across practices, dependencies, and baseline.

Usage:
    python3 utils/audit-method-references.py <method.json> --baseline <baseline.json>
    python3 utils/audit-method-references.py <practice-dir/> --baseline <baseline.json>
    python3 utils/audit-method-references.py <method.json> --baseline <baseline.json> --json
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils._shared import load_json, detect_kind


def load_practices(path):
    """Load practices from a method JSON or a directory of practice JSONs.

    Returns (list_of_practice_dicts, source_description).
    """
    p = Path(path)
    if p.is_file():
        data = load_json(p)
        kind = detect_kind(data)
        if kind == "method":
            return data.get("practices", []), f"method:{p.name}"
        return [data], f"practice:{p.name}"

    if p.is_dir():
        practices = []
        for f in sorted(p.glob("*.json")):
            if f.name.startswith("_"):
                continue
            data = load_json(f, exit_on_error=False)
            if data is None:
                continue
            kind = detect_kind(data)
            if kind == "method":
                practices.extend(data.get("practices", []))
            elif kind == "practice":
                practices.append(data)
        return practices, f"dir:{p.name}"

    print(json.dumps({"error": f"Not a file or directory: {path}"}))
    sys.exit(1)


def build_alpha_index(practices, baseline):
    """Build lookup: alpha_name -> {states: set, practice: str, source: str}."""
    index = {}

    for alpha in baseline.get("alphas", []):
        name = alpha.get("name")
        if name:
            states = {s.get("name") for s in alpha.get("states", []) if s.get("name")}
            index[name] = {"states": states, "practice": None, "source": "baseline"}

    for practice in practices:
        pname = practice.get("name", "?")
        for alpha in practice.get("alphas", []):
            name = alpha.get("name")
            if name:
                states = {s.get("name") for s in alpha.get("states", []) if s.get("name")}
                if name in index and index[name]["source"] == "baseline":
                    merged_states = index[name]["states"] | states
                    index[name] = {"states": merged_states, "practice": pname, "source": "redeclaration"}
                else:
                    index[name] = {"states": states, "practice": pname, "source": "practice"}

    return index


def find_alpha_references(practice):
    """Extract all alphaName/stateName references from a practice.

    Returns list of {alphaName, stateName, location} dicts.
    """
    refs = []
    pname = practice.get("name", "?")

    for act in practice.get("activities", []):
        aname = act.get("name", "?")
        for i, c in enumerate(act.get("contributesTo", [])):
            if isinstance(c, dict) and c.get("alphaName"):
                refs.append({
                    "alphaName": c["alphaName"],
                    "stateName": c.get("stateName", c.get("alphaStateName")),
                    "location": f"activities[{aname}].contributesTo[{i}]",
                })

    for wp in practice.get("workProducts", []):
        wpname = wp.get("name", "?")
        for lod in wp.get("levelsOfDetail", []):
            lodname = lod.get("name", "?")
            for i, c in enumerate(lod.get("contributesTo", [])):
                if isinstance(c, dict) and c.get("alphaName"):
                    refs.append({
                        "alphaName": c["alphaName"],
                        "stateName": c.get("stateName", c.get("alphaStateName")),
                        "location": f"workProducts[{wpname}].levelsOfDetail[{lodname}].contributesTo[{i}]",
                    })

    for pat in practice.get("patterns", []):
        patname = pat.get("name", "?")
        for view in pat.get("patternViews", []):
            vname = view.get("name", "?")
            for i, state in enumerate(view.get("alphaStates", [])):
                if isinstance(state, dict) and state.get("alphaName"):
                    refs.append({
                        "alphaName": state["alphaName"],
                        "stateName": state.get("stateName", state.get("alphaStateName")),
                        "location": f"patterns[{patname}].patternViews[{vname}].alphaStates[{i}]",
                    })

    return refs


def resolve_references(practices, baseline):
    """Check all alpha/state references resolve. Returns list of issue dicts."""
    alpha_index = build_alpha_index(practices, baseline)
    issues = []

    for practice in practices:
        pname = practice.get("name", "?")
        refs = find_alpha_references(practice)

        for ref in refs:
            alpha_name = ref["alphaName"]
            state_name = ref["stateName"]

            if alpha_name not in alpha_index:
                issues.append({
                    "severity": "error",
                    "category": "unresolved-alpha-ref",
                    "practice": pname,
                    "path": ref["location"],
                    "message": f"Alpha '{alpha_name}' not found in practice, dependencies, or baseline",
                })
                continue

            if state_name and state_name not in alpha_index[alpha_name]["states"]:
                issues.append({
                    "severity": "error",
                    "category": "unresolved-state-ref",
                    "practice": pname,
                    "path": ref["location"],
                    "message": f"State '{state_name}' not found on alpha '{alpha_name}'",
                })

    return issues


def find_cross_practice_duplicates(practices):
    """Find duplicate element names across practices (excluding alpha redeclarations)."""
    issues = []
    exempt_types = {"alphas"}

    for element_type in ["activities", "workProducts", "personas", "personaGroups", "patterns"]:
        name_locations = {}
        for practice in practices:
            pname = practice.get("name", "?")
            for elem in practice.get(element_type, []):
                name = elem.get("name")
                if name:
                    name_locations.setdefault(name, []).append(pname)

        for name, locations in name_locations.items():
            if len(locations) > 1:
                issues.append({
                    "severity": "warning",
                    "category": "cross-practice-duplicate",
                    "path": element_type,
                    "message": f"'{name}' defined in multiple practices: {', '.join(locations)}",
                })

    return issues


def check_persona_consistency(practices):
    """Check persona/personaGroup references resolve within each practice."""
    issues = []

    for practice in practices:
        pname = practice.get("name", "?")

        defined_personas = {p.get("name") for p in practice.get("personas", []) if p.get("name")}
        defined_groups = {g.get("name") for g in practice.get("personaGroups", []) if g.get("name")}

        for act in practice.get("activities", []):
            pg = act.get("personaGroupName")
            if pg and pg not in defined_groups:
                issues.append({
                    "severity": "warning",
                    "category": "unresolved-persona-group",
                    "practice": pname,
                    "path": f"activities[{act.get('name', '?')}].personaGroupName",
                    "message": f"PersonaGroup '{pg}' not defined in practice '{pname}'",
                })

        for group in practice.get("personaGroups", []):
            gname = group.get("name", "?")
            for pn in group.get("personaNames", []):
                if pn not in defined_personas:
                    issues.append({
                        "severity": "warning",
                        "category": "unresolved-persona",
                        "practice": pname,
                        "path": f"personaGroups[{gname}].personaNames",
                        "message": f"Persona '{pn}' not defined in practice '{pname}'",
                    })

    return issues


def audit_method(practices, baseline):
    """Run all audit checks. Returns structured report dict."""
    all_issues = []

    all_issues.extend(resolve_references(practices, baseline))
    all_issues.extend(find_cross_practice_duplicates(practices))
    all_issues.extend(check_persona_consistency(practices))

    per_practice = {}
    for practice in practices:
        pname = practice.get("name", "?")
        refs = find_alpha_references(practice)
        practice_issues = [i for i in all_issues if i.get("practice") == pname]
        per_practice[pname] = {
            "alphaRefCount": len(refs),
            "errorCount": sum(1 for i in practice_issues if i["severity"] == "error"),
            "warningCount": sum(1 for i in practice_issues if i["severity"] == "warning"),
        }

    error_count = sum(1 for i in all_issues if i["severity"] == "error")
    warning_count = sum(1 for i in all_issues if i["severity"] == "warning")

    return {
        "practiceCount": len(practices),
        "issues": all_issues,
        "perPractice": per_practice,
        "summary": f"{error_count} error(s), {warning_count} warning(s)",
    }


def main():
    parser = argparse.ArgumentParser(
        description="Cross-practice reference auditing within a method"
    )
    parser.add_argument("path", help="Method JSON file or directory of practice JSONs")
    parser.add_argument("--baseline", required=True, help="Baseline or effective-baseline JSON")
    parser.add_argument("--json", action="store_true",
                        help="Output as JSON (default is human-readable)")
    args = parser.parse_args()

    practices, source = load_practices(args.path)
    baseline = load_json(args.baseline)

    if not practices:
        print(json.dumps({"error": "No practices found", "source": source}))
        sys.exit(1)

    report = audit_method(practices, baseline)
    report["source"] = source

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"Audited {report['practiceCount']} practice(s) from {source}")
        print(f"  {report['summary']}")
        print()
        for pname, stats in report["perPractice"].items():
            status = "OK" if stats["errorCount"] == 0 else f"{stats['errorCount']} error(s)"
            print(f"  {pname}: {stats['alphaRefCount']} refs, {status}")
        print()
        for issue in report["issues"]:
            sev = "E" if issue["severity"] == "error" else "W"
            practice = issue.get("practice", "method")
            print(f"  [{sev}] {practice}: {issue['message']}")
            if issue.get("path"):
                print(f"       {issue['path']}")

    error_count = sum(1 for i in report["issues"] if i["severity"] == "error")
    sys.exit(0 if error_count == 0 else 1)


if __name__ == "__main__":
    main()
