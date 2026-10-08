#!/usr/bin/env python3
"""Render diagram specs into SVG, or into Google Slides requests.

Two spec forms, three routes, one CLI. A `.json` spec is laid out natively by
diagram.py. A `.mmd` spec is Mermaid source with frontmatter: a flowchart is
laid out by Mermaid and redrawn here in house shapes, and every other Mermaid
diagram type keeps its own picture and gets themed. `spec_loader` decides
which; see references/method-catalogue.md for why.

Usage:
    render-diagram.py <spec>.json -o <out>.svg
    render-diagram.py <spec>.mmd  -o <out>.svg
    render-diagram.py <spec>.json --stdout
    render-diagram.py --dir <dir>/                 # render every spec in place
    render-diagram.py <spec>.json --fit 16:9       # suit a frame
    render-diagram.py <spec>.json --palette redhat
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
import spec_loader  # noqa: E402
from diagram import PALETTES, use_palette  # noqa: E402
from mermaid_render import MermaidUnavailable  # noqa: E402
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

layout: "matrix"
----------------
A grid with row and column headers. Zachman, pace layering, capability heat
maps, 2x2s.

  columns       [{label, sublabel?}]
  rows          [{label, sublabel?, cells: [cell|null, ...]}]
  legend        [{role, label}]    required when cells carry a role
  cellWidth     optional, default 150
  headerWidth   optional, default 130

A null cell is drawn as an empty outline. In a completeness audit the gap is
the finding, so it has to be visible as a gap.

layout: "wardley"
-----------------
Components on a value-chain / evolution grid. Build-versus-buy, spotting
commoditisation.

  anchor      who the value chain serves, e.g. "Account team"
  components  [{id, label, sublabel?, visibility, evolution, emphasis?}]
  edges       [{from, to}]        the value chain; undirected, no arrow heads
  movements   [{from, to}]        `to` is a target evolution, drawn dashed

visibility 1 is the user anchor, 0 is invisible infrastructure. evolution runs
0 genesis to 1 commodity. Both are 0 to 1.

layout: "swimlane"
------------------
Lanes of steps with handoffs between them. Process modelling where who does
what is the point.

  lanes   [{label, steps: [{id, label, sublabel?, shape?, column?}]}]
  edges   [{from, to, label?, dash?, arrow?}]

Columns are ranked from the edge graph, as in `flow`. Set `column` to pin a
step that has no incoming edge.

layout: "canvas"
----------------
An Event Storming wall: a left-to-right timeline of coloured stickies.

  columns  [{label?, stickies: [{label, sublabel?, role}]}]

`role` is one of storm.actor, storm.command, storm.aggregate, storm.event,
storm.policy, storm.readmodel, storm.external, storm.hotspot. Each lands on
its own row, in that order, and only rows in use are drawn.

Shapes, roles and connectors
----------------------------
Any node in any layout may carry:

  shape     rounded (default) | rect | stadium | cylinder | hexagon |
            diamond | event | note | sticky | person
  emphasis  default | muted | accent | selected
  role      a semantic colour — storm.*, heat.1-5, evolution.*, pace.*

Any edge may carry:

  dash      solid (default) | dashed | dotted
  arrow     arrow (default) | open | none | diamond | crowsfoot

See references/visual-language.md for what each one means.

Mermaid specs (.mmd)
--------------------
A `.mmd` file is YAML frontmatter, then Mermaid source:

  ---
  method: c4-container
  title: Keleo Studio containers
  description: Deployable units and the protocols between them.
  render: scene        # scene (default) | picture
  ---
  flowchart TB
    subgraph studio["Keleo Studio"]
      web[Web app]:::accent --> api[API service]
      api --> db[(Document store)]
    end

`render: scene` lets Mermaid lay the graph out, then redraws it here in house
shapes — so it becomes editable Google Slides shapes like any native spec.
Only a flowchart can do this; a sequenceDiagram, erDiagram, classDiagram or
stateDiagram keeps Mermaid's own picture, themed to the palette, and says so.

In a .mmd source, a role is written with a hyphen because Mermaid class names
cannot contain a dot: `:::storm-event`, not `:::storm.event`.

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


def parse_ratio(raw):
    try:
        w, _, h = raw.partition(":")
        return float(w) / float(h)
    except (ValueError, ZeroDivisionError):
        raise argparse.ArgumentTypeError(f"--fit wants W:H, got {raw!r}")


def prepare(path, fit_ratio):
    """Load by whichever route the file calls for. Returns (diagram, error)."""
    try:
        return spec_loader.load(path, fit_ratio), None
    except (spec_loader.SpecError, MermaidUnavailable) as exc:
        return None, str(exc)
    except (KeyError, TypeError, ValueError, ZeroDivisionError) as exc:
        return None, f"{path}: could not lay out ({exc})"


def render_file(spec_path, out_path, fit_ratio=None):
    """Render one spec file to SVG. Returns (ok, message)."""
    diagram, error = prepare(spec_path, fit_ratio)
    if error:
        return False, error
    try:
        svg = diagram.svg()
    except (KeyError, TypeError, ValueError, ZeroDivisionError) as exc:
        return False, f"{spec_path}: could not render ({exc})"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(svg, encoding="utf-8")
    suffix = f" — {diagram.note}" if diagram.note else ""
    return True, f"{out_path}{suffix}"


def main():
    parser = argparse.ArgumentParser(
        description="Render diagram specs into SVG or Google Slides requests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Run --spec-help for the full spec reference.",
    )
    parser.add_argument("spec", nargs="?",
                        help="Path to a diagram spec: .json or .mmd")
    parser.add_argument("-o", "--output", help="Output path (default: spec path with .svg)")
    parser.add_argument("--dir", dest="directory",
                        help="Render every *.json and *.mmd spec in a directory "
                             "alongside itself")
    parser.add_argument("--palette", choices=sorted(PALETTES), default="navigator",
                        help="Colour family (default: navigator)")
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

    # Before anything is laid out: use_palette mutates THEME in place and the
    # backends bound it at import, so a later switch would not reach them.
    use_palette(args.palette)

    if args.directory:
        specs = sorted(p for p in Path(args.directory).iterdir()
                       if spec_loader.is_spec(p))
        if not specs:
            print(f"No .json or .mmd specs found in {args.directory}",
                  file=sys.stderr)
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
        diagram, error = prepare(args.spec, args.fit)
        if error:
            print(error, file=sys.stderr)
            return 1
        if not diagram.editable:
            # A picture has no geometry to turn into shapes. Say so plainly
            # rather than emitting an empty request list the caller would
            # read as success.
            print(f"{args.spec}: this diagram renders as a picture, so it has "
                  "no shapes to emit. Publish the SVG or PNG instead."
                  + (f" ({diagram.note})" if diagram.note else ""),
                  file=sys.stderr)
            return 1
        try:
            box = tuple(float(v) for v in args.box.split(","))
            if len(box) != 4:
                raise ValueError
        except ValueError:
            parser.error("--box wants four EMU values: X,Y,W,H")
        requests = scene_requests(diagram.scene(), args.page_id, box, args.prefix)
        payload = json.dumps({"requests": requests}, indent=2) + "\n"
        if args.stdout or not args.output:
            sys.stdout.write(payload)
        else:
            Path(args.output).write_text(payload, encoding="utf-8")
            print(f"wrote {args.output} ({len(requests)} requests)"
                  + (f" — {diagram.note}" if diagram.note else ""))
        return 0

    if args.stdout:
        diagram, error = prepare(args.spec, args.fit)
        if error:
            print(error, file=sys.stderr)
            return 1
        sys.stdout.write(diagram.svg())
        if diagram.note:
            print(diagram.note, file=sys.stderr)
        return 0

    out_path = Path(args.output) if args.output else Path(args.spec).with_suffix(".svg")
    ok, message = render_file(Path(args.spec), out_path, args.fit)
    print(("rendered " if ok else "FAILED   ") + message,
          file=sys.stdout if ok else sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
