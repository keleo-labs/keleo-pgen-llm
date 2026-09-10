#!/usr/bin/env python3
"""Generate a structured summary of a practice/baseline/method for subagent prompt construction.

Produces everything a Phase 2/3 subagent needs to know about a practice as JSON:
metadata, alphas (with types, targets, states), patterns (with view names),
patternGroups, outcomes, work products, activities, personas, and schema
feature coverage flags.

Usage:
    python3 utils/practice-summary.py <practice>.json [--baseline <baseline>.json] [--json]
    python3 utils/practice-summary.py --dir <dir>/ [--baseline <baseline>.json] [--json]
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils._shared import load_json, detect_kind


def alpha_relationship_type(alpha):
    """Determine an alpha's relationship type and target."""
    if alpha.get("mapsTo"):
        rel_type = "mapsTo"
        target = alpha["mapsTo"]
    elif alpha.get("contributesTo"):
        ct = alpha["contributesTo"]
        rel_type = "contributesTo"
        target = ct if isinstance(ct, str) else ct.get("alphaName", str(ct))
    else:
        rel_type = "redeclaration"
        target = None
    return rel_type, target


def checklist_priority_distribution(items):
    """Count priority distribution across a list of checklist items."""
    dist = {"must": 0, "should": 0, "could": 0, "unset": 0}
    for item in items:
        p = item.get("priority", "must")
        if p in dist:
            dist[p] += 1
        else:
            dist["must"] += 1
    return dist


def summarize_alpha(alpha):
    """Summarize a single alpha."""
    rel_type, target = alpha_relationship_type(alpha)
    states = alpha.get("states", [])

    all_checklists = []
    for s in states:
        all_checklists.extend(s.get("checklist", []))

    priority_dist = checklist_priority_distribution(all_checklists)

    relates_to = []
    for r in alpha.get("relatesTo", []):
        entry = {
            "alphaName": r.get("alphaName"),
            "relationship": r.get("relationship"),
            "direction": r.get("direction"),
        }
        if r.get("relationshipKind"):
            entry["relationshipKind"] = r["relationshipKind"]
        relates_to.append(entry)

    result = {
        "name": alpha.get("name"),
        "relationshipType": rel_type,
        "stateNames": [s.get("name") for s in states],
        "checklistCount": len(all_checklists),
        "priorityDistribution": priority_dist,
    }
    if target:
        result["target"] = target
    if alpha.get("mapsTo") and alpha.get("contributesTo"):
        ct = alpha["contributesTo"]
        result["alsoContributesTo"] = ct if isinstance(ct, str) else ct.get("alphaName", str(ct))
    if relates_to:
        result["relatesTo"] = relates_to
    if alpha.get("focus"):
        result["focus"] = alpha["focus"]
    return result


def summarize_pattern(pattern):
    """Summarize a single pattern."""
    views = pattern.get("patternViews", [])
    sorted_views = sorted(views, key=lambda v: v.get("seq", 0))
    return {
        "name": pattern.get("name"),
        "viewNames": [v.get("name") for v in sorted_views],
        "viewCount": len(views),
    }


def summarize_outcome(outcome):
    """Summarize a single outcome."""
    result = {
        "name": outcome.get("name"),
        "measureDescription": outcome.get("measureDescription", ""),
    }
    ocs = outcome.get("objectiveContributions", [])
    if ocs:
        result["objectiveContributions"] = []
        for oc in ocs:
            entry = {
                "patternName": oc.get("patternName"),
                "recognizedAtPatternViewName": oc.get("recognizedAtPatternViewName"),
            }
            fws = oc.get("forecastWeights", [])
            if fws:
                entry["forecastWeights"] = {
                    fw.get("patternViewName"): fw.get("weight") for fw in fws
                }
            result["objectiveContributions"].append(entry)
    mcs = outcome.get("metricContributions", [])
    if mcs:
        result["hasMetricContributions"] = True
    return result


def summarize_work_product(wp):
    """Summarize a single work product."""
    lods = wp.get("levelsOfDetail", [])
    result = {
        "name": wp.get("name"),
        "lodNames": [l.get("name") for l in lods],
    }
    if wp.get("mapsTo"):
        result["relationshipType"] = "mapsTo"
        result["target"] = wp["mapsTo"]
    elif wp.get("partOf"):
        result["relationshipType"] = "partOf"
        result["target"] = wp["partOf"]
    else:
        result["relationshipType"] = "standalone"
    return result


