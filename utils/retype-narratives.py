#!/usr/bin/env python3
"""Retype narratives from one narrative type to another, relabelling their contexts.

Phase 3 agents routinely type a narrative against the leaf baseline's narrative
list rather than the type the mapping guide specifies — carrying the guide's prose
over verbatim but relabelling it onto the wrong elements, so explanatory body text
ends up under "Task" and procedural steps under "The Call to Adventure". The prose
is right and only the labels are wrong, which makes the correction mechanical:
re-point narrativeTypeName and relabel each context onto the target type's
elements in order.

Context names are remapped positionally by seq, because that is how the
mis-typing happened — the generator walked the guide's contexts in order and
wrote them against whatever element list it had. An explicit elementMap overrides
this where the order is not one-to-one.

Usage:
    # Dry run across the whole document
    python3 utils/retype-narratives.py practice.json --context _effective-context.json \
        --spec '[{"fromType": "The STAR Format", "toType": "Essay"}]'

    # Restrict to named elements, and apply
    python3 utils/retype-narratives.py practice.json --context _effective-context.json \
        --spec-file retype.json --fix

Spec format (array of operations):
    [
      {
        "fromType": "The STAR Format",
        "toType": "Essay",
        "only": ["Workload Migration", "Migration Team"],     # optional element-name filter
        "elementMap": {"Situation": "Introduction"}           # optional explicit relabel
      }
    ]
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils._shared import load_json, load_json_pair

# Element collections that can carry narratives, with the owning element's name
# used for the --only filter and for reporting.
NARRATIVE_HOSTS = [
    "alphas",
    "activities",
    "workProducts",
    "personas",
    "personaGroups",
    "patterns",
    "outcomes",
    "activitySpaces",
    "competencies",
]


def collect_narrative_types(context_data):
    """Map narrative type name → ordered element names, from a context document."""
    types = {}
    for nt in context_data.get("narrativeTypes", []):
        name = nt.get("name")
        if not name:
            continue
        elements = nt.get("narrativeElements", nt.get("elements", []))
        ordered = []
        for idx, el in enumerate(elements):
            if isinstance(el, str):
                ordered.append((idx, el))
            elif isinstance(el, dict) and el.get("name"):
                ordered.append((el.get("seq", idx), el["name"]))
        ordered.sort(key=lambda t: t[0])
        types[name] = [name_ for _, name_ in ordered]
    return types


def iter_narratives(data):
    """Yield (host_collection, element_name, narrative) for every narrative in a document.

    Covers the document root and each practice of a method, so one spec applies
    uniformly whether it is pointed at a practice or at a method.
    """
    roots = [data] + [p for p in data.get("practices", []) if isinstance(p, dict)]
    for root in roots:
        for narrative in root.get("narratives", []) or []:
            yield "(document)", root.get("name", "?"), narrative
        for collection in NARRATIVE_HOSTS:
            for element in root.get(collection, []) or []:
                if not isinstance(element, dict):
                    continue
                for narrative in element.get("narratives", []) or []:
                    yield collection, element.get("name", "?"), narrative


def build_element_map(op, narrative, source_elements, target_elements):
    """Decide the from→to context relabelling for one narrative.

    Returns (mapping, error). Positional by default: the contexts actually used,
    in seq order, onto the target type's elements in order. A narrative using more
    contexts than the target type has elements is an error rather than a guess —
    dropping prose silently is worse than stopping.
    """
    explicit = op.get("elementMap") or {}
    contexts = sorted(
        narrative.get("narrativeContexts", []) or [],
        key=lambda c: c.get("seq", 0),
    )
    if not contexts:
        return {}, None

    mapping = {}
    unresolved = []
    for idx, ctx in enumerate(contexts):
        current = ctx.get("narrativeElementName", "")
        if current in explicit:
            mapping[current] = explicit[current]
        elif idx < len(target_elements):
            mapping[current] = target_elements[idx]
        else:
            unresolved.append(current)

    if unresolved:
        return None, (
            f"{len(contexts)} context(s) but target type has "
            f"{len(target_elements)} element(s); no mapping for "
            f"{', '.join(repr(u) for u in unresolved)}"
        )
    return mapping, None


def retype(data, spec, narrative_types):
    """Apply retype operations. Returns (changes, errors)."""
    changes = []
    errors = []

    for op_idx, op in enumerate(spec):
        from_type = op.get("fromType")
        to_type = op.get("toType")
        if not from_type or not to_type:
            errors.append(f"spec[{op_idx}]: both 'fromType' and 'toType' are required")
            continue
        if to_type not in narrative_types:
            errors.append(
                f"spec[{op_idx}]: target narrative type '{to_type}' is not defined in "
                f"the context document — retyping to it would produce a dangling reference"
            )
            continue

        target_elements = narrative_types[to_type]
        only = set(op.get("only") or [])
        matched = 0

        for collection, element_name, narrative in iter_narratives(data):
            if narrative.get("narrativeTypeName") != from_type:
                continue
            if only and element_name not in only:
                continue

            mapping, err = build_element_map(
                op, narrative, narrative_types.get(from_type, []), target_elements
            )
            if err:
                errors.append(
                    f"{collection}[{element_name}] narrative "
                    f"'{narrative.get('name', '?')}': {err}"
                )
                continue

            narrative["narrativeTypeName"] = to_type
            relabelled = []
            for ctx in narrative.get("narrativeContexts", []) or []:
                current = ctx.get("narrativeElementName", "")
                if current in mapping and mapping[current] != current:
                    ctx["narrativeElementName"] = mapping[current]
                    relabelled.append(f"{current}→{mapping[current]}")
            matched += 1
            changes.append({
                "collection": collection,
                "element": element_name,
                "narrative": narrative.get("name", "?"),
                "fromType": from_type,
                "toType": to_type,
                "relabelled": relabelled,
            })

        if matched == 0 and not only:
            errors.append(
                f"spec[{op_idx}]: no narratives of type '{from_type}' found — "
                f"the spec may be stale or already applied"
            )

    return changes, errors


def main():
    parser = argparse.ArgumentParser(
        description="Retype narratives to a different narrative type, relabelling contexts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("file", help="Practice, method or baseline JSON file")
    parser.add_argument("--context", required=True,
                        help="Context document defining the narrative types "
                             "(an _effective-context.json or a baseline)")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--spec", help="Inline JSON spec (array of retype operations)")
    group.add_argument("--spec-file", help="Path to a JSON spec file")
    parser.add_argument("--fix", action="store_true",
                        help="Apply changes in place (default: dry run)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    data, err = load_json_pair(args.file)
    if err:
        print(json.dumps({"error": err}))
        sys.exit(1)

    context_data = load_json(args.context)
    narrative_types = collect_narrative_types(context_data)
    if not narrative_types:
        print(json.dumps({
            "error": f"No narrativeTypes defined in {args.context}"
        }))
        sys.exit(1)

    if args.spec:
        try:
            spec = json.loads(args.spec)
        except json.JSONDecodeError as exc:
            print(json.dumps({"error": f"invalid JSON in --spec: {exc}"}))
            sys.exit(1)
    else:
        spec = load_json(args.spec_file)

    if not isinstance(spec, list):
        print(json.dumps({"error": "spec must be a JSON array of operations"}))
        sys.exit(1)

    changes, errors = retype(data, spec, narrative_types)

    if args.fix and not errors:
        with open(args.file, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
            fh.write("\n")

    result = {
        "file": args.file,
        "applied": bool(args.fix and not errors),
        "changeCount": len(changes),
        "changes": changes,
        "errors": errors,
    }

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        mode = "APPLIED" if result["applied"] else "DRY RUN"
        print(f"=== {mode} — {len(changes)} narrative(s) ===")
        for c in changes:
            print(f"  {c['collection']}[{c['element']}] '{c['narrative']}'")
            print(f"      {c['fromType']} → {c['toType']}")
            for r in c["relabelled"]:
                print(f"      context: {r}")
        for e in errors:
            print(f"  ERROR: {e}", file=sys.stderr)
        if errors and not args.fix:
            print("  (no changes applied)", file=sys.stderr)

    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
