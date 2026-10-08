#!/usr/bin/env python3
"""Re-copy user-level skills into the project so a clone is self-contained.

Several skills live upstream at `~/.claude/skills/` and are vendored here so
the repository distributes with deck and diagram capability — CLAUDE.md states
the convention: fix upstream, then re-copy. Doing that by hand is how the two
trees drift, which is what this exists to prevent.

Text files are rewritten on the way down so `~/.claude/skills/...` becomes
`.claude/skills/...`; CLAUDE.md calls repo-relative paths the only intended
difference.

One file is deliberately excluded. `deck-foundation/scripts/inspect-template.py`
re-execs into a virtualenv managed by `skills/python-env`, which is not
vendored; the project copy imports python-pptx directly instead. Copying the
upstream version down would point it at a directory that does not exist here.

Usage:
    python3 utils/vendor-skills.py --check      # report drift, write nothing
    python3 utils/vendor-skills.py              # re-copy everything
    python3 utils/vendor-skills.py --only deck-foundation

Exit codes: 0 in sync (or copied), 1 drift found with --check, 2 bad arguments.
"""

from __future__ import annotations

import argparse
import filecmp
import shutil
import sys
from pathlib import Path

UPSTREAM = Path.home() / ".claude" / "skills"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOCAL = PROJECT_ROOT / ".claude" / "skills"

VENDORED = [
    "diagram-foundation",
    "diagram",
    "deck-foundation",
    "slide-deck",
    "pitch-deck",
    "exec-readout",
]

# Paths, relative to a vendored skill, that must keep the project's version.
PRESERVE = {
    "deck-foundation": {"scripts/inspect-template.py"},
}

SKIP_DIRS = {"__pycache__", ".git", "node_modules"}
TEXT_SUFFIXES = {".md", ".py", ".vue", ".ts", ".js", ".json", ".css", ".feature"}

REWRITE = ("~/.claude/skills/", ".claude/skills/")

NOTE_MARKER = "> **Vendored copy.**"
NOTE_TEMPLATE = """\
> **Vendored copy.** This tree is distributed with `keleo-pgen-llm` so the
> capability works from a clone without a user-level install. It tracks the
> global skill at `~/.claude/skills/{name}/` version by version; the only
> intended difference is that paths are repo-relative rather than
> `~/.claude/skills/…`. If the two diverge otherwise, the global copy is
> upstream. Re-copy with `python3 utils/vendor-skills.py`.
"""


def entry_doc(rel: Path) -> bool:
    """Is this a skill's front-door document, where the note belongs?"""
    return len(rel.parts) == 1 and (
        rel.name == "SKILL.md" or rel.name.endswith("-FOUNDATION.md"))


def inject_note(text: str, name: str) -> str:
    """Put the vendoring note under the first heading.

    The note is applied on the way down rather than kept in the project copy,
    because any re-copy would otherwise wipe it — which is exactly what
    happened before this tool existed.
    """
    if NOTE_MARKER in text:
        return text
    note = NOTE_TEMPLATE.format(name=name)
    lines = text.splitlines(keepends=True)
    for index, line in enumerate(lines):
        if line.startswith("# "):
            rest = lines[index + 1:]
            # Skip a blank line so the note does not butt against the title.
            offset = 1 if rest and not rest[0].strip() else 0
            head = lines[:index + 1 + offset]
            gap = "" if offset else "\n"
            return "".join(head) + gap + note + "\n" + "".join(rest[offset:])
    return note + "\n" + text


def iter_files(root: Path):
    for path in sorted(root.rglob("*")):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.is_file():
            yield path


def localise(text: str, name: str, rel: Path) -> str:
    text = text.replace(*REWRITE)
    if entry_doc(rel):
        text = inject_note(text, name)
    return text


def would_differ(src: Path, dst: Path, name: str, rel: Path) -> bool:
    if not dst.exists():
        return True
    if src.suffix in TEXT_SUFFIXES:
        try:
            return localise(src.read_text(encoding="utf-8"), name, rel) != \
                dst.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            pass
    return not filecmp.cmp(src, dst, shallow=False)


def copy_one(src: Path, dst: Path, name: str, rel: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.suffix in TEXT_SUFFIXES:
        try:
            dst.write_text(localise(src.read_text(encoding="utf-8"), name, rel),
                           encoding="utf-8")
            return
        except UnicodeDecodeError:
            pass
    shutil.copy2(src, dst)


def sync(names: list[str], check: bool) -> tuple[list[str], list[str]]:
    """Returns (changed, missing-upstream)."""
    changed, missing = [], []

    for name in names:
        src_root = UPSTREAM / name
        if not src_root.is_dir():
            missing.append(name)
            continue
        dst_root = LOCAL / name
        preserve = PRESERVE.get(name, set())

        upstream_rel = set()
        for src in iter_files(src_root):
            rel = src.relative_to(src_root)
            upstream_rel.add(rel.as_posix())
            if rel.as_posix() in preserve:
                continue
            dst = dst_root / rel
            if would_differ(src, dst, name, rel):
                changed.append(f"{name}/{rel.as_posix()}")
                if not check:
                    copy_one(src, dst, name, rel)

        # A file deleted upstream should go here too, or the project keeps
        # running something that no longer exists in the source of truth.
        if dst_root.is_dir():
            for dst in iter_files(dst_root):
                rel = dst.relative_to(dst_root).as_posix()
                if rel in preserve or rel in upstream_rel:
                    continue
                changed.append(f"{name}/{rel} (removed upstream)")
                if not check:
                    dst.unlink()

    return changed, missing


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true",
                        help="report drift without writing; exits 1 if any")
    parser.add_argument("--only", nargs="+", metavar="SKILL",
                        help=f"limit to named skills (default: {', '.join(VENDORED)})")
    args = parser.parse_args()

    names = args.only or VENDORED
    unknown = [n for n in names if n not in VENDORED]
    if unknown:
        print(f"Error: not vendored skills: {', '.join(unknown)}", file=sys.stderr)
        return 2

    if not UPSTREAM.is_dir():
        print(f"Error: no upstream skills at {UPSTREAM}", file=sys.stderr)
        return 2

    changed, missing = sync(names, args.check)

    for name in missing:
        print(f"warning: {name} not found upstream at {UPSTREAM / name}",
              file=sys.stderr)

    if not changed:
        print(f"in sync — {len(names)} vendored skill(s) match upstream")
        return 0

    verb = "drifted" if args.check else "copied"
    print(f"{verb}: {len(changed)} file(s)")
    for entry in changed:
        print(f"  {entry}")
    if args.check:
        print("\nrun `python3 utils/vendor-skills.py` to re-copy", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