def summarize_activity(activity):
    """Summarize a single activity."""
    result = {
        "name": activity.get("name"),
    }
    if activity.get("activitySpaceName"):
        result["activitySpaceName"] = activity["activitySpaceName"]
    if activity.get("ledBy"):
        result["ledBy"] = activity["ledBy"]

    ct = activity.get("contributesTo", [])
    if ct:
        result["contributesTo"] = [
            {"alphaName": c.get("alphaName"), "stateName": c.get("stateName")}
            for c in ct
        ]
    return result


def schema_feature_coverage(data):
    """Check which schema features are present."""
    all_checklists = []
    for alpha in data.get("alphas", []):
        for state in alpha.get("states", []):
            all_checklists.extend(state.get("checklist", []))
    for wp in data.get("workProducts", []):
        for lod in wp.get("levelsOfDetail", []):
            all_checklists.extend(lod.get("checklist", []))

    priority_count = sum(1 for c in all_checklists if c.get("priority"))
    total_checklists = len(all_checklists)

    has_gherkin = any(
        alpha.get("states", [{}])[0].get("background") is not None
        for alpha in data.get("alphas", [])
        if alpha.get("states")
    )

    return {
        "outcomes": len(data.get("outcomes", [])) > 0,
        "outcomeCount": len(data.get("outcomes", [])),
        "patternGroups": len(data.get("patternGroups", [])) > 0,
        "patternGroupCount": len(data.get("patternGroups", [])),
        "checklistPriority": priority_count > 0,
        "checklistPriorityPct": round(priority_count / total_checklists * 100, 1) if total_checklists else 0,
        "references": len(data.get("references", [])) > 0,
        "referenceCount": len(data.get("references", [])),
        "acknowledgements": len(data.get("acknowledgements", [])) > 0,
        "dependencyVersions": len(data.get("dependencyVersions", [])) > 0,
        "gherkinStructures": has_gherkin,
    }


def summarize_practice(data, baseline_data=None):
    """Generate full practice summary."""
    kind = detect_kind(data)

    summary = {
        "name": data.get("name", ""),
        "kind": kind,
        "version": data.get("version", ""),
        "schemaVersion": data.get("schemaVersion", ""),
        "baselinePracticeName": data.get("baselinePracticeName", ""),
        "practiceDependencyNames": data.get("practiceDependencyNames", []),
    }

    if kind == "method":
        summary["practiceNames"] = data.get("practiceNames", [])

    summary["alphas"] = [summarize_alpha(a) for a in data.get("alphas", [])]
    summary["patterns"] = [summarize_pattern(p) for p in data.get("patterns", [])]

    pg_summary = []
    for pg in data.get("patternGroups", []):
        entries = pg.get("entries", [])
        pg_summary.append({
            "name": pg.get("name"),
            "patterns": [e.get("patternName") for e in entries if e.get("patternName")],
        })
    summary["patternGroups"] = pg_summary

    summary["outcomes"] = [summarize_outcome(o) for o in data.get("outcomes", [])]
    summary["workProducts"] = [summarize_work_product(wp) for wp in data.get("workProducts", [])]
    summary["activities"] = [summarize_activity(a) for a in data.get("activities", [])]
    summary["personas"] = [p.get("name") for p in data.get("personas", [])]
    summary["personaGroups"] = [pg.get("name") for pg in data.get("personaGroups", [])]
    summary["featureCoverage"] = schema_feature_coverage(data)

    total_priority = {"must": 0, "should": 0, "could": 0, "unset": 0}
    for a in summary["alphas"]:
        for k, v in a.get("priorityDistribution", {}).items():
            total_priority[k] = total_priority.get(k, 0) + v
    summary["totalPriorityDistribution"] = total_priority

    return summary


