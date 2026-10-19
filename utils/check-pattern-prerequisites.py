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

Three orderings look like an inversion and are not, so each is named rather
than reported as a defect:

``entry``
    The first view states the conditions holding before the progression begins
    (Section 9.2 rule 3), so its states were reached outside the pattern and
    nothing can precede them. ``--strict-entry`` judges it like any other view.

``cyclical``
    Inside a ``loopsBackTo`` span the work repeats, and a re-entered view's
    states are the minimum that must hold on that pass rather than a reset
    (Section 9.2a.1). A prerequisite reached later in ``seq`` order was reached
    on an earlier lap.

``ambiguous``
    A view declaring one alpha twice only appears to move backwards. The
    ambiguity is the defect; the regression it implies is suppressed.

``--variant-smell`` asks a question instead of reporting a defect: an alpha
whose states name kinds of the thing rather than stages of it cannot be walked
monotonically by any pattern, and no reordering will fix that. Remodelling the
alpha reaches every document depending on it, so it is raised for mapping to
decide.

``--cycles`` asks a different question of the same graph. Two practices on one
baseline can declare opposing prerequisites between the same pair of states,
and because redeclaration is additive the contradiction exists only in the
union — each document validates clean holding half of it. ``--on-baseline``
sweeps every document whose baseline chain reaches the named one, so the
conflict is found before someone declares a dependency and inherits it.

Usage:
    python3 utils/check-pattern-prerequisites.py <practice>.json \\
        [<baseline>.json <dependency>.json ...] \\
        [--pattern "Name"] [--matrix] [--strict-entry] [--variant-smell] [--json]

    python3 utils/check-pattern-prerequisites.py --cycles \\
        --on-baseline "<Baseline Name>" [--json]

Exit status is 1 on an inversion, a regression, an ambiguous view, or a
prerequisite contradiction; 0 otherwise.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils._shared import load_json


#: Findings that mean the document is wrong, as against ones that explain why
#: the walk looks odd. ``entry`` and ``cyclical`` describe orderings the
#: language permits, ``unreached`` follows from ordinary view compression, and
#: ``variant-smell`` is a question for mapping rather than a defect.
BLOCKING_KINDS = frozenset({"inverted", "regression", "ambiguous"})


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


def add_implicit_order_edges(prereqs, state_order):
    """Add the sequential edge every alpha carries between consecutive states.

    A state is reached by passing through the one before it, so ``seq`` is a
    prerequisite edge the document never writes down. A declared
    ``background.alphaStates`` graph can be acyclic on its explicit edges alone
    and still deadlock once those implicit edges are present, which is the
    graph a reader actually has to satisfy.
    """
    for aname, names in state_order.items():
        for earlier, later in zip(names, names[1:]):
            entry = prereqs.setdefault(
                (aname, later),
                {"prereqs": set(), "sources": set(), "edgeSources": {}},
            )
            entry["prereqs"].add((aname, earlier))
            entry["edgeSources"].setdefault((aname, earlier), set()).add("state order")
    return prereqs


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


def loop_spans(views):
    """View index ranges re-entered by a ``loopsBackTo`` edge.

    Section 9.2a declares a cycle as an edge from the view where it closes back
    to the view it returns to, so the span it re-runs is ``[target, closing]``
    inclusive. Edges are kept separate rather than merged because they compose —
    a build loop inside a release loop is two spans, and collapsing them would
    excuse an ordering neither loop actually permits.

    An edge naming a view at or after its own is not a loop and is ignored here;
    `validate-practice-json.py` owns that as a reference error.
    """
    by_name = {}
    for idx, view in enumerate(views):
        name = view.get("name")
        if name and name not in by_name:
            by_name[name] = idx
    spans = []
    for idx, view in enumerate(views):
        loop = view.get("loopsBackTo") or {}
        target = by_name.get(loop.get("patternViewName"))
        if target is not None and target < idx:
            spans.append((target, idx, loop.get("patternViewName"), view.get("name")))
    return spans


def spanning_loop(spans, *indices):
    """The first loop span covering every index given, or None.

    Two views sit on the same lap only when one span holds both. A state that
    looks out of order across a loop boundary is genuinely out of order; only
    within a lap is the earlier declaration a per-pass minimum rather than a
    step backwards.
    """
    for lo, hi, target_name, closing_name in spans:
        if all(lo <= i <= hi for i in indices):
            return {"from": closing_name, "to": target_name}
    return None


