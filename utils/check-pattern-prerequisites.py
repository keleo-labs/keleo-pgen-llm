#!/usr/bin/env python3
"""Check pattern views against the alpha-state prerequisite graph.

A pattern view declares the alpha states that hold at that point in the
lifecycle. Each of those states may itself declare prerequisites in
``background.alphaStates``. A view that asserts a state whose prerequisites are
only reached by a *later* view of the same pattern is an inversion: the pattern
claims the state holds before the document says it can.

The prerequisite graph is built across every document supplied, because state
redeclaration is additive — a practice redeclaring a baseline or dependency
state contributes extra prerequisites rather than replacing them. Pass the
practice plus its baseline and dependencies to see the merged picture, or the
practice alone to see only what one document can prove.

Usage:
    python3 utils/check-pattern-prerequisites.py <practice>.json \\
        [<baseline>.json <dependency>.json ...] \\
        [--pattern "Name"] [--matrix] [--json]

Exit status is 1 when an inversion is found, 0 otherwise.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils._shared import load_json


def iter_documents(data):
    """Yield the practice-shaped objects inside a document."""
    yield data
    for practice in data.get("practices", []):
        if isinstance(practice, dict):
            yield practice


def build_prerequisites(documents):
    """Merge state prerequisites across documents.

    Returns {(alphaName, stateName): {"prereqs": set[(alpha, state)],
                                      "sources": set[str]}}
    """
    merged = {}
    for doc_name, data in documents:
        for source in iter_documents(data):
            for alpha in source.get("alphas", []):
                aname = alpha.get("name")
                if not aname:
                    continue
                for state in alpha.get("states", []):
                    sname = state.get("name")
                    if not sname:
                        continue
                    entry = merged.setdefault(
                        (aname, sname), {"prereqs": set(), "sources": set()}
                    )
                    entry["sources"].add(doc_name)
                    background = state.get("background") or {}
                    for req in background.get("alphaStates", []):
                        ra, rs = req.get("alphaName"), req.get("stateName")
                        if ra and rs:
                            entry["prereqs"].add((ra, rs))
    return merged


def build_state_order(documents):
    """Return {alphaName: [stateName, ...]} using the first document to declare it."""
    order = {}
    for _, data in documents:
        for source in iter_documents(data):
            for alpha in source.get("alphas", []):
                aname = alpha.get("name")
                if not aname or aname in order:
                    continue
                names = [s.get("name") for s in alpha.get("states", []) if s.get("name")]
                if names:
                    order[aname] = names
    return order


def sorted_views(pattern):
    return sorted(pattern.get("patternViews", []), key=lambda v: v.get("seq", 0))


def first_reached(views, prereqs_index):
    """Return {(alpha, state): view_index} for the earliest view declaring it.

    A view also implicitly carries every earlier state of an alpha it has
    already advanced past, so an earlier state counts as reached at the view
    that first declared any state at or beyond it.
    """
    reached = {}
    for idx, view in enumerate(views):
        for astate in view.get("alphaStates", []):
            key = (astate.get("alphaName"), astate.get("stateName"))
            if key[0] and key[1] and key not in reached:
                reached[key] = idx
    return reached


def earliest_satisfaction(alpha, state, reached, state_order):
    """Earliest view index at which (alpha, state) can be considered reached.

    A later state of the same alpha implies the earlier one has been passed, so
    reaching ``Executing`` at view 2 satisfies a prerequisite of ``Approved``.
    Returns None when no view of the pattern reaches it.
    """
    order = state_order.get(alpha, [])
    if state not in order:
        return reached.get((alpha, state))
    want = order.index(state)
    best = None
    for idx, sname in enumerate(order):
        if idx < want:
            continue
        hit = reached.get((alpha, sname))
        if hit is not None and (best is None or hit < best):
            best = hit
    return best


def check_pattern(pattern, prereqs, state_order, entry_view_is_prerequisites=True):
    views = sorted_views(pattern)
    reached = first_reached(views, prereqs)
    findings = []
    for idx, view in enumerate(views):
        for astate in view.get("alphaStates", []):
            alpha = astate.get("alphaName")
            state = astate.get("stateName")
            if not alpha or not state:
                continue
            entry = prereqs.get((alpha, state))
            if not entry:
                continue
            for ra, rs in sorted(entry["prereqs"]):
                sat = earliest_satisfaction(ra, rs, reached, state_order)
                if sat is None:
                    findings.append({
                        "pattern": pattern.get("name"),
                        "viewSeq": view.get("seq"),
                        "viewName": view.get("name"),
                        "state": f"{alpha}.{state}",
                        "prerequisite": f"{ra}.{rs}",
                        "kind": "unreached",
                        "detail": "no view of this pattern reaches the prerequisite",
                    })
                elif sat > idx:
                    findings.append({
                        "pattern": pattern.get("name"),
                        "viewSeq": view.get("seq"),
                        "viewName": view.get("name"),
                        "state": f"{alpha}.{state}",
                        "prerequisite": f"{ra}.{rs}",
                        "kind": "inverted",
                        "detail": (
                            f"prerequisite first reached at view "
                            f"{views[sat].get('seq')} '{views[sat].get('name')}'"
                        ),
                    })
    return findings


def check_monotonicity(pattern, state_order):
    """Flag an alpha whose declared state goes backwards across views."""
    views = sorted_views(pattern)
    findings = []
    last = {}
    for view in views:
        for astate in view.get("alphaStates", []):
            alpha = astate.get("alphaName")
            state = astate.get("stateName")
            order = state_order.get(alpha, [])
            if not alpha or state not in order:
                continue
            idx = order.index(state)
            prev = last.get(alpha)
            if prev is not None and idx < prev[0]:
                findings.append({
                    "pattern": pattern.get("name"),
                    "viewSeq": view.get("seq"),
                    "viewName": view.get("name"),
                    "state": f"{alpha}.{state}",
                    "kind": "regression",
                    "detail": f"follows {alpha}.{prev[1]} at view {prev[2]}",
                })
            if prev is None or idx >= prev[0]:
                last[alpha] = (idx, state, view.get("seq"))
    return findings


def print_matrix(pattern, state_order):
    views = sorted_views(pattern)
    alphas = []
    for view in views:
        for astate in view.get("alphaStates", []):
            if astate.get("alphaName") and astate["alphaName"] not in alphas:
                alphas.append(astate["alphaName"])
    header = ["Alpha"] + [f"{v.get('seq')} {v.get('name')}" for v in views]
    rows = []
    for alpha in sorted(alphas):
        row = [alpha]
        for view in views:
            cells = [
                a.get("stateName")
                for a in view.get("alphaStates", [])
                if a.get("alphaName") == alpha
            ]
            row.append(", ".join(cells) if cells else "-")
        rows.append(row)
    widths = [max(len(r[i]) for r in [header] + rows) for i in range(len(header))]
    def line(cells):
        return " | ".join(c.ljust(widths[i]) for i, c in enumerate(cells))
    print(line(header))
    print("-+-".join("-" * w for w in widths))
    for row in rows:
        print(line(row))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("documents", nargs="+",
                    help="Practice JSON first, then baseline and dependencies")
    ap.add_argument("--pattern", action="append",
                    help="Limit to named pattern(s); repeatable")
    ap.add_argument("--matrix", action="store_true",
                    help="Print the view-by-view alpha state matrix")
    ap.add_argument("--json", dest="as_json", action="store_true",
                    help="Emit findings as JSON")
    args = ap.parse_args()

    documents = []
    for path in args.documents:
        data = load_json(path)
        if data is None:
            print(f"ERROR: could not load {path}", file=sys.stderr)
            return 2
        documents.append((Path(path).name, data))

    prereqs = build_prerequisites(documents)
    state_order = build_state_order(documents)

    primary = documents[0][1]
    findings = []
    for source in iter_documents(primary):
        for pattern in source.get("patterns", []):
            if args.pattern and pattern.get("name") not in args.pattern:
                continue
            if args.matrix:
                print(f"\n== {pattern.get('name')} ==")
                print_matrix(pattern, state_order)
            findings.extend(check_pattern(pattern, prereqs, state_order))
            findings.extend(check_monotonicity(pattern, state_order))

    if args.as_json:
        print(json.dumps(findings, indent=2))
    else:
        if not findings:
            print("\nNo prerequisite inversions or state regressions found.")
        for f in findings:
            print(f"\n[{f['kind']}] {f['pattern']} view {f['viewSeq']} "
                  f"'{f['viewName']}'")
            print(f"  state: {f['state']}")
            if "prerequisite" in f:
                print(f"  requires: {f['prerequisite']}")
            print(f"  {f['detail']}")

    return 1 if any(f["kind"] != "unreached" for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
