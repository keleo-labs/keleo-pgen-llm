# Flowchart

Route B (`flowchart`), so it becomes editable Slides shapes.

## When

A short procedure with a couple of decisions, for an audience that needs no
formality. Onboarding steps, a triage path, a runbook decision tree.

**Be honest that it is informal.** A flowchart has no governing metamodel, no
exception semantics and nothing to validate against. That is fine for a
runbook and not fine for a regulated process — if handoffs between roles
matter, use `swimlane`; if it will be executed or audited, the catalogue
points at Camunda.

## Notation

Conventional shapes, and the engine maps Mermaid's syntax onto the house set:

| Mermaid | Shape | Use for |
|---|---|---|
| `A[Step]` | rounded | An action |
| `A([Start])` | stadium | Start and end |
| `A{Decision?}` | diamond | A branch |
| `A[(Store)]` | cylinder | Reading or writing data |
| `A{{Gateway}}` | hexagon | A parallel split or join |
| `A((Event))` | event | A trigger or wait |

Label every branch out of a decision. Keep it to one page: more than about a
dozen steps and the reader loses the thread — split it, or raise the level.

## Spec

```
---
method: flowchart
title: Incident triage
description: First thirty minutes of an incident.
render: scene
---
flowchart TB
  start([Alert fires]) --> ack[Acknowledge]
  ack --> sev{Customer impact?}
  sev -->|yes| page[Page the on-call lead]:::accent
  sev -->|no| queue[Queue for business hours]
  page --> comms[Open an incident channel]
  comms --> fix[Mitigate]
  fix --> done([Resolved])
  queue --> done
```

## Mistakes this invites

- **Letting it grow into a process model.** Past a dozen steps it wants lanes
  and a real notation.
- **Decisions that are not questions.** A diamond reading "Payment" tells the
  reader nothing; "Payment authorised?" does.
- **No terminal.** The reader cannot tell where the procedure ends.
- **Using it where handoffs matter.** A flowchart cannot show who does what,
  which is usually the thing people actually need.