def ambiguous_alphas(views):
    """{view_index: {alphaName: [stateName, ...]}} for alphas declared more than once.

    Schema-wise this is an error `validate-practice-json.py` already reports as
    an ambiguous pattern view. It matters here because the second declaration
    makes the walk appear to move backwards, so a defect of one kind would
    otherwise be reported as a defect of another.
    """
    found = {}
    for idx, view in enumerate(views):
        seen = {}
        for astate in view.get("alphaStates", []) or []:
            alpha, state = astate.get("alphaName"), astate.get("stateName")
            if not alpha or not state:
                continue
            seen.setdefault(alpha, []).append(state)
        repeated = {a: s for a, s in seen.items() if len(s) > 1}
        if repeated:
            found[idx] = repeated
    return found


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
    """Findings for one pattern's views against the prerequisite graph.

    ``entry_view_is_prerequisites`` reflects Section 9.2 rule 3: the first view
    establishes the conditions holding before the progression begins, so its
    states were reached outside the pattern and nothing can precede them. Left
    true, a shortfall there is reported as ``entry`` rather than as a defect;
    set it false to audit an entry view that is meant to stand on its own.
    """
    views = sorted_views(pattern)
    reached = first_reached(views, prereqs)
    spans = loop_spans(views)
    findings = []

    def record(idx, view, alpha, state, ra, rs, kind, detail):
        finding = {
            "pattern": pattern.get("name"),
            "viewSeq": view.get("seq"),
            "viewName": view.get("name"),
            "state": f"{alpha}.{state}",
            "prerequisite": f"{ra}.{rs}",
            "kind": kind,
            "detail": detail,
        }
        findings.append(finding)
        return finding

    # Alphas this pattern actually carries. A prerequisite naming an alpha that
    # appears in no view is not something the pattern could ever reach, and
    # saying "no view reaches it" of such a prerequisite describes the design
    # rather than a defect: the state was satisfied outside the pattern, which
    # is the same reasoning the `entry` exemption already encodes for view 0.
    #
    # This corpus relies on it deliberately. A sales play asserts `Sales Play →
    # Activated`, whose prerequisite sits on `Technical Decision Point` — an
    # alpha owned by six decision-point practices that no play carries, and
    # which the project explicitly instructs plays not to restate. A `mapsTo`
    # variant likewise inherits its parent's background while carrying only
    # itself. Reported as `external` so it stays visible without reading as a
    # fault; 83 of 98 findings across the worst five documents were this.
    carried_alphas = {
        astate.get("alphaName")
        for v in views
        for astate in v.get("alphaStates", [])
        if astate.get("alphaName")
    }

    for idx, view in enumerate(views):
        is_entry = idx == 0 and entry_view_is_prerequisites
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
                    if is_entry:
                        record(idx, view, alpha, state, ra, rs, "entry",
                               "entry condition established before the pattern begins")
                    elif ra not in carried_alphas:
                        record(idx, view, alpha, state, ra, rs, "external",
                               f"'{ra}' is carried by no view of this pattern, so "
                               f"the prerequisite is satisfied outside it")
                    else:
                        record(idx, view, alpha, state, ra, rs, "unreached",
                               "no view of this pattern reaches the prerequisite")
                elif sat > idx:
                    where = (f"prerequisite first reached at view "
                             f"{views[sat].get('seq')} '{views[sat].get('name')}'")
                    if is_entry:
                        record(idx, view, alpha, state, ra, rs, "entry",
                               f"entry condition established before the pattern "
                               f"begins; {where}")
                        continue
                    loop = spanning_loop(spans, idx, sat)
                    if loop:
                        found = record(
                            idx, view, alpha, state, ra, rs, "cyclical",
                            f"{where}, reached on an earlier lap of the loop from "
                            f"'{loop['from']}' back to '{loop['to']}'")
                        found["loop"] = loop
                    else:
                        record(idx, view, alpha, state, ra, rs, "inverted", where)
    return findings


