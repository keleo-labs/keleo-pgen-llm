#!/usr/bin/env python3
"""
Assemble standalone practice JSON files into a single method JSON.

Usage:
    python3 utils/assemble-method-json.py \\
        --name "Method Name" \\
        --baseline-name "Baseline Practice Name" \\
        --practices practice1.json practice2.json ... \\
        --output method.json \\
        [--description "Method description"] \\
        [--version "1.0.0"] \\
        [--authors "Author1" "Author2"] \\
        [--keywords "kw1" "kw2"] \\
        [--narrative-type "Narrative Type Name"] \\
        [--narrative-contexts '{"seq":1,"narrativeElementName":"...","context":"..."}' ...] \\
        [--narrative-file narratives.json] \\
        [--merge-assets]

Merges citations and assets across all practices (deduped by name).
Embeds each practice (minus method-level fields) into the practices array.
Sets kind: "method" at root level.

With --merge-assets, includes deduped assets from all practices at method level.
With --narrative-file, loads full narrative definitions from a JSON file.
"""
import argparse
import json
import sys
from collections import OrderedDict
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils._shared import load_json


def dedup_by_name(items):
    seen = set()
    result = []
    for item in items:
        name = item.get("name")
        if name and name not in seen:
            seen.add(name)
            result.append(item)
    return result


def build_method(args):
    practices_data = []
    all_citations = []
    all_assets = []
    all_domain_tags = set()
    all_lifecycle_tags = set()
    all_org_tags = set()
    all_keywords = set()

    for path in args.practices:
        practice = load_json(path)
        practices_data.append(practice)

        all_citations.extend(practice.get("citations", []))
        all_assets.extend(practice.get("assets", []))

        tags = practice.get("tags", {})
        all_domain_tags.update(tags.get("domainTags", []))
        all_lifecycle_tags.update(tags.get("lifecycleTags", []))
        all_org_tags.update(tags.get("organizationalTags", []))
        all_keywords.update(practice.get("keywords", []))

    merged_citations = dedup_by_name(all_citations)
    merged_assets = dedup_by_name(all_assets)

    embedded_practices = []
    for p in practices_data:
        ep = OrderedDict()
        ep["kind"] = "practice"
        ep["name"] = p["name"]
        ep["description"] = p["description"]
        ep["baselinePracticeName"] = p["baselinePracticeName"]

        if p.get("practiceDependencyNames"):
            ep["practiceDependencyNames"] = p["practiceDependencyNames"]

        ep["tags"] = p.get("tags", {})
        ep["keywords"] = p.get("keywords", [])
        ep["authors"] = p.get("authors", [])
        ep["createdAt"] = p.get("createdAt", str(date.today()))
        ep["updatedAt"] = p.get("updatedAt", str(date.today()))
        ep["version"] = p.get("version", "1.0.0")

        if p.get("narrativeTypes"):
            ep["narrativeTypes"] = p["narrativeTypes"]
        if p.get("narratives"):
            ep["narratives"] = p["narratives"]
        if p.get("assetNames"):
            ep["assetNames"] = p["assetNames"]
        if p.get("practiceElementAliases"):
            ep["practiceElementAliases"] = p["practiceElementAliases"]

        ep["alphas"] = p.get("alphas", [])
        ep["activities"] = p.get("activities", [])
        ep["workProducts"] = p.get("workProducts", [])
        ep["personas"] = p.get("personas", [])
        ep["personaGroups"] = p.get("personaGroups", [])
        ep["patterns"] = p.get("patterns", [])

        ep["citations"] = p.get("citations", [])
        ep["assets"] = p.get("assets", [])

        embedded_practices.append(ep)

    method = OrderedDict()
    method["kind"] = "method"
    method["name"] = args.name
    method["description"] = args.description or f"Comprehensive methodology combining {len(practices_data)} practices."
    method["baselinePracticeName"] = args.baseline_name

    method["tags"] = {
        "domainTags": sorted(all_domain_tags),
        "lifecycleTags": sorted(all_lifecycle_tags),
        "organizationalTags": sorted(all_org_tags),
    }

    if args.narrative_file:
        narratives = load_json(args.narrative_file)
        if not isinstance(narratives, list):
            narratives = [narratives]
        method["narratives"] = narratives
    elif args.narrative_type and args.narrative_contexts:
        contexts = []
        for ctx_str in args.narrative_contexts:
            contexts.append(json.loads(ctx_str))
        method["narratives"] = [{
            "name": f"{args.name} Journey",
            "description": f"Method-level narrative describing the {args.name} transformation lifecycle.",
            "narrativeTypeName": args.narrative_type,
            "narrativeContexts": contexts,
        }]

    method["citations"] = merged_citations
    method["assets"] = merged_assets if args.merge_assets else []
    method["practices"] = embedded_practices

    return method


def main():
    parser = argparse.ArgumentParser(
        description="Assemble standalone practice JSONs into a method JSON"
    )
    parser.add_argument("--name", required=True, help="Method name")
    parser.add_argument("--baseline-name", required=True, help="Baseline practice name")
    parser.add_argument("--practices", nargs="+", required=True, help="Practice JSON file paths (order matters)")
    parser.add_argument("--output", "-o", required=True, help="Output method JSON path")
    parser.add_argument("--description", help="Method description")
    parser.add_argument("--version", default="1.0.0", help="Method version")
    parser.add_argument("--authors", nargs="+", help="Method authors")
    parser.add_argument("--keywords", nargs="+", help="Method keywords (default: merged from practices)")
    parser.add_argument("--narrative-type", help="Narrative type name for method-level narrative")
    parser.add_argument("--narrative-contexts", nargs="+", help="JSON objects for narrative contexts")
    parser.add_argument("--narrative-file", help="JSON file with method-level narrative definitions (array or single object)")
    parser.add_argument("--merge-assets", action="store_true",
                        help="Include merged assets from all practices in method-level assets array")

    args = parser.parse_args()

    method = build_method(args)

    citation_names = {c["name"] for c in method.get("citations", [])}
    warnings = []
    for narr in method.get("narratives", []):
        for cname in narr.get("citationNames", []):
            if cname not in citation_names:
                warnings.append(f"Narrative '{narr.get('name', '?')}' references unknown citation '{cname}'")

    with open(args.output, "w") as f:
        json.dump(method, f, indent=2, ensure_ascii=False)

    practice_names = [p["name"] for p in method["practices"]]
    total_alphas = sum(len(p.get("alphas", [])) for p in method["practices"])
    total_activities = sum(len(p.get("activities", [])) for p in method["practices"])
    total_wps = sum(len(p.get("workProducts", [])) for p in method["practices"])

    print(f"Method '{method['name']}' assembled successfully.")
    print(f"  Practices: {len(practice_names)} ({', '.join(practice_names)})")
    print(f"  Total alphas: {total_alphas}")
    print(f"  Total activities: {total_activities}")
    print(f"  Total work products: {total_wps}")
    print(f"  Merged citations: {len(method['citations'])}")
    print(f"  Merged assets: {len(method['assets'])}")
    print(f"  Output: {args.output}")
    for w in warnings:
        print(f"  WARNING: {w}")


if __name__ == "__main__":
    main()
