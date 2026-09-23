---
name: decision-analysis
description: Structured trade-off analysis for architectural, strategic, or technical decisions — balanced options evaluation with contextual verdicts
triggerPatterns:
  - "analyze.*question"
  - "decision.*analysis"
  - "trade.*off"
  - "weigh.*options"
  - "compare.*approaches"
  - "should.*we"
  - "which.*approach"
  - "pros.*cons"
---

# Decision Analysis Skill

Produce a structured trade-off analysis for a posed question, architectural choice, or strategic decision. Each option receives balanced treatment — strengths, weaknesses, and the contexts where it is the right choice. The synthesis provides contextual verdicts ("if X, then A; if Y, then B") rather than a single absolute recommendation, plus a reusable decision framework the reader can apply to their own circumstances.

The practice context provides the domain expertise — its alphas define the evaluation dimensions, its activities and patterns inform feasibility assessment, and its narratives supply domain-specific framing.

The output is a standalone analysis document in plain English. No Keleo terminology.

## Workflow Overview

**Step 0: Plan** → Identify practice context, the question, options, and evaluation dimensions
**Step 1: Load Context** → Resolve practice/method into effective context
**Step 2: Analyze & Select** → Extract domain knowledge, evaluate each option against dimensions
**Step 3: Generate Report** → Write analysis with balanced options and contextual synthesis

---

## Reporting Foundation

This skill builds on the common reporting infrastructure. Load these **on demand**:

| Document | Load at | What it provides |
|---|---|---|
| `.claude/skills/reporting-foundation/REPORT-FOUNDATION.md` | Steps 1–3 | Context resolution, domain extraction, citations, voice/tone, output format, shared rules |
| `.claude/skills/reporting-foundation/narrative-guide.md` | Step 0 | Narrative selection reference |

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
| `gws` CLI | Optional | Extract context from Google Docs/Sheets containing requirements or constraints |
| Playwright MCP | Optional | Load vendor comparison pages, documentation, or technical references |
| Remote bundle repository | Optional | Downloads `.keleo` bundles when the target practice isn't available locally |

---

## Preferred Narrative Structures

| Context | Primary | Secondary |
|---|---|---|
| Technical/architectural decision | Essay Narrative | STAR (for real-world evidence per option) |
| Strategic/business decision | Report Narrative | Essay (for thesis development) |
| Evaluating iterative approaches | Essay Narrative | PDCA (for evaluation cycles) |

---

## Step 0: EnterPlanMode (REQUIRED)

**MANDATORY FIRST STEP.**

In plan mode:

1. **Identify the practice context**
   - Which practice, method, baseline, or `.keleo` bundle provides the domain framework?
   - The practice's alphas become the evaluation dimensions

2. **Frame the question**
   - What is the question or decision to analyse?
   - Why does it matter? What are the consequences of choosing wrong?
   - What constraints shape the decision? (budget, timeline, existing commitments, team capabilities)

3. **Identify options**
   - What are the options under consideration? (minimum 2)
   - If the user hasn't identified options, propose candidates from the practice's domain knowledge
   - Are there options the user hasn't considered that the practice framework suggests?

4. **Define evaluation dimensions**
   - Derive dimensions from the practice's domain concerns (alphas, activities)
   - Are some dimensions more important than others for this specific context?
   - Confirm dimensions and weighting approach with the user

**ExitPlanMode** once the user approves the plan.

---

## Step 3: Output Structure

```markdown
# <Question as Title>

---

## Framing the Question

<Context: why this decision matters, what constraints shape it, what the consequences of choosing wrong are. Set up the reader to understand why a simple answer is insufficient.>

---

## Options Under Consideration

### Option 1: <Name>

#### How It Works
<Mechanism, approach, or architecture — what this option actually entails.>

#### Strengths
- <strength with evidence or reasoning>
- ...

#### Weaknesses
- <weakness with evidence or reasoning>
- ...

#### When to Choose This
<The specific contexts, constraints, or priorities that make this the right choice.>

### Option 2: <Name>

<Same structure as Option 1 — comparable depth and balance.>

---

## Trade-Off Analysis

<Comparison matrix across the evaluation dimensions.>

| Dimension | Option 1 | Option 2 | ... |
|-----------|----------|----------|-----|
| <Dim 1> | <assessment> | <assessment> | |
| ... | | | |

<Weighting rationale: which dimensions matter most for the user's specific context, and why. This is where the practice's domain expertise adds the most value.>

---

## Synthesis

<Not a binary verdict but a contextual recommendation:>

<"If your priority is X, then Option A is the stronger choice because..."
"If your priority is Y, then Option B better serves that goal because..."
"If you need Z and can accept the trade-off on W, then...">>

<When one option is clearly dominant for the user's stated context, say so — contextual does not mean fence-sitting. But explain what would change the recommendation.>

---

## Decision Framework

<A reusable set of criteria the reader can apply to their own situation. This section should be valuable even if the reader's specific constraints differ from those analysed above.>

<Present as a decision tree, weighted scorecard, or structured checklist — whichever fits the decision type.>

---

## References
```

---

## Feature: Decision Analysis Quality

### Scenario: Options receive balanced treatment (@rule:report-660)
- Given: multiple options are analysed
- When: each option section is written
- Then: all options receive comparable depth (word count within 25% of each other)
- And: every option includes both strengths and weaknesses

### Scenario: Trade-off analysis includes structured comparison (@rule:report-661)
- Given: options are evaluated across dimensions
- When: the trade-off analysis section is written
- Then: a comparison matrix or table assesses all options across the same named dimensions
- And: the comparison includes weighting rationale for the user's specific context

### Scenario: Synthesis is contextual, not absolute (@rule:report-662)
- Given: options have been compared
- When: the synthesis section is written
- Then: the verdict is framed as "if X, then A" rather than "always choose A"
- And: the synthesis identifies what would change the recommendation

### Scenario: Question framing establishes stakes (@rule:report-663)
- Given: a question is posed for analysis
- When: the framing section is written
- Then: the section explains why the decision matters
- And: the section identifies constraints that shape the decision space

### Scenario: Decision framework is reusable (@rule:report-664)
- Given: a decision analysis is completed
- When: the decision framework section is written
- Then: the framework is applicable beyond this specific instance
- And: a reader with different constraints can use the framework to reach their own conclusion

---

## Post-Completion

After generating the analysis, perform the Post-Completion Review per SKILL-STANDARD.md §11.
