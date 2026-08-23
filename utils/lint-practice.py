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


def discover_schema():
    """Return schema path if deps/language.schema.json exists."""
    candidate = UTILS_DIR.parent / "deps" / "language.schema.json"
    return str(candidate) if candidate.exists() else None


def run_validator(practice, baseline, schema):
    """Run validate-practice-json.py and return (error_count, warning_count, report)."""
    cmd = [
        sys.executable,
        str(UTILS_DIR / "validate-practice-json.py"),
        str(practice),
        str(baseline),
        str(schema),
    ]
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


def run_assess(practice, baseline):
    """Run assess-practice.py --errors-only. Returns error count."""
    cmd = [
        sys.executable,
        str(UTILS_DIR / "assess-practice.py"),
        str(practice),
        "--baseline",
        str(baseline),
        "--errors-only",
    ]
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

    initial_errors, initial_warnings, initial_report = run_validator(practice, baseline, schema)
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

            current_errors, current_warnings, _ = run_validator(practice, baseline, schema)

            if current_errors == 0:
                break

            if common_fixes == 0 and comp_fixes == 0:
                break
    else:
        current_warnings = initial_warnings

    assess_errors = 0
    if baseline:
        assess_errors = run_assess(practice, baseline)

    final_errors = current_errors + assess_errors
    status = "PASS" if final_errors == 0 else "FAIL"

    if iterations > 0:
        one_line = f"{status} {final_errors} errors ({current_warnings} warnings) after {iterations} fix iteration(s)"
    else:
        one_line = f"{status} {final_errors} errors ({current_warnings} warnings)"

    report = {
        "practice": str(practice),
        "baseline": str(baseline),
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
