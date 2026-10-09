---
name: project-plan
description: Create high-level project plans, PoC outlines, and implementation roadmaps — with optional SOW generation for T&M consulting engagements
triggerPatterns:
  - "project.*plan"
  - "poc.*plan"
  - "implementation.*plan"
  - "migration.*plan"
  - "sow"
  - "statement.*of.*work"
  - "engagement.*plan"
  - "proof.*of.*concept"
---

# Project Plan Skill

Create high-level project plans for achieving specific objectives — PoC plans, implementation plans, migration plans, and engagement outlines. The practice context provides the domain framework — its activities and patterns inform the plan's phases, its alphas shape scope and success criteria, and its personas map to project roles.

Includes a **SOW sub-mode** for generating Statements of Work for Time & Materials consulting engagements, either as a standalone document or appended to a project plan.

The output is a standalone plan document in plain English. No Keleo terminology.

## Workflow Overview

**Step 0: Plan** → Identify practice context, objectives, scope, engagement model
**Step 1: Load Context** → Resolve practice/method into effective context
**Step 2: Analyze & Select** → Extract domain knowledge, map to plan phases and roles
**Step 3: Generate Report** → Write plan document (and optionally SOW)

---

## Reporting Foundation

This skill builds on the common reporting infrastructure. Load these **on demand**:

| Document | Load at | What it provides |
|---|---|---|
| `.claude/skills/reporting-foundation/REPORT-FOUNDATION.md` | Steps 0–3 | Report workspace layout, session provenance, context resolution, domain extraction, citations, voice/tone, output format, framework attribution, shared rules |
| `.claude/skills/reporting-foundation/narrative-guide.md` | Step 0 | Narrative selection reference |
| `.claude/skills/reporting-foundation/diagram-guide.md` | Steps 2–3 — figure candidates are identified during domain extraction | The eight layouts and the Mermaid routes, deriving figures from the practice graph with `derive-diagram.py` — `--view journey` turns a practice pattern straight into a phased `timeline`, `flow` suits dependency chains, and `swimlane` suits handoffs between roles |

---

## Supporting Standards

`.claude/skills/SKILL-STANDARD.md` defines cross-cutting standards for all skills. **Do not read it upfront** — read the relevant section when a trigger fires:

| If you find yourself... | Stop and read |
|---|---|
| Writing `python3 -c`, `bash -c`, heredocs, or any ad-hoc inline script | §7 |
| Creating or extending a utility script | §7.4 |
| Finishing the workflow without auditing the session | §11 |
| Working around a defect in the practice content you are consuming | §13 — accommodate it, then file it with `/report-issue` |

---

## External Dependencies

| Dependency | Required? | Role |
|---|---|---|
| `gws` CLI | Optional | Extract requirements from Google Docs/Sheets; export plan as PDF |
| Playwright MCP | Optional | Load customer-facing requirements or engagement briefs from web |
| Remote bundle repository | Optional | Downloads `.keleo` bundles when the target practice isn't available locally |

---

## Preferred Narrative Structures

| Context | Primary | Secondary |
|---|---|---|
| Technical implementation plan | SDLC | Crawl-Walk-Run (for phased rollout) |
| Broad project or transformation | DBRO | Report Narrative (for formal structure) |
| PoC or pilot engagement | SDLC | Report Narrative (for executive sections) |
| SOW (standalone) | Report Narrative | SDLC (for scope of services phases) |

---

## Step 0: EnterPlanMode (REQUIRED)

**MANDATORY FIRST STEP.**

In plan mode:

1. **Identify the practice context**
   - Which practice, method, baseline, or `.keleo` bundle provides the domain framework?
   - The practice's activities and patterns inform the plan's work breakdown

2. **Identify objectives and scope**
   - What are the project's specific objectives? (measurable outcomes)
   - What is in scope? What is explicitly out of scope?
   - Who is the customer or partner? Who is the intended audience for the plan?
   - What is the engagement type? (PoC, implementation, migration, assessment)

3. **Identify roles and organisations**
   - Which organisations are involved? (customer, partner, vendor)
   - What roles does each organisation play?
   - Map practice personas to real-world roles in this engagement

4. **SOW mode decision**
   - Does the user want a project plan only, SOW only, or both?
   - If SOW: engagement model (T&M is default), role/rate structure, effort estimation approach

5. **Preview the plan structure**
   - Propose tracks or phases based on the practice's activities and patterns
   - Confirm the approach with the user

**ExitPlanMode** once the user approves the plan.

**Then open the report workspace, before any content work begins:** derive the kebab-case slug from the agreed title, create `reports/<report-slug>/`, initialise the prompt history, and record the sources identified during planning. See `reporting-foundation/REPORT-FOUNDATION.md` → Report Workspace and Session Provenance. `--init` arms the interaction hooks, so do it before the next exchange with the user.

---

## Step 3: Output Structure (Project Plan)

