#!/usr/bin/env python3
"""Render every diagram a deck references, fitted to the slide.

Walks a Slidev markdown file for `diagram:` frontmatter keys, lays each spec
out for the slide's aspect ratio, and writes a PNG beside the spec — which is
where `layouts/diagram.vue` looks for it. Also writes a manifest so
publish-deck.py knows which diagrams can be upgraded to native Slides shapes
after the deck is published.

Specs are laid out for 16:9 before rendering, so a flow authored top-to-bottom
for a report page is reconsidered for a landscape frame. Where no orientation
fits, the diagram is left alone and the reason is reported — a diagram that
will not fit a slide is usually one carrying more than one idea.

Diagrams render in the deck's brand palette rather than the engine default,
so a figure on a slide reads as part of the deck instead of as something
pasted in from a report. Only the colour family changes; geometry and type
are identical, and the spec is untouched.

Usage:
    build-diagrams.py slides.md
    build-diagrams.py slides.md --width 1600      # raster width in px
    build-diagrams.py slides.md --palette navigator   # engine default colours
    build-diagrams.py slides.md --check           # report, write nothing

Exit codes: 0 ok, 1 a diagram failed to build, 2 bad arguments.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

DIAGRAM_SCRIPTS = Path(__file__).resolve().parent.parent.parent / "diagram-foundation" / "scripts"
sys.path.insert(0, str(DIAGRAM_SCRIPTS))

try:
    import spec_loader
    from diagram import use_palette
    from mermaid_render import MermaidUnavailable
except ImportError as exc:  # pragma: no cover - surfaced to the user
    print(f"Error: diagram-foundation not found at {DIAGRAM_SCRIPTS} ({exc})",
          file=sys.stderr)
    sys.exit(1)

# Slidev's 16:9 canvas. Diagrams are fitted to the area left under a title.
SLIDE_RATIO = 16 / 9
FRAME_RATIO = 16 / 7.4

RE_DIAGRAM_KEY = re.compile(r"^diagram:\s*(\S+)\s*$", re.MULTILINE)


def find_references(source: Path) -> list[str]:
    """Spec paths referenced by the deck, in document order."""
    return RE_DIAGRAM_KEY.findall(source.read_text(encoding="utf-8"))


def rasterise(svg_path: Path, png_path: Path, width: int) -> None:
    proc = subprocess.run(
        ["npx", "--yes", "sharp-cli", "--input", str(svg_path),
         "--output", str(png_path.parent), "--format", "png",
         "resize", str(width)],
        capture_output=True, text=True, timeout=300,
    )
    produced = png_path.parent / f"{svg_path.stem}.png"
    if proc.returncode != 0 or not produced.exists():
        detail = (proc.stderr or proc.stdout).strip()
        raise RuntimeError(f"sharp-cli failed on {svg_path.name}: {detail[:300]}")
    if produced != png_path:
        produced.replace(png_path)


def build(source: Path, width: int, check: bool,
          palette: str = "redhat") -> tuple[list[dict], list[str]]:
    """Render each referenced diagram. Returns (manifest, notes)."""
    use_palette(palette)
    manifest, notes = [], []
    for order, ref in enumerate(find_references(source)):
        spec_path = (source.parent / ref).resolve()
        if not spec_path.exists():
            raise RuntimeError(f"diagram spec not found: {ref}")

        try:
            diagram = spec_loader.load(spec_path, FRAME_RATIO)
        except (spec_loader.SpecError, MermaidUnavailable) as exc:
            raise RuntimeError(str(exc)) from None

        if diagram.note:
            notes.append(f"{spec_path.stem}: {diagram.note}")

        # The scene travels in the manifest rather than the spec, because a
        # Mermaid-backed diagram has no declarative spec to rebuild it from —
        # and re-deriving one would mean invoking Mermaid a second time at
        # publish. A picture-only diagram carries no scene and is skipped by
        # the upgrade pass.
        entry = {
            "order": order,
            "marker": spec_path.stem,
            "spec": str(spec_path),
            "png": str(spec_path.with_suffix(".png")),
            "editable": diagram.editable,
            "scene": diagram.scene(),
        }
        manifest.append(entry)

        if check:
            continue

        svg_path = spec_path.with_suffix(".svg")
        svg_path.write_text(diagram.svg(), encoding="utf-8")
        rasterise(svg_path, spec_path.with_suffix(".png"), width)

    return manifest, notes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("source", type=Path, help="Slidev markdown entry file")
    parser.add_argument("--width", type=int, default=1600,
                        help="raster width in px (default 1600)")
    parser.add_argument("--workdir", type=Path,
                        help="build directory (default: <source dir>/build)")
    parser.add_argument("--check", action="store_true",
                        help="report what would be built, write nothing")
    parser.add_argument("--palette", default="redhat",
                        help="colour family: redhat (default) or navigator")
    args = parser.parse_args()

    if not args.source.exists():
        print(f"Error: no such file: {args.source}", file=sys.stderr)
        return 2

    workdir = args.workdir or args.source.parent / "build"

    try:
        manifest, notes = build(args.source, args.width, args.check, args.palette)
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if not manifest:
        print("no diagrams referenced")
        return 0

    if not args.check:
        workdir.mkdir(parents=True, exist_ok=True)
        (workdir / "diagrams.json").write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    verb = "would build" if args.check else "built"
    print(f"{verb} {len(manifest)} diagram(s)")
    for entry in manifest:
        print(f"  {entry['marker']}")
    for note in notes:
        print(f"  note: {note}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
