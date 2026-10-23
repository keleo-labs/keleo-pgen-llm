#!/usr/bin/env python3
"""Check that check-pattern-prerequisites.py tells its orderings apart.

The checker distinguishes seven kinds, and the distinctions are the whole
point: an entry view, a loop span and an ambiguous view all make a pattern look
as though it asserts a state before reaching it, and only one of the three is a
defect. Classifying any of them wrongly either hides real work or sends someone
to fix a document that is already correct.

The corpus cannot verify this. Exactly one practice declares `loopsBackTo` and
it has no finding inside the loop, so the cyclical path is unreachable from
real documents — which is how it went unimplemented in the first place.
tests/fixtures/pattern-prerequisites/practice-orderings.json puts all seven
side by side instead.

Usage:
    python3 tests/check-prerequisite-classification.py [--verbose]

Exit codes:
    0 - every check passed
    1 - at least one check failed
"""

import argparse
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURE = ROOT / "tests" / "fixtures" / "pattern-prerequisites" / "practice-orderings.json"


def load_checker():
    spec = importlib.util.spec_from_file_location(
        "check_pattern_prerequisites",
        ROOT / "utils" / "check-pattern-prerequisites.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def findings_for(mod, data, pattern_name, strict_entry=False, variant_smell=False):
    documents = [("fixture", data)]
    prereqs = mod.build_prerequisites(documents)
    state_order = mod.build_state_order(documents)
    pattern = next(p for p in data["patterns"] if p["name"] == pattern_name)
    found = mod.check_pattern(
        pattern, prereqs, state_order,
        entry_view_is_prerequisites=not strict_entry,
    )
    found += mod.check_ambiguity(pattern)
    found += mod.check_monotonicity(pattern, state_order)
    if variant_smell:
        found += mod.check_variant_smell(pattern, state_order)
    return found


def kinds_at(findings, view_name=None):
    return sorted(
        f["kind"] for f in findings
        if view_name is None or f.get("viewName") == view_name
    )


#: (description, pattern, kwargs, assertion) — each assertion takes the findings
#: list and returns None when satisfied or a string saying what was seen.
def build_cases():
    def has(findings, kind, view=None, state=None, count=None):
        hits = [
            f for f in findings
            if f["kind"] == kind
            and (view is None or f.get("viewName") == view)
            and (state is None or f.get("state") == state)
        ]
        if count is not None and len(hits) != count:
            return f"expected {count} {kind} but saw {len(hits)}: {kinds_at(findings, view)}"
        if count is None and not hits:
            return f"no {kind} finding; saw {kinds_at(findings, view)}"
        return None

    def lacks(findings, kind, view=None):
        hits = [f for f in findings
                if f["kind"] == kind and (view is None or f.get("viewName") == view)]
        return f"unexpected {kind}: {[f['detail'] for f in hits]}" if hits else None

    return [
        (
            "the first view's unmet prerequisite is an entry condition",
            "Cadence", {},
            lambda f: has(f, "entry", view="Prerequisites"),
        ),
        (
            "--strict-entry judges the first view like any other",
            "Cadence", {"strict_entry": True},
            lambda f: lacks(f, "entry") or has(f, "inverted", view="Prerequisites"),
        ),
        (
            "a prerequisite met on an earlier lap is cyclical, not inverted",
            "Cadence", {},
            lambda f: has(f, "cyclical", view="Act") or lacks(f, "inverted", view="Act"),
        ),
        (
            "a state re-declared lower inside a loop is a per-pass minimum",
            "Cadence", {},
            lambda f: has(f, "cyclical", view="Adapt") or lacks(f, "regression", view="Adapt"),
        ),
        (
            "the loop edge is named on the finding",
            "Cadence", {},
            lambda f: None if all(
                x.get("loop", {}).get("to") == "Sense"
                for x in f if x["kind"] == "cyclical"
            ) else "a cyclical finding does not name the loop it sits in",
        ),
        (
            "without a loop the same ordering is a genuine inversion",
            "Linear", {},
            lambda f: has(f, "inverted", view="Gate"),
        ),
        (
            "a prerequisite the pattern never carries is unreached, not inverted",
            "Linear", {},
            lambda f: has(f, "unreached", view="Run"),
        ),
        (
            "without a loop a lower state later is a genuine regression",
            "Linear", {},
            lambda f: has(f, "regression", view="Close"),
        ),
        (
            "two states of one alpha in a view are reported as ambiguous",
            "Ambiguous", {},
            lambda f: has(f, "ambiguous", view="Pick"),
        ),
        (
            "the same state declared twice is reported as ambiguous",
            "Ambiguous", {},
            lambda f: has(f, "ambiguous", view="Repeat"),
        ),
        (
            "an ambiguous view does not also report the regression it implies",
            "Ambiguous", {},
            lambda f: lacks(f, "regression"),
        ),
        (
            "co-occurring states read as a variant smell",
            "Ambiguous", {"variant_smell": True},
            lambda f: has(f, "variant-smell", state="Source"),
        ),
        (
            "repeated descent reads as a variant smell",
            "Oscillate", {"variant_smell": True},
            lambda f: has(f, "variant-smell", state="Gate"),
        ),
        (
            "an oscillating alpha still reports its regressions",
            "Oscillate", {},
            lambda f: has(f, "regression", count=2),
        ),
        (
            "variant smell is silent unless asked for",
            "Oscillate", {},
            lambda f: lacks(f, "variant-smell"),
        ),
        (
            "a clean walk reports nothing blocking",
            "Cadence", {},
            lambda f: None if not [
                x for x in f if x["kind"] in build_cases.blocking
            ] else "the cyclical pattern reports a blocking finding",
        ),
    ]


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--verbose", action="store_true",
                    help="Print every finding alongside each case")
    args = ap.parse_args()

    mod = load_checker()
    build_cases.blocking = mod.BLOCKING_KINDS
    data = json.loads(FIXTURE.read_text())

    failures = 0
    for description, pattern_name, kwargs, assertion in build_cases():
        findings = findings_for(mod, data, pattern_name, **kwargs)
        problem = assertion(findings)
        if problem:
            failures += 1
            print(f"FAIL  {description}\n      {problem}")
        else:
            print(f"ok    {description}")
        if args.verbose:
            for f in findings:
                where = f" {f.get('viewName')}" if f.get("viewName") else ""
                print(f"        [{f['kind']}]{where} {f['state']} — {f['detail']}")

    print(f"\n{'FAIL' if failures else 'PASS'}: "
          f"{len(build_cases()) - failures}/{len(build_cases())} checks passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
