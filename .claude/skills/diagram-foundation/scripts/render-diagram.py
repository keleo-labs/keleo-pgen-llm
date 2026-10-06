#!/usr/bin/env python3
"""Render declarative diagram specs into SVG, or into Google Slides requests.

Layout lives in diagram.py and emits a backend-neutral scene; this is the CLI
over the two backends. Standard library only.

Usage:
    render-diagram.py <spec>.json -o <out>.svg
    render-diagram.py <spec>.json --stdout
    render-diagram.py --dir <dir>/                 # render every spec in place
    render-diagram.py <spec>.json --fit 16:9       # transpose to suit a frame
    render-diagram.py <spec>.json --emit slides --page-id p \
                      --box 914400,914400,7315200,3657600 -o requests.json
    render-diagram.py --spec-help

Exit codes: 0 ok, 1 runtime failure, 2 bad arguments.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import svg_backend  # noqa: E402
from diagram import build_scene, fit_to_aspect, validate  # noqa: E402
from slides_backend import scene_requests  # noqa: E402

SPEC_HELP = """\
Diagram spec reference
======================

Every spec is a JSON object with a "layout" plus optional "title" and
"description".

Neither is drawn. The title becomes the SVG's <title>, the description its
<desc> and aria-label, falling back to the title when omitted. A diagram in a
report sits under a heading that already names it, so rendering the title
inside the image would print the same line twice.

Shared node fields (flow nodes, stack tiers, timeline phases, hub centre and
satellites all accept these):

  label      required  Short noun phrase. Wrapped to at most 3 lines.
  sublabel   optional  Secondary line in muted grey, at most 2 lines.
  emphasis   optional  default | muted | accent | selected

layout: "flow"
--------------
Layered boxes with directed edges. The workhorse: topologies, pipelines,
process flows, data paths.

  direction  "TB" (default) or "LR"
  nodes      [{id, label, sublabel?, emphasis?, group?, rank?}]
  edges      [{from, to, label?}]
  groups     [{id, label}]     draws a cluster rect behind member nodes

Rank is derived from the edge graph (longest path from a source). Setting
"rank" on a node pins that node and pushes its descendants below it; use it to
place a node that has no incoming edge, such as an out-of-band path joining
partway down.

layout: "stack"
---------------
Vertical tiers, top to bottom. Layer models, maturity stacks.

  tiers      [{label, sublabel?, emphasis?, items?: [str]}]
  width      optional band width in px (default 460)

layout: "timeline"
------------------
Sequential phase bands joined by arrows. Roadmaps, adoption journeys.

  phases     [{label, sublabel?, emphasis?, items?: [str]}]

layout: "hub"
-------------
Centre node with satellites on an ellipse. Relationship maps, fan-out.

  centre     {label, sublabel?, emphasis?}
  satellites [{label, sublabel?, emphasis?, edgeLabel?}]

Fitting a frame
---------------
--fit W:H transposes a `flow` between TB and LR when the other orientation
fills the frame markedly better. Only `flow` has a direction, so the other
layouts are unaffected. The flip is lossless: same nodes, same edges.

