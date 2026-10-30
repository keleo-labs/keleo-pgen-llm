#!/usr/bin/env python3
"""Render declarative diagram specs into styled SVG for markdown reports.

Thin wrapper. The engine lives in the canonical
`skills/diagram-foundation/` tree.

The engine is shared because the deck skills need the same layouts: a diagram
on a slide is upgraded to native Google Slides shapes, which needs the spec's
structure rather than its rendered SVG.

Usage is unchanged:
    python3 utils/render-diagram.py <spec>.json [-o <out>.svg] [--stdout]
    python3 utils/render-diagram.py --dir reports/<report-slug>/assets/
    python3 utils/render-diagram.py --spec-help

Run `--spec-help` for the spec reference, or read
`skills/diagram-foundation/DIAGRAM-FOUNDATION.md` for the design
language and when to use which layout.
"""

import runpy
import sys
from pathlib import Path

ENGINE = (Path(__file__).resolve().parent.parent
          / "skills" / "diagram-foundation" / "scripts")

if not (ENGINE / "render-diagram.py").exists():
    print(f"Error: diagram engine missing at {ENGINE}",
          file=sys.stderr)
    sys.exit(1)

sys.path.insert(0, str(ENGINE))
runpy.run_path(str(ENGINE / "render-diagram.py"), run_name="__main__")
