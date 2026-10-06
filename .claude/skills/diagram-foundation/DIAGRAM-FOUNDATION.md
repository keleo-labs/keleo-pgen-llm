# Diagram Foundation

Version: 1.0.0

Shared diagram engine. A declarative JSON spec goes in; an SVG for a markdown
report or native Google Slides shapes for a deck comes out. Not a skill — a
foundation, like `deck-foundation` and `reporting-foundation`.

Consumers: the reporting skills (via `reports/<report-slug>/assets/*.json`), the deck
skills (via a `diagram:` slide), and `keleo-pgen-llm`, which vendors a copy.

## Why a spec and not an SVG

You cannot un-draw an SVG. Everything beyond "show the picture" — reshaping a
diagram for a slide, turning it into editable shapes, restyling the whole set
at once — needs the structure, which only the spec carries. Keep the spec
beside its output and under version control; the SVG and PNG are build
artifacts.

## Layouts

| Layout | Shape | Reach for it when |
|---|---|---|
| `flow` | Layered boxes, directed edges, optional cluster groups | Topologies, pipelines, data paths, process flows. The default |
| `stack` | Vertical tiers | Layer models, maturity stacks, architecture tiers |
| `timeline` | Sequential phase bands joined by arrows | Roadmaps, adoption journeys, phased rollouts |
| `hub` | Centre node with satellites on an ellipse | Relationship maps, integration fan-out |

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
| `slides_backend` | `batchUpdate` requests | Rounded rectangles with their own fill, outline and text; lines with arrow heads. Genuinely editable in the deck |

Two differences in the Slides output, both deliberate:

- **Edges are straight.** `createLine` offers `STRAIGHT`, `BENT` and `CURVED`
  but not arbitrary béziers. Every vertical and horizontal hop is identical to
  the SVG; a diagonal that curves in the SVG is a straight diagonal on a slide.
- **Type is eased down ~8%.** Google sets text wider than Chromium, which the
  deck foundation already warns about. Box geometry comes from Chromium-
  calibrated metrics, so without the easing a two-line label becomes three and
  overflows the box it was sized for.

## Vendoring

`keleo-pgen-llm` carries a copy under `.claude/skills/diagram-foundation/`, the
same convention its CLAUDE.md states for the deck tree. Fix here, then re-copy
down. `utils/render-diagram.py` in that repo is a thin wrapper over the copy.
