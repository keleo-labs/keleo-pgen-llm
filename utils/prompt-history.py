#!/usr/bin/env python3
"""Manage prompt history files for practice/baseline generation sessions.

Records the user prompt, source materials, resolved dependencies, phase
execution, key decisions, and final deliverables as a structured markdown
document inside the practice/baseline output folder.

Usage:
    # Initialise a new prompt history
    python3 utils/prompt-history.py practices/my-practice/ --init \
        --type practice --name "My Practice" --prompt "Generate a practice for ..."

    # Record source materials (one per call, or multiple)
    python3 utils/prompt-history.py practices/my-practice/ --add-source \
        --source-type file --source-path docs/guide.pdf --source-desc "Migration guide"

    # Record a resolved dependency
    python3 utils/prompt-history.py practices/my-practice/ --add-dependency \
        --dep-type baseline --dep-name "Platform Adoption Essentials" \
        --dep-path deps/platform-adoption-kernel.json --dep-version "2.3.0"

    # Record a decision
    python3 utils/prompt-history.py practices/my-practice/ --add-decision \
        --decision-label "Delineation Gate" \
        --decision-text "Single practice: 5 alphas across 2 focuses. Primary alpha: Platform Migration"

    # Record phase start
    python3 utils/prompt-history.py practices/my-practice/ --start-phase \
        --phase "Phase 1: Analysis"

    # Record phase completion
    python3 utils/prompt-history.py practices/my-practice/ --end-phase \
        --phase "Phase 1: Analysis" --phase-output "01-analysis-report.md" \
        --phase-validation "PASS"

    # Record a deliverable
    python3 utils/prompt-history.py practices/my-practice/ --add-deliverable \
        --deliverable-path "bundles/my-practice.keleo" \
        --deliverable-desc "Packaged practice bundle"

    # Finalise the session
    python3 utils/prompt-history.py practices/my-practice/ --finalize
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone

HISTORY_FILENAME = "00-prompt-history.md"


def _now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _history_path(directory):
    return os.path.join(directory, HISTORY_FILENAME)


def _ensure_dir(directory):
    os.makedirs(directory, exist_ok=True)


def _read_history(directory):
    path = _history_path(directory)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return None


def _write_history(directory, content):
    _ensure_dir(directory)
    path = _history_path(directory)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def _append_section(directory, section_text):
    """Append text before the final --- marker, or at end if no marker."""
    content = _read_history(directory)
    if content is None:
        print(json.dumps({"error": f"No prompt history found in {directory}. Run --init first."}))
        sys.exit(1)

    # Insert before the final horizontal rule + status line, if present
    finalize_marker = "\n---\n\n**Status:**"
    if finalize_marker in content:
        idx = content.index(finalize_marker)
        content = content[:idx] + section_text + content[idx:]
    else:
        content = content.rstrip("\n") + "\n" + section_text
    _write_history(directory, content)


def _append_to_section(directory, section_heading, entry_text):
    """Append an entry under an existing section heading."""
    content = _read_history(directory)
    if content is None:
        print(json.dumps({"error": f"No prompt history found in {directory}. Run --init first."}))
        sys.exit(1)

    if section_heading not in content:
        # Section doesn't exist yet — create it and add the entry
        _append_section(directory, f"\n{section_heading}\n\n{entry_text}\n")
        return

    # Find the section and append before the next ## heading or end
    lines = content.split("\n")
    insert_idx = None
    in_section = False
    for i, line in enumerate(lines):
        if line.strip() == section_heading.strip():
            in_section = True
            continue
        if in_section and line.startswith("## "):
            insert_idx = i
            break
        if in_section and line.strip() == "---":
            insert_idx = i
            break

    if insert_idx is None:
        insert_idx = len(lines)

    # Walk backwards past blank lines to find the real end of section content
    while insert_idx > 0 and lines[insert_idx - 1].strip() == "":
        insert_idx -= 1

    lines.insert(insert_idx, entry_text)
    _write_history(directory, "\n".join(lines))


def _count_entries(directory, section_heading):
    """Count numbered entries (lines starting with | N |) in a section."""
    content = _read_history(directory)
    if content is None or section_heading not in content:
        return 0
    lines = content.split("\n")
    in_section = False
    count = 0
    for line in lines:
        if line.strip() == section_heading.strip():
            in_section = True
            continue
        if in_section and line.startswith("## "):
            break
        if in_section and re.match(r"^\| \d+ \|", line):
            count += 1
    return count


def cmd_init(args):
    """Create a new prompt history file."""
    directory = args.directory
    existing = _read_history(directory)
    if existing and not args.force:
        print(json.dumps({"error": f"Prompt history already exists in {directory}. Use --force to overwrite."}))
        sys.exit(1)

    prompt_text = args.prompt.replace("\n", "\n> ")
    gen_type = args.type or "practice"

    content = f"""# Prompt History