def print_human_readable(summary):
    """Print a human-readable summary."""
    s = summary
    print(f"{s['name']} ({s['kind']}) v{s['version']} schema={s['schemaVersion']}")
    if s.get("baselinePracticeName"):
        print(f"  baseline: {s['baselinePracticeName']}")
    if s.get("practiceDependencyNames"):
        print(f"  dependencies: {s['practiceDependencyNames']}")
    if s.get("practiceNames"):
        print(f"  practices: {s['practiceNames']}")
    print()

    if s["alphas"]:
        print(f"Alphas ({len(s['alphas'])}):")
        for a in s["alphas"]:
            target = f" → {a['target']}" if a.get("target") else ""
            also = f" (also contributesTo: {a['alsoContributesTo']})" if a.get("alsoContributesTo") else ""
            print(f"  {a['name']} ({a['relationshipType']}{target}){also}")
            print(f"    states: {a['stateNames']}")
            pd = a.get("priorityDistribution", {})
            if any(pd.values()):
                print(f"    checklists: {a['checklistCount']} (must={pd.get('must',0)} should={pd.get('should',0)} could={pd.get('could',0)})")
        print()

    if s["patterns"]:
        print(f"Patterns ({len(s['patterns'])}):")
        for p in s["patterns"]:
            print(f"  {p['name']} ({p['viewCount']} views)")
            for v in p["viewNames"]:
                print(f"    - {v}")
        print()

    if s["patternGroups"]:
        print(f"Pattern Groups ({len(s['patternGroups'])}):")
        for pg in s["patternGroups"]:
            print(f"  {pg['name']}: {pg['patterns']}")
        print()

    if s["outcomes"]:
        print(f"Outcomes ({len(s['outcomes'])}):")
        for o in s["outcomes"]:
            print(f"  {o['name']}")
            for oc in o.get("objectiveContributions", []):
                print(f"    pattern: {oc['patternName']}")
                print(f"    recognizedAt: {oc['recognizedAtPatternViewName']}")
                if oc.get("forecastWeights"):
                    for vn, w in oc["forecastWeights"].items():
                        print(f"      {vn}: {w}")
        print()

    if s["workProducts"]:
        print(f"Work Products ({len(s['workProducts'])}):")
        for wp in s["workProducts"]:
            target = f" → {wp['target']}" if wp.get("target") else ""
            print(f"  {wp['name']} ({wp['relationshipType']}{target})")
            print(f"    LODs: {wp['lodNames']}")
        print()

    if s["activities"]:
        print(f"Activities ({len(s['activities'])}):")
        for a in s["activities"]:
            space = f" [{a['activitySpaceName']}]" if a.get("activitySpaceName") else ""
            led = f" (ledBy: {a['ledBy']})" if a.get("ledBy") else ""
            print(f"  {a['name']}{space}{led}")
        print()

    fc = s["featureCoverage"]
    print("Feature Coverage:")
    print(f"  outcomes: {'✓' if fc['outcomes'] else '✗'} ({fc['outcomeCount']})")
    print(f"  patternGroups: {'✓' if fc['patternGroups'] else '✗'} ({fc['patternGroupCount']})")
    print(f"  checklistPriority: {'✓' if fc['checklistPriority'] else '✗'} ({fc['checklistPriorityPct']}%)")
    print(f"  references: {'✓' if fc['references'] else '✗'} ({fc['referenceCount']})")
    print(f"  dependencyVersions: {'✓' if fc['dependencyVersions'] else '✗'}")
    print(f"  gherkinStructures: {'✓' if fc['gherkinStructures'] else '✗'}")

    tp = s["totalPriorityDistribution"]
    total = sum(tp.values())
    if total:
        print(f"\nPriority Distribution: must={tp['must']} ({tp['must']*100//total}%) "
              f"should={tp['should']} ({tp['should']*100//total}%) "
              f"could={tp['could']} ({tp['could']*100//total}%)")


def main():
    parser = argparse.ArgumentParser(
        description="Generate structured practice summary for subagent prompt construction"
    )
    parser.add_argument("json_file", nargs="?", help="Path to practice JSON file")
    parser.add_argument("--dir", help="Process all practice JSON files in directory")
    parser.add_argument("--baseline", help="Baseline JSON for context")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    if not args.json_file and not args.dir:
        parser.error("Either json_file or --dir is required")

    baseline_data = load_json(args.baseline) if args.baseline else None

    files = []
    if args.dir:
        dir_path = Path(args.dir)
        files = sorted(
            f for f in dir_path.glob("*.json")
            if not f.name.startswith("_")
            and not f.name.startswith("change-request")
            and "backup" not in str(f)
        )
    else:
        files = [Path(args.json_file)]

    summaries = []
    for f in files:
        data = load_json(f)
        kind = detect_kind(data)
        if kind not in ("practice", "method", "practiceBaseline"):
            continue
        summary = summarize_practice(data, baseline_data)
        summary["_filePath"] = str(f)
        summaries.append(summary)

    if args.json:
        if len(summaries) == 1:
            print(json.dumps(summaries[0], indent=2))
        else:
            print(json.dumps(summaries, indent=2))
    else:
        for i, s in enumerate(summaries):
            if i > 0:
                print("\n" + "=" * 60 + "\n")
            print_human_readable(s)


if __name__ == "__main__":
    main()
