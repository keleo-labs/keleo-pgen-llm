# Diagram method catalogue

Version: 1.0.0

Which diagram to draw, and how it gets produced here. Read this before
authoring a spec. Load one `methods/<slug>.md` page afterwards — not all of
them.

## Choosing

Four questions, in order. The first two decide the method; the last two
usually decide only its level of detail.

1. **Who reads it?** A board, a buying committee, an architecture review, the
   engineer implementing it. This sets the notation's formality.
2. **What decision does it support?** Invest or not; build or buy; approve the
   design; find the bug; agree the domain boundary. A diagram that supports no
   decision does not need to exist — prose will do.
3. **What detail is load-bearing?** Anything that could be omitted without
   changing the decision should be omitted.
4. **Where will it live?** A slide, a report, a repository, a workshop wall.

Two failure modes, and both are common:

**Semantic inflation** — a formal notation imposed on a conversation that
cannot use it. A BPMN model with boundary error events shown to a CFO. The
rigour is real and entirely wasted, and it costs the author the audience.

**Semantic deficiency** — an informal drawing standing in for a specification.
Boxes and arrows handed to an implementer with no cardinality, no protocol, no
error path. The gaps get filled by guesswork, and the guesses diverge.

When unsure, pick the *less* formal method and add detail if asked. Inflation
is harder to recover from than deficiency, because the audience disengages.

## The methods

Route A renders natively; B uses Mermaid for layout and draws it in the house
style; C renders with Mermaid and themes the result. See "How each route
behaves" below. A dash in **Here** means this repository does not produce it —
the method still appears because knowing it exists is part of choosing well.

### Strategy and portfolio

| Method | Abstraction | Audience | Origin | Reach for it when | Here |
|---|---|---|---|---|---|
| [Wardley map](methods/wardley.md) | Strategic landscape | CTO, strategy, product directors | Simon Wardley | Deciding build versus buy, spotting commoditisation, arguing about where to invest effort | A `wardley` |
| [Capability map](methods/capability-map.md) | High, strategic | C-suite, enterprise architects | BIZBOK, TOGAF Phase B | Showing *what* the organisation does, independent of how or who; heat-mapping debt or investment | A `matrix` |
| [Pace layering](methods/pace-layering.md) | High, categorical | Portfolio leads, architects | Gartner | Justifying different governance for systems of record, differentiation and innovation | A `matrix` |
| [Zachman grid](methods/zachman.md) | Meta, classification | Chief architects, auditors | John Zachman | Auditing whether the architecture description is complete; finding the missing viewpoint | A `matrix` |
| ArchiMate | High to medium | Enterprise architects, CIOs | The Open Group | You need cross-layer traceability and automated impact analysis across a real model | — Archi, Bizzdesign |

### Software architecture

| Method | Abstraction | Audience | Origin | Reach for it when | Here |
|---|---|---|---|---|---|
| [C4 context (L1)](methods/c4.md) | Very high | Execs, product, anyone | Simon Brown | Establishing the system boundary and who talks to it, with no internals | B `flowchart` |
| [C4 container (L2)](methods/c4.md) | High | Architects, ops, engineers | Simon Brown | Showing deployable units and the protocols between them — the most useful single diagram most systems have | B `flowchart` |
| [C4 component (L3)](methods/c4.md) | Medium | Developers in that codebase | Simon Brown | Explaining one container's internal structure before a feature lands in it | B `flowchart` |
| [Cloud topology](methods/cloud-topology.md) | Medium to low | Cloud architects, security reviewers | AWS, Azure, GCP conventions | A design review or audit needs the containment hierarchy and the security perimeters made explicit | A `flow` nested groups |
| [Solution overview](methods/solution-overview.md) | Very high | Prospects, executives, investors | Commercial practice | Pitching capability and outcome, not mechanism. Never hand this to an implementer | B or A `flow` |
| Isometric architecture | High | Prospects, keynote audiences | Visual design practice | A launch or keynote needs visual weight more than it needs precision | — Figma, Illustrator |

