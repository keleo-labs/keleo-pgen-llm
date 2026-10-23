# State machine diagram

Route C, `stateDiagram-v2`.

## When

An entity has a lifecycle, transitions are guarded, and some states are
illegal. Order lifecycles, subscription status, a connection protocol, an
approval workflow.

The test: can you name three or more states the thing can be in, and is
getting from one to another conditional? If transitions are unconditional,
a list in prose is clearer.

The real value is making illegal transitions visible — which is also the
cheapest way to find a bug before it is written.

## Notation

- `[*] --> First` is the initial state; `Last --> [*]` is terminal. Both
  matter: a machine with no terminal state is making a claim.
- Transitions are `Source --> Target : trigger [guard] / effect`. Mermaid has
  no formal guard syntax, so write it in the label and be consistent.
- Composite states (`state Name { … }`) group a sub-machine. Use them rather
  than drawing a second diagram when the sub-states only matter inside one
  parent.
- `state fork_state <<fork>>` for concurrency.
- Name states as **conditions**, not actions: `Awaiting payment`, not
  `Wait for payment`.

## Spec

```
---
method: state-machine
title: Order lifecycle
description: States an order can hold, and what moves it between them.
render: picture
---
stateDiagram-v2
    [*] --> Draft
    Draft --> Placed : submit [lines > 0]
    Placed --> Reserved : stock available
    Placed --> Backordered : stock short
    Backordered --> Reserved : restocked
    Reserved --> Dispatched : carrier collects
    Dispatched --> Delivered : signed for
    Placed --> Cancelled : cancel [before dispatch]
    Reserved --> Cancelled : cancel [before dispatch]
    Delivered --> [*]
    Cancelled --> [*]
```

## Mistakes this invites

- **States named as actions.** A state is something the entity *is*, not
  something it does.
- **No terminal state**, so nobody knows where the lifecycle ends.
- **Unguarded transitions that are actually conditional.** The guard is
  usually the business rule worth writing down.
- **Modelling a process.** If it is a sequence of steps performed by people,
  you want `swimlane`.

## Why this one is a picture

Route C. Mermaid draws it and the engine themes the result; it does not
become editable Google Slides shapes. Lifelines, activation bars and
attribute compartments have no Slides equivalent, so reading the geometry
back would produce a heap of loose rectangles that is worse than the picture.
Set `render: picture` explicitly — it is the default for this method anyway.
