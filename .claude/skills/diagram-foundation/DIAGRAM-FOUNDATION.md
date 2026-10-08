# Diagram Foundation

> **Vendored copy.** This tree is distributed with `keleo-pgen-llm` so the
> capability works from a clone without a user-level install. It tracks the
> global skill at `~/.claude/skills/diagram-foundation/` version by version; the only
> intended difference is that paths are repo-relative rather than
> `~/.claude/skills/…`. If the two diverge otherwise, the global copy is
> upstream. Re-copy with `python3 utils/vendor-skills.py`.

Version: 1.2.0

Shared diagram engine. A spec goes in; an SVG for a markdown report or native
Google Slides shapes for a deck comes out. Not a skill — a foundation, like
`deck-foundation` and `reporting-foundation`.

Consumers: the `diagram` skill, the reporting skills (via
`reports/<report-slug>/assets/*.json`), the deck skills (via a `diagram:`
slide), and `keleo-pgen-llm`, which vendors a copy.

**Choosing what to draw is a separate question from drawing it.**
`references/method-catalogue.md` carries the selection matrix — fifteen
methods, their audiences, and which of them this engine produces.
`references/visual-language.md` is the shape, connector and colour vocabulary
every route draws from.

## Why a spec and not an SVG

You cannot un-draw an SVG. Everything beyond "show the picture" — reshaping a
diagram for a slide, turning it into editable shapes, restyling the whole set
at once — needs the structure, which only the spec carries. Keep the spec
beside its output and under version control; the SVG and PNG are build
artifacts.

## Three routes

A spec is either a `.json` using a native layout, or a `.mmd` carrying YAML
frontmatter and Mermaid source. `spec_loader.load` is the single entry point
and decides the route; callers do not need to know which they got, except to
ask `diagram.editable` before expecting shapes.

| Route | How | House style | Editable slides |
|---|---|---|---|
| **A. Native** | A layout in `diagram.py` → Scene → SVG or Slides | by construction | yes |
| **B. Mermaid as layout engine** | Mermaid → SVG → `mermaid_import` → Scene | by construction | yes |
| **C. Mermaid as renderer** | Mermaid → SVG → `mermaid_theme` | applied as CSS | no |

The rule: a published notation with a mature diagram-as-code grammar (UML,
ERD) is Mermaid's to draw — reimplementing a standard is waste, and a
near-miss of UML reads worse than none. A *graph* is Mermaid's to lay out and
ours to draw. A layout Mermaid has no grammar for — grids, two-axis maps,
lanes — is ours end to end.

Route B is the interesting one. Mermaid does the hard part and nothing of its
styling survives: semantics come from the source we were given, geometry from
its SVG. Anything the importer cannot read falls back to route C **and says
so**, rather than emitting a half-built scene.

Route C exists because lifelines, activation bars and attribute compartments
have no Slides equivalent. A picture is the right artifact for them.

## Layouts

| Layout | Shape | Reach for it when |
|---|---|---|
| `flow` | Layered boxes, directed edges, nestable cluster groups | Topologies, pipelines, data paths, cloud containment. The default |
| `stack` | Vertical tiers | Layer models, maturity stacks, architecture tiers |
| `timeline` | Sequential phase bands joined by arrows | Roadmaps, adoption journeys, phased rollouts |
| `hub` | Centre node with satellites on an ellipse | Relationship maps, integration fan-out |
| `matrix` | Grid with row and column headers | Zachman, pace layering, capability heat maps, 2×2s |
| `wardley` | Components on a value-chain / evolution grid | Build versus buy, spotting commoditisation |
| `swimlane` | Lanes of steps with handoffs between them | Process modelling where who does what is the point |
| `canvas` | Left-to-right timeline of coloured stickies | Event Storming |

`scripts/render-diagram.py --spec-help` prints the full field reference. Point
an agent at that command rather than pasting its output into a prompt.

## Design language

Tokens come from the keleo-studio-gas navigator diagrams — `computeNodeStyle`
and the layout constants in `src/scripts/views/Navigator*.html` — so reports,
decks and the studio UI read as one system. They live in the `THEME` dict at
the top of `scripts/diagram.py`. Restyle there, never per diagram: a spec
carries content and structure only.

Body text and muted grey match the deck theme's `--rh-black` and
`--rh-grey-text`, so a diagram does not fight the surface it sits on.

### Palettes

Only the colour family varies; geometry, type scale and spacing are fixed, and
the spec never carries colour. `PALETTES` in `scripts/diagram.py` holds the
two, and `use_palette(name)` switches between them:

| Palette | Accent | Used by |
|---|---|---|
| `navigator` (default) | `#0066cc` | Reports, the studio UI |
| `redhat` | `#ee0000` | Decks — `build-diagrams.py` applies it |

