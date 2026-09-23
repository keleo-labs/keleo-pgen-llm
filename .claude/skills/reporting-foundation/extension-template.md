# Reporting Skill Extension Guide

How to create a new specialised reporting skill that builds on the shared reporting foundation.

---

## Checklist

1. **Choose a name** — kebab-case, describes the report type (e.g., `risk-assessment`, `migration-plan`)
2. **Allocate a rule ID range** — 20-number block within 600–799 (see current allocation below). If 600–799 is full, use 1000+
3. **Create the directory** — `.claude/skills/<name>/` with `SKILL.md`, `contract.feature`, and `evals/` directory
4. **Write the SKILL.md** — follow the template below
5. **Register** — add the skill to `CLAUDE.md` directory structure and skill descriptions
6. **Add trigger patterns** — in the SKILL.md frontmatter

### Current Rule ID Allocation (600–799)

| Owner | Range |
|-------|-------|
| Shared foundation (REPORT-FOUNDATION.md) | 600–619 |
| reference-architecture | 620–639 |
| project-plan | 640–659 |
| decision-analysis | 660–679 |
| document-review | 680–699 |
| method-based-report (type-specific) | 700–719 |
| Reserved | 720–799 |

---

## SKILL.md Template

```markdown
---
name: <skill-name>
description: <one-line description — what the report is and who it's for>
triggerPatterns:
  - "<pattern-1>"
  - "<pattern-2>"
---

# <Skill Name> Skill

<2–3 sentence purpose statement. What kind of report this produces, when to use it, and what makes it distinct from the general-purpose method-based-report.>

## Workflow Overview

**Step 0: Plan** → <type-specific planning focus>
**Step 1: Load Context** → Resolve practice/method into effective context
**Step 2: Analyze & Select** → Extract domain knowledge, select narrative structures
**Step 3: Generate Report** → Write report using type-specific structure

---

## Reporting Foundation

This skill builds on the common reporting infrastructure. Load these **on demand**:

| Document | Load at | What it provides |
|---|---|---|
| `.claude/skills/reporting-foundation/REPORT-FOUNDATION.md` | Steps 1–3 | Context resolution, domain extraction, citations, voice/tone, output format, shared rules |
| `.claude/skills/reporting-foundation/narrative-guide.md` | Step 0 and Step 2 | Narrative selection and element-to-heading mappings |

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

<Same table as method-based-report — adjust if this type has additional dependencies.>

---

## Preferred Narrative Structures

<Which primary and secondary narrative types suit this report type. Reference narrative-guide.md for the full mapping table.>

| Context | Primary | Secondary |
|---|---|---|
| <default case> | <type> | <type> |
| <variant case> | <type> | <type> |

---

## Step 0: EnterPlanMode (REQUIRED)

<Type-specific planning questions beyond the common ones. What additional input does this report type need?>

In plan mode:

1. **Identify the practice context** — same as base skill
2. **Clarify subject and purpose** — <type-specific questions>
3. **<Type-specific input>** — <what this type uniquely needs>
4. **Preview the narrative strategy** — using the preferred structures above

**ExitPlanMode** once the user approves the plan.

---

## Steps 1–3: Execution

Steps 1–2 follow `reporting-foundation/REPORT-FOUNDATION.md`.

Step 3 output uses this structure:

```markdown
# <Title>

## <Section 1>
...
## <Section N>
## References
```

<Describe each section's purpose and what practice knowledge feeds into it.>

---

## Type-Specific Content Rules

<Any content generation rules unique to this type — tables that must be present, specific section requirements, formatting conventions.>

---

## Feature: <Type Name> Report Quality

### Scenario: <Rule description> (@rule:report-NNN)
- Given: <precondition>
- When: <action>
- Then: <outcome>

<Add 3–6 Gherkin rules specific to this report type.>

---

## Post-Completion

After generating the report, perform the Post-Completion Review per SKILL-STANDARD.md §11.
```

---

## Design Decisions for New Types

When designing a new reporting skill, decide:

1. **What makes this distinct from `/method-based-report`?** If the answer is just "different narrative type selection", it probably doesn't need a separate skill — the base skill's planning step handles that. A separate skill is warranted when the report type has a distinct output structure, unique input requirements, or type-specific content rules.

2. **What input does the user provide beyond practice context?** Each specialised skill exists because it needs something the base skill doesn't ask for (a document to review, technology constraints, a question to analyse, project objectives).

3. **What output structure is mandatory?** Specialised skills define a fixed output skeleton. This is their main value — users know what they'll get. The base skill's output structure is flexible.

4. **Which Gherkin rules encode type-specific quality?** These rules distinguish the specialised skill from the base. They should be verifiable and specific (not just "report is good").
