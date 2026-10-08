---
name: reference-architecture
description: Create reference architecture documents — topology, component selection, evaluation frameworks, sizing guidance, and deployment recommendations
triggerPatterns:
  - "reference.*architecture"
  - "architecture.*report"
  - "architecture.*recommendation"
  - "topology.*report"
  - "sizing.*guide"
---

# Reference Architecture Skill

Create reference architecture documents that evaluate technology options, recommend topologies, and provide sizing guidance. The practice context provides the domain framework — its alphas define the evaluation dimensions, its activities inform implementation sequencing, and its patterns shape the deployment approach.

The output is a standalone architecture document in plain English with diagrams, evaluation tables, and actionable recommendations. No Keleo terminology.

## Workflow Overview

**Step 0: Plan** → Identify practice context, technology requirements, evaluation dimensions
**Step 1: Load Context** → Resolve practice/method into effective context
**Step 2: Analyze & Select** → Extract domain knowledge, define evaluation framework
**Step 3: Generate Report** → Write architecture document with options analysis and recommendation

---

## Reporting Foundation

This skill builds on the common reporting infrastructure. Load these **on demand**:

| Document | Load at | What it provides |
|---|---|---|
| `.claude/skills/reporting-foundation/REPORT-FOUNDATION.md` | Steps 0–3 | Report workspace layout, session provenance, context resolution, domain extraction, citations, voice/tone, output format, framework attribution, shared rules |
| `.claude/skills/reporting-foundation/narrative-guide.md` | Step 0 | Narrative selection reference |
| `.claude/skills/reporting-foundation/diagram-guide.md` | Steps 2–3 — figure candidates are identified during domain extraction | The eight layouts and the Mermaid routes, deriving figures from the practice graph with `derive-diagram.py`, drawing the subject's instances rather than the practice's types, spec authoring, embedding convention — every option needs a topology diagram |

---

## Supporting Standards

`.claude/skills/SKILL-STANDARD.md` defines cross-cutting standards for all skills. **Do not read it upfront** — read the relevant section when a trigger fires:

| If you find yourself... | Stop and read |
|---|---|
| Writing `python3 -c`, `bash -c`, heredocs, or any ad-hoc inline script | §7 |
| Creating or extending a utility script | §7.4 |
| Finishing the workflow without auditing the session | §11 |

---

## External Dependencies

| Dependency | Required? | Role |
|---|---|---|
| `gws` CLI | Optional | Extract content from Google Slides/Docs with architecture diagrams or requirements |
| Playwright MCP | Optional | Load vendor documentation, product pages, or technical references |
| Remote bundle repository | Optional | Downloads `.keleo` bundles when the target practice isn't available locally |

---

## Preferred Narrative Structures

| Context | Primary | Secondary |
|---|---|---|
| Architecture comparison with recommendation | Report Narrative | SDLC or DBRO (for implementation phases) |
| Architecture with phased adoption path | Report Narrative | Crawl-Walk-Run (for maturity progression) |
| Implementation-focused architecture | DBRO or SDLC | Report Narrative (for formal evaluation) |

---

## Step 0: EnterPlanMode (REQUIRED)

**MANDATORY FIRST STEP.**

In plan mode:

1. **Identify the practice context**
   - Which practice, method, baseline, or `.keleo` bundle provides the domain framework?
   - The practice's alphas become the evaluation dimensions

2. **Identify the architecture challenge**
   - What technology decision needs to be made?
   - What are the candidate options? (minimum 2)
   - What are the environmental constraints? (scale, budget, existing infrastructure, vendor preferences)

3. **Define evaluation dimensions**
   - Derive evaluation dimensions from the practice's domain concerns
   - The user may specify priority dimensions or accept the practice-derived defaults
   - Each dimension should be assessable for each architecture option

4. **Determine scope**
   - Comparison only, or comparison with recommendation?
   - Include sizing guidance? Implementation approach?
   - Target audience technical depth

**ExitPlanMode** once the user approves the plan.

**Then open the report workspace, before any content work begins:** derive the kebab-case slug from the agreed title, create `reports/<report-slug>/`, initialise the prompt history, and record the sources identified during planning. See `reporting-foundation/REPORT-FOUNDATION.md` → Report Workspace and Session Provenance. `--init` arms the interaction hooks, so do it before the next exchange with the user.

