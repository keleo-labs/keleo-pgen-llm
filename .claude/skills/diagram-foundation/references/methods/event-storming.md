# Event Storming

Route A, layout `canvas`.

## When

The domain is not understood yet, and the people who understand parts of it
are not the people who will build it. Run it *before* committing to a design,
not to document one afterwards.

Three levels: big picture (the whole value chain, spotting bottlenecks and
conflicting vocabulary), process modelling (one workflow in detail), and
software design (finding aggregate boundaries for a service decomposition).
Say which you are at.

The real artifact is the workshop and the arguments it surfaces. This layout
captures the wall afterwards so it survives; it does not replace the session.

## Notation

The colours *are* the notation. A facilitator reads the wall by colour, so
these do not follow the palette and do not change between `navigator` and
`redhat`.

| `role` | Sticky | Means |
|---|---|---|
| `storm.event` | orange | A domain event. **Past tense, always** — "Order placed" |
| `storm.command` | blue | An action requested — "Place order" |
| `storm.actor` | small yellow | Who or what issues the command |
| `storm.aggregate` | pale yellow | The state holder, and the consistency boundary |
| `storm.policy` | lilac | "Whenever X, then Y" |
| `storm.readmodel` | green | A projection someone reads to decide |
| `storm.external` | pink | A third party or legacy system outside your control |
| `storm.hotspot` | red | A disagreement, an unknown, a bottleneck |

Time runs left to right. Each role lands on its own row, in the order above,
so the same kind of sticky lines up across columns; only rows in use are
drawn. Actors render smaller, as they are on a real wall.

**Keep the hot spots.** They are the most valuable output — a sanitised
canvas with the disagreements removed has thrown away the finding.

## Spec

```json
{"layout": "canvas",
 "title": "Order fulfilment",
 "description": "Process-level Event Storming.",
 "columns": [
   {"label": "Checkout", "stickies": [
     {"label": "Customer", "role": "storm.actor"},
     {"label": "Place order", "role": "storm.command"},
     {"label": "Order", "role": "storm.aggregate"},
     {"label": "Order placed", "role": "storm.event"}]},
   {"label": "Reserve", "stickies": [
     {"label": "Whenever an order is placed", "role": "storm.policy"},
     {"label": "Stock reserved", "role": "storm.event"},
     {"label": "Warehouse API", "role": "storm.external"},
     {"label": "Partial stock: split or hold?", "role": "storm.hotspot"}]}]}
```

## Mistakes this invites

- **Events in the present tense.** "Place order" is a command. "Order placed"
  is an event. The tense is how the two are told apart.
- **Deleting the hot spots** to make the output look resolved.
- **Jumping to aggregates.** At big-picture level you want events and hot
  spots only; aggregates arrive at software-design level.
- **One person authoring it.** Then it is a guess with sticky colours. The
  method is the collaboration.
