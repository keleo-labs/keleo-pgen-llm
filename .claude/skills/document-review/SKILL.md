---
name: document-review
description: Review a provided document against practice domain knowledge — what's strong, what could be improved, what isn't needed
triggerPatterns:
  - "review.*document"
  - "review.*deck"
  - "review.*presentation"
  - "assess.*document"
  - "improve.*document"
  - "critique.*document"
  - "gap.*analysis"
  - "deck.*review"
---

# Document Review Skill

Review a provided document (deck, whitepaper, proposal, presentation, or other content) and produce a structured improvement report. The practice context provides the analytical lens — the review assesses the document against the practice's domain knowledge, identifying strengths, gaps, and actionable recommendations.

The output is a standalone improvement report, not an annotated copy of the original. Readers see domain-informed assessment in plain English, not Keleo framework terminology.

## Workflow Overview

**Step 0: Plan** → Identify practice context, document to review, review focus
**Step 1: Load Context** → Resolve practice/method into effective context
**Step 2: Analyze & Select** → Extract domain knowledge, ingest the document, assess coverage
**Step 3: Generate Report** → Write review report with findings and recommendations

---

## Reporting Foundation

This skill builds on the common reporting infrastructure. Load these **on demand**:

| Document | Load at | What it provides |
|---|---|---|
| `.claude/skills/reporting-foundation/REPORT-FOUNDATION.md` | Steps 1–3 | Context resolution, domain extraction, citations, voice/tone, output format, shared rules |
| `.claude/skills/reporting-foundation/narrative-guide.md` | Step 0 | Narrative selection (this skill uses fixed structures — guide is for reference only) |

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
| `gws` CLI | Optional | Extract content from Google Slides/Docs when the document to review is a Google Workspace file |
| Playwright MCP | Optional | Load web-hosted documents or pages for review |
| Remote bundle repository | Optional | Downloads `.keleo` bundles when the target practice isn't available locally |

---

## Preferred Narrative Structures

| Context | Primary | Secondary |
|---|---|---|
| Standard document review | Report Narrative | Crawl-Walk-Run (for prioritising improvements) |
| Gap analysis focus | Report Narrative | STAR (for illustrating what good looks like) |

---

## Step 0: EnterPlanMode (REQUIRED)

**MANDATORY FIRST STEP.**

In plan mode:

1. **Identify the practice context**
   - Which practice, method, baseline, or `.keleo` bundle provides the analytical framework?
   - The practice's alphas and activities become the assessment dimensions

2. **Identify the document to review**
   - Accept: local file path, Google Docs/Slides URL, web URL, or pasted content
   - Determine document type (deck, whitepaper, proposal, report, etc.)
   - Note the document's stated purpose and intended audience

3. **Clarify the review focus**
   - Full review (assess against all relevant practice dimensions) — default
   - Focused review (assess against specific aspects the user cares about)
   - What is the user trying to achieve with this document?

4. **Preview the assessment approach**
   - Identify which practice dimensions (alphas/concerns) are relevant to this document type
   - Confirm the assessment scope with the user

**ExitPlanMode** once the user approves the plan.

---

## Step 2: Document Ingestion

After loading the practice context (Step 1 per REPORT-FOUNDATION.md), ingest the document:

- **Local file:** Read the file directly
- **Google Docs/Slides:** Use `gws drive files export <file-id> --mime text/plain` to extract text content
- **Web URL:** Use WebFetch first; fall back to Playwright if access fails
- **Pasted content:** Work directly with the provided text

Build a mental map of the document's structure, coverage, messaging, and gaps relative to the practice's domain knowledge.

---

## Step 3: Output Structure

```markdown
# <Review Title>

**<Subtitle: "Recommendations for improving ..." or "Assessment of ...">**

## Executive Summary

<Headline assessment — overall quality verdict + top 3 priority recommendations. Brief and direct.>

## Current Document Assessment

### Scope and Audience
<What the document covers, who it targets, and whether these align with its stated purpose.>

### Strengths
<What works well, with specific callouts to sections, slides, or passages. Be concrete — "Slide 12's architecture diagram clearly shows..." not "the diagrams are good".>

### Structural Weaknesses
<Systematic issues — not line-by-line nitpicks but patterns that reduce the document's effectiveness.>

## Gap Analysis

<One subsection per relevant practice domain dimension. Each dimension maps to a practice alpha or activity cluster.>

### <Dimension 1> — <Coverage Level>

<Current state: what the document says about this dimension.>
<What's missing: gaps relative to what the practice framework considers important.>
<Recommendation: specific, actionable improvement.>

### <Dimension 2> — <Coverage Level>
...

## Priority Recommendations

<Numbered, actionable, with rationale connecting each to the practice's domain framework.>

1. **<Recommendation title>.** <Detail — what to change, why, and what good looks like.>
2. ...

## Implementation Guidance

<Optional: suggested order for applying recommendations. Use Crawl-Walk-Run or a simple priority ranking.>

## References
```

**Coverage levels** for gap analysis dimensions: use plain language indicators (Strong, Adequate, Partial, Minimal, Absent) — not numeric scores or letter grades.

---

## Feature: Document Review Quality

### Scenario: Review identifies both strengths and weaknesses (@rule:report-680)
- Given: a document is reviewed against a practice framework
- When: the review report is generated
- Then: the report includes a Strengths section with specific positive callouts
- And: the report includes a Structural Weaknesses section with pattern-level issues

### Scenario: Gap analysis dimensions come from practice domain (@rule:report-681)
- Given: a practice provides domain knowledge via alphas and activities
- When: gap analysis dimensions are determined
- Then: each dimension maps to a practice alpha, activity cluster, or domain concern
- And: dimensions are not generic quality criteria (grammar, formatting) but domain-specific

### Scenario: Recommendations are actionable (@rule:report-682)
- Given: gaps are identified in the reviewed document
- When: recommendations are written
- Then: each recommendation is specific enough to implement (not just "improve X")
- And: each recommendation describes what to change and what good looks like

### Scenario: Review cites evidence from the reviewed document (@rule:report-683)
- Given: a document is being assessed
- When: findings are reported
- Then: the review cites specific examples from the document (section references, slide numbers, quoted passages)
- And: findings are grounded in concrete evidence, not abstract impressions

### Scenario: Recommendations connect to domain framework (@rule:report-684)
- Given: recommendations are informed by the practice framework
- When: recommendations are written
- Then: each recommendation includes rationale grounded in the practice's domain expertise
- And: the rationale uses plain language (no Keleo terminology)

---

## Post-Completion

After generating the review report, perform the Post-Completion Review per SKILL-STANDARD.md §11.
