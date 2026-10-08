---
name: diagram
description: Choose the right kind of diagram for a job and produce it — architecture, strategy, process, data or behaviour. Use when asked to draw, diagram, visualise, map or sketch a system, architecture, process, workflow, domain, schema, roadmap, capability landscape or org capability; when asked for a C4, UML, sequence, ERD, flowchart, swimlane, BPMN, Wardley map, capability map, Event Storming canvas or architecture diagram; when asked which diagram type suits an audience; or when a report, article or deck needs a figure. Not for charts of quantitative data — that is dataviz.
compatibility: >-
  Requires Python 3.9+ and, for Mermaid-backed diagram types, the npx CLI at
  /opt/homebrew/bin/npx (Node.js 18+), which fetches mermaid-cli on demand.
  The native layouts need Python only.
metadata:
  version: "1.0.0"
---

# Diagram

> **Vendored copy.** This tree is distributed with `keleo-pgen-llm` so the
> capability works from a clone without a user-level install. It tracks the
> global skill at `~/.claude/skills/diagram/` version by version; the only
> intended difference is that paths are repo-relative rather than
> `~/.claude/skills/…`. If the two diverge otherwise, the global copy is
> upstream. Re-copy with `python3 utils/vendor-skills.py`.

Version: 1.0.0

Picking the method is the first decision and the one most often skipped. A
BPMN model with boundary events shown to a CFO fails; so does a box-and-arrow
sketch handed to the engineer who has to build it. Choose, say why, then draw.

**Engine:** `.claude/skills/diagram-foundation/`. Everything below refers to
paths under it.

## 1. Establish the job

Four questions. Ask the user only what you cannot infer.

| | |
|---|---|
| **Audience** | Board, buying committee, architecture review, the implementer |
| **Decision** | What does this diagram help someone decide? |
| **Detail** | What could be left out without changing that decision? Leave it out |
| **Destination** | A file, a deck slide, a report or Doc, a repository |

A diagram supporting no decision does not need to exist. Say so and offer
prose instead.

## 2. Choose the method

Read `references/method-catalogue.md`. It carries the selection matrix, the
decision procedure and the two failure modes — semantic inflation and
semantic deficiency.

**State the method and why, in one line, before drawing.** The user can
redirect you for the cost of a sentence; they cannot redirect a finished
diagram without throwing it away.

> Container-level C4, because the question is which services talk to which
> and over what — one level up would not answer it, one level down is detail
> this review does not need.

Where the catalogue says this repository cannot produce the right method —
ArchiMate, executable BPMN 2.0, isometric, a living model — say that, name
the tool, and offer the nearest thing that *is* producible. Do not
approximate a standard. A near-miss of a notation reads as a mistake to
anyone who knows it and misleads everyone who does not.

## 3. Read the method's page

`references/methods/<slug>.md`, linked from the catalogue. One page: notation
rules, the spec shape, a worked example, the mistakes that method invites.
Read the one you chose, not the set.

## 4. Author the spec

Two forms, and the method page says which:

| File | Contents |
|---|---|
| `<name>.json` | A declarative spec — the native layouts |
| `<name>.mmd` | YAML frontmatter, then Mermaid source |

`python3 scripts/render-diagram.py --spec-help` is the full field reference.
Run it rather than guessing; do not paste its output into a prompt.

Keep the spec beside its output and under version control. The spec is the
artifact — an SVG or PNG is a build product. You cannot un-draw an SVG, and
everything beyond "show the picture" needs the structure.

Four rules that apply whatever the method:

- **Three to nine elements.** Below three, prose is clearer. Above nine,
  split the diagram or raise its level of abstraction.
- **Labels are noun phrases.** "Automation controller", not "The controller
  runs scheduled scans". Detail belongs in `sublabel` or the surrounding prose.
- **Emphasis is for one or two things.** Everything accented is nothing
  accented.
- **Label the edges that carry meaning.** "scheduled scan" earns its place;
  "connects to" does not.

## 5. Render, then look at it

```bash
python3 .claude/skills/diagram-foundation/scripts/render-diagram.py spec.json -o out.svg
npx --yes sharp-cli --input out.svg --output . --format png resize 1200
```

**Read the PNG.** Every time. Check for text overflowing its shape, elements
colliding, edges crossing through a node, an unreadable label, a palette that
is not the house one. Layout problems are invisible in a spec and obvious in
a thumbnail.

Fix what reads badly and render again. Never report a diagram as done without
having looked at it.

The renderer reports rather than reshapes when a diagram will not fit its
frame, because a diagram that will not fit is usually one carrying more than
one idea. The fix is to split it, not to shrink it.

## 6. Place it

| Destination | How |
|---|---|
| Standalone | The SVG and its spec, side by side in a directory |
| Deck slide | `layout: diagram` with `diagram: ./assets/<name>.json`. `deck-foundation` renders it and upgrades it to native, editable Google Slides shapes |
| Markdown or Google Doc | Reference the SVG; the `google-doc` skill rasterises it on the way into Docs |
| Repository | A `.mmd` spec is diagram-as-code already — commit it and render in CI |

A native spec and an imported Mermaid flowchart both become editable Slides
shapes. A sequence, ERD, class or state diagram stays a picture, because
lifelines and attribute compartments have no Slides equivalent. The renderer
says which you got; pass that on rather than letting someone discover it in
the deck.

## Palette

`--palette navigator` (default, for reports and documents) or `--palette
redhat` (decks). Only the colour family changes; the spec never carries a
colour. A deck build swaps it automatically.