A diagram in a report belongs to the document and reads in the navigator
family. The same spec rendered onto a branded slide belongs to the deck, so
the deck build swaps the palette before laying anything out. Pass
`--palette navigator` to opt a deck out.

`use_palette` mutates `THEME` and `EMPHASIS` **in place**. The backends bind
them at import (`from diagram import THEME`), so rebinding would leave them
pointing at the old dict. Any new consumer must call it before `build_scene`,
not after — and `build-diagrams.py` and `upgrade-diagrams.py` must agree, or
the native Slides shapes will not match the picture they replace.

## Writing a good spec

**The title is not drawn.** `title` and `description` become the SVG's
`<title>` and `<desc>`/`aria-label`. The heading above the diagram already
names it, so rendering the title would print the same line twice. Set both
anyway — they are what a non-sighted reader gets.

**Labels are noun phrases.** "Automation controller", not "The automation
controller runs scheduled scans". Detail belongs in `sublabel` or the prose.

**Three to nine nodes.** Below three, prose is clearer. Above nine, split the
diagram or raise its level of abstraction.

**Use `emphasis` sparingly.** One or two `accent` nodes draw the eye; everything
accented is nothing accented. `muted` recedes context.

**Label the edges that carry meaning.** "scheduled scan" earns its place;
"connects to" does not.

## Fitting a frame

`--fit W:H` scores both orientations of a `flow` and picks the better. The flip
is lossless, which is why it is applied without asking.

It helps less often than it looks like it should. Each extra rank costs a node
width (160–220px) in `LR` but only a node height (48–66px) in `TB`, so flipping
a *deep* flow yields a thin ribbon that scores worse than the original —
measured across three real topologies, `TB` won every time. The flip pays off
for a shallow flow with wide ranks.

When neither orientation fits, the engine says so rather than reshaping
harder. Wrapping a deep flow into columns does fill the frame — it took a
seven-rank topology from 23% to 77% — but cross-column edges have no sane
route and loop off the canvas, and a cluster group cannot span columns. It was
built, measured, and removed. **A diagram that will not fit a slide is usually
a diagram carrying more than one idea**, and that fix belongs with the author:
split it, or raise its abstraction.

## Backends

| Backend | Output | Notes |
|---|---|---|
| `svg_backend` | Standalone SVG | Native `<text>`, not `foreignObject` — the latter does not render through a markdown `<img>`. Paints an opaque background so dark-theme pages do not swallow the text |
| `slides_backend` | `batchUpdate` requests | Every house shape maps to a real Slides shape type, so a node stays selectable and movable rather than degrading to a picture |

Three differences in the Slides output, all deliberate:

- **Edges are straight segments.** `createLine` offers `STRAIGHT`, `BENT` and
  `CURVED` but not arbitrary béziers. A routed edge becomes one connector per
  leg, with the arrow head on the last; a single hop between its endpoints
  would discard the routing and drive the line through whatever it avoided.
- **Type is eased down ~8%.** Google sets text wider than Chromium, which the
  deck foundation already warns about. Box geometry comes from Chromium-
  calibrated metrics, so without the easing a two-line label becomes three and
  overflows the box it was sized for.
- **Crow's foot has no equivalent.** It is a route C notation only, and an
  ERD never reaches this backend.

## Gotchas worth knowing before changing the Mermaid routes

Each of these cost a debugging cycle and will again if undone.

- **`measure_node` imposes a house minimum width.** That is right for our own
  layouts and wrong for an imported one: widening every node past what
  Mermaid routed around sends the edges through the shapes. `mermaid_import`
  passes `min_width=0, min_height=0`.
- **Mermaid transforms nest.** A cylinder's path starts at its left edge and
  is recentred by a `transform` on the path element itself. Reading only the
  node group's transform puts the shape half its width off.
- **An SVG arc is not a pair of coordinates.** `a65,12.8 0,0,0 132,0` carries
  radii, a rotation and two flags before its endpoint. `_path_bbox` walks the
  commands; reading numbers in pairs inflates a cylinder several times over.
- **Sweep flag 0, left to right, bulges *down*.** Mermaid's own cylinder base
  is the reference. Getting it backwards turns a datastore inside out.
- **Mermaid's root element already has `role`.** Appending a second one makes
  the document malformed and every rasteriser rejects it outright.
- **`-C/--cssFile` is not reliable.** It is fed in as `themeCSS` and the
  rules did not survive into the output; `classDef` emits `!important` rules
  that would beat them anyway. The house stylesheet is appended to the
  `<style>` block in the emitted SVG instead.
- **mermaid-cli 12 has no target size.** Only `--size`, a maximum, which for
  SVG moves `max-width` and nothing else. Fit is judged after the fact.

## Vendoring

`keleo-pgen-llm` carries a copy under `.claude/skills/diagram-foundation/`, the
same convention its CLAUDE.md states for the deck tree. Fix here, then re-copy
down. `utils/render-diagram.py` in that repo is a thin wrapper over the copy.