## Session

| Field | Value |
|-------|-------|
| **Date** | {_now_iso()} |
| **Type** | {gen_type} |
| **Name** | {args.name} |

## User Prompt

> {prompt_text}

## Source Materials

| # | Type | Path / URL | Description |
|---|------|-----------|-------------|

## Dependencies

| # | Role | Name | Path | Version |
|---|------|------|------|---------|

## Decisions

## Execution Log

"""
    _write_history(directory, content)
    print(json.dumps({
        "status": "created",
        "path": _history_path(directory),
        "name": args.name,
        "type": gen_type,
    }))


def cmd_add_source(args):
    """Record a source material."""
    directory = args.directory
    n = _count_entries(directory, "## Source Materials") + 1
    entry = f"| {n} | {args.source_type} | `{args.source_path}` | {args.source_desc} |"
    _append_to_section(directory, "## Source Materials", entry)
    print(json.dumps({"status": "added", "section": "sources", "index": n}))


def cmd_add_dependency(args):
    """Record a resolved dependency."""
    directory = args.directory
    n = _count_entries(directory, "## Dependencies") + 1
    version = args.dep_version or "-"
    entry = f"| {n} | {args.dep_type} | {args.dep_name} | `{args.dep_path}` | {version} |"
    _append_to_section(directory, "## Dependencies", entry)
    print(json.dumps({"status": "added", "section": "dependencies", "index": n}))


def cmd_add_decision(args):
    """Record a key decision."""
    directory = args.directory
    timestamp = _now_iso()
    entry = f"\n### {args.decision_label}\n\n- **Time:** {timestamp}\n- {args.decision_text}\n"
    _append_to_section(directory, "## Decisions", entry)
    print(json.dumps({"status": "added", "section": "decisions", "label": args.decision_label}))


def cmd_start_phase(args):
    """Record phase start."""
    directory = args.directory
    timestamp = _now_iso()
    entry = f"\n### {args.phase}\n\n- **Started:** {timestamp}\n"
    _append_to_section(directory, "## Execution Log", entry)
    print(json.dumps({"status": "started", "phase": args.phase, "time": timestamp}))


def cmd_end_phase(args):
    """Record phase completion."""
    directory = args.directory
    content = _read_history(directory)
    if content is None:
        print(json.dumps({"error": "No prompt history found."}))
        sys.exit(1)

    timestamp = _now_iso()
    completion_lines = [f"- **Completed:** {timestamp}"]
    if args.phase_output:
        completion_lines.append(f"- **Output:** `{args.phase_output}`")
    if args.phase_validation:
        completion_lines.append(f"- **Validation:** {args.phase_validation}")

    phase_heading = f"### {args.phase}"
    if phase_heading in content:
        # Append completion info to the existing phase section
        lines = content.split("\n")
        insert_idx = None
        found_heading = False
        for i, line in enumerate(lines):
            if line.strip() == phase_heading:
                found_heading = True
                continue
            if found_heading and (line.startswith("### ") or line.startswith("## ") or line.strip() == "---"):
                insert_idx = i
                break
        if insert_idx is None:
            insert_idx = len(lines)
        # Walk backwards past blank lines
        while insert_idx > 0 and lines[insert_idx - 1].strip() == "":
            insert_idx -= 1
        for j, cl in enumerate(completion_lines):
            lines.insert(insert_idx + j, cl)
        _write_history(directory, "\n".join(lines))
    else:
        # Phase wasn't started — create a combined entry
        entry = f"\n### {args.phase}\n\n" + "\n".join(completion_lines) + "\n"
        _append_to_section(directory, "## Execution Log", entry)

    print(json.dumps({"status": "completed", "phase": args.phase, "time": timestamp}))


def cmd_add_deliverable(args):
    """Record a deliverable."""
    directory = args.directory
    content = _read_history(directory)
    if content is None:
        print(json.dumps({"error": "No prompt history found."}))
        sys.exit(1)

    section = "## Deliverables"
    if section not in content:
        table_header = f"\n{section}\n\n| # | File | Description |\n|---|------|-------------|\n"
        _append_section(directory, table_header)

    n = _count_entries(directory, section) + 1
    entry = f"| {n} | `{args.deliverable_path}` | {args.deliverable_desc} |"
    _append_to_section(directory, section, entry)
    print(json.dumps({"status": "added", "section": "deliverables", "index": n}))


def cmd_finalize(args):
    """Mark the session as complete."""
    directory = args.directory
    content = _read_history(directory)
    if content is None:
        print(json.dumps({"error": "No prompt history found."}))
        sys.exit(1)

    timestamp = _now_iso()
    footer = f"\n---\n\n**Status:** Complete ({timestamp})\n"

    # Remove existing status line if re-finalising
    status_pattern = r"\n---\n\n\*\*Status:\*\*.*\n"
    content = re.sub(status_pattern, "", content)

    content = content.rstrip("\n") + "\n" + footer
    _write_history(directory, content)
    print(json.dumps({"status": "finalised", "time": timestamp, "path": _history_path(directory)}))


def main():
    parser = argparse.ArgumentParser(
        description="Manage prompt history files for practice/baseline generation sessions"
    )
    parser.add_argument(
        "directory",
        help="Practice or baseline output directory (e.g., practices/my-practice/)",
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--init", action="store_true", help="Create a new prompt history")
    group.add_argument("--add-source", action="store_true", help="Record a source material")
    group.add_argument("--add-dependency", action="store_true", help="Record a resolved dependency")
    group.add_argument("--add-decision", action="store_true", help="Record a key decision")
    group.add_argument("--start-phase", action="store_true", help="Record phase start")
    group.add_argument("--end-phase", action="store_true", help="Record phase completion")
    group.add_argument("--add-deliverable", action="store_true", help="Record a deliverable")
    group.add_argument("--finalize", action="store_true", help="Mark session complete")

    # --init options
    parser.add_argument("--type", choices=["practice", "baseline", "method"], help="Generation type")
    parser.add_argument("--name", help="Practice/baseline/method name")
    parser.add_argument("--prompt", help="User's original prompt text")
    parser.add_argument("--force", action="store_true", help="Overwrite existing history")

    # --add-source options
    parser.add_argument("--source-type", help="Source type (file, url, google-doc, google-slides)")
    parser.add_argument("--source-path", help="Source file path or URL")
    parser.add_argument("--source-desc", help="Source description")

    # --add-dependency options
    parser.add_argument("--dep-type", help="Dependency role (baseline, practice, method, bundle)")
    parser.add_argument("--dep-name", help="Dependency name")
    parser.add_argument("--dep-path", help="Resolved file path")
    parser.add_argument("--dep-version", help="Dependency version")

    # --add-decision options
    parser.add_argument("--decision-label", help="Decision label (e.g., 'Delineation Gate')")
    parser.add_argument("--decision-text", help="Decision description")

    # --start-phase / --end-phase options
    parser.add_argument("--phase", help="Phase name (e.g., 'Phase 1: Analysis')")
    parser.add_argument("--phase-output", help="Output file name")
    parser.add_argument("--phase-validation", help="Validation result (e.g., 'PASS', 'FAIL - 2 errors')")

    # --add-deliverable options
    parser.add_argument("--deliverable-path", help="Deliverable file path")
    parser.add_argument("--deliverable-desc", help="Deliverable description")

    args = parser.parse_args()

    if args.init:
        if not args.name or not args.prompt:
            parser.error("--init requires --name and --prompt")
        cmd_init(args)
    elif args.add_source:
        if not args.source_type or not args.source_path or not args.source_desc:
            parser.error("--add-source requires --source-type, --source-path, and --source-desc")
        cmd_add_source(args)
    elif args.add_dependency:
        if not args.dep_type or not args.dep_name or not args.dep_path:
            parser.error("--add-dependency requires --dep-type, --dep-name, and --dep-path")
        cmd_add_dependency(args)
    elif args.add_decision:
        if not args.decision_label or not args.decision_text:
            parser.error("--add-decision requires --decision-label and --decision-text")
        cmd_add_decision(args)
    elif args.start_phase:
        if not args.phase:
            parser.error("--start-phase requires --phase")
        cmd_start_phase(args)
    elif args.end_phase:
        if not args.phase:
            parser.error("--end-phase requires --phase")
        cmd_end_phase(args)
    elif args.add_deliverable:
        if not args.deliverable_path or not args.deliverable_desc:
            parser.error("--add-deliverable requires --deliverable-path and --deliverable-desc")
        cmd_add_deliverable(args)
    elif args.finalize:
        cmd_finalize(args)


if __name__ == "__main__":
    main()
