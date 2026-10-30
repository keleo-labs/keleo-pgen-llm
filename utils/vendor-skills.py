#!/usr/bin/env python3
"""Synchronise thin agent entrypoints with canonical repository skills.

Version 2.0.0: repository skills replace the former personal upstream sync.

Examples:
    python3 utils/vendor-skills.py --check
    python3 utils/vendor-skills.py --fix
    python3 utils/vendor-skills.py --fix --skills-dir .new-agent/skills
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CANONICAL = ROOT / "skills"
VENDORS = ROOT / "config" / "agent-vendors.json"


def frontmatter(source: str) -> str:
    if not source.startswith("---\n"):
        raise ValueError("canonical skill lacks YAML frontmatter")
    end = source.find("\n---\n", 4)
    if end < 0:
        raise ValueError("canonical skill lacks closing frontmatter marker")
    return source[: end + 5]


def wrapper(name: str, source: str, skills_dir: str) -> str:
    detail = ""
    overlay = ROOT / skills_dir / name / "adapter.md"
    if overlay.is_file():
        detail = f"Read `{skills_dir}/{name}/adapter.md` for this runtime's additions.\n"
    if skills_dir == ".claude/skills":
        detail += (
            "For Claude Code, use AskUserQuestion for structured user choices, "
            "the available web and browser tools for sources, and the Task tool "
            "when the canonical workflow calls for subagents.\n"
        )
    return (
        frontmatter(source)
        + f"\n# {name} agent entrypoint\n\n"
        + f"Read and follow `skills/{name}/SKILL.md`. Resolve its relative references "
          "from that canonical skill directory.\n\n"
        + detail
    ).rstrip() + "\n"


def sync(skills_dir: str, fix: bool) -> list[str]:
    rel = Path(skills_dir)
    if rel.is_absolute() or ".." in rel.parts or not rel.parts or rel.parts[0] == "skills":
        raise ValueError("skills directory must be a project-relative agent path")
    target = ROOT / rel
    problems = []
    expected = set()
    for skill in sorted(CANONICAL.glob("*/SKILL.md")):
        name = skill.parent.name
        destination = target / name / "SKILL.md"
        expected.add(destination)
        content = wrapper(name, skill.read_text(encoding="utf-8"), skills_dir)
        if not destination.exists() or destination.read_text(encoding="utf-8") != content:
            if fix:
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(content, encoding="utf-8")
            else:
                problems.append(str(destination.relative_to(ROOT)))
    for extra in target.glob("*/SKILL.md"):
        if extra not in expected:
            problems.append(f"unexpected {extra.relative_to(ROOT)}")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="report wrapper drift without writing")
    mode.add_argument("--fix", action="store_true", help="write missing or stale wrappers")
    parser.add_argument("--skills-dir", action="append", help="project-relative agent skill directory; defaults to Codex and Claude")
    args = parser.parse_args()
    try:
        vendors = json.loads(VENDORS.read_text(encoding="utf-8"))["vendors"]
        problems = []
        for vendor in vendors:
            for key in ("instructions", "hooks"):
                if not (ROOT / vendor[key]).is_file():
                    problems.append(f"missing {vendor['name']} {key}: {vendor[key]}")
        directories = args.skills_dir or [vendor["skillsDir"] for vendor in vendors if vendor["skillsDir"]]
        for directory in directories:
            problems.extend(sync(directory, args.fix))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(2, f"error: {exc}\n")
    if problems:
        print("\n".join(problems))
        return 1
    print("vendor skill entrypoints are in sync" if args.check else "vendor skill entrypoints updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
