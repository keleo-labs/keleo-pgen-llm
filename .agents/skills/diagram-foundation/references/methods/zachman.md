# Zachman classification grid

Route A, layout `matrix`.

## When

Auditing whether an architecture *description* is complete. Zachman is an
ontology, not a method: it tells you which artifacts exist and which are
missing, not how to build anything.

Reach for it when someone asks "what have we not documented?" or a regulator
asks for evidence of coverage. Audience is chief architects and auditors.

Zachman classifies; TOGAF governs change. Pair them rather than choosing.

## Notation

Six columns, always these six interrogatives, in this order:

| What | How | Where | Who | When | Why |
|---|---|---|---|---|---|
| Data | Function | Network | People | Time | Motivation |

Six rows, each a stakeholder perspective, most abstract at the top:

Scope (planner) · Business model (owner) · System model (designer) ·
Technology model (builder) · Detailed representations (implementer) ·
Functioning enterprise (worker)

A cell holds the *name of the artifact* that fills it, not a description of
the concept. "Customer MDM logical model", not "customer data".

**A `null` cell is the point of the exercise.** It is drawn as an empty
outline, and that gap is the audit finding.

Thirty-six cells is wide. Drawing a subset — three columns, four rows — is
normal and usually more useful; say in the description which subset and why.

## Spec

```json
{"layout": "matrix",
 "title": "Architecture coverage audit",
 "description": "Zachman columns What, How and Who across four perspectives.",
 "cellWidth": 170,
 "columns": [{"label": "What", "sublabel": "data"},
             {"label": "How", "sublabel": "function"},
             {"label": "Who", "sublabel": "people"}],
 "rows": [
   {"label": "Scope", "sublabel": "planner", "cells": [
     {"label": "Subject area list"}, {"label": "Capability map"},
     {"label": "Stakeholder register"}]},
   {"label": "Business model", "sublabel": "owner", "cells": [
     {"label": "Conceptual data model"}, {"label": "Value streams"}, null]},
   {"label": "System model", "sublabel": "designer", "cells": [
     {"label": "Logical data model"}, {"label": "Service catalogue"}, null]}]}
```

## Mistakes this invites

- **Using it as a delivery plan.** It has no lifecycle. Filling all 36 cells
  is not a goal and chasing it produces documentation nobody reads.
- **Putting concepts in cells instead of artifacts.** The grid inventories
  what exists; a concept name tells you nothing about coverage.
- **Hiding the gaps.** Omitting an empty cell to make the grid look tidy
  destroys the only reason to draw it.
