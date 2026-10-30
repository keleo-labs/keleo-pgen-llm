# Pace layering

Route A, layout `matrix`.

## When

Justifying that one governance model cannot serve a whole application
portfolio. Gartner's framing: systems change at three different rates, and
forcing the slow model onto the fast ones kills innovation while forcing the
fast model onto the slow ones breaks the general ledger.

Audience is application portfolio leads and enterprise architects, usually
during a modernisation or an ERP argument.

## Notation

Three rows, in this order, fastest at the top:

| Layer | Rate of change | Governance |
|---|---|---|
| Systems of innovation | Weeks to months | Experiment, tolerate failure, minimal overhead |
| Systems of differentiation | Quarters | Unique IP, customer experience, reconfigurable |
| Systems of record | Years | Integrity, compliance, centralised change control |

Columns are whatever dimension carries the argument — business domain,
delivery cadence, funding model. Use `role` of `pace.innovation`,
`pace.differentiation`, `pace.record` on the row headers so the layer reads
as a gradient from accent to neutral.

The point of the diagram is the *contrast between rows*, so keep the columns
few and the cells short.

## Spec

```json
{"layout": "matrix",
 "title": "Portfolio by pace layer",
 "columns": [{"label": "Customer"}, {"label": "Supply"}, {"label": "Finance"}],
 "rows": [
   {"label": "Innovation", "sublabel": "weeks", "role": "pace.innovation",
    "cells": [{"label": "Next-best-action pilot"}, {"label": "Demand sensing"}, null]},
   {"label": "Differentiation", "sublabel": "quarters",
    "role": "pace.differentiation",
    "cells": [{"label": "Quoting engine"}, {"label": "Route planning"},
              {"label": "Rebate modelling"}]},
   {"label": "Record", "sublabel": "years", "role": "pace.record",
    "cells": [{"label": "CRM"}, {"label": "WMS"}, {"label": "ERP"}]}]}
```

## Mistakes this invites

- **Treating the layer as a quality judgement.** A system of record is not a
  legacy problem. It is supposed to change slowly.
- **Putting a system in the layer someone wishes it were in.** Classify by
  observed change frequency, not ambition.
- **Drawing it without the governance consequence.** The diagram is an
  argument about how to govern. Say what follows from each row.
