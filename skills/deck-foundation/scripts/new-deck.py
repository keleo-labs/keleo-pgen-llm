#!/usr/bin/env python3
"""Scaffold a Slidev deck project wired to a local brand theme.

Every deck needs the same four things: a package.json, the Slidev CLI,
Playwright (which the export path depends on), and a theme on disk that
Slidev can resolve by relative path. Doing that by hand each time invites
the drift that breaks exports, so it lives here.

The theme is copied, not symlinked. A symlinked theme resolves outside the
project root, and Vite then skips the SFC scoped-style transform for its
layouts — the deck builds and exports cleanly but renders unstyled. The cost
is that a theme fix does not reach decks already scaffolded; re-running this
script on an existing directory refreshes the theme and leaves slides.md
alone.

    new-deck.py ~/decks/platform-adoption --title "Platform adoption"
    new-deck.py ./pitch --theme redhat --no-install
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
DEV_DEPS = ["@slidev/cli", "playwright-chromium"]

STARTER = """---
theme: {theme_ref}
title: {title_yaml}
layout: cover
variant: dark
eyebrow: Eyebrow
byline: {byline}
date: {date}
---

# {title}

One sentence saying why this matters to the people in the room.

---
layout: default
---

# Replace this with an assertion, not a topic

- Evidence for the assertion
- A second piece of evidence
- What follows from it
"""


def available_themes() -> list[str]:
    return sorted(
        p.name.removeprefix("theme-")
        for p in SKILL_DIR.glob("theme-*")
        if p.is_dir()
    )


def resolve_theme(name: str) -> Path:
    path = SKILL_DIR / f"theme-{name}"
    if not path.is_dir():
        themes = ", ".join(available_themes()) or "none found"
        sys.exit(f"unknown theme {name!r} (available: {themes})")
    return path


def npm_install(project: Path) -> None:
    print(f"installing {', '.join(DEV_DEPS)} …", flush=True)
    subprocess.run(
        ["npm", "install", "--silent", "--save-dev", *DEV_DEPS],
        cwd=project,
        check=True,
    )
    # Slidev's export path shells out to Playwright, which needs a browser
    # binary present — not just the npm package.
    print("installing chromium …", flush=True)
    subprocess.run(
        ["npx", "playwright", "install", "chromium"],
        cwd=project,
        check=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("directory", help="project directory to create")
    parser.add_argument("--title", default="Untitled deck")
    parser.add_argument("--theme", default="redhat", help="brand theme name")
    parser.add_argument("--byline", default="", help="speaker name for the cover")
    parser.add_argument("--date", default="", help="date shown on the cover")
    parser.add_argument(
        "--no-install",
        action="store_true",
        help="scaffold only; skip npm and browser installation",
    )
    parser.add_argument("--force", action="store_true", help="overwrite slides.md")
    args = parser.parse_args()

    theme_src = resolve_theme(args.theme)
    project = Path(args.directory).expanduser().resolve()
    project.mkdir(parents=True, exist_ok=True)

    pkg = project / "package.json"
    if not pkg.exists():
        pkg.write_text(
            json.dumps(
                {"name": project.name, "private": True, "type": "module"}, indent=2
            )
            + "\n"
        )

    # Copied, not symlinked — see the module docstring. node_modules would be
    # stale the moment the deck installs its own, so it never comes along.
    theme_dst = project / theme_src.name
    if theme_dst.is_symlink():
        theme_dst.unlink()
    elif theme_dst.exists():
        shutil.rmtree(theme_dst)
    shutil.copytree(
        theme_src,
        theme_dst,
        ignore=shutil.ignore_patterns("node_modules", "*.log", ".DS_Store"),
    )

    slides = project / "slides.md"
    if slides.exists() and not args.force:
        print(f"slides.md exists, leaving it alone (use --force to replace)")
    else:
        slides.write_text(
            STARTER.format(
                theme_ref=f"./{theme_src.name}",
                title=args.title,
                # A title containing ':' is valid prose but invalid unquoted
                # YAML, and the parse error it causes surfaces much later, at
                # export. JSON string syntax is a subset of YAML's, so this
                # quotes and escapes correctly.
                title_yaml=json.dumps(args.title),
                byline=args.byline,
                date=args.date,
            )
        )

    if not args.no_install:
        try:
            npm_install(project)
        except subprocess.CalledProcessError as exc:
            return exc.returncode or 1
        except FileNotFoundError:
            sys.exit("npm not found on PATH — install Node 18+ and retry")

    publish = SKILL_DIR / "scripts" / "publish-deck.py"
    print(f"\nscaffolded {project}")
    print(f"  theme    {theme_src.name} (copied)")
    print(f"  edit     {slides}")
    print(f"  preview  cd {project} && npx slidev")
    print(f"  publish  python3 {publish} {slides.name} --name {args.title!r} --pdf")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
