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
- `method-based-report`: 600–799
- `improve-tooling`: 800–999

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
| `naming` | Element names, descriptions, name uniqueness, polarity | Checklist names are noun phrases, positive/additive framing, global name uniqueness |
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

**Compound bash scripts are also prohibited.** Patterns like `TARGET="..." && grep ... && wc ...`, `for f in ...; do ... done`, or variable-assignment-prefixed commands trigger permission prompts because they don't match simple command allow-list patterns (`Bash(grep *)`, `Bash(wc *)`, etc.). Use separate tool calls for each simple command, or write a utility script for batch operations.

### 7.4 Utils Self-Extension Protocol

`utils/README.md` is the canonical registry of all utility scripts — their purpose, capabilities, and usage. Skills MUST follow this protocol when they need programmatic functionality during execution:

**Step 1 — Consult the registry.** Read `utils/README.md` to find an existing script that covers the need. If the script name looks relevant but you're unsure of its full capabilities, run `python3 utils/<script>.py --help` for detailed usage.

**Step 2 — Use, extend, or create.**

- **Existing script covers it:** Use it directly. No further action.
- **Existing script is close but missing a feature:** Extend that script with the new capability. Follow the script's existing patterns (argument style, output format, `_shared.py` usage). Add a test run to confirm the extension works.
- **No existing script covers it:** Create a new utility in `utils/`. Import from `_shared.py` where applicable. Include `--help` documentation via `argparse`. Keep the interface consistent with peer scripts (positional file args, `--fix` for writes, `--dry-run` for previews).

For non-trivial extensions or new scripts, skills may invoke `/improve-tooling` via the Skill tool to delegate the work. The `improve-tooling` skill applies the same protocol with added assessment, verification, and registry discipline. In mid-execution mode it auto-proceeds without user interaction.

**Step 3 — Update the registry.** After extending or creating a script, update `utils/README.md` to reflect the change. Add new scripts to the appropriate section. Update existing entries if capabilities were extended.

**Step 4 — Continue processing.** Do not halt or defer to the user. The skill should seamlessly create/extend the utility and proceed with its workflow.

**Scope guard:** Only create utilities for operations that are mechanical and generalizable across practices/baselines. Scripts must not make semantic decisions — those belong in the LLM layer. One-off data transformations specific to a single source methodology belong in the skill's workflow, not in a reusable script. Practice-specific data (mappings, IDs, URLs) must be externalized into config files, not hardcoded.

**Post-completion:** The Post-Completion Review (Section 11) validates that no ad-hoc inline logic slipped through. If it did, remediate immediately rather than proposing.

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

---

## 11. Post-Completion Review

After completing the skill workflow OR after completing planning, every skill MUST review the session for improvement opportunities and **apply fixes directly** rather than proposing them to the user.

### 11.1 Utils Remediation (Apply Immediately)

1. **Audit for inline scripts**: Scan the session for any `python3 -c`, `bash -c`, heredocs, shell loops, or ad-hoc logic that performed generalizable operations.
2. **Check for new capabilities**: Did the skill need functionality that required manual steps or workarounds?
3. **Remediate**: For each finding, follow the Utils Self-Extension Protocol (§7.4) — extend an existing util or create a new one, update `utils/README.md`, and confirm it works.
4. **Report**: Briefly tell the user what utils were created or extended and why.

### 11.2 Permission Gaps (Propose to User)

Identify Bash commands that triggered permission prompts but could be auto-allowed. Propose additions to `.claude/settings.json` — do not apply unilaterally since permission changes are a user decision.

### 11.3 Skill Improvements (Propose to User)

Identify patterns that indicate skill instruction gaps (repeated manual corrections, ambiguous guidance that led to wrong output). Propose specific SKILL.md edits — do not apply unilaterally since skill changes affect all future runs.
