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

``--cycles`` asks a different question of the same graph. Two practices on one
baseline can declare opposing prerequisites between the same pair of states,
and because redeclaration is additive the contradiction exists only in the
union — each document validates clean holding half of it. ``--on-baseline``
sweeps every document whose baseline chain reaches the named one, so the
conflict is found before someone declares a dependency and inherits it.

Usage:
    python3 utils/check-pattern-prerequisites.py <practice>.json \\
        [<baseline>.json <dependency>.json ...] \\
        [--pattern "Name"] [--matrix] [--json]

    python3 utils/check-pattern-prerequisites.py --cycles \\
        --on-baseline "<Baseline Name>" [--json]

Exit status is 1 when an inversion or a contradiction is found, 0 otherwise.
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
                                      "sources": set[str],
                                      "edgeSources": {(alpha, state): set[str]}}}

    ``edgeSources`` records which document declared each prerequisite, which is
    what makes a contradiction attributable: the edge and its opposite are in
    different documents, and neither author can see the other's.
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
                        (aname, sname),
                        {"prereqs": set(), "sources": set(), "edgeSources": {}},
                    )
                    entry["sources"].add(doc_name)
                    background = state.get("background") or {}
                    for req in background.get("alphaStates", []):
                        ra, rs = req.get("alphaName"), req.get("stateName")
                        if ra and rs:
                            entry["prereqs"].add((ra, rs))
                            entry["edgeSources"].setdefault((ra, rs), set()).add(doc_name)
    return merged


def find_prerequisite_cycles(prereqs):
    """Cycles in the merged prerequisite graph, with the author of each edge.

    A practice redeclaring a baseline state contributes prerequisites rather
    than replacing them, so the real graph is the union of what every document
    declared — a graph none of them contains. Two practices can therefore state
    opposing orderings between the same pair of states, and each validates
    clean on its own because each holds only half of the cycle.

    Returns a list of {"cycle": [...], "edges": [{"from", "to", "declaredBy"}]}.
    """
    found = []
    seen_cycles = set()

    def walk(node, path, on_path):
        for nxt in sorted(prereqs.get(node, {}).get("prereqs", ())):
            if nxt in on_path:
                start = path.index(nxt)
                cycle = path[start:] + [nxt]
                key = _canonical_cycle(cycle)
                if key in seen_cycles:
                    continue
                seen_cycles.add(key)
                found.append({
                    "cycle": [f"{a}.{s}" for a, s in cycle],
                    "edges": [
                        {
                            "from": f"{cycle[i][0]}.{cycle[i][1]}",
                            "to": f"{cycle[i + 1][0]}.{cycle[i + 1][1]}",
                            "declaredBy": sorted(
                                prereqs[cycle[i]]["edgeSources"].get(cycle[i + 1], ())
                            ),
                        }
                        for i in range(len(cycle) - 1)
                    ],
                })
                continue
            if nxt in path:
                continue
            walk(nxt, path + [nxt], on_path | {nxt})

    for node in sorted(prereqs):
        walk(node, [node], {node})
    return found


def _canonical_cycle(cycle):
    """A rotation-independent key, so one cycle is not reported once per member."""
    ring = cycle[:-1]
    if not ring:
        return ()
    lowest = min(range(len(ring)), key=lambda i: ring[i])
    return tuple(ring[lowest:] + ring[:lowest])


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


def _declared_baselines(data):
    names = list(data.get("baselinePracticeNames") or [])
    single = data.get("baselinePracticeName")
    if single:
        names.append(single)
    return names


def documents_on_baseline(baseline_name, root=None):
    """Every authored document in the corpus whose baseline chain reaches `baseline_name`.

    Transitively, because most practices sit on an intermediate baseline rather
    than naming the root one — a sweep matching only direct declarations would
    miss the documents most likely to disagree with each other.

    Skips backups and underscore-prefixed build artifacts, matching the rule
    `scan-corpus.py` applies: a merge is not something anyone authored, and a
    contradiction reported against one is not actionable.
    """
    root = Path(root or Path(__file__).resolve().parent.parent)
    corpus = []
    for dirname in ("baselines", "practices", "deps"):
        base = root / dirname
        if not base.is_dir():
            continue
        patterns = ["*.json"] if base.name == "deps" else ["*.json", "*/*.json"]
        for pattern in patterns:
            for path in sorted(base.glob(pattern)):
                if path.name.startswith("_") or "backup" in str(path).lower():
                    continue
                if path.name.endswith(".changerequest.json"):
                    continue
                try:
                    data = load_json(path, exit_on_error=False)
                except Exception:
                    continue
                if isinstance(data, dict):
                    corpus.append((str(path.relative_to(root)), data))

    by_name = {}
    for _, data in corpus:
        by_name.setdefault(data.get("name"), data)

    def reaches(data, depth=0):
        if data.get("name") == baseline_name:
            return True
        if depth > 8:
            return False
        for parent in _declared_baselines(data):
            if parent == baseline_name:
                return True
            upstream = by_name.get(parent)
            if upstream is not None and reaches(upstream, depth + 1):
                return True
        return False

    return [(rel, data) for rel, data in corpus if reaches(data)]


def report_cycles(cycles, as_json):
    if as_json:
        print(json.dumps(cycles, indent=2))
        return 1 if cycles else 0
    if not cycles:
        print("No contradictory prerequisite edges found.")
        return 0
    print(f"{len(cycles)} contradictory prerequisite cycle(s):\n")
    for c in cycles:
        print("  " + " -> ".join(c["cycle"]))
        for edge in c["edges"]:
            authors = ", ".join(edge["declaredBy"]) or "unknown"
            print(f"    {edge['from']} requires {edge['to']}  [{authors}]")
        print()
    return 1


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("documents", nargs="*",
                    help="Practice JSON first, then baseline and dependencies")
    ap.add_argument("--cycles", action="store_true",
                    help="Report contradictory prerequisite edges across the "
                         "documents given, naming the document that declared each")
    ap.add_argument("--on-baseline", metavar="NAME",
                    help="With --cycles, sweep every corpus document building on "
                         "this baseline instead of naming them individually")
    ap.add_argument("--pattern", action="append",
                    help="Limit to named pattern(s); repeatable")
    ap.add_argument("--matrix", action="store_true",
                    help="Print the view-by-view alpha state matrix")
    ap.add_argument("--json", dest="as_json", action="store_true",
                    help="Emit findings as JSON")
    args = ap.parse_args()

    if args.on_baseline:
        if not args.cycles:
            print("ERROR: --on-baseline is only meaningful with --cycles",
                  file=sys.stderr)
            return 2
        documents = documents_on_baseline(args.on_baseline)
        if not documents:
            print(f"ERROR: no documents build on '{args.on_baseline}'",
                  file=sys.stderr)
            return 2
    else:
        if not args.documents:
            print("ERROR: give at least one document, or --on-baseline with --cycles",
                  file=sys.stderr)
            return 2
        documents = []
        for path in args.documents:
            data = load_json(path)
            if data is None:
                print(f"ERROR: could not load {path}", file=sys.stderr)
                return 2
            documents.append((Path(path).name, data))

    prereqs = build_prerequisites(documents)

    if args.cycles:
        return report_cycles(find_prerequisite_cycles(prereqs), args.as_json)

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
