#!/usr/bin/env python3
"""
Lint Practice JSON

Combined validate-fix-revalidate loop that runs the standard fix chain in a
single command, eliminating 5+ separate bash calls during Phase 3.

Usage:
    # Validate only (no fixes):
    python3 utils/lint-practice.py practices/<name>/<name>.json

    # Validate and auto-fix until clean (auto-discovers baseline/schema):
    python3 utils/lint-practice.py practices/<name>/<name>.json --fix

    # Explicit baseline and schema:
    python3 utils/lint-practice.py <practice>.json <baseline>.json <schema>.json --fix

    # One-line summary (for scripting):
    python3 utils/lint-practice.py practices/<name>/<name>.json --fix --one-line

    # Limit fix iterations:
    python3 utils/lint-practice.py <practice>.json --fix --max-iterations 5

Fix chain (per iteration):
    1. validate-practice-json.py  →  schema/baseline/integrity errors
    2. fix-common-issues.py --fix --all  →  structural fixes
    3. fix-competency-levels.py --fix  →  competency level name alignment
    4. Re-validate  →  check remaining errors
    5. assess-practice.py --errors-only  →  final quality check

Exit codes:
    0 - No errors (warnings are acceptable)
    1 - Errors remain after fix iterations
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils._shared import load_json

UTILS_DIR = Path(__file__).resolve().parent


def discover_baseline(practice_path):
    """Resolve baseline path from practice JSON's baselinePracticeName."""
    project_root = UTILS_DIR.parent
    try:
        data = load_json(practice_path, exit_on_error=False)
        bl_name = data.get("baselinePracticeName")
        if not bl_name:
            return None
        slug = re.sub(r"[^a-z0-9]+", "-", bl_name.lower()).strip("-")
        candidates = [
            project_root / "deps" / f"{slug}.json",
            project_root / "baselines" / slug / f"{slug}.json",
        ]
        for c in candidates:
            if c.exists():
                return str(c)
        # Fallback: scan deps/ and baselines/ for files whose name field matches
        for json_file in (project_root / "deps").glob("*.json"):
            try:
                d = load_json(json_file, exit_on_error=False)
                if d.get("name") == bl_name:
                    return str(json_file)
            except Exception:
                continue
        result = subprocess.run(
            [sys.executable, str(UTILS_DIR / "discover-dependencies.py"), "--resolve", bl_name],
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            try:
                report = json.loads(result.stdout)
                if report.get("status") == "found":
                    return report.get("path")
            except (json.JSONDecodeError, TypeError):
                pass
    except Exception:
        pass
    return None


def _resolve_baseline_by_name(bl_name):
    """Resolve a baseline document name to a path under deps/ or baselines/."""
    if not bl_name:
        return None
    project_root = UTILS_DIR.parent
    slug = re.sub(r"[^a-z0-9]+", "-", bl_name.lower()).strip("-")
    for c in (project_root / "deps" / f"{slug}.json",
              project_root / "baselines" / slug / f"{slug}.json"):
        if c.exists():
            return str(c)
    for json_file in list((project_root / "deps").glob("*.json")) + \
            list((project_root / "baselines").glob("*/*.json")):
        try:
            if load_json(json_file, exit_on_error=False).get("name") == bl_name:
                return str(json_file)
        except Exception:
            continue
    return None


def ancestor_baselines(baseline_path):
    """Resolve the baseline's own ancestor baselines, transitively.

    A baseline may itself extend another, through the array
    `baselinePracticeNames` or the singular `baselinePracticeName`. The
    dependency walk below covers `practiceDependencyNames` only, so for a
    practice sitting under an extension baseline the root baseline's
    vocabulary — its focuses, activity spaces and competencies — was never
    supplied to the validator.

    The failure is the dangerous kind: `Partner Ecosystem Essentials` extends
    `Red Hat Sales Essentials`, and every shipped document in that subtree
    reported *confident* `Invalid competency name`, `Unknown focus` and
    `Unknown activity space` errors for vocabulary that resolves perfectly
    well. An agent clearing them would remap correct references onto baseline
    substitutes. Reproduced before the fix on four shipped documents at 58, 26,
    24 and 8 errors, every one of which clears when the root baseline is
    supplied.
    """
    paths, seen, queue = [], set(), []
    try:
        data = load_json(baseline_path, exit_on_error=False)
    except Exception:
        return paths
    if not isinstance(data, dict):
        return paths
    queue.extend(data.get("baselinePracticeNames", []) or [])
    if data.get("baselinePracticeName"):
        queue.append(data["baselinePracticeName"])

    while queue:
        name = queue.pop(0)
        if not name or name in seen:
            continue
        seen.add(name)
        resolved = _resolve_baseline_by_name(name)
        if not resolved:
            continue
        paths.append(resolved)
        try:
            parent = load_json(resolved, exit_on_error=False)
        except Exception:
            continue
        if isinstance(parent, dict):
            queue.extend(parent.get("baselinePracticeNames", []) or [])
            if parent.get("baselinePracticeName"):
                queue.append(parent["baselinePracticeName"])
    return paths


def discover_schema():
    """Return schema path if deps/language.schema.json exists."""
    candidate = UTILS_DIR.parent / "deps" / "language.schema.json"
    return str(candidate) if candidate.exists() else None


def _canonical_candidate(name, candidates):
    """Pick the authoring home from the candidates of an ambiguous resolution.

    Mirrors _canonical_entry in discover-dependencies.py: prefer the directory
    named after the document itself, then deps/, then any other path.
    """
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    paths = [c["path"] for c in candidates if c.get("path")]
    if not paths:
        return None

    def score(p):
        path = Path(p)
        parent, stem = path.parent.name, path.stem
        if parent == slug and stem == slug:
            return (0, len(p))
        if parent == stem:
            return (1, len(p))
        if parent == slug or stem == slug:
            return (2, len(p))
        if parent == "deps":
            return (3, len(p))
        return (4, len(p))

    return sorted(paths, key=score)[0]


def discover_parents(practice_path, baseline_path=None):
    """Resolve parent practice paths from practiceDependencyNames, transitively.

    A dependency has dependencies of its own, and everything they declare is in
    scope for the document at the bottom. Resolving only the first hop made a
    clean tier-4 practice report **FAIL with 46 errors** — 46 `Invalid
    competency name` findings for competencies declared two hops out, on
    `Partner Go-to-Market Execution`, which this document reaches through
    `Partner Demand Generation`. Every one vanishes when that second hop is
    supplied.

    That is the dangerous direction: an agent clearing 46 confident competency
    errors would remap every persona and activity reference onto baseline
    substitutes. `resolve-context.py --transitive` has always walked this;
    the three checkers did not.
    """
    # The baseline's own ancestor baselines, which the dependency walk below
    # does not reach. Supplied first so their vocabulary is present even for a
    # practice that declares no practice dependencies at all.
    parents = ancestor_baselines(baseline_path) if baseline_path else []

    try:
        data = load_json(practice_path, exit_on_error=False)
        dep_names = list(data.get("practiceDependencyNames", []) or [])
        if not dep_names:
            return parents

        # Breadth-first over the dependency graph; `seen` keyed on name so a
        # diamond or a cycle terminates. Each parent resolved is loaded so its
        # own dependencies join the queue.
        seen = set(dep_names)
        queue = list(dep_names)

        while queue:
            name = queue.pop(0)
            resolved_path = None

            result = subprocess.run(
                [sys.executable, str(UTILS_DIR / "discover-dependencies.py"), "--resolve", name],
                capture_output=True, text=True,
            )
            if result.returncode == 0:
                try:
                    report = json.loads(result.stdout)
                    # --resolve emits {"results": [ ... ]}, one entry per name.
                    entry = (report.get("results") or [report])[0]
                    if entry.get("status") == "found" and entry.get("path"):
                        resolved_path = entry["path"]
                    # A document synced beside each consumer makes its name
                    # ambiguous. Dropping the parent in silence is worse than
                    # picking the authoring home, because every reference into
                    # that parent then reads as an unresolvable error.
                    elif entry.get("status") == "ambiguous":
                        resolved_path = _canonical_candidate(
                            name, entry.get("candidates", []))
                except (json.JSONDecodeError, TypeError, IndexError):
                    pass

            if resolved_path:
                parents.append(resolved_path)
                parent_data = load_json(resolved_path, exit_on_error=False)
                if isinstance(parent_data, dict):
                    for onward in parent_data.get("practiceDependencyNames", []) or []:
                        if onward and onward not in seen:
                            seen.add(onward)
                            queue.append(onward)
                continue

            # Fallback: an effective context beside the practice covers them all.
            practice_dir = Path(practice_path).parent
            ec_path = practice_dir / "_effective-context.json"
            if ec_path.exists():
                parents.append(str(ec_path))
                break
        return parents
    except Exception:
        return parents


def run_validator(practice, baseline, schema, parents=None):
    """Run validate-practice-json.py and return (error_count, warning_count, report).

    Dependency practices are forwarded as trailing positional arguments. Without
    them the validator cannot resolve a reference into a declared dependency —
    an orchestration stage nested to a dependency's pattern, for instance — and
    reports it as an error the document cannot fix.
    """
    cmd = [
        sys.executable,
        str(UTILS_DIR / "validate-practice-json.py"),
        str(practice),
        str(baseline),
        str(schema),
    ]
    cmd.extend(str(p) for p in (parents or []))
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        report = json.loads(result.stdout)
        errors = report.get("error_count", 0)
        warnings = len(report.get("warnings", []))
        return errors, warnings, report
    except (json.JSONDecodeError, TypeError):
        return -1, 0, {"error": "validator output not parseable", "stderr": result.stderr[:500]}


def run_fix_common(practice, baseline=None):
    """Run fix-common-issues.py --fix --all. Returns fix count."""
    cmd = [
        sys.executable,
        str(UTILS_DIR / "fix-common-issues.py"),
        str(practice),
        "--fix",
        "--all",
    ]
    if baseline:
        cmd.append(str(baseline))
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        report = json.loads(result.stdout)
        return report.get("fixCount", 0)
    except (json.JSONDecodeError, TypeError):
        return 0


def run_fix_competency(practice, baseline):
    """Run fix-competency-levels.py --fix. Returns fix count."""
    cmd = [
        sys.executable,
        str(UTILS_DIR / "fix-competency-levels.py"),
        str(practice),
        str(baseline),
        "--fix",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        report = json.loads(result.stdout)
        if report.get("valid"):
            return 0
        return report.get("fixCount", len(report.get("mismatches", [])))
    except (json.JSONDecodeError, TypeError):
        return 0


def run_assess(practice, baseline, parents=None):
    """Run assess-practice.py --errors-only. Returns error count."""
    cmd = [
        sys.executable,
        str(UTILS_DIR / "assess-practice.py"),
        str(practice),
        "--baseline",
        str(baseline),
        "--errors-only",
    ]
    for p in (parents or []):
        cmd.extend(["--parent", str(p)])
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        report = json.loads(result.stdout)
        issues = report.get("issues", [])
        return sum(1 for i in issues if i.get("severity") == "error")
    except (json.JSONDecodeError, TypeError):
        return 0


def main():
    parser = argparse.ArgumentParser(
        description="Combined validate-fix-revalidate loop for practice JSON"
    )
    parser.add_argument("practice", help="Practice JSON file path")
    parser.add_argument("baseline", nargs="?", help="Baseline JSON (auto-discovered if omitted)")
    parser.add_argument("schema", nargs="?", help="Schema JSON (auto-discovered if omitted)")
    parser.add_argument("--fix", action="store_true", help="Apply auto-fixes (default: validate only)")
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=3,
        help="Maximum fix iterations (default: 3)",
    )
    parser.add_argument(
        "--one-line",
        action="store_true",
        help="Print one-line summary instead of JSON",
    )
    parser.add_argument(
        "--parent",
        action="append",
        default=[],
        help="Parent practice JSON (repeatable; auto-discovered from practiceDependencyNames if omitted)",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Structured JSON output (default behaviour — flag exists for discoverability)",
    )
    args = parser.parse_args()

    practice = Path(args.practice)
    if not practice.exists():
        print(json.dumps({"error": f"File not found: {practice}"}))
        sys.exit(1)

    baseline = args.baseline or discover_baseline(practice)
    schema = args.schema or discover_schema()

    if not baseline:
        print(json.dumps({"error": "No baseline found. Provide baseline path or set baselinePracticeName in practice JSON."}))
        sys.exit(1)
    if not schema:
        print(json.dumps({"error": "No schema found. Provide schema path or ensure deps/language.schema.json exists."}))
        sys.exit(1)

    parents = args.parent if args.parent else discover_parents(practice, baseline)

    initial_errors, initial_warnings, initial_report = run_validator(practice, baseline, schema, parents)
    fixes_applied = []
    iterations = 0
    current_errors = initial_errors

    if args.fix and current_errors > 0:
        for i in range(args.max_iterations):
            iterations += 1

            common_fixes = run_fix_common(practice, baseline)
            if common_fixes > 0:
                fixes_applied.append(f"fix-common-issues: {common_fixes} fixes")

            comp_fixes = run_fix_competency(practice, baseline)
            if comp_fixes > 0:
                fixes_applied.append(f"fix-competency-levels: {comp_fixes} fixes")

            current_errors, current_warnings, _ = run_validator(practice, baseline, schema, parents)

            if current_errors == 0:
                break

            if common_fixes == 0 and comp_fixes == 0:
                break
    else:
        current_warnings = initial_warnings

    assess_errors = 0
    if baseline:
        assess_errors = run_assess(practice, baseline, parents)

    final_errors = current_errors + assess_errors
    status = "PASS" if final_errors == 0 else "FAIL"

    if iterations > 0:
        one_line = f"{status} {final_errors} errors ({current_warnings} warnings) after {iterations} fix iteration(s)"
    else:
        one_line = f"{status} {final_errors} errors ({current_warnings} warnings)"

    report = {
        "practice": str(practice),
        "baseline": str(baseline),
        "parents": [str(p) for p in parents],
        "iterations": iterations,
        "initial_errors": initial_errors,
        "final_errors": final_errors,
        "final_warnings": current_warnings,
        "assess_errors": assess_errors,
        "fixes_applied": fixes_applied,
        "status": status,
        "one_line": one_line,
    }

    if args.one_line:
        print(one_line)
    else:
        print(json.dumps(report, indent=2))

    sys.exit(0 if final_errors == 0 else 1)


if __name__ == "__main__":
    main()
