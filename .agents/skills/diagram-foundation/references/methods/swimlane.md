# Swimlane process

Route A, layout `swimlane`.

## When

The handoffs are the point. Who does what, in what order, and where work
crosses an organisational or system boundary. Audience is process analysts
and operations.

This is BPMN-shaped but not BPMN. It has lanes, gateways and events; it has
no boundary error events, no compensation, no XML, and it cannot be deployed
to an engine. For a process that will be executed or audited against a
regulation, say so and point at Camunda Modeler — see the catalogue.

## Notation

One lane per actor or system. Steps are ranked into columns from the edge
graph, so you declare the handoffs and the engine lines them up; set
`column` to pin a step with no incoming edge.

Shapes carry meaning here, more than in other layouts:

| Shape | Use for |
|---|---|
| `stadium` | Process start and end |
| `rounded` | An activity — the default |
| `diamond` | A decision with labelled outcomes |
| `hexagon` | A gateway: parallel split or join |
| `event` | A timer, message or signal |
| `cylinder` | A store the process reads or writes |

Label every edge leaving a decision. An unlabelled branch is a guess.

## Spec

```json
{"layout": "swimlane",
 "title": "Expense approval",
 "lanes": [
   {"label": "Employee", "steps": [
     {"id": "a", "label": "Submit claim", "shape": "stadium"},
     {"id": "f", "label": "Correct and resubmit"}]},
   {"label": "Line manager", "steps": [
     {"id": "b", "label": "Review claim"},
     {"id": "c", "label": "Within policy?", "shape": "diamond"}]},
   {"label": "Finance", "steps": [
     {"id": "d", "label": "Schedule payment", "emphasis": "accent"},
     {"id": "e", "label": "Paid", "shape": "stadium"}]}],
 "edges": [{"from": "a", "to": "b"},
           {"from": "b", "to": "c"},
           {"from": "c", "to": "d", "label": "yes"},
           {"from": "c", "to": "f", "label": "no", "dash": "dashed"},
           {"from": "d", "to": "e"}]}
```

## Mistakes this invites

- **Lanes that are not actors.** A lane per phase is a timeline, not a
  swimlane, and it hides the handoffs that justify the method.
- **Unlabelled decision branches.** The reader has to guess which way is
  which.
- **No start or end.** Without terminals, nobody can tell whether the process
  is complete or you ran out of room.
- **Claiming it is BPMN.** It is not, and someone will eventually try to
  deploy it.
