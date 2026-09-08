#!/usr/bin/env python3
"""Extract content from existing practice/method JSON for reverse-engineering into analysis format."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils._shared import load_json


def extract_metadata(data):
    focuses = sorted(set(
        a.get("focusName", "Unknown")
        for a in data.get("alphas", [])
        if isinstance(a, dict)
    ))
    return {
        "name": data.get("name", ""),
        "kind": data.get("kind", ""),
        "description": data.get("description", ""),
        "baselinePracticeName": data.get("baselinePracticeName", ""),
        "focuses": focuses,
    }


def extract_alphas(data):
    return [
        {
            "name": a.get("name", ""),
            "description": a.get("description", ""),
            "focusName": a.get("focusName", ""),
            "contributesTo": a.get("contributesTo", ""),
            "relatesTo": a.get("relatesTo", []),
            "states": [
                {"name": s.get("name", ""), "description": s.get("description", "")}
                for s in a.get("states", [])
            ],
        }
        for a in data.get("alphas", [])
    ]


def extract_work_products(data):
    return [
        {
            "name": wp.get("name", ""),
            "description": wp.get("description", ""),
            "levels": [
                {"name": l.get("name", ""), "description": l.get("description", "")}
                for l in wp.get("levelsOfDetail", [])
            ],
        }
        for wp in data.get("workProducts", [])
    ]


def extract_activities(data):
    return [
        {
            "name": act.get("name", ""),
            "description": act.get("description", ""),
            "activitySpaceName": act.get("activitySpaceName", ""),
            "requiredCompetencies": act.get("requiredCompetencies", []),
            "recommendedCompetencyLevels": act.get("recommendedCompetencyLevels", []),
        }
        for act in data.get("activities", [])
    ]


def extract_personas(data):
    return [
        {
            "name": p.get("name", ""),
            "description": p.get("description", ""),
            "competencies": [
                c.get("competencyName", "") for c in p.get("competencies", [])
            ],
        }
        for p in data.get("personas", [])
    ]


def extract_patterns(data):
    return [
        {
            "name": pat.get("name", ""),
            "description": pat.get("description", ""),
            "views": [v.get("name", "") for v in pat.get("patternViews", [])],
        }
        for pat in data.get("patterns", [])
    ]


def extract_citations(data):
    citations = []
    for c in data.get("citations", []):
        entry = {"name": c.get("name", "")}
        for ctx in c.get("narrativeContexts", []):
            elem = ctx.get("narrativeElementName", "")
            val = ctx.get("context", "")
            if elem == "Author":
                entry["author"] = val
            elif elem == "Title":
                entry["title"] = val
            elif elem == "Source":
                entry["source"] = val
            elif elem == "Date":
                entry["date"] = val
        citations.append(entry)
    return citations


def extract_outcomes(data):
    return [
        {
            "name": o.get("name", ""),
            "description": o.get("description", ""),
            "measureDescription": o.get("measureDescription", ""),
            "metricContributions": o.get("metricContributions", []),
            "objectiveContributions": o.get("objectiveContributions", []),
        }
        for o in data.get("outcomes", [])
        if isinstance(o, dict)
    ]


def generate_markdown(data):
    meta = extract_metadata(data)
    alphas = extract_alphas(data)
    work_products = extract_work_products(data)
    activities = extract_activities(data)
    personas = extract_personas(data)
    patterns = extract_patterns(data)
    citations = extract_citations(data)
    outcomes = extract_outcomes(data)

    lines = [f"# Analysis Report: {meta['name']}", ""]
    lines.append(f"> Extracted from existing {meta['kind']} JSON")
    lines.append("")

    lines.append("## 1. Outcomes")
    lines.append("")
    if outcomes:
        for i, o in enumerate(outcomes, 1):
            lines.append(f"### 1.{i} {o['name']}")
            lines.append(f"**Description:** {o['description']}")
            if o.get("measureDescription"):
                lines.append(f"**How Value is Measured:** {o['measureDescription']}")
            if o.get("metricContributions"):
                mc_alphas = ", ".join(mc.get("alphaName", "") for mc in o["metricContributions"])
                lines.append(f"**Metric Contributions:** {mc_alphas}")
            if o.get("objectiveContributions"):
                oc_parts = []
                for oc in o["objectiveContributions"]:
                    pn = oc.get("patternName", "")
                    vn = oc.get("recognizedAtPatternViewName", "")
                    if pn and vn:
                        oc_parts.append(f"{pn} → {vn}")
                    elif pn:
                        oc_parts.append(pn)
                if oc_parts:
                    lines.append(f"**Objective Contributions:** {', '.join(oc_parts)}")
            lines.append("")
    else:
        lines.append(meta["description"])
        lines.append("")

    lines.append("## 2. Concerns")
    lines.append("")
    for i, a in enumerate(alphas, 1):
        lines.append(f"### {i}. {a['name']}")
        lines.append("")
        lines.append(f"**Description:** {a['description']}")
        lines.append(f"**Focus:** {a.get('focusName', 'N/A')}")
        if a.get("contributesTo"):
            lines.append(f"**Contributes To:** {a['contributesTo']}")
        lines.append("")

    lines.append("## 3. Progressive States")
    lines.append("")
    for a in alphas:
        lines.append(f"### {a['name']}")
        lines.append("")
        for j, s in enumerate(a["states"], 1):
            lines.append(f"{j}. **{s['name']}**: {s['description']}")
        lines.append("")

    lines.append("## 4. Activities")
    lines.append("")
    for i, act in enumerate(activities, 1):
        lines.append(f"### {i}. {act['name']}")
        lines.append("")
        lines.append(f"**Description:** {act['description']}")
        lines.append(f"**Activity Space:** {act.get('activitySpaceName', 'N/A')}")
        if act.get("requiredCompetencies"):
            lines.append(f"**Competencies:** {', '.join(act['requiredCompetencies'])}")
        lines.append("")

    lines.append("## 5. Competencies")
    lines.append("")
    competencies_seen = set()
    for act in activities:
        for c in act.get("requiredCompetencies", []):
            competencies_seen.add(c)
    for p in personas:
        for c in p.get("competencies", []):
            competencies_seen.add(c)
    for c in sorted(competencies_seen):
        lines.append(f"- {c}")
    lines.append("")

    lines.append("## 6. Personas")
    lines.append("")
    for p in personas:
        lines.append(f"### {p['name']}")
        lines.append("")
        lines.append(f"**Description:** {p['description']}")
        if p.get("competencies"):
            lines.append(f"**Competencies:** {', '.join(p['competencies'])}")
        lines.append("")

    lines.append("## 7. Persona Groups")
    lines.append("")
    for pg in data.get("personaGroups", []):
        lines.append(f"### {pg.get('name', '')}")
        lines.append("")
        lines.append(f"**Description:** {pg.get('description', '')}")
        lines.append("")

    lines.append("## 8. Workflows")
    lines.append("")
    for pat in patterns:
        lines.append(f"### {pat['name']}")
        lines.append("")
        lines.append(f"**Description:** {pat['description']}")
        lines.append(f"**Views:** {', '.join(pat['views'])}")
        lines.append("")

    lines.append("## 9. Work Products")
    lines.append("")
    for wp in work_products:
        lines.append(f"### {wp['name']}")
        lines.append("")
        lines.append(f"**Description:** {wp['description']}")
        lines.append("**Levels of Detail:**")
        for l in wp["levels"]:
            lines.append(f"- **{l['name']}**: {l['description']}")
        lines.append("")

    lines.append("## 10. Citations")
    lines.append("")
    for c in citations:
        parts = []
        if c.get("author"):
            parts.append(c["author"])
        if c.get("date"):
            parts.append(f"({c['date']})")
        if c.get("title"):
            parts.append(f"*{c['title']}*")
        if c.get("source"):
            parts.append(c["source"])
        lines.append(f"- {' '.join(parts)}" if parts else f"- {c.get('name', '')}")
    lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Extract content from practice/method JSON for reverse-engineering"
    )
    parser.add_argument("file", help="Path to practice/method JSON file")
    parser.add_argument(
        "--output",
        help="Write Phase 1 analysis report markdown to this path (default: print JSON summary to stdout)",
    )
    parser.add_argument(
        "--extract-narratives",
        metavar="PATH",
        help="Extract top-level narratives array to a JSON file (for --method-narrative-file in package-keleo.py)",
    )
    args = parser.parse_args()

    data = load_json(args.file)

    if args.extract_narratives:
        narratives = data.get("narratives", [])
        with open(args.extract_narratives, "w", encoding="utf-8") as f:
            json.dump(narratives, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print(json.dumps({
            "output": args.extract_narratives,
            "narratives": len(narratives),
        }, indent=2))
        return

    if data.get("kind") == "method" and "practices" in data:
        practices = data.get("practices", [])
        merged = dict(data)
        for key in ["alphas", "workProducts", "activities", "personas", "patterns", "citations", "assets", "outcomes"]:
            merged_list = list(data.get(key, []))
            for p in practices:
                merged_list.extend(p.get(key, []))
            merged[key] = merged_list
        data = merged

    if args.output:
        md = generate_markdown(data)
        with open(args.output, "w") as f:
            f.write(md)
        print(json.dumps({
            "output": args.output,
            "alphas": len(extract_alphas(data)),
            "activities": len(extract_activities(data)),
            "workProducts": len(extract_work_products(data)),
            "personas": len(extract_personas(data)),
            "patterns": len(extract_patterns(data)),
            "citations": len(extract_citations(data)),
            "outcomes": len(extract_outcomes(data)),
        }, indent=2))
    else:
        summary = {
            "metadata": extract_metadata(data),
            "alphas": extract_alphas(data),
            "workProducts": extract_work_products(data),
            "activities": extract_activities(data),
            "personas": extract_personas(data),
            "patterns": extract_patterns(data),
            "citations": extract_citations(data),
            "outcomes": extract_outcomes(data),
        }
        print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