def check_monotonicity(pattern, state_order):
    """Flag an alpha whose declared state goes backwards across views.

    Two cases that look like this are not it. Inside a loop span the earlier
    state is the minimum that must hold on that pass rather than a reset
    (Section 9.2a.1), so it is reported as ``cyclical``. And where a view
    declares one alpha twice, the walk only appears to move backwards because
    the view is ambiguous; `check_ambiguity` owns that, and reporting both
    would hide a defect of one kind behind a defect of another.
    """
    views = sorted_views(pattern)
    spans = loop_spans(views)
    ambiguous = ambiguous_alphas(views)
    findings = []
    last = {}
    for view_idx, view in enumerate(views):
        repeated = ambiguous.get(view_idx, {})
        for astate in view.get("alphaStates", []):
            alpha = astate.get("alphaName")
            state = astate.get("stateName")
            order = state_order.get(alpha, [])
            if not alpha or state not in order or alpha in repeated:
                continue
            idx = order.index(state)
            prev = last.get(alpha)
            if prev is not None and idx < prev[0]:
                loop = spanning_loop(spans, prev[3], view_idx)
                finding = {
                    "pattern": pattern.get("name"),
                    "viewSeq": view.get("seq"),
                    "viewName": view.get("name"),
                    "state": f"{alpha}.{state}",
                    "kind": "cyclical" if loop else "regression",
                    "detail": f"follows {alpha}.{prev[1]} at view {prev[2]}",
                }
                if loop:
                    finding["loop"] = loop
                    finding["detail"] += (
                        f", and is the minimum for this pass of the loop from "
                        f"'{loop['from']}' back to '{loop['to']}'")
                findings.append(finding)
            if prev is None or idx >= prev[0]:
                last[alpha] = (idx, state, view.get("seq"), view_idx)
    return findings


def check_ambiguity(pattern):
    """Flag a view declaring one alpha more than once.

    `validate-practice-json.py` reports this as an error, but only when run
    with a resolvable baseline, and `assess-practice.py` does not check it at
    all — so it reaches neither `scan-corpus.py` nor anyone running this script
    on a document alone. Reporting it here costs nothing and stops the derived
    regression from being mistaken for an ordering defect.
    """
    findings = []
    views = sorted_views(pattern)
    for view_idx, repeated in sorted(ambiguous_alphas(views).items()):
        view = views[view_idx]
        for alpha, states in sorted(repeated.items()):
            distinct = sorted(set(states))
            detail = (
                f"declared {len(states)} times at the same state"
                if len(distinct) == 1
                else f"targets {len(distinct)} states: {', '.join(distinct)}"
            )
            findings.append({
                "pattern": pattern.get("name"),
                "viewSeq": view.get("seq"),
                "viewName": view.get("name"),
                "state": f"{alpha}.{distinct[0]}",
                "kind": "ambiguous",
                "detail": detail,
            })
    return findings


def check_variant_smell(pattern, state_order):
    """Flag an alpha whose states read as variants rather than a progression.

    Some alphas are given states that name *kinds* of the thing rather than
    stages of its maturing — four sorts of inventory source, say. A pattern
    cannot walk those monotonically, so they surface as regressions that no
    reordering fixes. The remedy is to remodel the alpha, which reaches every
    document depending on it, so this is raised as a question for mapping and
    never as something to correct in place.
    """
    views = sorted_views(pattern)
    ambiguous = ambiguous_alphas(views)
    walks = {}
    for view_idx, view in enumerate(views):
        for astate in view.get("alphaStates", []) or []:
            alpha, state = astate.get("alphaName"), astate.get("stateName")
            order = state_order.get(alpha, [])
            if not alpha or state not in order:
                continue
            walks.setdefault(alpha, []).append(order.index(state))

    findings = []
    for alpha, walk in sorted(walks.items()):
        co_occurs = sorted(
            views[i].get("name")
            for i, repeated in ambiguous.items()
            if alpha in repeated and len(set(repeated[alpha])) > 1
        )
        descents = sum(1 for a, b in zip(walk, walk[1:]) if b < a)
        reasons = []
        if co_occurs:
            reasons.append(
                f"two of its states hold at once in {', '.join(repr(v) for v in co_occurs)}")
        if descents >= 2:
            reasons.append(f"the pattern moves back down its states {descents} times")
        if not reasons:
            continue
        findings.append({
            "pattern": pattern.get("name"),
            "state": alpha,
            "kind": "variant-smell",
            "detail": (
                f"{'; and '.join(reasons)} — these read as variants of {alpha} "
                f"rather than stages of it. Consider mapsTo variant alphas, work "
                f"product levels of detail, or alpha instances instead of states."
            ),
        })
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