Example
-------
{
  "layout": "flow",
  "direction": "TB",
  "title": "Controller-centric scheduled remediation",
  "groups": [{"id": "onprem", "label": "On-premises"}],
  "nodes": [
    {"id": "lw",   "label": "Lightwell Network",
     "sublabel": "signed packages, SBOMs", "emphasis": "accent"},
    {"id": "repo", "label": "Artifactory / Nexus", "group": "onprem"},
    {"id": "ctrl", "label": "Automation controller", "group": "onprem"}
  ],
  "edges": [
    {"from": "lw",   "to": "repo", "label": "remote repository"},
    {"from": "repo", "to": "ctrl", "label": "scheduled scan"}
  ]
}
"""


def load_spec(path):
    """Return (spec, error)."""
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle), None
    except FileNotFoundError:
        return None, f"File not found: {path}"
    except json.JSONDecodeError as exc:
        return None, f"Invalid JSON in {path}: {exc}"


def parse_ratio(raw):
    try:
        w, _, h = raw.partition(":")
        return float(w) / float(h)
    except (ValueError, ZeroDivisionError):
        raise argparse.ArgumentTypeError(f"--fit wants W:H, got {raw!r}")


def prepare(path, fit_ratio):
    """Load, validate and optionally transpose. Returns (spec, note, error)."""
    spec, error = load_spec(path)
    if error:
        return None, None, error
    problems = validate(spec)
    if problems:
        return None, None, f"{path}: " + "; ".join(problems)
    note = None
    if fit_ratio:
        spec, note = fit_to_aspect(spec, fit_ratio)
    return spec, note, None


def render_file(spec_path, out_path, fit_ratio=None):
    """Render one spec file to SVG. Returns (ok, message)."""
    spec, note, error = prepare(spec_path, fit_ratio)
    if error:
        return False, error
    try:
        svg = svg_backend.render(build_scene(spec), spec)
    except (KeyError, TypeError, ValueError, ZeroDivisionError) as exc:
        return False, f"{spec_path}: could not render ({exc})"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(svg, encoding="utf-8")
    suffix = f" — {note}" if note else ""
    return True, f"{out_path}{suffix}"


def main():
    parser = argparse.ArgumentParser(
        description="Render diagram specs into SVG or Google Slides requests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Run --spec-help for the full spec reference.",
    )
    parser.add_argument("spec", nargs="?", help="Path to a diagram spec JSON file")
    parser.add_argument("-o", "--output", help="Output path (default: spec path with .svg)")
    parser.add_argument("--dir", dest="directory",
                        help="Render every *.json spec in a directory alongside itself")
    parser.add_argument("--stdout", action="store_true", help="Write output to stdout")
    parser.add_argument("--emit", choices=["svg", "slides"], default="svg",
                        help="Output form (default: svg)")
    parser.add_argument("--fit", metavar="W:H", type=parse_ratio,
                        help="Transpose a flow to better fill this frame, e.g. 16:9")
    parser.add_argument("--page-id", help="Slides page objectId (--emit slides)")
    parser.add_argument("--box", metavar="X,Y,W,H",
                        help="Target box on the slide in EMU (--emit slides)")
    parser.add_argument("--prefix", default="dg",
                        help="Object id prefix for generated shapes (--emit slides)")
    parser.add_argument("--spec-help", action="store_true",
                        help="Print the diagram spec reference and exit")
    args = parser.parse_args()

    if args.spec_help:
        print(SPEC_HELP)
        return 0

    if args.directory:
        specs = sorted(Path(args.directory).glob("*.json"))
        if not specs:
            print(f"No .json specs found in {args.directory}", file=sys.stderr)
            return 1
        failures = 0
        for spec_path in specs:
            ok, message = render_file(spec_path, spec_path.with_suffix(".svg"), args.fit)
            print(("rendered " if ok else "FAILED   ") + message,
                  file=sys.stdout if ok else sys.stderr)
            failures += 0 if ok else 1
        return 1 if failures else 0

    if not args.spec:
        parser.error("provide a spec file, --dir, or --spec-help")

    if args.emit == "slides":
        if not args.page_id or not args.box:
            parser.error("--emit slides needs --page-id and --box")
        spec, note, error = prepare(args.spec, args.fit)
        if error:
            print(error, file=sys.stderr)
            return 1
        try:
            box = tuple(float(v) for v in args.box.split(","))
            if len(box) != 4:
                raise ValueError
        except ValueError:
            parser.error("--box wants four EMU values: X,Y,W,H")
        requests = scene_requests(build_scene(spec), args.page_id, box, args.prefix)
        payload = json.dumps({"requests": requests}, indent=2) + "\n"
        if args.stdout or not args.output:
            sys.stdout.write(payload)
        else:
            Path(args.output).write_text(payload, encoding="utf-8")
            print(f"wrote {args.output} ({len(requests)} requests)"
                  + (f" — {note}" if note else ""))
        return 0

    if args.stdout:
        spec, note, error = prepare(args.spec, args.fit)
        if error:
            print(error, file=sys.stderr)
            return 1
        sys.stdout.write(svg_backend.render(build_scene(spec), spec))
        if note:
            print(note, file=sys.stderr)
        return 0

    out_path = Path(args.output) if args.output else Path(args.spec).with_suffix(".svg")
    ok, message = render_file(Path(args.spec), out_path, args.fit)
    print(("rendered " if ok else "FAILED   ") + message,
          file=sys.stdout if ok else sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
