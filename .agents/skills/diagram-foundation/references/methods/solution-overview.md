# Solution overview

Route B (`flowchart`), or route A `flow` when you want to place things by hand.

Sometimes called a "marketecture". The name is not an insult — this is a real
and necessary artifact, as long as nobody mistakes it for a specification.

## When

Sales engagements, executive briefings, investor material, keynote slides.
The question it answers is "what does this do for me", never "how is it
built". Audience is prospects, executives and investors.

## Notation

Arrange into clean horizontal tiers, four at most:

1. Client touchpoints
2. Integration and API layer
3. Core domain services
4. Data

Abstract away everything the audience cannot act on — subnets, ports,
connection pools, retry logic, queue names. Balance the tiers: four boxes on
one row and one on the next reads as an accident.

Capability names, not product names, unless the product name *is* the value.
"Automated governance", not "OPA Gatekeeper v3.14".

Use `accent` on the one or two things that are the differentiator. That is
the whole message; everything else is context.

## Spec

```
---
method: solution-overview
title: Platform overview
description: Capabilities and how they connect, for a buying audience.
render: scene
---
flowchart TB
  subgraph touch["Your teams"]
    portal[Self-service portal]
    cli[CLI and API]
  end
  subgraph core["Platform"]
    gov[Automated governance]:::accent
    orch[Workflow orchestration]
    ins[Insight and reporting]
  end
  subgraph data["Your estate"]
    cloud[Multi-cloud estate]
    rec[Systems of record]
  end
  portal --> gov
  cli --> gov
  gov --> orch
  orch --> cloud
  orch --> rec
  cloud --> ins
```

## Mistakes this invites

- **Letting it become the build spec.** This is the real risk. It has no
  error handling, no security boundaries and no failure modes, and a team
  that builds from it will discover all three late. Say plainly that it is a
  conceptual overview when you hand it over.
- **Implementation detail creeping in.** One Kubernetes reference and the
  conversation is about Kubernetes.
- **Everything accented.** Then nothing is the differentiator.
- **Unbalanced tiers.** Reads as unfinished, whatever the content.