```markdown
# <Project Title>

**Prepared for:** <Recipient>
**Date:** <Date>
**Opportunity:** <Customer / engagement context>
**Classification:** <Internal, Confidential, etc.>

---

## Executive Summary

<One paragraph: what the plan covers, who is involved, what it will achieve.>

---

## Objectives and Scope

<What this engagement is for and where its edges are, before the lists.
Why the scope is drawn here rather than wider or narrower, and what that choice
rules out. Two to four sentences. (@rule:report-618)>

### Objectives

<Numbered list of specific, measurable objectives.>

### What the <Project> Will Deliver

<Bulleted list of concrete deliverables or demonstrations.>

### What the <Project> Will Not Cover

<Explicit exclusions — manage expectations upfront.>

---

## Approach

<Overall approach — tracks, phases, or stages. Derived from practice activities and patterns.>

### <Track/Phase 1>

<Purpose, key activities, dependencies.>

### <Track/Phase 2>
...

---

## Roles and Responsibilities

<Per-role sections identifying organisation, responsibility, and key tasks.>

| Role | Organisation | Key Responsibilities |
|------|-------------|---------------------|
| ... | ... | ... |

---

## Activities and Deliverables

<How many phases or tracks there are, what each one is for, and why the work is
cut this way — sequence, dependency, or parallel teams. A reader meeting Phase 1
must already know what follows it. Two to four sentences. (@rule:report-618)>

### <Phase/Track 1>

| Activity | Deliverable | Dependencies |
|----------|-------------|--------------|
| ... | ... | ... |

### <Phase/Track 2>
...

---

## Success Criteria

| Criterion | Evidence | Measurement |
|-----------|----------|-------------|
| ... | ... | ... |

---

## Timeline and Milestones

<Table or timeline showing key milestones, durations, and dependencies.>

---

## Risks and Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| ... | ... | ... | ... |

---

## References
```

---

## SOW Sub-Mode

When the user requests a Statement of Work (via trigger pattern, plan mode decision, or explicit request), generate the SOW as either a standalone document or an appendix to the project plan.

### SOW Output Structure

```markdown
## Statement of Work

<What this statement of work commits to and what it deliberately leaves to a
later phase, before the subsections. Two to four sentences. (@rule:report-618)>

### Engagement Overview

<One paragraph: what is being engaged, who the parties are, what model (T&M).>

### Engagement Model

<Time & Materials: describe the billing model, reporting cadence, change control.>

### Scope of Services

<What services will be delivered. Derived from the project plan's Activities section.>

### Deliverables

<Concrete deliverables with acceptance criteria.>

| Deliverable | Description | Acceptance Criteria |
|-------------|-------------|-------------------|
| ... | ... | ... |

### Roles and Level of Effort

| Role | Organisation | Estimated Days | Rate Basis |
|------|-------------|---------------|------------|
| ... | ... | ... | ... |

**Total estimated effort:** <sum> days

### Assumptions

<All assumptions that the SOW depends on. Infrastructure readiness, access, availability, etc.>

### Out of Scope

<Services, deliverables, or outcomes explicitly excluded from this engagement.>

### Acceptance Criteria

<How the engagement is formally accepted as complete.>
```

---

## Feature: Project Plan Quality

### Scenario: Plan includes explicit scope boundaries (@rule:report-640)
- Given: a project plan is generated
- When: the scope section is written
- Then: both in-scope deliverables and out-of-scope exclusions are explicitly stated
- And: exclusions manage expectations for items the reader might assume are included

### Scenario: Roles identify organisations (@rule:report-641)
- Given: a roles and responsibilities section is written
- When: roles are listed
- Then: each role identifies the responsible organisation or team
- And: roles are not just generic titles but contextualised to this engagement

### Scenario: Success criteria are measurable (@rule:report-642)
- Given: success criteria are defined
- When: each criterion is written
- Then: each has an evidence description (what proves success)
- And: each has a measurement method (how evidence is assessed)

### Scenario: Activities map to deliverables (@rule:report-643)
- Given: activities are listed in the plan
- When: activities and deliverables are presented
- Then: every activity produces or contributes to a named deliverable
- And: no deliverable exists without a supporting activity

### Scenario: SOW effort table includes role and rate basis (@rule:report-644)
- Given: a SOW is generated with a T&M engagement model
- When: the level of effort section is written
- Then: a table lists each role, estimated effort (days or hours), and rate basis
- And: a total estimated effort is provided

### Scenario: SOW assumptions section captures dependencies (@rule:report-645)
- Given: a SOW is generated
- When: the assumptions section is written
- Then: all implicit dependencies are captured (infrastructure, access, availability, prerequisites)
- And: assumptions are specific enough to detect if they prove false

---

## Verification

Lint and the verification gate are mandatory before handover — see REPORT-FOUNDATION → Output (Step 3). Brief the `type-specific` verifier on this skill's row in `verification-foundation/verifiers/report.md`: every estimate traces to a stated assumption, the assumptions are listed rather than implied, and a SOW's scope matches the plan's activities and deliverables without quietly widening or narrowing them.

Where a SOW was produced, lint and verify it too — it is a second deliverable, and the one with commercial consequences.

## Post-Completion

Record the plan, the SOW if one was produced, and any PDF or published Google Doc URL as separate deliverables, then `--finalize` the prompt history (REPORT-FOUNDATION → Session Provenance). The SOW is a second document in the same workspace: `reports/<report-slug>/<report-slug>-sow.md`.

Then perform the Post-Completion Review per SKILL-STANDARD.md §11.
