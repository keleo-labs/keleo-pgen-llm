#!/usr/bin/env python3
"""Generate a structured summary of a practice/baseline/method for subagent prompt construction.

Produces everything a Phase 2/3 subagent needs to know about a practice as JSON:
metadata, alphas (with types, targets, states), patterns (with view names),
patternGroups, outcomes, work products, activities, personas, and schema
feature coverage flags.

`--show` switches to a detail view instead, printing the underlying text —
persona competencies and narratives, alpha state checklists, work product
levels of detail, citations — for reading a practice rather than summarising it.

Usage:
    python3 utils/practice-summary.py <practice>.json [--baseline <baseline>.json] [--json]
    python3 utils/practice-summary.py --dir <dir>/ [--baseline <baseline>.json] [--json]
    python3 utils/practice-summary.py <practice>.json --show personas --name "Architect"
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
        # Per-view alpha states are what you need to judge whether a pattern
        # reads as a progression or repeats one snapshot; viewNames alone
        # cannot show that.
        "views": [
            {
                "seq": v.get("seq"),
                "name": v.get("name"),
                "alphaStates": [
                    {"alphaName": a.get("alphaName"), "stateName": a.get("stateName")}
                    for a in v.get("alphaStates", [])
                ],
            }
            for v in sorted_views
        ],
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
            for v in p.get("views", []):
                print(f"    - {v['name']}")
                for a in v["alphaStates"]:
                    print(f"        {a['alphaName']} -> {a['stateName']}")
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


DETAIL_KEYS = [
    "personas", "personaGroups", "alphas", "workProducts",
    "activities", "outcomes", "narratives", "citations",
]


def _matches(name, needle):
    """Case-insensitive substring match; an empty needle matches everything."""
    return not needle or needle.lower() in (name or "").lower()


def _print_narratives(narratives, indent):
    """Print narratives with their ordered contexts."""
    pad = " " * indent
    for n in narratives:
        type_name = n.get("narrativeTypeName", "")
        suffix = f" [{type_name}]" if type_name else ""
        print(f"{pad}narrative: {n.get('name')}{suffix}")
        if n.get("description"):
            print(f"{pad}  {n['description']}")
        for c in sorted(n.get("narrativeContexts", []), key=lambda x: x.get("seq", 0)):
            print(f"{pad}  {c.get('narrativeElementName')}: {c.get('context', '')}")
        if n.get("citationNames"):
            print(f"{pad}  cites: {', '.join(n['citationNames'])}")


def print_detail(data, keys, needle):
    """Print full detail for the requested element types.

    Complements the summary view, which deliberately reduces elements to names
    and counts. Reading a persona's narrative or an alpha's state checklists
    needs the underlying text, not a count of it.
    """
    for key in keys:
        items = [i for i in (data.get(key) or []) if _matches(i.get("name"), needle)]
        if not items:
            continue
        print(f"=== {key} ({len(items)}) ===")
        for item in items:
            print(f"- {item.get('name')}")
            if item.get("description"):
                print(f"    {item['description']}")

            if key == "citations":
                for field in ("author", "date", "source", "url", "pages"):
                    if item.get(field):
                        print(f"    {field}: {item[field]}")

            if item.get("competencies"):
                comps = ", ".join(
                    f"{c.get('competencyName')} ({c.get('competencyLevelName')})"
                    for c in item["competencies"]
                )
                print(f"    competencies: {comps}")

            if item.get("personaNames"):
                print(f"    personas: {', '.join(item['personaNames'])}")
            if item.get("personaGroupNames"):
                print(f"    groups: {', '.join(item['personaGroupNames'])}")
            if item.get("ledBy"):
                print(f"    ledBy: {item['ledBy']}")
            if item.get("measureDescription"):
                print(f"    measure: {item['measureDescription']}")

            for state in item.get("states", []):
                print(f"    state: {state.get('name')} — {state.get('description', '')}")
                for given in (state.get("background") or {}).get("given", []):
                    print(f"      given: {given}")
                for c in state.get("checklist", []):
                    pri = c.get("priority", "must")
                    print(f"      [{pri}] {c.get('name')}: {c.get('description', '')}")

            for lod in item.get("levelsOfDetail", []):
                print(f"    lod: {lod.get('name')} — {lod.get('description', '')}")
                for c in lod.get("checklist", []):
                    pri = c.get("priority", "must")
                    print(f"      [{pri}] {c.get('name')}: {c.get('description', '')}")

            if item.get("narratives"):
                _print_narratives(item["narratives"], 4)
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Generate structured practice summary for subagent prompt construction"
    )
    parser.add_argument("json_file", nargs="?", help="Path to practice JSON file")
    parser.add_argument("--dir", help="Process all practice JSON files in directory")
    parser.add_argument("--baseline", help="Baseline JSON for context")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--names-only", action="store_true",
                        help="List only name, kind, and version per file (compact)")
    parser.add_argument("--show", nargs="+", metavar="KEY", choices=DETAIL_KEYS + ["all"],
                        help="Print full detail (descriptions, checklists, narratives, "
                             f"competencies) for these element types instead of the "
                             f"summary. Choices: {', '.join(DETAIL_KEYS)}, all")
    parser.add_argument("--name", metavar="SUBSTRING",
                        help="With --show, restrict output to elements whose name "
                             "contains this substring (case-insensitive)")
    args = parser.parse_args()

    if args.name and not args.show:
        parser.error("--name requires --show")

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

    if args.names_only:
        for f in files:
            data = load_json(f)
            kind = detect_kind(data)
            if kind not in ("practice", "method", "practiceBaseline"):
                continue
            name = data.get("name", f.stem)
            version = data.get("version", "?")
            print(f"{name} ({kind}) v{version}")
        return

    if args.show:
        keys = DETAIL_KEYS if "all" in args.show else args.show
        for i, f in enumerate(files):
            if i > 0:
                print("\n" + "=" * 60 + "\n")
            data = load_json(f)
            # Not gated on detect_kind: a resolved effective context carries the
            # same element arrays and is the common thing to interrogate.
            print(f"{data.get('name', f.stem)} [{f}]\n")
            print_detail(data, keys, args.name)
        return

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