### Process and domain

| Method | Abstraction | Audience | Origin | Reach for it when | Here |
|---|---|---|---|---|---|
| [Swimlane process](methods/swimlane.md) | Medium | Process analysts, operations | BPMN-derived | Handoffs between roles or systems are the point; who does what, in order | A `swimlane` |
| [Event Storming](methods/event-storming.md) | Big picture to aggregate | Domain experts and engineers together | Alberto Brandolini | Exploring a domain nobody fully understands yet, before committing to a design | A `canvas` |
| [Flowchart](methods/flowchart.md) | Low, informal | Anyone | No governing metamodel | A short procedure with a couple of decisions. Honest about being informal | B `flowchart` |
| BPMN 2.0 executable | Medium to low | Workflow engineers | OMG | The model will be deployed to an engine, or audited against a regulation | — Camunda Modeler, Signavio |

### Data and behaviour

| Method | Abstraction | Audience | Origin | Reach for it when | Here |
|---|---|---|---|---|---|
| [ERD](methods/erd.md) | Conceptual, logical or physical | Data architects, DBAs, developers | Chen, Crow's Foot, IDEF1X | Agreeing entities and cardinality before a schema exists, or documenting one that does | C `erDiagram` |
| [Sequence](methods/sequence.md) | Medium to low | Engineers, QA | OMG UML | Tracing a distributed call, an auth flow, or a race condition over time | C `sequenceDiagram` |
| [State machine](methods/state-machine.md) | Medium to low | Engineers, analysts | OMG UML | An entity has a lifecycle with guarded transitions and illegal states worth naming | C `stateDiagram-v2` |
| [Class](methods/class.md) | Low | Engineers | OMG UML | Domain logic is intricate enough that inheritance and cardinality need stating | C `classDiagram` |

### Keeping diagrams alive

Diagrams-as-code addresses architectural drift — the gap that opens between a
drawing and the system it describes. A `.mmd` spec here is first-generation:
version-controlled text, reviewable in a merge request, but each file is
independent, so renaming a component means editing every file that names it.

Second-generation tools (Structurizr DSL, LikeC4) keep one model and generate
views as filtered projections of it, so a rename propagates. Neither is
installed here. When a system's architecture needs to stay accurate across
many views over years rather than be documented once, say so and point at
LikeC4 — producing fifteen `.mmd` files that will drift is not a kindness.

## How each route behaves

| | A. Native | B. Mermaid layout | C. Mermaid render |
|---|---|---|---|
| Spec file | `.json` | `.mmd`, `render: scene` | `.mmd`, `render: picture` |
| House style | by construction | by construction | applied as CSS |
| Editable Google Slides shapes | yes | yes | no, stays a picture |
| Layout control | explicit, you place things | automatic | automatic |

Route B renders the Mermaid source, reads the geometry back, and redraws every
node and edge from house tokens — Mermaid does the layout, nothing of its
styling survives. If the importer meets something it cannot read it falls back
to route C and says so, rather than emitting a half-built diagram.

Route C exists because lifelines, activation bars and attribute compartments
have no Google Slides equivalent. A picture is the right artifact for them.

## When to decline

Say the method is right, say this repository cannot produce it, and name the
tool. Do not approximate a standard — a near-miss of ArchiMate or BPMN reads
as a mistake to anyone who knows the notation, and misleads everyone who does
not.

| Asked for | Say |
|---|---|
| ArchiMate | Archi (free) or Bizzdesign. The value is the model and its impact analysis, not the picture |
| Executable BPMN 2.0 | Camunda Modeler. The XML serialisation is the deliverable; a drawing of it is not |
| Isometric | Figma or Illustrator. This is illustration work, not diagram generation |
| A living architecture model | LikeC4 or Structurizr DSL, in the repository alongside the code |
