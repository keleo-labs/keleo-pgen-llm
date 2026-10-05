#!/usr/bin/env python3
"""List, audit, and remove practiceElementAliases across practice documents.

An alias names what an element IS, as a synonym usable anywhere the element
appears. When an alias is placed on an element that several documents share,
it stops being a synonym and starts asserting one practice's local framing
onto the shared element — e.g. aliasing the root alpha "Platform" as
"Monitoring Infrastructure" from an observability practice.

The audit mode detects exactly that: aliases whose target element is defined
in more than one document within the given scope.

Usage:
    python3 utils/manage-aliases.py --list practices/red-hat-ai/*.json
    python3 utils/manage-aliases.py --audit --scope practices/red-hat-ai/
    python3 utils/manage-aliases.py <file>.json --remove "Persona:Platform Engineer" --fix
    python3 utils/manage-aliases.py --audit --scope practices/red-hat-ai/ --json
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _shared import load_json_pair  # noqa: E402

# practiceElementType -> the document arrays that can define that element
TYPE_TO_ARRAYS = {
    "Alpha": ["alphas"],
    "WorkProduct": ["workProducts"],
    "Activity": ["activities"],
    "ActivitySpace": ["activitySpaces"],
    "Persona": ["personas"],
    "PersonaGroup": ["personaGroups"],
    "Pattern": ["patterns"],
    "PatternGroup": ["patternGroups"],
    "Outcome": ["outcomes"],
    "NarrativeType": ["narrativeTypes"],
    "Competency": ["competencies"],
    "Focus": ["focuses"],
    "Citation": ["citations"],
}


def iter_documents(path):
    """Yield (path, data) for a JSON file, or for every eligible JSON in a directory."""
    p = Path(path)
    if p.is_dir():
        # One level down too, so `practices/` covers every practice directory.
        candidates = sorted(set(p.glob("*.json")) | set(p.glob("*/*.json")))
    else:
        candidates = [p]

    for candidate in candidates:
        if candidate.name.startswith("_"):
            continue
        if "backup" in str(candidate).lower():
            continue
        if candidate.name.endswith(".changerequest.json"):
            continue
        data, err = load_json_pair(candidate)
        if err or not isinstance(data, dict):
            continue
        yield candidate, data


def defines_element(data, element_type, element_name):
    """True if this document defines (or redeclares) the named element."""
    for array_name in TYPE_TO_ARRAYS.get(element_type, []):
        for item in data.get(array_name, []) or []:
            if isinstance(item, dict) and item.get("name") == element_name:
                return True
    return False


def collect_aliases(documents):
    """Flatten every alias across the given (path, data) pairs."""
    rows = []
    for path, data in documents:
        for alias in data.get("practiceElementAliases", []) or []:
            rows.append({
                "file": str(path),
                "document": data.get("name", path.name),
                "practiceElementType": alias.get("practiceElementType", ""),
                "practiceElementName": alias.get("practiceElementName", ""),
                "aliasName": alias.get("aliasName", ""),
            })
    return rows


def audit(documents, ignore_baseline_aliases=False):
    """Flag aliases whose target element is defined in more than one document.

    A baseline aliasing an element it redeclares from its parent baseline is
    establishing domain vocabulary for everything beneath it, which is the
    point of a baseline — `--ignore-baseline-aliases` excludes those so only
    practice-level narrowing is reported.
    """
    documents = list(documents)
    baseline_docs = {
        data.get("name")
        for _, data in documents
        if data.get("kind") == "practiceBaseline"
    }
    rows = collect_aliases(documents)

    owners = defaultdict(list)
    for path, data in documents:
        for row in rows:
            key = (row["practiceElementType"], row["practiceElementName"])
            if key in owners and str(path) in owners[key]:
                continue
            if defines_element(data, *key):
                owners[key].append(data.get("name", path.name))

    findings = []
    for row in rows:
        key = (row["practiceElementType"], row["practiceElementName"])
        definers = sorted(set(owners.get(key, [])))
        shared = len(definers) > 1
        from_baseline = row["document"] in baseline_docs
        if shared and from_baseline and ignore_baseline_aliases:
            shared = False
        findings.append({
            **row,
            "definedIn": definers,
            "shared": shared,
            "fromBaseline": from_baseline,
            "verdict": "scope-narrowing" if shared else "local-synonym",
        })
    return findings


def remove_aliases(data, targets):
    """Drop aliases matching 'Type:Name' targets. Returns (new_list, removed)."""
    existing = data.get("practiceElementAliases", []) or []
    kept, removed = [], []
    for alias in existing:
        key = f"{alias.get('practiceElementType', '')}:{alias.get('practiceElementName', '')}"
        if key in targets:
            removed.append(alias)
        else:
            kept.append(alias)
    return kept, removed


def main():
    parser = argparse.ArgumentParser(
        description="List, audit, and remove practiceElementAliases"
    )
    parser.add_argument("files", nargs="*", help="Practice JSON file(s) to operate on")
    parser.add_argument("--list", action="store_true", help="List aliases")
    parser.add_argument(
        "--audit", action="store_true",
        help="Flag aliases on elements shared by multiple documents in --scope",
    )
    parser.add_argument(
        "--scope", action="append",
        help="File or directory defining the comparison set for --audit (repeatable)",
    )
    parser.add_argument(
        "--remove", action="append", metavar="TYPE:NAME",
        help="Remove the alias on this element, e.g. 'Persona:Platform Engineer' (repeatable)",
    )
    parser.add_argument(
        "--ignore-baseline-aliases", action="store_true",
        help="Exclude aliases declared by a baseline (domain vocabulary, not narrowing)",
    )
    parser.add_argument("--fix", action="store_true", help="Write changes to disk")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    args = parser.parse_args()

    if args.audit:
        scope = args.scope or args.files
        if not scope:
            parser.error("--audit requires --scope or file arguments")
        documents = [d for s in scope for d in iter_documents(s)]
        findings = audit(documents, args.ignore_baseline_aliases)

        if args.json:
            print(json.dumps({
                "aliasesAudited": len(findings),
                "scopeNarrowing": sum(1 for f in findings if f["shared"]),
                "findings": findings,
            }, indent=2))
        else:
            narrowing = [f for f in findings if f["shared"]]
            print(f"=== Alias Audit ({len(findings)} aliases across {len(documents)} documents) ===\n")
            for f in sorted(findings, key=lambda x: (not x["shared"], x["document"])):
                mark = "NARROWING" if f["shared"] else "ok       "
                print(f"  {mark} [{f['document']}] "
                      f"{f['practiceElementType']} {f['practiceElementName']!r} "
                      f"-> {f['aliasName']!r}")
                if f["shared"]:
                    print(f"            shared by: {', '.join(f['definedIn'])}")
            print(f"\n--- Summary ---\nScope-narrowing aliases: {len(narrowing)}")
        return 1 if any(f["shared"] for f in findings) else 0

    if not args.files:
        parser.error("file arguments are required")

    documents = [d for f in args.files for d in iter_documents(f)]

    if args.remove:
        targets = set(args.remove)
        total = 0
        for path, data in documents:
            kept, removed = remove_aliases(data, targets)
            if not removed:
                continue
            total += len(removed)
            print(f"{'REMOVE' if args.fix else 'WOULD REMOVE'} in {path}:")
            for alias in removed:
                print(f"  {alias.get('practiceElementType')} "
                      f"{alias.get('practiceElementName')!r} -> {alias.get('aliasName')!r}")
            if args.fix:
                if kept:
                    data["practiceElementAliases"] = kept
                else:
                    data.pop("practiceElementAliases", None)
                with open(path, "w", encoding="utf-8") as fh:
                    json.dump(data, fh, indent=2, ensure_ascii=False)
                    fh.write("\n")
        print(f"\nTotal aliases {'removed' if args.fix else 'matched'}: {total}")
        if not args.fix and total:
            print("Re-run with --fix to apply.")
        return 0

    # default: list
    rows = collect_aliases(documents)
    if args.json:
        print(json.dumps({"aliases": rows}, indent=2))
    else:
        by_doc = defaultdict(list)
        for row in rows:
            by_doc[row["document"]].append(row)
        for doc in sorted(by_doc):
            print(f"=== {doc} ({len(by_doc[doc])}) ===")
            for row in by_doc[doc]:
                print(f"  {row['practiceElementType']}: "
                      f"{row['practiceElementName']!r} -> {row['aliasName']!r}")
            print()
        print(f"Total aliases: {len(rows)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
