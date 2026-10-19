#!/usr/bin/env python3
"""Strip code-span backticks from symbolic-reference fields in a phase guide.

A Phase 2 mapping guide is prose, so authors reasonably write element names in
backticks. `validate-phase-output.py` extracts those names literally, so a
pattern view that says

    - Alpha Name: `RHEL Campaign Cascade`, State Name: `Red Hat Equipped`

yields the alpha name "`RHEL Campaign Cascade`", which never matches the name
taken from the `#### Alpha: RHEL Campaign Cascade` heading. The guide then fails
`alpha_pattern_coverage` with "0/N alphas take part in at least one pattern" —
a confident, wrong finding about a guide whose patterns are complete.

The same literal extraction reaches Phase 3, where a backticked name copied into
a JSON string value is a dangling symbolic reference. CARRY-FORWARD records 27
corrections of exactly that class on one document.

This normalises the labelled reference fields only. Prose, headings, tables and
backticked element names inside narrative text are left alone, because there the
code span is doing its job.

Usage:
    python3 utils/normalize-guide-refs.py <guide>.md [--fix] [--json]
    python3 utils/normalize-guide-refs.py --dir practices/<unit> [--fix]

Without --fix it reports what it would change and exits 1 if anything would.
Idempotent: a second run over a fixed file reports nothing.
"""

import argparse
import json
import re
import sys
from pathlib import Path

# Fields whose value is a symbolic reference to a named element rather than
# prose. Ordered longest-first so that "Work Product Instance Name" is matched
# before "Work Product Name" would partially match it.
REFERENCE_FIELDS = [
    "Work Product Instance Name",
    "Level Of Detail Name",
    "Narrative Element Name",
    "Recognized At Pattern View Name",
    "Recognized At State Name",
    "Activity Space Name",
    "Narrative Type Name",
    "Persona Group Name",
    "Work Product Name",
    "Orchestration Name",
    "Pattern View Name",
    "Competency Level Name",
    "Competency Name",
    "Alpha Instance Name",
    "Instance Name",
    "Persona Name",
    "Pattern Name",
    "Parent Alpha",
    "Target State",
    "Alpha Name",
    "State Name",
    "Focus Name",
    "Metric Name",
    "Relative To",
    "Led By",
]

# `Name` or `Name`, or `Name` at end of line. The value runs to a comma or the
# end of the line, so "Alpha Name: `X`, State Name: `Y`" is handled in one pass
# by applying the rule per field.
_FIELD_RE = re.compile(
    r"(?P<label>\b(?:" + "|".join(re.escape(f) for f in REFERENCE_FIELDS) + r")\s*:\s*)"
    r"`(?P<value>[^`\n]+)`"
)


def normalize(text):
    """Return (new_text, [(label, value), ...]) for every span stripped."""
    changes = []

    def _sub(m):
        changes.append((m.group("label").split(":")[0].strip(), m.group("value")))
        return m.group("label") + m.group("value")

    return _FIELD_RE.sub(_sub, text), changes


def process(path, fix):
    original = path.read_text(encoding="utf-8")
    updated, changes = normalize(original)
    if changes and fix:
        path.write_text(updated, encoding="utf-8")
    return changes


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="*", type=Path, help="Markdown guide files")
    ap.add_argument("--dir", type=Path, action="append", default=[],
                    help="Directory to sweep for 0*-*.md guides, recursively "
                         "(repeatable)")
    ap.add_argument("--fix", action="store_true", help="Write the normalised file")
    ap.add_argument("--json", action="store_true", help="Emit a JSON report")
    args = ap.parse_args()

    targets = list(args.files)
    for d in args.dir:
        # Recursive: guides live one level down, in `practices/<unit>/`, so a
        # non-recursive glob made the obvious `--dir practices` find nothing
        # and exit with "no input files" — which reads as "nothing to do"
        # rather than "wrong directory depth".
        targets.extend(sorted(p for p in d.rglob("0*-*.md")
                              if p.is_file() and "backup" not in str(p).lower()))

    if not targets:
        ap.error("no input files — pass a path or --dir")

    report = {"mode": "fix" if args.fix else "dry-run", "files": []}
    total = 0
    for path in targets:
        if not path.exists():
            print(f"missing: {path}", file=sys.stderr)
            continue
        changes = process(path, args.fix)
        total += len(changes)
        entry = {"path": str(path), "count": len(changes)}
        if changes:
            counts = {}
            for label, _ in changes:
                counts[label] = counts.get(label, 0) + 1
            entry["byField"] = counts
        report["files"].append(entry)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        for entry in report["files"]:
            if entry["count"]:
                fields = ", ".join(f"{k} x{v}" for k, v in sorted(entry["byField"].items()))
                verb = "stripped" if args.fix else "would strip"
                print(f"{entry['path']}: {verb} {entry['count']} code spans — {fields}")
            else:
                print(f"{entry['path']}: clean")

    return 0 if (args.fix or total == 0) else 1


if __name__ == "__main__":
    sys.exit(main())