def _sweep_directories(args):
    """Run the per-document check across whole trees and summarise.

    Exists because the alternative is assembling a dependency list by hand per
    document, which is both the tedious part and the part that goes wrong: a
    forgotten dependency makes the check weaker and still prints a pass.
    """
    import subprocess

    targets = []
    for d in args.dir:
        for found in sorted(Path(d).rglob("*.json")):
            if found.name.startswith("_") or "backup" in str(found).lower():
                continue
            if found.name.startswith("change-request") or \
               found.name.endswith(".changerequest.json"):
                continue
            targets.append(found)

    flags = [f for f, on in (("--cycles", args.cycles),
                             ("--implicit-order", args.implicit_order),
                             ("--strict-entry", args.strict_entry),
                             ("--variant-smell", args.variant_smell)) if on]

    rows, failures = [], 0
    for path in targets:
        result = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), str(path),
             "--resolve-deps", *flags],
            capture_output=True, text=True,
        )
        # Count only what a reader should act on. `entry`, `external` and
        # `cyclical` are orderings the language permits and the tool names them
        # precisely so they are not read as faults; folding them into the
        # headline count makes a clean document look dirty and buries the one
        # finding that matters.
        lines = result.stdout.splitlines()
        count = sum(1 for line in lines
                    if line.startswith("[")
                    and not line.startswith(("[entry]", "[external]", "[cyclical]")))
        # Count `external` separately rather than discarding it. It is not a
        # fault — the prerequisite sits on an alpha the pattern does not carry
        # — but it is not always the right answer either: on one document five
        # of them were cases where the pattern *should* have carried the alpha,
        # and classifying them away would have shipped four real inversions.
        # Folding them into the headline drowns the signal; hiding them
        # entirely removes the prompt to check. So: reported, not counted.
        external = sum(1 for line in lines if line.startswith("[external]"))
        if result.returncode not in (0, 1):
            continue
        if count:
            failures += 1
        rows.append((count, external, str(path)))

    rows.sort(reverse=True)
    for count, external, path in rows:
        if count:
            print(f"{count:5d}  {path}")
    clean = len(rows) - failures
    total_external = sum(e for _, e, _ in rows)
    print(f"\n{len(rows)} documents checked · {clean} clean · "
          f"{failures} with findings")
    if total_external:
        docs_with = sum(1 for _, e, _ in rows if e)
        print(f"{total_external} 'external' prerequisites across {docs_with} "
              f"documents — not faults, but worth a read: each is a pattern "
              f"asserting a state whose prerequisite sits on an alpha it does "
              f"not carry. Usually right; sometimes the pattern should carry "
              f"the alpha. Run a single document without --dir to list them.")
    return 1 if failures else 0


