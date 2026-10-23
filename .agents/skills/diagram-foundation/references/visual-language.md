# House visual language

Version: 1.0.0

The vocabulary every diagram draws from, and how each of the three routes
realises it. This is the contract that keeps a Wardley map, a C4 container
view and an Event Storming canvas looking like they came from one place.

The register is flat and minimal: no gradients, no shadows, no bevels, 1.5px
strokes, one accent colour per palette. Geometry and type scale are fixed in
`THEME`; only the colour family varies, and a spec never carries a colour.

## Shapes

Ten, each earning its place from a method in the catalogue. A node declares
one with `"shape"`; omitting it gives `rounded`.

| `shape` | Means | SVG | Google Slides type |
|---|---|---|---|
| `rounded` | A thing. The default — a service, a capability, a step | rect, r=4 | `ROUND_RECTANGLE` |
| `rect` | A structural or rigid element: a container, a component, a matrix cell | rect, r=0 | `RECTANGLE` |
| `stadium` | A terminal: process start, process end | rect, r=h/2 | `FLOW_CHART_TERMINATOR` |
| `cylinder` | A datastore: database, queue, bucket | path | `FLOW_CHART_MAGNETIC_DISK` |
| `hexagon` | A gateway: exclusive or parallel branch | polygon | `HEXAGON` |
| `diamond` | A decision in an informal flowchart | polygon | `DIAMOND` |
| `event` | A moment: start, intermediate, end event | ellipse | `ELLIPSE` |
| `note` | An annotation, hanging off the diagram | polygon | `FOLDED_CORNER` |
| `sticky` | An Event Storming sticky | rect, r=2 | `RECTANGLE` |
| `person` | An actor, role or user | rect r=4 with a head | `ROUND_RECTANGLE` |

**Route B mapping.** Mermaid node syntax maps onto the set; anything without
a house equivalent becomes `rounded` and the importer says so.

| Mermaid | House |
|---|---|
| `[text]` `(text)` | `rounded` |
| `([text])` | `stadium` |
| `[(text)]` | `cylinder` |
| `{text}` | `diamond` |
| `{{text}}` | `hexagon` |
| `((text))` | `event` |
| `>text]` | `note` |
| anything else | `rounded`, reported |

## Connectors

An edge declares `dash` and `arrow`; omitting both gives a solid filled arrow.

| `dash` | Means |
|---|---|
| `solid` | A real call, flow or dependency. The default |
| `dashed` | Something weaker: asynchronous, optional, planned, or a boundary that is not traversed |
| `dotted` | A reference or annotation link, not a flow |

| `arrow` | Means | Slides |
|---|---|---|
| `arrow` | Directed. The default | `FILL_ARROW` |
| `open` | Directed, lighter weight — a return, a response | `OPEN_ARROW` |
| `none` | An association with no direction | `NONE` |
| `diamond` | Aggregation or composition (UML) | `FILL_DIAMOND` |
| `crowsfoot` | ERD cardinality. **Route C only** — Slides has no crow's foot, so an ERD never becomes shapes | — |

## Containers

| Kind | Draws as | Used by |
|---|---|---|
| `group` | Rounded rect, r=6, muted fill at 50%, label top-left | `flow` clusters, C4 boundaries, cloud nesting |
| `lane` | Full-width band with a label strip on the left edge | `swimlane` |
| `pool` | Outer frame around lanes, label rotated on the left | `swimlane` |
| `band` | Unfilled region with a dividing rule and a label | `wardley` evolution bands, `matrix` headers |

Groups nest. A group names its `parent`, which is what makes
Region → VPC → AZ → Subnet expressible. Nesting adds padding per level and
steps the fill one shade; beyond four levels the engine reports rather than
drawing something unreadable.

## Colour

Two independent axes. **Emphasis** is structural — how much this node matters
in *this* diagram. **Role** is semantic — what this node *is*, under a
notation that assigns meaning to colour.

### Emphasis

Unchanged, and still the right answer for most diagrams. One or two accents;
everything accented is nothing accented.

`default` · `muted` · `accent` · `selected`

### Roles

A node sets `"role"`. Role decides the fill; emphasis still decides the stroke
weight, so an accented sticky is a sticky with a heavier border.

**`storm.*` — Event Storming.** These hues *are* the notation. A facilitator
reads the wall by colour, so they do not follow the palette and do not change
between `navigator` and `redhat`. Softened from the sticky-note originals to
sit in the flat register, with hue relationships preserved.

| Role | Sticky | Means |
|---|---|---|
| `storm.event` | orange | A domain event. Past tense, always |
| `storm.command` | blue | An action someone or something requests |
| `storm.actor` | small yellow | The person or role issuing a command |
| `storm.aggregate` | pale yellow | The state holder and consistency boundary |
| `storm.policy` | lilac | "Whenever X, then Y" — reactive logic |
| `storm.readmodel` | green | A projection someone reads to decide |
| `storm.external` | pink | A third party or legacy system outside your control |
| `storm.hotspot` | red | A disagreement, an unknown, a bottleneck |

**`heat.1`–`heat.5` — capability heat maps.** A five-step scale, 1 healthy to
5 critical. Fixed, not palette-derived: neither palette carries a diverging
scale, and a heat map that changed meaning with the deck theme would be worse
than useless. Always render the legend.

**`evolution.*` — Wardley.** `genesis`, `custom`, `product`, `commodity`.
Four steps from the accent colour toward neutral, so they follow the palette:
a component's maturity reads as "how settled", which is a house-style
gradient, not a fixed semantic.

**`pace.*` — pace layering.** `innovation`, `differentiation`, `record`. Three
steps, same reasoning as evolution.

### How each route gets colour

| Route | Mechanism |
|---|---|
| A | `EMPHASIS` and `ROLES` resolved at layout time, written into the Scene |
| B | The Mermaid source carries `classDef` names; the importer maps those to roles and redraws from house tokens. Mermaid's own fills are discarded |
| C | `house_css.py` emits `themeVariables` plus a CSS block appended to the SVG's `<style>`, where the cascade beats both Mermaid's defaults and its `classDef` `!important` rules |

Route C is approximate by nature. Colour and type will match; corner radii,
spacing and arrowheads are Mermaid's. That is the price of letting it draw a
notation it knows better than we do.

## Changing any of this

In `scripts/diagram.py` — `THEME`, `EMPHASIS`, `ROLES`, `PALETTES` — never in
a spec and never per diagram. `use_palette` mutates `THEME` and `EMPHASIS`
**in place** because the backends bind them at import; a new consumer must
call it before `build_scene`, not after.

Then update this file. A shape in the code and not in this table is a shape
nobody will use.
