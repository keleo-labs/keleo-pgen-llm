#!/usr/bin/env python3
"""Check resolve-context.py against the merge specification's composition rules.

Exercises the constructs schema 2.18.0–3.0.0 added to the merge algorithm —
specificity chains, suppression, loop edges and orchestration merging — using
the fixtures in tests/fixtures/merge-constructs/. No corpus document uses them
yet, so without fixtures the behaviour is unverifiable.

Each case is resolved in several input orders, because the merge must depend on
the declared dependency graph rather than on how the documents were supplied.

Usage:
    python3 tests/check-merge-semantics.py [--verbose]

Exit codes:
    0 - every check passed
    1 - at least one check failed
"""

import argparse
import itertools
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "fixtures" / "merge-constructs"
RESOLVER = ROOT / "utils" / "resolve-context.py"

DOCUMENTS = ["baseline.json", "practice-idp.json", "practice-edge.json"]


def resolve(paths):
    """Run the resolver over `paths` and return (effective_context, report)."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "effective.json"
        proc = subprocess.run(
            [sys.executable, str(RESOLVER), *paths, "-o", str(out), "--force"],
            capture_output=True, text=True, cwd=ROOT,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"resolver failed: {proc.stdout}{proc.stderr}")
        return json.loads(out.read_text()), json.loads(proc.stdout)


def named(items, name):
    for item in items or []:
        if item.get("name") == name:
            return item
    return None


def checks(effective, report):
    """Yield (description, passed, detail) for one resolved composition."""
    platform = named(effective.get("alphas"), "Platform")

    # merge.md §7.2e — specificity chain accumulation.
    yield (
        "specificity chain is most specific first",
        platform and platform.get("specificity") == ["OpenShift", "IDP"],
        platform.get("specificity") if platform else "Platform alpha missing",
    )

    # merge.md §5.1 / §6.2 — a redeclaration adds to what it inherits.
    states = [s["name"] for s in (platform or {}).get("states", [])]
    yield (
        "redeclared alpha keeps the states it inherits",
        states == ["Identified", "Built", "Operational"],
        states,
    )
    operational = named((platform or {}).get("states"), "Operational")
    items = [c["name"] for c in (operational or {}).get("checklist", [])]
    yield (
        "checklist items from every layer survive",
        items == ["Production workload running", "Golden paths published", "Edge sites enrolled"],
        items,
    )

    # merge.md §6.5 — a loop edge is a single object; the overlay wins whole.
    loop = (operational or {}).get("loopsBackTo") or {}
    yield (
        "loop edge is replaced atomically by the overlay",
        loop.get("stateName") == "Identified" and "edge site" in loop.get("description", ""),
        loop,
    )

    # merge.md §7.2f — suppression resolution.
    alphas = [a["name"] for a in effective.get("alphas", [])]
    yield (
        "suppressed alpha is removed from the composition",
        "Multi-Cluster Federation" not in alphas,
        alphas,
    )
    dangling = (report.get("suppression") or {}).get("danglingReferences") or []
    yield (
        "references into the suppressed alpha are reported",
        any(d["target"] == "Multi-Cluster Federation" for d in dangling),
        dangling,
    )

    # merge.md §6.15a — orchestration merging.
    orchestration = named(effective.get("patternOrchestrations"), "Platform Endeavour")
    stages = (orchestration or {}).get("stages", [])
    placements = [(s["patternName"], s["relationship"]) for s in stages]
    yield (
        "one pattern placed twice survives as two stages",
        placements == [
            ("Platform Bootstrap", "sequential"),
            ("Steady State", "sequential"),
            ("Site Rollout", "nested"),
            ("Site Rollout", "onDemand"),
        ],
        placements,
    )
    bootstrap = stages[0] if stages else {}
    yield (
        "stage entry criteria are first-writer-wins",
        bootstrap.get("entryCriteria") == "Funding approved."
        and bootstrap.get("exitCriteria") == "A cluster serves traffic.",
        {k: bootstrap.get(k) for k in ("entryCriteria", "exitCriteria")},
    )

    # merge.md §7.2e — an authored chain is discarded, not merged.
    yield (
        "authored specificity is discarded",
        platform and "Authored" not in (platform.get("specificity") or []),
        platform.get("specificity") if platform else None,
    )

    # Bookkeeping must not reach consumers.
    leaked = json.dumps(effective)
    yield (
        "merge tracking annotations are stripped",
        all(key not in leaked for key in
            ("_layers", "_suppressedByLayers", "_specificityContributions")),
        "",
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verbose", action="store_true",
                        help="Print every check, not only failures")
    args = parser.parse_args()

    failures = []
    passes = 0
    for permutation in itertools.permutations(DOCUMENTS):
        label = " ".join(permutation)
        effective, report = resolve([str(FIXTURES / name) for name in permutation])
        for description, passed, detail in checks(effective, report):
            if passed:
                passes += 1
                if args.verbose:
                    print(f"PASS [{label}] {description}")
            else:
                failures.append(f"FAIL [{label}] {description}: {detail!r}")

    for failure in failures:
        print(failure)
    print(f"\n{passes} passed, {len(failures)} failed "
          f"across {len(list(itertools.permutations(DOCUMENTS)))} input orders.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
