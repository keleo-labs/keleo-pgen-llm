# Business capability map

Route A, layout `matrix`.

## When

Showing *what* an organisation does, independent of how it does it or who
does it. Portfolio rationalisation, post-merger overlap, technical debt made
visible to people who do not read architecture diagrams. Audience is the
C-suite and enterprise architects.

A capability map is deliberately organisation-neutral: it survives a
reorganisation, which is most of its value. If your rows are team names, you
have drawn an org chart.

## Notation

Columns are value-chain stages; rows are capability domains; cells are
capabilities. Standard practice decomposes three tiers deep — this layout
draws one grid, so pick the tier that carries the argument.

Heat is the usual reason to draw one. `role` on a cell takes `heat.1` to
`heat.5`, 1 healthy to 5 critical. The scale is fixed rather than palette-
derived, because a heat map whose meaning changed with the deck theme would
be worse than none.

**Always include the legend.** A reader cannot infer what amber means.

A `null` cell draws as an empty outline. The gap is often the finding.

## Spec

```json
{"layout": "matrix",
 "title": "Capability heat map",
 "description": "Capability domains scored for technical debt.",
 "columns": [{"label": "Acquire"}, {"label": "Fulfil"}, {"label": "Service"}],
 "rows": [
   {"label": "Customer", "sublabel": "tier 1", "cells": [
     {"label": "Lead capture", "role": "heat.2"},
     {"label": "Order intake", "role": "heat.1"},
     {"label": "Case management", "role": "heat.4"}]},
   {"label": "Partner", "cells": [
     {"label": "Onboarding", "role": "heat.5"}, null,
     {"label": "Support desk", "role": "heat.2"}]}],
 "legend": [{"role": "heat.1", "label": "Healthy"},
            {"role": "heat.3", "label": "Watch"},
            {"role": "heat.5", "label": "Critical"}]}
```

## Mistakes this invites

- **Capabilities that are processes.** "Onboard a partner" is a process;
  "Partner onboarding" is a capability. Noun phrases, always.
- **Rows that are teams or systems.** Then it is an org chart or an
  application inventory, and it dies at the next reorganisation.
- **Heat with no legend or no basis.** State what was scored and how, in the
  description or the surrounding prose.
- **Too fine a tier.** Forty cells is an inventory. Pick the tier at which
  the leadership decision is made.
