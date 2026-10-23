# Wardley map

Route A, layout `wardley`.

## When

Build versus buy. Where to put scarce engineering effort. Arguing that
something the team is lovingly hand-building is already a commodity. Audience
is a CTO, a strategy lead, a product director — people deciding where money
goes, not how code is structured.

Not a dependency diagram. If nobody is going to make a positioning decision
from it, draw a C4 context instead.

## Notation

Two axes, both load-bearing.

**Visibility** (y, 0 to 1). How directly the user anchor sees this component.
1 is the anchor itself; 0 is infrastructure nobody outside the team names.
Position by *distance along the value chain*, not importance.

**Evolution** (x, 0 to 1). How settled the component is as a market.

| Range | Phase | Means |
|---|---|---|
| 0.00–0.25 | Genesis | Novel, uncertain, built because nothing exists |
| 0.25–0.50 | Custom-built | Understood, still bespoke to you |
| 0.50–0.75 | Product | Buyable, differentiated by feature |
| 0.75–1.00 | Commodity | Utility. Buying it is the only sane choice |

Edges are the value chain: what depends on what. They carry no arrow heads
and no labels — a Wardley map is a landscape, not a flow.

`movements` draw a dashed arrow to a future evolution. Use them for the one
or two components whose drift is the argument.

## Spec

```json
{"layout": "wardley",
 "title": "Account planning platform",
 "anchor": "Account team",
 "components": [
   {"id": "user", "label": "Account team", "visibility": 1.0,
    "evolution": 0.1, "emphasis": "accent"},
   {"id": "insight", "label": "Opportunity insight", "visibility": 0.68,
    "evolution": 0.16, "sublabel": "differentiating"},
   {"id": "llm", "label": "LLM inference", "visibility": 0.34, "evolution": 0.62},
   {"id": "compute", "label": "Compute", "visibility": 0.06, "evolution": 0.95}],
 "edges": [{"from": "user", "to": "insight"},
           {"from": "insight", "to": "llm"},
           {"from": "llm", "to": "compute"}],
 "movements": [{"from": "llm", "to": 0.84}]}
```

## Mistakes this invites

- **Positioning by importance rather than evolution.** A critical database is
  still a commodity. Criticality is not maturity, and conflating them is how
  a map ends up arguing for building your own.
- **No anchor.** A map with no named user is a dependency graph with extra
  axes. Set `anchor`.
- **Too many components.** Above about a dozen, nobody reads the shape. The
  argument is usually three or four components anyway.
- **Arrow heads.** The engine does not draw them. If you want flow direction
  you want a different method.
