#!/usr/bin/env python3
"""Manage prompt history files for generation sessions.

Records the user prompt, source materials, resolved dependencies, phase
execution, key decisions, and final deliverables as a structured markdown
document inside the practice, baseline, or report output folder.

Usage:
    # Initialise a new prompt history
    python3 utils/prompt-history.py practices/my-practice/ --init \
        --type practice --name "My Practice" --prompt "Generate a practice for ..."

    # ... or for a report workspace (reports/<slug>/)
    python3 utils/prompt-history.py reports/my-report/ --init \
        --type report --name "My Report" --prompt "Write a report on ..."

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

    # Record a question put to the user and their answer
    python3 utils/prompt-history.py practices/my-practice/ --add-interaction \
        --interaction-label "Phase 1 Review Gate" \
        --interaction-question "Review 01-analysis-report.md — confirm or request changes?" \
        --interaction-answer "Drop the legacy VM section, otherwise fine"

    # Hook mode: record the active session's user turns automatically (stdin JSON)
    python3 utils/prompt-history.py --hook user-prompt
    python3 utils/prompt-history.py --hook tool

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
import contextlib
import io
import json
import os
import re
import sys
from datetime import datetime, timezone

HISTORY_FILENAME = "00-prompt-history.md"

#: Written by --init, cleared by --finalize. Tells the hooks which history is live.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POINTER_PATH = os.path.join(PROJECT_ROOT, ".tmp", "active-prompt-history.json")

#: Interactions are provenance, not an archive — long pastes get trimmed.
MAX_INTERACTION_CHARS = 4000


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


def _set_active(directory, name, gen_type):
    """Point the hooks at this history. Last --init wins."""
    os.makedirs(os.path.dirname(POINTER_PATH), exist_ok=True)
    with open(POINTER_PATH, "w", encoding="utf-8") as f:
        json.dump({
            "directory": os.path.abspath(directory),
            "name": name,
            "type": gen_type,
            "activated": _now_iso(),
        }, f, indent=2)


def _clear_active():
    with contextlib.suppress(OSError):
        os.remove(POINTER_PATH)


def _read_active():
    """Return the active history directory, or None if no session is live."""
    try:
        with open(POINTER_PATH, "r", encoding="utf-8") as f:
            directory = json.load(f).get("directory")
    except (OSError, ValueError):
        return None
    if directory and os.path.exists(_history_path(directory)):
        return directory
    return None


def _trim(text):
    text = (text or "").strip()
    if len(text) > MAX_INTERACTION_CHARS:
        omitted = len(text) - MAX_INTERACTION_CHARS
        text = text[:MAX_INTERACTION_CHARS] + f"\n… [{omitted} characters omitted]"
    return text


def _quote(text):
    """Render text as a markdown blockquote."""
    return "\n".join(f"> {line}" if line else ">" for line in _trim(text).split("\n"))


def _record_interaction(directory, label, question, answer):
    """Append one exchange to the Interaction Log."""
    parts = [f"\n### {_now_iso()} — {label}\n"]
    if question:
        parts.append(f"\n**Asked:**\n\n{_quote(question)}\n")
        parts.append(f"\n**Answered:**\n\n{_quote(answer)}")
    else:
        parts.append(f"\n{_quote(answer)}")
    _append_to_section(directory, "## Interaction Log", "".join(parts))


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

## Interaction Log

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
    _set_active(directory, args.name, gen_type)
    print(json.dumps({
        "status": "created",
        "path": _history_path(directory),
        "name": args.name,
        "type": gen_type,
        "hooksActive": True,
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


def cmd_add_interaction(args):
    """Record a user turn, or a question put to the user and their answer."""
    directory = args.directory
    label = args.interaction_label or ("Question" if args.interaction_question else "User input")
    _record_interaction(directory, label, args.interaction_question, args.interaction_answer)
    print(json.dumps({"status": "added", "section": "interactions", "label": label}))


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
    _clear_active()
    print(json.dumps({"status": "finalised", "time": timestamp, "path": _history_path(directory)}))


#: Maps a batch-file ``op`` value to its handler and required fields.
BATCH_OPS = {
    "add-source": ("cmd_add_source", ("source_type", "source_path", "source_desc")),
    "add-dependency": ("cmd_add_dependency", ("dep_type", "dep_name", "dep_path")),
    "add-decision": ("cmd_add_decision", ("decision_label", "decision_text")),
    "add-interaction": ("cmd_add_interaction", ("interaction_answer",)),
    "start-phase": ("cmd_start_phase", ("phase",)),
    "end-phase": ("cmd_end_phase", ("phase",)),
    "add-deliverable": ("cmd_add_deliverable", ("deliverable_path", "deliverable_desc")),
}


def cmd_batch(args):
    """Apply a list of operations from a JSON file in order.

    The file holds a list of objects, each with an ``op`` key naming a
    BATCH_OPS entry plus that op's fields using the same underscore names as
    the CLI flags (e.g. ``source_path``). Recording twenty source links is one
    call instead of twenty.
    """
    directory = args.directory
    with open(args.batch, "r", encoding="utf-8") as f:
        entries = json.load(f)

    if not isinstance(entries, list):
        print(json.dumps({"error": "Batch file must contain a JSON list of operations."}))
        sys.exit(1)

    applied = []
    for i, entry in enumerate(entries):
        op = entry.get("op")
        if op not in BATCH_OPS:
            print(json.dumps({"error": f"Entry {i}: unknown op '{op}'", "validOps": sorted(BATCH_OPS)}))
            sys.exit(1)
        func_name, required = BATCH_OPS[op]
        missing = [k for k in required if not entry.get(k)]
        if missing:
            print(json.dumps({"error": f"Entry {i} ({op}): missing {missing}"}))
            sys.exit(1)
        sub = argparse.Namespace(directory=directory, **{k: v for k, v in entry.items() if k != "op"})
        for key in ("source_type", "source_path", "source_desc", "dep_type", "dep_name",
                    "dep_path", "dep_version", "decision_label", "decision_text", "phase",
                    "phase_output", "phase_validation", "deliverable_path", "deliverable_desc",
                    "interaction_label", "interaction_question", "interaction_answer"):
            if not hasattr(sub, key):
                setattr(sub, key, None)
        with contextlib.redirect_stdout(io.StringIO()):  # per-op JSON would drown the summary
            globals()[func_name](sub)
        applied.append(op)

    print(json.dumps({"status": "batch-applied", "count": len(applied), "ops": applied}))


def cmd_activate(args):
    """Re-point the hooks at an existing history (e.g. resuming in a new session)."""
    directory = args.directory
    content = _read_history(directory)
    if content is None:
        print(json.dumps({"error": f"No prompt history found in {directory}."}))
        sys.exit(1)

    def field(label):
        match = re.search(rf"^\| \*\*{label}\*\* \| (.+?) \|$", content, re.MULTILINE)
        return match.group(1).strip() if match else None

    _set_active(directory, field("Name") or os.path.basename(directory.rstrip("/")),
                field("Type") or "practice")
    print(json.dumps({"status": "activated", "path": _history_path(directory)}))


def _render_answer(tool_response):
    """Flatten whatever AskUserQuestion returned into readable text."""
    if isinstance(tool_response, str):
        return tool_response
    if isinstance(tool_response, dict):
        answers = tool_response.get("answers")
        if isinstance(answers, dict):
            if len(answers) == 1:  # the question is already recorded above
                return next(iter(answers.values()))
            return "\n".join(f"{q} → {a}" for q, a in answers.items())
        for key in ("text", "content", "result"):
            if isinstance(tool_response.get(key), str):
                return tool_response[key]
    if isinstance(tool_response, list):
        texts = [b.get("text", "") for b in tool_response if isinstance(b, dict)]
        if any(texts):
            return "\n".join(t for t in texts if t)
    return json.dumps(tool_response, ensure_ascii=False)


def _ask_user_question_exchange(payload):
    """Return (question, answer) for an AskUserQuestion PostToolUse payload."""
    tool_input = payload.get("tool_input") or {}
    questions = tool_input.get("questions") or []
    asked = "\n".join(
        q.get("question", "") for q in questions if isinstance(q, dict) and q.get("question")
    )
    return asked or "(question text unavailable)", _render_answer(payload.get("tool_response"))


def cmd_hook(args):
    """Record a user turn from hook stdin. Never fails loudly — hooks must not break a session."""
    try:
        payload = json.load(sys.stdin)
    except (ValueError, OSError):
        return

    directory = _read_active()
    if directory is None:
        return  # no generation session is live

    # Bind the pointer to the first session that fires, so a concurrent session
    # in this project does not leak its prompts into someone else's history.
    session_id = payload.get("session_id")
    try:
        with open(POINTER_PATH, "r", encoding="utf-8") as f:
            pointer = json.load(f)
    except (OSError, ValueError):
        return
    bound = pointer.get("sessionId")
    if bound is None and session_id:
        pointer["sessionId"] = session_id
        with open(POINTER_PATH, "w", encoding="utf-8") as f:
            json.dump(pointer, f, indent=2)
    elif bound and session_id and bound != session_id:
        return

    if args.hook == "user-prompt":
        prompt = (payload.get("prompt") or "").strip()
        if prompt:
            _record_interaction(directory, "User input", None, prompt)
    elif args.hook == "tool":
        if payload.get("tool_name") != "AskUserQuestion":
            return
        asked, answered = _ask_user_question_exchange(payload)
        _record_interaction(directory, "Question", asked, answered)


def main():
    parser = argparse.ArgumentParser(
        description="Manage prompt history files for practice, baseline, and report sessions"
    )
    parser.add_argument(
        "directory",
        nargs="?",
        help="Practice, baseline, or report output directory (e.g., practices/my-practice/, "
        "reports/my-report/). Omitted in --hook mode, where the directory comes from the "
        "active-session pointer.",
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--init", action="store_true", help="Create a new prompt history")
    group.add_argument("--add-source", action="store_true", help="Record a source material")
    group.add_argument("--add-dependency", action="store_true", help="Record a resolved dependency")
    group.add_argument("--add-decision", action="store_true", help="Record a key decision")
    group.add_argument(
        "--add-interaction",
        action="store_true",
        help="Record a user turn, or a question put to the user and their answer",
    )
    group.add_argument(
        "--activate",
        action="store_true",
        help="Re-point the hooks at an existing history (resuming in a new session)",
    )
    group.add_argument(
        "--hook",
        choices=["user-prompt", "tool"],
        help="Hook mode: read the hook payload from stdin and record it against the active history",
    )
    group.add_argument("--start-phase", action="store_true", help="Record phase start")
    group.add_argument("--end-phase", action="store_true", help="Record phase completion")
    group.add_argument("--add-deliverable", action="store_true", help="Record a deliverable")
    group.add_argument("--finalize", action="store_true", help="Mark session complete")
    group.add_argument(
        "--batch",
        metavar="FILE",
        help="Apply a JSON list of operations in order (each entry has an 'op' key: "
        + ", ".join(sorted(BATCH_OPS)),
    )

    # --init options
    parser.add_argument(
        "--type",
        choices=["practice", "baseline", "method", "report"],
        help="Generation type",
    )
    parser.add_argument("--name", help="Practice/baseline/method/report name")
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

    # --add-interaction options
    parser.add_argument("--interaction-label", help="Context label (e.g., 'Phase 1 Review Gate')")
    parser.add_argument("--interaction-question", help="Question put to the user (omit for unprompted input)")
    parser.add_argument("--interaction-answer", help="What the user said, verbatim")

    # --start-phase / --end-phase options
    parser.add_argument("--phase", help="Phase name (e.g., 'Phase 1: Analysis')")
    parser.add_argument("--phase-output", help="Output file name")
    parser.add_argument("--phase-validation", help="Validation result (e.g., 'PASS', 'FAIL - 2 errors')")

    # --add-deliverable options
    parser.add_argument("--deliverable-path", help="Deliverable file path")
    parser.add_argument("--deliverable-desc", help="Deliverable description")

    args = parser.parse_args()

    if args.hook:
        cmd_hook(args)
        return

    if not args.directory:
        parser.error("directory is required outside --hook mode")

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
    elif args.add_interaction:
        if not args.interaction_answer:
            parser.error("--add-interaction requires --interaction-answer")
        cmd_add_interaction(args)
    elif args.activate:
        cmd_activate(args)
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
    elif args.batch:
        cmd_batch(args)


if __name__ == "__main__":
    main()