def _resolve_dependency_documents(documents):
    """Load the baselines and dependency practices the given documents declare.

    The prerequisite graph is only as complete as the documents handed to it,
    and assembling that list by hand is both tedious and easy to get wrong — a
    missing dependency makes the check quietly weaker rather than noisier, so
    the omission looks like a pass. Resolving it from what the document
    declares removes the judgement call.

    Walks `baselinePracticeName`, the array `baselinePracticeNames` and
    `practiceDependencyNames`, transitively, keyed on name so a diamond or a
    cycle terminates.
    """
    import importlib.util

    helper = Path(__file__).resolve().parent / "discover-dependencies.py"
    spec = importlib.util.spec_from_file_location("_dd", helper)
    dd = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(dd)

    index, _ = dd.build_index(["baselines", "practices", "deps"])
    seen = {name for name, _ in documents}
    queue = [data for _, data in documents]
    extra = []

    while queue:
        current = queue.pop(0)
        wanted = []
        if current.get("baselinePracticeName"):
            wanted.append(current["baselinePracticeName"])
        wanted.extend(current.get("baselinePracticeNames", []) or [])
        wanted.extend(current.get("practiceDependencyNames", []) or [])

        for dep_name in wanted:
            if not dep_name or dep_name in seen:
                continue
            seen.add(dep_name)
            match = dd.resolve_name(dep_name, index, prefer_filesystem=True,
                                    prefer_canonical=True)
            if match["status"] != "found":
                print(f"Warning: dependency '{dep_name}' not loaded "
                      f"(status: {match['status']}) — the prerequisite graph is "
                      f"incomplete without it", file=sys.stderr)
                continue
            dep_data, err = dd.load_resolved_json(match)
            if err or not dep_data:
                continue
            extra.append((Path(match["path"]).name, dep_data))
            queue.append(dep_data)

    return extra


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("documents", nargs="*",
                    help="Practice JSON first, then baseline and dependencies")
    ap.add_argument("--cycles", action="store_true",
                    help="Report contradictory prerequisite edges across the "
                         "documents given, naming the document that declared each")
    ap.add_argument("--implicit-order", action="store_true",
                    help="With --cycles, also walk the sequential edge between "
                         "consecutive states of an alpha. A background graph "
                         "can be acyclic on its declared edges alone and still "
                         "deadlock once state order is included")
    ap.add_argument("--on-baseline", metavar="NAME",
                    help="With --cycles, sweep every corpus document building on "
                         "this baseline instead of naming them individually")
    ap.add_argument("--pattern", action="append",
                    help="Limit to named pattern(s); repeatable")
    ap.add_argument("--matrix", action="store_true",
                    help="Print the view-by-view alpha state matrix")
    ap.add_argument("--strict-entry", action="store_true",
                    help="Judge the first view like any other, instead of "
                         "treating its states as conditions met before the "
                         "pattern begins")
    ap.add_argument("--variant-smell", action="store_true",
                    help="Also report alphas whose states read as variants "
                         "rather than stages — a question for mapping, not a fix")
    ap.add_argument("--dir", action="append", default=[], metavar="DIR",
                    help="Check every authored document under DIR, one at a time, "
                         "each with its own dependencies resolved. Repeatable. "
                         "Prints a per-document count and exits non-zero if any "
                         "document has a blocking finding.")
    ap.add_argument("--resolve-deps", action="store_true",
                    help="Also load the baselines and dependency practices the "
                         "named documents declare, transitively. The graph is only "
                         "as complete as what you pass it, and a missing dependency "
                         "weakens the check silently rather than failing loudly.")
    ap.add_argument("--json", dest="as_json", action="store_true",
                    help="Emit findings as JSON")
    args = ap.parse_args()

    if args.dir:
        return _sweep_directories(args)

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

        if args.resolve_deps:
            documents.extend(_resolve_dependency_documents(documents))

    prereqs = build_prerequisites(documents)

    # `--cycles` used to return here, which made it exclusive rather than
    # additive. The merged command this project prescribes —
    # `--cycles --implicit-order --strict-entry --variant-smell` — therefore ran
    # the cycle check and silently skipped every view check the other three
    # flags exist to configure, printing "No contradictory prerequisite edges
    # found" about a question it had never asked. Proven on a document with a
    # planted inverted edge: the full command reported clean, and dropping
    # `--cycles` reported two `unreached` findings on the same file. The two
    # questions are different and are now both answered in one run.
    cycles = None
    if args.cycles:
        cycle_graph = build_prerequisites(documents)
        if args.implicit_order:
            add_implicit_order_edges(cycle_graph, build_state_order(documents))
        cycles = find_prerequisite_cycles(cycle_graph)
        if args.on_baseline:
            # A corpus sweep has no single pattern owner, so there is nothing
            # to walk views against. Cycles are the whole question there.
            return report_cycles(cycles, args.as_json)
        if not args.as_json:
            report_cycles(cycles, False)

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
            findings.extend(check_pattern(
                pattern, prereqs, state_order,
                entry_view_is_prerequisites=not args.strict_entry))
            findings.extend(check_ambiguity(pattern))
            findings.extend(check_monotonicity(pattern, state_order))
            if args.variant_smell:
                findings.extend(check_variant_smell(pattern, state_order))

    if args.as_json:
        if cycles is None:
            print(json.dumps(findings, indent=2))
        else:
            print(json.dumps({"cycles": cycles, "findings": findings}, indent=2))
    else:
        if not findings:
            print("\nNo prerequisite inversions or state regressions found.")
        for f in findings:
            where = (f" view {f['viewSeq']} '{f['viewName']}'"
                     if f.get("viewSeq") is not None else "")
            print(f"\n[{f['kind']}] {f['pattern']}{where}")
            print(f"  state: {f['state']}")
            if "prerequisite" in f:
                print(f"  requires: {f['prerequisite']}")
            print(f"  {f['detail']}")

    blocking = any(f["kind"] in BLOCKING_KINDS for f in findings)
    return 1 if (blocking or cycles) else 0


if __name__ == "__main__":
    sys.exit(main())
