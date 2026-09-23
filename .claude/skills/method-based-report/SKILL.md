---
name: method-based-report
description: Generate plain English reports structured by practice/method narrative frameworks — audience sees domain insight, not Keleo internals
triggerPatterns:
  - "method.*report"
  - "practice.*report"
  - "report.*using"
  - "write.*report"
  - "generate.*report"
---

# Method-Based Report Skill

Generate a well-structured markdown report on a user-specified subject, using the narrative frameworks and domain knowledge from a Keleo practice, method, or baseline. The report reads as a standalone document for a general audience — no Keleo terminology, no schema references, no Practice Language jargon.

This is the **general-purpose** reporting skill. For specialised report types, use:
- `/reference-architecture` — topology, component selection, sizing, evaluation frameworks
- `/project-plan` — project plans, PoC outlines, SOW generation
- `/decision-analysis` — trade-off analysis, weighing architectural or strategic choices
- `/document-review` — review a document and recommend improvements

## Workflow Overview

**Step 0: Plan** → Identify practice context, subject, and report strategy
**Step 1: Load Context** → Resolve practice/method into effective context
**Step 2: Analyze & Select** → Extract domain knowledge and select narrative structures
**Step 3: Generate Report** → Write plain English report structured by narrative frameworks

---

## Reporting Foundation

This skill builds on the common reporting infrastructure. Load these **on demand** at the step that needs them:

| Document | Load at | What it provides |
|---|---|---|
| `.claude/skills/reporting-foundation/REPORT-FOUNDATION.md` | Steps 1–3 | Context resolution, domain extraction, citations, voice/tone, output format, shared Gherkin rules (@rule:report-600 through 608) |
| `.claude/skills/reporting-foundation/narrative-guide.md` | Step 0 and Step 2 | Narrative type selection, purpose-to-narrative mapping, element-to-heading mappings |

---

## Supporting Standards

`.claude/skills/SKILL-STANDARD.md` defines cross-cutting standards for all skills. **Do not read it upfront** — read the relevant section when a trigger fires:

| If you find yourself... | Stop and read |
|---|---|
| Writing `python3 -c`, `bash -c`, heredocs, or any ad-hoc inline script | §7 — these are prohibited; use reusable utils instead |
| Creating or extending a utility script | §7.4 — follow the Utils Self-Extension Protocol |
| Needing functionality that no existing util covers | §7.4 — create/extend, don't work around it |
| Finishing the workflow without auditing the session | §11 — Post-Completion Review is mandatory |

---

## External Dependencies

| Dependency | Required? | Role |
|---|---|---|
| `gws` CLI | Optional | Google Drive export for PDF output; Google Slides content extraction for source material |
| Playwright MCP | Optional | Content sourcing from web pages when researching the report subject |
| Remote bundle repository | Optional | Downloads `.keleo` bundles when the target practice/method isn't available locally |

Both `gws` and Playwright are content sourcing tools — they help gather subject-matter material during the research phase. The core report generation works without either, as long as the practice context is available locally.

---

## Step 0: EnterPlanMode (REQUIRED)

**MANDATORY FIRST STEP.** Before generating any report, you MUST use EnterPlanMode to:

1. **Identify the practice context**
   - The user must specify a practice, method, baseline, or `.keleo` bundle
   - Accept any of: `.keleo` path, `.json` path, practice name (resolved from `practices/`, `baselines/`, `deps/`, `bundles/`)
   - If ambiguous, ask the user to clarify

2. **Clarify the subject and purpose**
   - What is the report about? (the domain subject, not the practice itself)
   - Who is the audience? (default: general business/technical audience)
   - What is the report's purpose? (inform, assess, recommend, persuade)
   - What scope or angle should the report take?

3. **Preview the narrative strategy**
   - Read `reporting-foundation/narrative-guide.md` to select structures
   - Note which narrative types are available from the baseline
   - Propose a primary narrative structure for the overall report
   - Propose any secondary structures for subsections
   - Confirm the approach with the user before proceeding

**ExitPlanMode** once the user approves the plan.

---

## Steps 1–3: Execution

Follow the common reporting workflow in `reporting-foundation/REPORT-FOUNDATION.md`:

1. **Load Context** — Context Resolution section
2. **Analyze & Select** — Domain Knowledge Extraction + Citation Pool sections. For narrative selection, use the purpose-to-narrative mapping in `reporting-foundation/narrative-guide.md`.
3. **Generate Report** — Voice and Tone, Content Sourcing, Report Structure, Length and Depth, Output, Citations in Reports sections

For multi-practice reports, also follow the Multi-Source Reports section.

---

## Post-Completion

After generating the report, perform the Post-Completion Review per SKILL-STANDARD.md §11.
