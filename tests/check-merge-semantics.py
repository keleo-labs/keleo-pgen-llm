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
    placements = [
        (s.get("orchestrationName") or s.get("patternName"), s["relationship"])
        for s in stages
    ]
    yield (
        "one pattern placed twice survives as two stages",
        placements == [
            ("Platform Bootstrap", "sequential"),
            ("Steady State", "sequential"),
            ("Site Rollout", "nested"),
            ("Site Rollout", "onDemand"),
            ("Rollout Endeavour", "nested"),
        ],
        placements,
    )
    bootstrap = next((s for s in stages
                      if s.get("patternName") == "Platform Bootstrap"), {})
    yield (
        "stage entry criteria are first-writer-wins",
        bootstrap.get("entryCriteria") == "Funding approved."
        and bootstrap.get("exitCriteria") == "A cluster serves traffic.",
        {k: bootstrap.get(k) for k in ("entryCriteria", "exitCriteria")},
    )
    # merge.md §6.15a — placement is first-writer-wins as of schema 3.1.0, so an
    # overlay restating an inherited stage cannot move it.
    yield (
        "an overlay cannot re-place a stage it inherited",
        bootstrap.get("seq") == 1,
        {"seq": bootstrap.get("seq"), "overlay asked for": 7},
    )
    embedded = next((s for s in stages
                     if s.get("orchestrationName") == "Rollout Endeavour"), None)
    yield (
        "an embedded orchestration survives the merge as a stage",
        embedded is not None
        and embedded.get("relativeTo", {}).get("patternName") == "Steady State",
        embedded,
    )

    # merge.md §7.2e — an authored chain is discarded, not merged.
    yield (
        "authored specificity is discarded",
        platform and "Authored" not in (platform.get("specificity") or []),
        platform.get("specificity") if platform else None,
    )

    # merge.md §4.2 / §7.4 — the layer that introduced an element owns what it IS.
    yield (
        "a redeclaration does not rewrite the description it inherits",
        platform and platform.get("description", "").startswith(
            "The platform on which the organisation"),
        (platform or {}).get("description"),
    )

    # merge.md §7.3 — a concrete focus beats the unresolved sentinel, and
    # §4.3 keeps the first substantive value against a later concrete one.
    yield (
        "focus name keeps the first concrete value",
        platform and platform.get("focusName") == "Solution",
        (platform or {}).get("focusName"),
    )

    # merge.md §5.3 — rows key on the target: a relationship to the same alpha
    # is replaced by the overlay, and one the overlay never mentions survives.
    relations = sorted((r.get("relationship"), r.get("alphaName"))
                       for r in (platform or {}).get("relatesTo", []))
    yield (
        "a relationship to the same alpha is replaced, others are kept",
        relations == [("maintained by", "Operational Automation"),
                      ("runs on", "Multi-Cluster Federation")],
        relations,
    )

    # merge.md §6.10 — assets replace whole rather than merging field by field.
    asset = named(effective.get("assets"), "Platform Icon")
    yield (
        "a redefined asset replaces the earlier definition entirely",
        asset and asset.get("url") and "path" not in asset,
        {k: v for k, v in (asset or {}).items() if not k.startswith("_")},
    )

    # merge.md §5.6 / §6.7 — primitive arrays union rather than replace.
    group = named(effective.get("personaGroups"), "Platform Team")
    members = sorted((group or {}).get("personaNames", []))
    yield (
        "persona group membership unions across practices",
        members == ["Platform Engineer", "Site Reliability Engineer"],
        members,
    )
    yield (
        "a redeclared persona group keeps the first description",
        group and group.get("description") == "Who runs the platform.",
        (group or {}).get("description"),
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
