# Skill Specification Standard

This document defines the design principles and structural requirements for all skills in keleo-pgen-llm. Any new skill or modification to an existing skill must conform to these standards.

---

## 1. Gherkin-Structured Rules

All testable rules in SKILL.md files must be expressed as Gherkin-style scenarios using this format:

```markdown
## Feature: <Feature Name>

### Scenario: <Descriptive rule name> (@rule:<category>-<NNN>)
- Given: <precondition>
- When: <action or trigger>
- Then: <expected outcome>
- And: <additional outcome>
```

### 1.1 Rule ID Scheme

Every scenario carries a `@rule:<category>-<NNN>` tag where:
- **category** — one of the 7 defined categories (see Section 2)
- **NNN** — zero-padded 3-digit sequence number within that category

Rule IDs are globally unique across all skills. Each skill owns a non-overlapping range within each category:
- `generate-method`: 001–199
- `create-baseline-method`: 200–399
- `update-method`: 400–599

### 1.2 Feature Grouping

Related scenarios are grouped under `## Feature:` headings. A feature typically maps to one functional area (e.g., "Alpha Relationship Integrity", "Terminology Aliasing", "Pattern Construction").

### 1.3 Step Language

- **Given** — preconditions, inputs, or context that must be true before the rule applies
- **When** — the action or trigger (typically a phase execution or JSON generation)
- **Then** — the verifiable outcome (measurable, specific, not vague)
- **And/But** — additional Given/When/Then steps (inherit the keyword of the preceding step)

Steps should be concrete and verifiable: "The alpha has exactly one of `contributesTo` or `mapsTo`" rather than "The alpha is properly connected".

---

## 2. Rule Categories

| Category | Scope | Examples |
|---|---|---|
| `structural` | JSON shape, required sections, element counts | Required arrays present, minimum element counts |
| `semantic` | Alpha relationships, cross-references, type correctness | contributesTo/mapsTo semantics, relatesTo direction |
| `naming` | Element names, descriptions, name uniqueness | Checklist names are noun phrases, global name uniqueness |
| `coverage` | Completeness of state/activity/pattern mapping | Every alpha state has supporting activity, pattern backfill |
| `narrative` | Citation linkage, placement, quality, self-containment | Narratives have citationNames, context length 1-3 sentences |
| `process` | Workflow steps, phase ordering, gate checks | Phase 1 before Phase 2, delineation gate decision |
| `aliasing` | Terminology aliases, keywords, domain term handling | One alias per element, alias names not in structural refs |

---

## 3. Triple-Duty Scenarios

Each Gherkin scenario serves three purposes simultaneously:

1. **Agent instruction** — tells the LLM what rule to follow during generation. The scenario's Given/When/Then structure communicates the constraint more precisely than prose.

2. **Eval assertion** — maps to a programmatic check via `assess_categories` in `specs-index.json`. The `extract-specs.py` utility bridges each `@rule:` ID to the corresponding `assess-practice.py` check categories.

3. **Verification contract** — defines what adversarial agents check during ultracode workflows. A verification agent reads the specs-index and confirms each automatable scenario against the output.

**Implication**: Adding a new rule requires one change (a scenario in SKILL.md). It automatically propagates to evals and workflows when `extract-specs.py` regenerates the specs index.

---

## 4. Automatable vs Manual Rules

- **Automatable** — the `Then` steps can be verified programmatically by `assess-practice.py` or `validate-phase-output.py`. The scenario has a non-empty `assess_categories` mapping in `extract-specs.py`.
- **Manual-only** — the `Then` steps require human or LLM judgment (e.g., "The analysis covers all four perspectives with balanced depth"). Marked `"automatable": false` in specs-index.json.

Target: at least 75% of scenarios should be automatable. Manual-only rules should still be structured as Gherkin — they serve as agent instructions and can be checked by adversarial verification agents.

---

## 5. Spec Extraction Pipeline

```
SKILL.md  →  extract-specs.py  →  specs/specs-index.json  →  eval-skill-output.py --specs
```

