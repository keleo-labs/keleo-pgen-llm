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
| `.claude/skills/reporting-foundation/REPORT-FOUNDATION.md` | Steps 0–3 | Report workspace layout, session provenance, context resolution, domain extraction, citations, voice/tone, output format, framework attribution, shared Gherkin rules (@rule:report-600 through 614) |
| `.claude/skills/reporting-foundation/narrative-guide.md` | Step 0 and Step 2 | Narrative type selection, purpose-to-narrative mapping, element-to-heading mappings |
| `.claude/skills/reporting-foundation/diagram-guide.md` | Steps 2–3 — figure candidates are identified during domain extraction | How many figures a report carries, the eight layouts and the Mermaid routes, deriving figures from the practice graph with `derive-diagram.py`, drawing the subject's instances rather than the practice's types, when a table beats a diagram, spec authoring, embedding convention |

---

## Supporting Standards

`.claude/skills/SKILL-STANDARD.md` defines cross-cutting standards for all skills. **Do not read it upfront** — read the relevant section when a trigger fires:

| If you find yourself... | Stop and read |
|---|---|
| Writing `python3 -c`, `bash -c`, heredocs, or any ad-hoc inline script | §7 — these are prohibited; use reusable utils instead |
| Creating or extending a utility script | §7.4 — follow the Utils Self-Extension Protocol |
| Needing functionality that no existing util covers | §7.4 — create/extend, don't work around it |
| Finishing the workflow without auditing the session | §11 — Post-Completion Review is mandatory |
| Working around a defect in the practice content you are consuming | §13 — accommodate it, then file it with `/report-issue` |

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
   - When multiple practices are specified, check their root baselines (`baselinePracticeName`). If they differ, note in the plan that separate effective-context.json files will be created — one per distinct root baseline. Identify which is the primary context (drives report structure) and which is supplementary (enriches specific sections).

2. **Recommend practices from the library**
   - Run `python3 utils/library-index.py --kind practice method --compact` to get a summary of all available practices and methods
   - Read the index output and identify 1–3 practices or methods whose description, outcomes, or keywords semantically align with the user's reporting objective
   - Present recommendations to the user with a brief rationale for each (e.g., "CRM Foundations addresses customer lifecycle management, which aligns with your report on account planning")
   - If the user already specified a practice, still present recommendations as supplementary options that may enrich the report
   - The user decides: accept one or more recommendations, decline all, or substitute their original selection
   - Proceed with whatever the user confirms — do not re-recommend after they decide

3. **Clarify the subject and purpose**
   - What is the report about? (the domain subject, not the practice itself)
   - Who is the audience? (default: general business/technical audience)
   - What is the report's purpose? (inform, assess, recommend, persuade)
   - What scope or angle should the report take?

4. **Preview the narrative strategy**
   - Read `reporting-foundation/narrative-guide.md` to select structures
   - Note which narrative types are available from the baseline
   - Propose a primary narrative structure for the overall report
   - Propose any secondary structures for subsections
   - Confirm the approach with the user before proceeding

**ExitPlanMode** once the user approves the plan.

**Then open the report workspace, before any content work begins:** derive the kebab-case slug from the agreed title, create `reports/<report-slug>/`, initialise the prompt history, and record the sources identified during planning. See `reporting-foundation/REPORT-FOUNDATION.md` → Report Workspace and Session Provenance. `--init` arms the interaction hooks, so do it before the next exchange with the user.

---

## Multi-Report Generation

When the user requests multiple separate reports from a shared method (e.g., one per product area, one per practice):

1. **Plan the batch in Step 0** — note all N reports, shared method, per-report subjects, any supplementary methods, and confirm the approach with the user.
2. **Extract per-report domain knowledge** — use `inspect-keleo.py --extract-doc` to pull individual practices from `.keleo` bundles, and `practice-summary.py` to build structured summaries for agent prompts.
3. **Launch parallel agents** — construct a prompt per report with embedded domain knowledge (alphas, outcomes, patterns, citations from the relevant practices), then launch all agents concurrently in a single message.
4. **Each agent follows Steps 1–3 independently** — resolving context, selecting narratives, and writing to its own output file.

See `reporting-foundation/REPORT-FOUNDATION.md` → "Parallel Multi-Report Generation" for the full pattern including context resolution, extraction commands, and supplementary method handling.

---

## Steps 1–3: Execution

Follow the common reporting workflow in `reporting-foundation/REPORT-FOUNDATION.md`:

1. **Load Context** — Context Resolution section
2. **Analyze & Select** — Domain Knowledge Extraction + Citation Pool sections. For narrative selection, use the purpose-to-narrative mapping in `reporting-foundation/narrative-guide.md`.
3. **Generate Report** — Voice and Tone, Content Sourcing, Report Structure, Framework Attribution, Length and Depth, Output, Citations in Reports sections

For multi-practice reports, also follow the Multi-Source Reports section.

---

## Verification

Lint and the verification gate are mandatory before handover — see REPORT-FOUNDATION → Output (Step 3). This skill has **no type-specific verifier**, so run the four base verifiers and omit `type-specific` from `--expect`.

## Post-Completion

Record the report — and any PDF or published Google Doc URL — as deliverables, then `--finalize` the prompt history (REPORT-FOUNDATION → Session Provenance).

Then perform the Post-Completion Review per SKILL-STANDARD.md §11.
