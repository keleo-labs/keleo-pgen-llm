#!/usr/bin/env python3
"""
Post-Validate Method

Run the full fix-validate pipeline across ALL practice/baseline JSONs in a
directory in one command. Wraps lint-practice.py for each file, then runs
cross-practice auditing for methods.

Replaces the manual loop of fix-common-issues + fix-competency-levels +
validate + assess across N practice files.

Usage:
    # Validate all practice JSONs in a directory (report only):
    python3 utils/post-validate-method.py practices/cisco-openshift/

    # Validate and auto-fix:
    python3 utils/post-validate-method.py practices/cisco-openshift/ --fix

    # One-line summary per practice + aggregate:
    python3 utils/post-validate-method.py practices/cisco-openshift/ --fix --one-line

    # Explicit baseline override:
    python3 utils/post-validate-method.py practices/cisco-openshift/ --baseline deps/idp-essentials.json --fix

    # Include cross-practice audit (methods):
    python3 utils/post-validate-method.py practices/cisco-openshift/ --fix --audit

Fix chain (per practice, delegated to lint-practice.py):
    1. validate-practice-json.py  →  schema/baseline/integrity errors
    2. fix-common-issues.py --fix --all  →  structural fixes
    3. fix-competency-levels.py --fix  →  competency level name alignment
    4. Re-validate  →  check remaining errors
    5. assess-practice.py --errors-only  →  final quality check

Exit codes:
    0 - All practices pass (no errors)
    1 - One or more practices have errors
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils._shared import load_json

UTILS_DIR = Path(__file__).resolve().parent
SKIP_PREFIXES = ("_",)
SKIP_NAMES = {"manifest.json"}


def discover_practice_jsons(directory):
    """Find all practice/baseline JSON files in a directory, excluding internal files."""
    jsons = []
    for f in sorted(directory.glob("*.json")):
        if f.name in SKIP_NAMES:
            continue
        if any(f.name.startswith(p) for p in SKIP_PREFIXES):
            continue
        try:
            data = load_json(f, exit_on_error=False)
            kind = data.get("kind", "")
            if kind in ("practice", "practiceBaseline", "method"):
                jsons.append((f, kind))
        except Exception:
            continue
    return jsons


def run_lint(practice_path, baseline=None, fix=False, max_iterations=3):
    """Run lint-practice.py on a single file. Returns parsed report dict."""
    cmd = [
        sys.executable,
        str(UTILS_DIR / "lint-practice.py"),
        str(practice_path),
    ]
    if baseline:
        cmd.append(str(baseline))
    if fix:
        cmd.append("--fix")
    cmd.extend(["--max-iterations", str(max_iterations)])
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return json.loads(result.stdout)
    except (json.JSONDecodeError, TypeError):
        return {
            "practice": str(practice_path),
            "status": "ERROR",
            "final_errors": -1,
            "one_line": f"ERROR: lint-practice output not parseable: {result.stderr[:200]}",
        }


def run_audit(keleo_path, baseline_path):
    """Run audit-method-references.py on a .keleo bundle. Returns parsed report."""
    cmd = [
        sys.executable,
        str(UTILS_DIR / "audit-method-references.py"),
        str(keleo_path),
        "--baseline",
        str(baseline_path),
        "--json",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return json.loads(result.stdout)
    except (json.JSONDecodeError, TypeError):
        return {"error": result.stderr[:300]}


def main():
    parser = argparse.ArgumentParser(
        description="Post-validate all practice JSONs in a method directory"
    )
    parser.add_argument("directory", help="Practice directory path (e.g., practices/cisco-openshift/)")
    parser.add_argument("--baseline", help="Baseline JSON override (auto-discovered per practice if omitted)")
    parser.add_argument("--fix", action="store_true", help="Apply auto-fixes (default: validate only)")
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=3,
        help="Maximum fix iterations per practice (default: 3)",
    )
    parser.add_argument(
        "--one-line",
        action="store_true",
        help="Print one-line summary per practice",
    )
    parser.add_argument(
        "--audit",
        action="store_true",
        help="Run cross-practice audit on the .keleo bundle (methods only)",
    )
    args = parser.parse_args()

    directory = Path(args.directory)
    if not directory.is_dir():
        print(json.dumps({"error": f"Not a directory: {directory}"}))
        sys.exit(2)

    practice_files = discover_practice_jsons(directory)
    if not practice_files:
        print(json.dumps({"error": f"No practice/baseline JSON files found in {directory}"}))
        sys.exit(2)

    practices_only = [(f, k) for f, k in practice_files if k == "practice"]
    baselines_found = [(f, k) for f, k in practice_files if k == "practiceBaseline"]
    methods_found = [(f, k) for f, k in practice_files if k == "method"]

    results = []
    all_pass = True

    for practice_path, kind in practice_files:
        if kind == "method":
            continue

        report = run_lint(
            practice_path,
            baseline=args.baseline,
            fix=args.fix,
            max_iterations=args.max_iterations,
        )
        report["kind"] = kind
        results.append(report)

        if report.get("status") != "PASS":
            all_pass = False

        if args.one_line:
            print(f"  {practice_path.name}: {report.get('one_line', 'UNKNOWN')}")

    audit_report = None
    if args.audit and methods_found:
        method_name = directory.name
        keleo_path = directory.parent.parent / "bundles" / f"{method_name}.keleo"
        if keleo_path.exists():
            baseline_for_audit = args.baseline
            if not baseline_for_audit:
                ec_path = directory / "_effective-context.json"
                if ec_path.exists():
                    baseline_for_audit = str(ec_path)
            if baseline_for_audit:
                audit_report = run_audit(keleo_path, baseline_for_audit)
                audit_errors = audit_report.get("error_count", 0)
                if audit_errors > 0:
                    all_pass = False
                if args.one_line:
                    audit_status = "PASS" if audit_errors == 0 else "FAIL"
                    print(f"  cross-practice audit: {audit_status} ({audit_errors} errors)")

    total_errors = sum(r.get("final_errors", 0) for r in results if r.get("final_errors", 0) > 0)
    total_fixes = sum(len(r.get("fixes_applied", [])) for r in results)
    status = "PASS" if all_pass else "FAIL"

    summary = {
        "directory": str(directory),
        "practice_count": len(results),
        "status": status,
        "total_errors": total_errors,
        "total_fix_rounds": total_fixes,
        "results": results,
    }
    if audit_report is not None:
        summary["audit"] = audit_report

    one_line = f"{status} — {len(results)} practices, {total_errors} total errors"
    if total_fixes > 0:
        one_line += f", {total_fixes} fix rounds applied"
    summary["one_line"] = one_line

    if args.one_line:
        print(f"\n{one_line}")
    else:
        print(json.dumps(summary, indent=2))

    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
