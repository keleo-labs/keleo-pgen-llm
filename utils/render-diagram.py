#!/usr/bin/env python3
"""Render declarative diagram specs into styled SVG for markdown reports.

Thin wrapper. The engine lives in `.claude/skills/diagram-foundation/`, which
is a vendored copy of the user-level foundation at
`~/.claude/skills/diagram-foundation/` — the same convention CLAUDE.md states
for the deck tree. Fix upstream, then re-copy down; do not edit the copy.

The engine is shared because the deck skills need the same layouts: a diagram
on a slide is upgraded to native Google Slides shapes, which needs the spec's
structure rather than its rendered SVG.

Usage is unchanged:
    python3 utils/render-diagram.py <spec>.json [-o <out>.svg] [--stdout]
    python3 utils/render-diagram.py --dir reports/assets/<report-slug>/
    python3 utils/render-diagram.py --spec-help

Run `--spec-help` for the spec reference, or read
`.claude/skills/diagram-foundation/DIAGRAM-FOUNDATION.md` for the design
language and when to use which layout.
"""

import runpy
import sys
from pathlib import Path

ENGINE = (Path(__file__).resolve().parent.parent
          / ".claude" / "skills" / "diagram-foundation" / "scripts")

if not (ENGINE / "render-diagram.py").exists():
    print(f"Error: diagram engine missing at {ENGINE}\n"
          f"Re-copy it from ~/.claude/skills/diagram-foundation/",
          file=sys.stderr)
    sys.exit(1)

sys.path.insert(0, str(ENGINE))
runpy.run_path(str(ENGINE / "render-diagram.py"), run_name="__main__")
