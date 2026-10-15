#!/usr/bin/env python3
"""Reconcile forward references between phase outputs produced in parallel.

When Phase 2 mapping agents run concurrently, each one references sibling
practices' alphas and states by predicted name -- it cannot see what the other
agents actually chose. Once all guides land, those predictions must be renamed
to the real names before Phase 3, or the generated JSON carries dangling
references.

This applies a rename map across one or more files, reporting per-file hit
counts so an unexpected zero (the rename did not apply) or an unexpected
spike (the term collided with unrelated prose) is visible rather than silent.

Usage:
    # Report what would change
    python3 utils/reconcile-cross-references.py practices/my-method/*.md \
        --map renames.json --dry-run

    # Apply
    python3 utils/reconcile-cross-references.py practices/my-method/*.md \
        --map renames.json --fix

    # Verify no predicted names survive anywhere
    python3 utils/reconcile-cross-references.py practices/my-method/*.md \
        --map renames.json --verify

Map file format -- a JSON list, longest `from` applied first so that a rename
whose target contains the source string cannot be partially re-applied:

    [
      {"from": "Red Hat AI Platform Certification", "to": "GPU Stack Certification",
       "kind": "alpha", "note": "practice 2 named it differently"},
      {"from": "Topology Validated", "to": "Topology Validated Against Serving Configuration",
       "kind": "state"}
    ]
"""

import argparse
import json
import re
import sys


def load_map(path):
    with open(path, "r", encoding="utf-8") as f:
        entries = json.load(f)

    if not isinstance(entries, list):
        raise ValueError("Map file must contain a JSON list of {from, to} objects.")

    for i, e in enumerate(entries):
        if not e.get("from") or not e.get("to"):
            raise ValueError(f"Entry {i}: both 'from' and 'to' are required.")
        # Identity entries are legitimate: they pin an already-correct long form
        # so a shorter rename that is its prefix cannot append the suffix twice.

    # Longest first so the single-pass alternation prefers the most specific
    # match: with "Topology Validated" and "Topology Validated Against Serving
    # Configuration" both present, the long form must win at a shared position.
    return sorted(entries, key=lambda e: len(e["from"]), reverse=True)


def apply_map(content, entries):
    """Return (new_content, {from: count}).

    Replacements run in a SINGLE regex pass with longest-first alternation, so
    each character position is rewritten at most once. Sequential str.replace
    calls would corrupt any rename whose target contains its own source -- e.g.
    "Topology Validated" -> "Topology Validated Against Serving Configuration"
    would re-match its own output and append the suffix repeatedly, and would
    also wreck occurrences of the long form that were already correct.
    """
    counts = {e["from"]: 0 for e in entries}
    lookup = {e["from"]: e["to"] for e in entries}
    pattern = re.compile("|".join(re.escape(e["from"]) for e in entries))

    def _sub(match):
        src = match.group(0)
        counts[src] += 1
        return lookup[src]

    return pattern.sub(_sub, content), counts


def apply_map_to_properties(data, entries, properties):
    """Rename exact-match values of named JSON properties. Returns counts.

    Textual replacement is right for a markdown guide and wrong for a JSON
    document: a symbolic reference is a whole value, and rewriting every
    mention of the string also rewrites the prose that happens to discuss it.
    `"STAR"` names a narrative type in `narrativeTypeName` and is an ordinary
    word in a description.

    `properties` entries are either a bare property name, matched anywhere in
    the document, or `array.field`, matched only on objects directly inside
    that array — which is how the defining element is renamed alongside the
    references to it.
    """
    counts = {e["from"]: 0 for e in entries}
    lookup = {e["from"]: e["to"] for e in entries}
    plain = {p for p in properties if "." not in p}
    scoped = {}
    for p in properties:
        if "." in p:
            array, _, field = p.partition(".")
            scoped.setdefault(array, set()).add(field)

    def rename(value):
        if isinstance(value, str) and value in lookup and lookup[value] != value:
            counts[value] += 1
            return lookup[value]
        return value

    def walk(node, array_context=None):
        if isinstance(node, dict):
            for key, value in list(node.items()):
                if key in plain:
                    node[key] = rename(value)
                elif array_context and key in scoped.get(array_context, ()):
                    node[key] = rename(value)
                walk(value, array_context)
        elif isinstance(node, list):
            for item in node:
                walk(item, array_context)

    if isinstance(data, dict):
        for key, value in data.items():
            walk(value, key if key in scoped else None)
    else:
        walk(data)
    return counts


def main():
    parser = argparse.ArgumentParser(
        description="Reconcile predicted cross-practice references in phase outputs"
    )
    parser.add_argument("file", nargs="+", help="Markdown or JSON files to reconcile")
    parser.add_argument("--map", required=True, help="JSON rename map file")

    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--fix", action="store_true", help="Apply the renames in place")
    mode.add_argument("--dry-run", action="store_true", help="Report hits without writing")
    mode.add_argument(
        "--verify",
        action="store_true",
        help="Exit 1 if any 'from' name still appears (post-fix gate)",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    parser.add_argument(
        "--property", dest="properties", action="append", metavar="NAME",
        help="Rename exact-match values of this JSON property rather than every "
             "textual occurrence. Repeatable. Use 'array.field' to scope to "
             "objects directly inside a top-level array, which is how a defining "
             "element is renamed alongside the references to it. Required for "
             "JSON documents where the name is also an ordinary word",
    )

    args = parser.parse_args()

    try:
        entries = load_map(args.map)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"error": str(exc)}))
        sys.exit(1)

    results = []
    total_hits = 0

    for path in args.file:
        try:
            with open(path, "r", encoding="utf-8") as f:
                original = f.read()
        except OSError as exc:
            results.append({"file": path, "error": str(exc)})
            continue

        if args.properties:
            try:
                data = json.loads(original)
            except json.JSONDecodeError as exc:
                results.append({"file": path, "error": f"--property needs JSON: {exc}"})
                continue
            counts = apply_map_to_properties(data, entries, args.properties)
            updated = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
        else:
            updated, counts = apply_map(original, entries)

        hits = {k: v for k, v in counts.items() if v}
        total_hits += sum(hits.values())

        if args.fix and sum(hits.values()):
            with open(path, "w", encoding="utf-8") as f:
                f.write(updated)

        results.append({"file": path, "hits": hits, "total": sum(hits.values())})

    unresolved = [r for r in results if args.verify and r.get("total")]

    if args.json:
        print(json.dumps({"mode": _mode(args), "totalHits": total_hits,
                          "results": results, "unresolved": len(unresolved)}, indent=2))
    else:
        for r in results:
            if "error" in r:
                print(f"ERROR {r['file']}: {r['error']}")
                continue
            if not r["total"]:
                print(f"  --  {r['file']}: no predicted names found")
                continue
            detail = ", ".join(f"{k} x{v}" for k, v in r["hits"].items())
            verb = "renamed" if args.fix else "found"
            print(f"  {r['total']:>3} {r['file']}: {verb} -- {detail}")
        print(f"\n{_mode(args)}: {total_hits} occurrence(s) across {len(args.file)} file(s)")

    if args.verify and total_hits:
        sys.exit(1)
    sys.exit(0)


def _mode(args):
    return "fix" if args.fix else ("verify" if args.verify else "dry-run")


if __name__ == "__main__":
    main()