1. **Author** scenarios inline in SKILL.md (replacing equivalent prose)
2. **Extract** via `python3 utils/extract-specs.py .claude/skills/<skill>/SKILL.md`
3. **Validate** the generated `specs-index.json` for duplicate IDs, unknown categories, and unmapped assessments
4. **Evaluate** via `python3 utils/eval-skill-output.py <dir> --specs specs-index.json`

The specs-index.json is a generated artifact — do not edit it directly. Edit the SKILL.md scenarios and re-extract.

---

## 6. Directory Structure

Each skill directory follows this layout:

```
.claude/skills/<skill-name>/
├── SKILL.md                    # Skill instructions with inline Gherkin scenarios
├── specs/
│   └── specs-index.json        # Generated by extract-specs.py (do not edit)
└── evals/
    ├── evals.json              # Test case definitions
    └── files/                  # Input fixtures for test cases
```

---

## 7. Programmatic Validation

### 7.1 Assessment Checks

Every automatable rule must have a corresponding check function in one of:
- `utils/assess-practice.py` — Phase 3 JSON validation (structural, semantic, naming, coverage, narrative, aliasing rules)
- `utils/validate-phase-output.py` — Phase 1/2 markdown validation (process and coverage rules for intermediate outputs)
- `utils/validate-baseline-json.py` — Baseline-specific validation

### 7.2 Adding New Checks

When adding a new Gherkin scenario with a new `@rule:` ID:

1. Add the scenario to SKILL.md
2. If automatable, add the corresponding check function to the relevant validation utility
3. Add the `@rule:` ID → assess category mapping to `ASSESS_CATEGORY_BRIDGE` in `extract-specs.py`
4. Add the assess category → assertion ID mapping to `ASSESS_CATEGORY_MAP` in `eval-skill-output.py` (if new category)
5. Re-run `extract-specs.py` to regenerate specs-index.json

### 7.3 No Inline Scripts

Validation logic lives in reusable utility scripts (`utils/`), never as inline `python3 -c` or `bash -c` commands in skill instructions. When a new validation need arises, extend an existing utility rather than creating a new one.

---

## 8. Eval Harness Integration

### 8.1 Assertion Severity

- **Error assertions** — failures that indicate broken output (wrong structure, dangling references). These gate the `error_pass_rate` metric.
- **Warning assertions** — quality issues that don't break functionality (naming style, coverage gaps). These affect `pass_rate` but not `error_pass_rate`.

### 8.2 Spec-to-Assertion Mapping

The `--specs` flag on `eval-skill-output.py` augments the standard assertion output with spec IDs:

```json
{
  "id": "rel:alpha-practice",
  "spec_ids": ["semantic-001"],
  "text": "All new alphas have contributesTo",
  "passed": true,
  "severity": "error",
  "evidence": "0 issues"
}
```

This provides traceability from spec scenario → eval assertion → assess-practice check.

---

## 9. Prose-to-Gherkin Migration

When modifying a SKILL.md section that contains prose rules:

1. **Identify** the testable claim in the prose
2. **Write** a Gherkin scenario that captures the same constraint
3. **Replace** the prose with the scenario (do not keep both)
4. **Map** the new `@rule:` ID to an assess category (create new check function if needed)
5. **Verify** by running the eval harness against existing practice outputs

Prose that is purely explanatory (context, examples, rationale) should remain as prose — only convert testable claims that have a clear pass/fail criterion.

---

## 10. Skill Modularity

### 10.1 update-method Inheritance

The `update-method` skill is a wrapper around `generate-method`. All phase processes, quality gates, and validation rules come from `generate-method/SKILL.md`. The `update-method/SKILL.md` adds only update-specific rules (mode selection, backup, content preservation).

When adding rules to `generate-method`, they automatically apply to `update-method` — do not duplicate them.

### 10.2 Baseline vs Extension Rules

Rules in `create-baseline-method` are structurally complementary to `generate-method`:
- Baselines define focuses, competencies, activitySpaces, narrativeTypes
- Extensions reference baseline elements and add activities, workProducts, patterns
- Some rules apply to both (naming uniqueness, narrative quality); these live in `generate-method` and are shared

### 10.3 Cross-Skill Consistency

Rules that appear identically in multiple skills should be maintained in one canonical location and referenced from others. If a rule diverges between skills, it should be split into separate scenarios with distinct IDs.
