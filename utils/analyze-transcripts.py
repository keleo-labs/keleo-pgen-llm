#!/usr/bin/env python3
"""
Analyze Claude Code session transcripts for user corrections and ad hoc scripts.

Parses .jsonl session transcript files to find:
- User correction messages (feedback, redirections, complaints)
- Ad hoc inline scripts (python3 -c, bash -c, etc.) that should be utils

Usage:
    python3 utils/analyze-transcripts.py <transcript.jsonl> [transcript2.jsonl ...]
    python3 utils/analyze-transcripts.py <transcript.jsonl> --corrections-only
    python3 utils/analyze-transcripts.py <transcript.jsonl> --scripts-only
    python3 utils/analyze-transcripts.py <transcript.jsonl> --json
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional


CORRECTION_PATTERNS = [
    r'\bno,\s',
    r'\bno\.\s',
    r'^no\s',
    r'\bnope\b',
    r'\bdon\'t\b',
    r'\bstop\b',
    r'\bwait\b',
    r'\bactually\b',
    r'\binstead\b',
    r'\bwrong\b',
    r'\bincorrect\b',
    r'\bmistake\b',
    r'\bshould(?:n\'t| not)\b',
    r'\bthat\'s not\b',
    r'\bnot what\b',
    r'\bnot that\b',
    r'\bundo\b',
    r'\brevert\b',
    r'\bchange\b.*\bback\b',
    r'\bI meant\b',
    r'\blet me clarify\b',
]

AD_HOC_PATTERNS = [
    r'python3?\s+-c\s+',
    r'bash\s+-c\s+',
    r'sh\s+-c\s+',
    r'perl\s+-[pe]\s+',
    r'ruby\s+-e\s+',
    r'node\s+-e\s+',
    r'awk\s+\'BEGIN\s*{',
]

SYSTEM_PREFIXES = ['<', 'Base directory', 'Tool loaded']
SYSTEM_KEYWORDS = ['task-notification', '<command-message>', 'SKILL.md', 'system-reminder']


def extract_text(msg: Dict[str, Any]) -> str:
    """Extract user-visible text from a message object."""
    content = msg.get("text") or msg.get("message", {}).get("content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
        return " ".join(parts)
    return ""


def extract_bash_commands(msg: Dict[str, Any]) -> List[str]:
    """Extract Bash tool commands from an assistant message."""
    commands = []
    message = msg.get("message", msg)
    content = message.get("content", [])
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict) and block.get("type") == "tool_use":
                if block.get("name") == "Bash":
                    cmd = block.get("input", {}).get("command", "")
                    if cmd:
                        commands.append(cmd)
    return commands


def is_system_message(text: str) -> bool:
    """Check if text is a system/framework message rather than user input."""
    for prefix in SYSTEM_PREFIXES:
        if text.startswith(prefix):
            return True
    text_lower = text.lower()
    return any(kw in text_lower for kw in SYSTEM_KEYWORDS)


def is_correction(text: str) -> bool:
    """Detect if user message contains correction language."""
    if is_system_message(text):
        return False
    text_lower = text.lower()
    return any(re.search(p, text_lower) for p in CORRECTION_PATTERNS)


def is_ad_hoc_script(command: str) -> bool:
    """Detect if command uses inline scripting instead of utils."""
    return any(re.search(p, command) for p in AD_HOC_PATTERNS)


def get_preceding_assistant_context(messages: List[Dict], index: int) -> str:
    """Get text context from the preceding assistant message."""
    for j in range(index - 1, max(0, index - 5), -1):
        if messages[j].get("type") == "assistant":
            msg = messages[j].get("message", messages[j])
            content = msg.get("content", [])
            if isinstance(content, list):
                for block in content[:2]:
                    if isinstance(block, dict) and block.get("type") == "text":
                        text = block.get("text", "").strip()
                        if text:
                            return text[:200]
    return ""


def extract_session_topic(messages: List[Dict]) -> str:
    """Extract session topic from first few user messages."""
    parts = []
    for msg in messages:
        if msg.get("type") != "user":
            continue
        text = extract_text(msg)
        if text and not is_system_message(text) and len(text) > 20:
            parts.append(text[:200])
        if len(parts) >= 3:
            break
    if not parts:
        return "Unknown"
    topic = " | ".join(parts)
    return topic[:400] + ("..." if len(topic) > 400 else "")


def analyze_transcript(filepath: Path) -> Dict[str, Any]:
    """Analyze a single transcript file."""
    result: Dict[str, Any] = {
        "file": str(filepath),
        "filename": filepath.name,
        "topic": "",
        "corrections": [],
        "ad_hoc_scripts": [],
        "total_messages": 0,
        "user_messages": 0,
        "assistant_messages": 0,
    }

    try:
        messages = []
        with open(filepath, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    messages.append(json.loads(line))
                except json.JSONDecodeError as e:
                    print(f"Warning: {filepath.name}:{line_num}: {e}", file=sys.stderr)

        result["total_messages"] = len(messages)
        result["topic"] = extract_session_topic(messages)

        for i, msg in enumerate(messages):
            msg_type = msg.get("type")

            if msg_type == "user":
                result["user_messages"] += 1
                text = extract_text(msg)
                if text and is_correction(text):
                    result["corrections"].append({
                        "index": i,
                        "text": text[:500],
                        "context": get_preceding_assistant_context(messages, i),
                    })

            elif msg_type == "assistant":
                result["assistant_messages"] += 1
                for cmd in extract_bash_commands(msg):
                    if is_ad_hoc_script(cmd):
                        result["ad_hoc_scripts"].append({
                            "index": i,
                            "command": cmd[:500],
                        })

    except Exception as e:
        print(f"Error analyzing {filepath}: {e}", file=sys.stderr)
        result["error"] = str(e)

    return result


def format_text_report(results: List[Dict], show_corrections: bool, show_scripts: bool) -> str:
    """Format analysis results as a readable text report."""
    lines = ["=" * 80, "CLAUDE CODE TRANSCRIPT ANALYSIS", "=" * 80, ""]

    totals = {"corrections": 0, "scripts": 0, "sessions": len(results)}

    for i, r in enumerate(results, 1):
        lines.append(f"{'=' * 80}")
        lines.append(f"SESSION {i}: {r['filename']}")
        lines.append(f"Messages: {r['total_messages']} (user: {r['user_messages']}, assistant: {r['assistant_messages']})")
        lines.append(f"{'=' * 80}")

        if r.get("error"):
            lines.append(f"ERROR: {r['error']}\n")
            continue

        lines.append(f"\nTOPIC: {r['topic']}")

        if show_corrections:
            corrections = r["corrections"]
            totals["corrections"] += len(corrections)
            if corrections:
                lines.append(f"\nUSER CORRECTIONS ({len(corrections)}):")
                lines.append("-" * 40)
                for j, c in enumerate(corrections, 1):
                    lines.append(f"\n  [{j}] Message #{c['index']}")
                    if c.get("context"):
                        lines.append(f"      Context: {c['context']}...")
                    lines.append(f"      User: {c['text']}")
            else:
                lines.append("\nUSER CORRECTIONS: None")

        if show_scripts:
            scripts = r["ad_hoc_scripts"]
            totals["scripts"] += len(scripts)
            if scripts:
                lines.append(f"\nAD HOC SCRIPTS ({len(scripts)}):")
                lines.append("-" * 40)
                for j, s in enumerate(scripts, 1):
                    lines.append(f"\n  [{j}] Message #{s['index']}")
                    lines.append(f"      {s['command']}")
            else:
                lines.append("\nAD HOC SCRIPTS: None")

        lines.append("")

    lines.append("=" * 80)
    summary_parts = [f"{totals['sessions']} session(s)"]
    if show_corrections:
        summary_parts.append(f"{totals['corrections']} correction(s)")
    if show_scripts:
        summary_parts.append(f"{totals['scripts']} ad hoc script(s)")
    lines.append(f"TOTALS: {', '.join(summary_parts)}")
    lines.append("=" * 80)

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Analyze Claude Code session transcripts for user corrections and ad hoc scripts.",
        epilog="Supports .jsonl transcript files from Claude Code sessions.",
    )
    parser.add_argument("transcripts", nargs="+", type=Path, help="Session transcript .jsonl files")
    parser.add_argument("--corrections-only", action="store_true", help="Show only user corrections")
    parser.add_argument("--scripts-only", action="store_true", help="Show only ad hoc scripts")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    for f in args.transcripts:
        if not f.exists():
            print(f"Error: File not found: {f}", file=sys.stderr)
            sys.exit(2)

    results = []
    for filepath in args.transcripts:
        print(f"Analyzing {filepath.name}...", file=sys.stderr)
        results.append(analyze_transcript(filepath))

    show_corrections = not args.scripts_only
    show_scripts = not args.corrections_only

    if args.json:
        output = []
        for r in results:
            entry: Dict[str, Any] = {"file": r["filename"], "topic": r["topic"]}
            if show_corrections:
                entry["corrections"] = r["corrections"]
            if show_scripts:
                entry["ad_hoc_scripts"] = r["ad_hoc_scripts"]
            entry["counts"] = {
                "total": r["total_messages"],
                "user": r["user_messages"],
                "assistant": r["assistant_messages"],
            }
            output.append(entry)
        json.dump(output, sys.stdout, indent=2)
        print()
    else:
        print(format_text_report(results, show_corrections, show_scripts))


if __name__ == "__main__":
    main()
