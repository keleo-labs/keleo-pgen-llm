#!/usr/bin/env python3
"""
Unified Context Resolver

Produces a single effective context document from a mix of baselines,
practices, and methods (including .keleo bundles). Every element is
annotated with _contributingPracticeName so the mapping agent knows
provenance without cross-referencing multiple files.

Usage:
    # Baseline + practice JSON files
    python3 utils/resolve-context.py baseline.json practice.json -o _effective-context.json

    # .keleo bundle (extracts all documents from the archive)
    python3 utils/resolve-context.py bundles/method.keleo -o _effective-context.json

    # Mixed inputs with transitive baseline resolution
    python3 utils/resolve-context.py baseline.json parent.keleo --transitive -o _effective-context.json

    # Resolve by document name (searches practices/, baselines/, deps/, bundles/)
    python3 utils/resolve-context.py --by-name "CRM Foundations" "MEDDPICC Qualification" --transitive -o context.json

    # Check-only mode (metadata report, no output file)
    python3 utils/resolve-context.py baseline.json --check-only

    # Describe the output JSON structure
    python3 utils/resolve-context.py --describe-output

Merge hierarchy (higher tiers override lower on name conflicts):
    Tier 1: Baselines (root-first topological sort)
    Tier 2: Practices (input order)
    Tier 3: Methods (highest precedence)

Exit codes:
    0 - Success
    1 - Error (missing files, invalid JSON, etc.)

Outputs structured JSON report to stdout.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils._shared import (
    detect_kind,
    finalize_variants,
    load_all_from_keleo,
    load_json,
    merge_by_name,
    merge_pattern_groups,
    MERGEABLE_ARRAYS,
)


def load_inputs(file_paths):
    """Load all input documents, extracting from .keleo bundles as needed.

    Returns list of (source_label, data_dict) tuples.
    """
    documents = []
    for path in file_paths:
        p = Path(path)
        if p.suffix == ".keleo":
            docs, err = load_all_from_keleo(str(p))
            if err:
                print(json.dumps({"error": err}))
                sys.exit(1)
            for doc in docs:
                name = doc.get("name", p.stem)
                documents.append((name, doc))
        else:
            data = load_json(p)
            name = data.get("name", p.stem)
            documents.append((name, data))
    return documents


def classify_documents(documents):
    """Sort documents into three tiers: baselines, practices, methods.

    For methods with embedded practices, extracts them into the practice tier.
    Returns dict with 'baselines', 'practices', 'methods' keys,
    each a list of (name, data) tuples.
    """
    tiers = {"baselines": [], "practices": [], "methods": []}
    seen_names = set()

    for name, data in documents:
        if name in seen_names:
            continue
        seen_names.add(name)

        kind = detect_kind(data)
        if kind == "practiceBaseline":
            tiers["baselines"].append((name, data))
        elif kind == "practice":
            tiers["practices"].append((name, data))
        elif kind == "method":
            for practice in data.get("practices", []):
                p_name = practice.get("name", "")
                if p_name and p_name not in seen_names:
                    seen_names.add(p_name)
                    tiers["practices"].append((p_name, practice))
            tiers["methods"].append((name, data))

    return tiers


def topo_sort_baselines(baselines):
    """Topologically sort baselines by baselinePracticeNames (root-first, leaf-last)."""
    by_name = {name: data for name, data in baselines}
    sorted_names = []
    resolved = set()

    def resolve(name):
        if name in resolved or name not in by_name:
            return
        data = by_name[name]
        for dep_name in data.get("baselinePracticeNames", []):
            resolve(dep_name)
        singular = data.get("baselinePracticeName")
        if singular and singular not in resolved and singular in by_name:
            resolve(singular)
        resolved.add(name)
        sorted_names.append(name)

    for name, _ in baselines:
        resolve(name)

    return [(name, by_name[name]) for name in sorted_names]


def _load_discover_module():
    """Import discover-dependencies.py (hyphenated filename requires importlib)."""
    import importlib.util

    module_path = Path(__file__).resolve().parent / "discover-dependencies.py"
    spec = importlib.util.spec_from_file_location("discover_dependencies", module_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def resolve_transitive_baselines(baselines, search_dirs):
    """Discover and add transitive baseline dependencies."""
    dd = _load_discover_module()
    index, _ = dd.build_index(search_dirs)
    existing = {name for name, _ in baselines}
    to_check = list(baselines)
    result = list(baselines)

    while to_check:
        name, data = to_check.pop(0)
        dep_names = list(data.get("baselinePracticeNames", []))
        singular = data.get("baselinePracticeName")
        if singular and singular not in dep_names:
            dep_names.append(singular)
        for dep_name in dep_names:
            if dep_name in existing:
                continue
            match = dd.resolve_name(dep_name, index, prefer_filesystem=True)
            if match["status"] == "found":
                dep_data, err = dd.load_resolved_json(match)
                if dep_data:
                    existing.add(dep_name)
                    result.append((dep_name, dep_data))
                    to_check.append((dep_name, dep_data))

    return result


def merge_tier(accumulated, entries):
    """Merge a list of (name, data) entries onto accumulated using annotated merge."""
    for source_name, data in entries:
        for key in MERGEABLE_ARRAYS:
            items = data.get(key, [])
            acc_items = accumulated.get(key, [])
            if items or acc_items:
                acc_source = accumulated.get("_merge_source", "")
                if key == "patternGroups":
                    accumulated[key] = merge_pattern_groups(
                        acc_items, items, acc_source, source_name
                    )
                else:
                    accumulated[key] = merge_by_name(
                        acc_items, items, acc_source, source_name
                    )
        accumulated["_merge_source"] = source_name
    return accumulated


def collect_aliases(documents):
    """Collect all practiceElementAliases from a list of (name, data) tuples."""
    aliases = []
    for _, data in documents:
        aliases.extend(data.get("practiceElementAliases", []))
        for practice in data.get("practices", []):
            aliases.extend(practice.get("practiceElementAliases", []))
    return aliases


def apply_alias_context(effective, aliases):
    """Add _aliasContext and _domainAlias annotations."""
    if not aliases:
        return effective

    alias_context = {
        "description": (
            "Domain-specific terminology from context sources. "
            "Use these terms for semantic understanding during analysis and mapping. "
            "Always use canonical names (canonicalName) in structural references "
            "(contributesTo, alphaName, stateName, competencyName, etc.)."
        ),
        "aliases": [
            {
                "type": a.get("practiceElementType", ""),
                "canonicalName": a.get("practiceElementName", ""),
                "domainName": a.get("aliasName", ""),
            }
            for a in aliases
        ],
    }
    effective["_aliasContext"] = alias_context

    alias_lookup = {}
    for a in aliases:
        element_type = a.get("practiceElementType", "")
        canonical = a.get("practiceElementName", "")
        domain = a.get("aliasName", "")
        alias_lookup.setdefault(element_type, {})[canonical] = domain

    type_to_array = {
        "Alpha": "alphas",
        "ActivitySpace": "activitySpaces",
        "Competency": "competencies",
        "Focus": "focuses",
        "NarrativeType": "narrativeTypes",
        "Narrative": "narratives",
        "WorkProduct": "workProducts",
        "Pattern": "patterns",
        "Persona": "personas",
        "PersonaGroup": "personaGroups",
        "Outcome": "outcomes",
    }

    for element_type, array_key in type_to_array.items():
        if element_type in alias_lookup and array_key in effective:
            for item in effective[array_key]:
                name = item.get("name", "")
                if name in alias_lookup[element_type]:
                    item["_domainAlias"] = alias_lookup[element_type][name]

    return effective


def build_provenance(effective, merge_order, tiers):
    """Build _provenance manifest from the effective context."""
    element_sources = {}
    for key in MERGEABLE_ARRAYS:
        items = effective.get(key, [])
        if items:
            sources = {}
            for item in items:
                name = item.get("name", "")
                source = item.get("_contributingPracticeName", "")
                if name:
                    sources[name] = source
            if sources:
                element_sources[key] = sources

    return {
        "mergeOrder": merge_order,
        "tiers": {
            "baselines": [name for name, _ in tiers["baselines"]],
            "practices": [name for name, _ in tiers["practices"]],
            "methods": [name for name, _ in tiers["methods"]],
        },
        "elementSources": element_sources,
    }


def resolve_context(file_paths, transitive=False, search_dirs=None):
    """Produce a unified effective context with provenance annotations.

    Returns (effective_context, report_dict).
    """
    if search_dirs is None:
        search_dirs = ["baselines", "practices", "deps", "bundles"]

    documents = load_inputs(file_paths)
    tiers = classify_documents(documents)

    if transitive and tiers["baselines"]:
        tiers["baselines"] = resolve_transitive_baselines(
            tiers["baselines"], search_dirs
        )

    if tiers["baselines"]:
        tiers["baselines"] = topo_sort_baselines(tiers["baselines"])

    effective = {}
    merge_order = []

    if tiers["baselines"]:
        effective = merge_tier(effective, tiers["baselines"])
        merge_order.extend(name for name, _ in tiers["baselines"])

    if tiers["practices"]:
        effective = merge_tier(effective, tiers["practices"])
        merge_order.extend(name for name, _ in tiers["practices"])

    if tiers["methods"]:
        effective = merge_tier(effective, tiers["methods"])
        merge_order.extend(name for name, _ in tiers["methods"])

    effective.pop("_merge_source", None)

    finalize_variants(effective)

    all_docs = tiers["baselines"] + tiers["practices"] + tiers["methods"]
    aliases = collect_aliases(all_docs)
    effective = apply_alias_context(effective, aliases)
    if aliases:
        effective["practiceElementAliases"] = aliases

    provenance = build_provenance(effective, merge_order, tiers)
    effective["_provenance"] = provenance

    source_names = [name for name, _ in all_docs]
    effective["name"] = " + ".join(source_names) if source_names else ""
    effective["description"] = f"Effective context merged from: {', '.join(source_names)}"

    first_doc = all_docs[0][1] if all_docs else {}
    if tiers["baselines"]:
        effective["kind"] = "practiceBaseline"
    elif tiers["practices"]:
        effective["kind"] = "practice"
    else:
        effective["kind"] = first_doc.get("kind", "practice")
    all_authors = []
    all_keywords = []
    latest_updated = ""
    for _, doc in all_docs:
        for a in doc.get("authors", []):
            if a not in all_authors:
                all_authors.append(a)
        all_keywords.extend(doc.get("keywords", []))
        updated = doc.get("updatedAt", "")
        if updated > latest_updated:
            latest_updated = updated
    effective["authors"] = all_authors or first_doc.get("authors", ["Unknown"])
    effective["version"] = first_doc.get("version", "1.0.0")
    effective["createdAt"] = first_doc.get("createdAt", "1970-01-01T00:00:00Z")
    effective["updatedAt"] = latest_updated or first_doc.get("updatedAt", "1970-01-01T00:00:00Z")
    seen_kw = set()
    effective["keywords"] = [k for k in all_keywords if k not in seen_kw and not seen_kw.add(k)]

    report = {
        "success": True,
        "inputCount": len(file_paths),
        "documentCount": len(all_docs),
        "tiers": {
            "baselines": [name for name, _ in tiers["baselines"]],
            "practices": [name for name, _ in tiers["practices"]],
            "methods": [name for name, _ in tiers["methods"]],
        },
        "mergeOrder": merge_order,
        "effectiveContext": {
            "alphaCount": len(effective.get("alphas", [])),
            "activitySpaceCount": len(effective.get("activitySpaces", [])),
            "competencyCount": len(effective.get("competencies", [])),
            "focusCount": len(effective.get("focuses", [])),
            "narrativeTypeCount": len(effective.get("narrativeTypes", [])),
            "workProductCount": len(effective.get("workProducts", [])),
            "patternCount": len(effective.get("patterns", [])),
            "personaCount": len(effective.get("personas", [])),
            "outcomeCount": len(effective.get("outcomes", [])),
            "aliasCount": len(aliases),
        },
    }

    return effective, report


OUTPUT_SCHEMA = {
    "description": "Effective context JSON structure produced by resolve-context.py",
    "topLevelKeys": {
        "alphas": "array — merged alphas from all tiers (each has name, description, states[], contributesTo, relatesTo, etc.)",
        "activitySpaces": "array — baseline activity spaces",
        "competencies": "array — baseline competencies with levels",
        "focuses": "array — baseline focuses (Value, Solution, Endeavor, etc.)",
        "narrativeTypes": "array — baseline narrative types with narrativeElements[]",
        "narratives": "array — practice narratives (named stories on elements)",
        "citations": "array — practice citations",
        "assets": "array — asset definitions",
        "workProducts": "array — practice work products with levels of detail",
        "patterns": "array — practice lifecycle patterns",
        "personas": "array — personas (name, description, aliases[], competencies[])",
        "personaGroups": "array — persona groups (name, description, personaNames[])",
        "workProductInstances": "array — curated work product instances",
        "outcomes": "array — practice-defined measurable value outcomes (name, description, measureDescription, metricContributions, objectiveContributions)",
        "_aliasContext": "object — {description, aliases[]} mapping domainName to canonicalName",
        "practiceElementAliases": "array — raw alias entries from all sources",
        "_provenance": "object — {mergeOrder[], tiers{}, elementSources{}} tracking where each element came from",
        "name": "string — combined name of all merged sources",
        "description": "string — merge summary",
        "kind": "string — practiceBaseline | practice | method",
        "authors": "array — merged author list",
        "version": "string — version from first document",
        "keywords": "array — deduplicated merged keywords",
    },
    "elementAnnotations": {
        "_contributingPracticeName": "string on each merged element — source practice/baseline name",
        "_domainAlias": "string on elements with aliases — the domain-specific name",
    },
}


def _normalize_name(name):
    """Normalize a name for fuzzy matching: lowercase, strip hyphens/underscores, collapse whitespace."""
    import re
    return re.sub(r'\s+', ' ', name.lower().replace('-', ' ').replace('_', ' ')).strip()


def _fuzzy_match(name, index):
    """Find the best fuzzy match for a name in the index.

    Strategy: normalize both sides, try exact match first, then substring containment,
    then word-overlap scoring. Returns the matching index key or None.
    """
    norm_input = _normalize_name(name)
    norm_lookup = {_normalize_name(k): k for k in index}

    if norm_input in norm_lookup:
        return norm_lookup[norm_input]

    containment_matches = []
    for norm_key, orig_key in norm_lookup.items():
        if norm_input in norm_key or norm_key in norm_input:
            containment_matches.append((norm_key, orig_key))
    if len(containment_matches) == 1:
        return containment_matches[0][1]
    if containment_matches:
        containment_matches.sort(key=lambda x: abs(len(x[0]) - len(norm_input)))
        return containment_matches[0][1]

    input_words = set(norm_input.split())
    scored = []
    for norm_key, orig_key in norm_lookup.items():
        key_words = set(norm_key.split())
        overlap = len(input_words & key_words)
        score = overlap / max(len(input_words | key_words), 1)
        if score >= 0.5:
            scored.append((score, abs(len(norm_key) - len(norm_input)), orig_key))
    if scored:
        scored.sort(key=lambda x: (-x[0], x[1]))
        return scored[0][2]
    return None


def resolve_names_to_paths(names, search_dirs):
    """Resolve document names to file paths using discover-dependencies index.

    Uses exact match first, then fuzzy matching (normalized, substring, word-overlap).
    """
    dd = _load_discover_module()
    index, _ = dd.build_index(search_dirs)
    resolved_paths = []
    errors = []
    for name in names:
        match = dd.resolve_name(name, index, prefer_filesystem=True)
        if match["status"] == "not_found":
            fuzzy_key = _fuzzy_match(name, index)
            if fuzzy_key:
                match = dd.resolve_name(fuzzy_key, index, prefer_filesystem=True)

        if match["status"] == "found":
            path = match.get("path", "")
            if "::" in path:
                keleo_path = match.get("keleo_path", path.split("::")[0])
                if keleo_path not in resolved_paths:
                    resolved_paths.append(keleo_path)
            else:
                if path not in resolved_paths:
                    resolved_paths.append(path)
        elif match["status"] == "ambiguous":
            candidates = match.get("candidates", [])
            errors.append(f"Ambiguous name '{name}': {[c.get('path','') for c in candidates]}")
        else:
            errors.append(f"Name '{name}' not found in {search_dirs}")
    return resolved_paths, errors


def filter_effective_context(effective, extract_keys):
    """Return a subset of the effective context containing only the requested element types."""
    filtered = {}
    for key in extract_keys:
        if key in effective:
            filtered[key] = effective[key]
    for meta_key in ("_provenance", "_aliasContext", "name", "description", "kind"):
        if meta_key in effective:
            filtered[meta_key] = effective[meta_key]
    return filtered


def main():
    parser = argparse.ArgumentParser(
        description="Unified context resolver for baselines, practices, methods, and .keleo bundles"
    )
    parser.add_argument(
        "inputs",
        nargs="*",
        help="Input files (.json or .keleo), or document names when --by-name is set.",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output path for the effective context JSON (required unless --check-only or --describe-output)",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Report metadata without producing output",
    )
    parser.add_argument(
        "--by-name",
        action="store_true",
        help="Treat inputs as document names instead of file paths. "
             "Resolves names against --search-dirs using the dependency index.",
    )
    parser.add_argument(
        "--extract",
        nargs="+",
        metavar="KEY",
        help="Output only specified element types (e.g., --extract personas alphas patterns). "
             "Always includes metadata (_provenance, name, kind).",
    )
    parser.add_argument(
        "--describe-output",
        action="store_true",
        help="Print the output JSON schema description and exit.",
    )
    parser.add_argument(
        "--transitive",
        action="store_true",
        help="Auto-resolve transitive baseline dependencies from baselines/, practices/, deps/, bundles/",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite output file without creating a backup",
    )
    parser.add_argument(
        "--search-dirs",
        nargs="+",
        default=["baselines", "practices", "deps", "bundles"],
        help="Override search directories for transitive resolution",
    )

    args = parser.parse_args()

    if args.describe_output:
        print(json.dumps(OUTPUT_SCHEMA, indent=2))
        return

    if not args.inputs:
        parser.error("No inputs provided. Pass file paths, or document names with --by-name.")

    if args.by_name:
        resolved_paths, errors = resolve_names_to_paths(args.inputs, args.search_dirs)
        if errors:
            print(json.dumps({"error": "Name resolution failed", "details": errors}))
            sys.exit(1)
        if not resolved_paths:
            print(json.dumps({"error": "No documents resolved from names", "names": args.inputs}))
            sys.exit(1)
        file_paths = resolved_paths
    else:
        file_paths = args.inputs

    if args.check_only:
        documents = load_inputs(file_paths)
        tiers = classify_documents(documents)
        check_report = {
            "success": True,
            "inputCount": len(file_paths),
            "documentCount": sum(len(v) for v in tiers.values()),
            "tiers": {
                "baselines": [name for name, _ in tiers["baselines"]],
                "practices": [name for name, _ in tiers["practices"]],
                "methods": [name for name, _ in tiers["methods"]],
            },
        }
        if args.by_name:
            check_report["resolvedPaths"] = file_paths
        print(json.dumps(check_report, indent=2))
        return

    if not args.output:
        print(json.dumps({"error": "Output path (-o) required unless --check-only or --describe-output"}))
        sys.exit(1)

    effective, report = resolve_context(
        file_paths,
        transitive=args.transitive,
        search_dirs=args.search_dirs,
    )

    if args.extract:
        effective = filter_effective_context(effective, args.extract)
        report["extractedKeys"] = args.extract

    if args.by_name:
        report["resolvedPaths"] = file_paths

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    backup_path = None
    if output_path.exists() and not args.force:
        backup_path = output_path.with_suffix(".json.bak")
        import shutil
        shutil.copy2(output_path, backup_path)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(effective, f, indent=2, ensure_ascii=False)

    if backup_path and backup_path.exists():
        backup_path.unlink()

    report["outputPath"] = str(output_path)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
