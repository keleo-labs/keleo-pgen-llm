#!/usr/bin/env python3
"""Remove non-progressing alphas from pattern views and remove degenerate patterns.

A non-progressing alpha is one that stays at the same state across all views
of a pattern — it's background context, not a lifecycle participant. Removing
it makes the pattern cleaner and more meaningful.

After removing non-progressing alphas, patterns with fewer than 2 remaining
alphas are removed entirely (single-alpha patterns are themselves an anti-pattern
since the state progression is already visible on the alpha itself).
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils._shared import load_json, increment_version


def find_non_progressing(pattern):
    """Find alphas that don't progress across a pattern's views."""
    views = pattern.get("patternViews", [])
    if len(views) < 2:
        return {}

    alpha_states_per_view = {}
    for view in views:
        for alpha_state in view.get("alphaStates", []):
            name = alpha_state.get("alphaName", "")
            state = alpha_state.get("stateName", "")
            alpha_states_per_view.setdefault(name, []).append(state)

    non_progressing = {}
    for alpha_name, states in alpha_states_per_view.items():
        unique_states = set(states)
        if len(unique_states) == 1:
            non_progressing[alpha_name] = states[0]

    return non_progressing


def fix_pattern_progression(data, dry_run=True):
    """Remove non-progressing alphas from patterns. Returns list of fix descriptions."""
    fixes = []
    sources = [data]
    if data.get("kind") == "method":
        sources = data.get("practices", [])

    for source in sources:
        source_name = source.get("name", "root")
        patterns = source.get("patterns", [])

        for pi in range(len(patterns) - 1, -1, -1):
            pattern = patterns[pi]
            pat_name = pattern.get("name", f"pattern[{pi}]")

            views = pattern.get("patternViews", [])
            total_alphas = set()
            for view in views:
                for alpha_state in view.get("alphaStates", []):
                    total_alphas.add(alpha_state.get("alphaName", ""))

            if len(total_alphas) < 2:
                fixes.append({
                    "action": "remove-pattern",
                    "pattern": pat_name,
                    "practice": source_name,
                    "reason": f"Single-alpha pattern ({len(total_alphas)} alpha); "
                              "state progression already visible on the alpha itself",
                })
                if not dry_run:
                    patterns.pop(pi)
                continue

            non_prog = find_non_progressing(pattern)
            if not non_prog:
                continue

            remaining = total_alphas - set(non_prog.keys())

            if len(remaining) < 2:
                fixes.append({
                    "action": "remove-pattern",
                    "pattern": pat_name,
                    "practice": source_name,
                    "reason": f"Only {len(remaining)} alpha(s) progress; removing degenerate pattern",
                    "removed_alphas": list(non_prog.keys()),
                })
                if not dry_run:
                    patterns.pop(pi)
                continue

            for alpha_name, stuck_state in non_prog.items():
                fixes.append({
                    "action": "remove-alpha",
                    "pattern": pat_name,
                    "practice": source_name,
                    "alpha": alpha_name,
                    "stuck_state": stuck_state,
                    "views_affected": len(views),
                })

            if not dry_run:
                for view in views:
                    view["alphaStates"] = [
                        a for a in view.get("alphaStates", [])
                        if a.get("alphaName", "") not in non_prog
                    ]

    return fixes


def main():
    parser = argparse.ArgumentParser(
        description="Remove non-progressing alphas from pattern views"
    )
    parser.add_argument("file", help="Practice or method JSON file")
    parser.add_argument("--fix", action="store_true",
                        help="Apply fixes in-place (default: dry run)")
    parser.add_argument("--bump", choices=["patch", "minor", "major"],
                        default=None,
                        help="Bump version after fixing (default: no bump)")
    parser.add_argument("--json", action="store_true",
                        help="Output fixes as JSON")
    args = parser.parse_args()

    data = load_json(args.file)
    if data is None:
        sys.exit(1)

    fixes = fix_pattern_progression(data, dry_run=not args.fix)

    if args.json:
        print(json.dumps(fixes, indent=2))
    else:
        if not fixes:
            print("No non-progressing alphas found.")
        else:
            for f in fixes:
                if f["action"] == "remove-pattern":
                    print(f"REMOVE PATTERN: '{f['pattern']}' in {f['practice']} "
                          f"({f['reason']})")
                else:
                    print(f"REMOVE ALPHA: '{f['alpha']}' (stuck at '{f['stuck_state']}' "
                          f"across {f['views_affected']} views) from pattern "
                          f"'{f['pattern']}' in {f['practice']}")

            print(f"\nTotal: {len(fixes)} fix(es)")

    if args.fix and fixes:
        if args.bump:
            old_ver = data.get("version", "0.0.0")
            new_ver = increment_version(old_ver, args.bump)
            data["version"] = new_ver
            print(f"Version: {old_ver} → {new_ver}")

        with open(args.file, "w") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        print(f"Fixed: {args.file}")


if __name__ == "__main__":
    main()