---

## Step 3: Output Structure

```markdown
# <Architecture Title>

**<Subtitle — e.g., "Architecture Recommendation for ..." or "Reference Architecture: ...">**

---

## Executive Summary

<Recommended option + one-paragraph rationale. If comparison-only (no recommendation), summarise the key trade-offs instead.>

---

## The Challenge

<What the architecture must achieve. Environmental constraints, scale requirements, existing infrastructure, and competing priorities that make the decision non-trivial.>

---

## Evaluation Framework

<Table of evaluation dimensions — derived from practice domain concerns. This section must always be present.>

| Dimension | What We Assessed |
|-----------|-----------------|
| **<Dimension 1>** | <Brief description> |
| **<Dimension 2>** | <Brief description> |
| ... | ... |

---

## Architecture Options

### Option A: <Name>

![<Option name> topology](assets/<option-slug>-topology.svg)

*Figure N — <Option name> topology*

<Rendered with `utils/render-diagram.py` from a `flow` spec. Never ASCII art.>

<How it works — mechanism, components, data flow.>

<A reference architecture normally carries more than one figure per option. Beyond the
topology, reach for a `stack` where the design is a layer model, a `timeline` where
adoption is phased, and a `matrix` where the point is coverage across two axes. Where the
deployment has several instances of one thing — production and DR, per-region clusters —
draw the instances, not the type. See `reporting-foundation/diagram-guide.md`, and derive
what the practice already knows with `utils/derive-diagram.py`.>

**Strengths:**
- <strength 1>
- <strength 2>

**Weaknesses:**
- <weakness 1>
- <weakness 2>

### Option B: <Name>

<Same structure as Option A.>

---

## Comparison and Recommendation

<Decision matrix comparing all options across evaluation dimensions.>

| Dimension | Option A | Option B | ... |
|-----------|----------|----------|-----|
| <Dim 1> | <assessment> | <assessment> | |
| ... | | | |

<Recommendation with rationale, or contextual verdict ("if X, then A; if Y, then B") when the best option depends on circumstances.>

---

## Sizing Guidance

<Optional but recommended. Concrete capacity numbers, node counts, resource calculations, or storage estimates. Present as tables where possible.>

---

## Implementation Approach

<Phased implementation using SDLC, DBRO, or CWR structure. What to do first, what to defer, what dependencies exist between phases.>

---

## References
```

---

## Feature: Reference Architecture Quality

### Scenario: Evaluation framework table is present (@rule:report-620)
- Given: an architecture document is generated
- When: the document includes an evaluation section
- Then: a structured evaluation framework table lists named dimensions with descriptions
- And: dimensions derive from the practice's domain concerns

### Scenario: Each option has topology and trade-offs (@rule:report-621)
- Given: architecture options are presented
- When: each option section is written
- Then: each option includes a rendered SVG topology diagram embedded with a relative path
- And: the diagrams were generated by `utils/render-diagram.py`, not hand-drawn (@rule:report-611)
- And: each option includes both a strengths list and a weaknesses list

### Scenario: Decision matrix compares all options (@rule:report-622)
- Given: multiple architecture options are evaluated
- When: the comparison section is written
- Then: a comparison table or decision matrix assesses all options across the same evaluation dimensions
- And: the comparison is balanced (no straw-man options)

### Scenario: Sizing guidance includes concrete numbers (@rule:report-623)
- Given: a sizing guidance section is included
- When: sizing information is presented
- Then: the section includes concrete capacity numbers, node counts, or resource calculations
- And: numbers are presented in tabular format where applicable

### Scenario: Implementation uses phased structure (@rule:report-624)
- Given: an implementation approach section is included
- When: the approach is described
- Then: implementation follows a phased structure (SDLC, DBRO, or CWR)
- And: phases identify dependencies and sequencing constraints

---

## Post-Completion

Record the architecture document — and any PDF or published Google Doc URL — as deliverables, then `--finalize` the prompt history (REPORT-FOUNDATION → Session Provenance).

Then perform the Post-Completion Review per SKILL-STANDARD.md §11.
