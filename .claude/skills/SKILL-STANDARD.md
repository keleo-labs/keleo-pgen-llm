# Skill Specification Standard

**Version:** 1.2.0

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
- `method-based-report` family: 600–799 (sub-allocated in 20-number blocks):
  - Shared foundation (`reporting-foundation/REPORT-FOUNDATION.md`): 600–619
  - `reference-architecture`: 620–639
  - `project-plan`: 640–659
  - `decision-analysis`: 660–679
  - `document-review`: 680–699
  - `method-based-report` (type-specific): 700–719
  - Reserved for future report types: 720–799
- `improve-tooling`: 800–949
- Cross-cutting standards defined in this document: 950–999

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
| `fidelity` | Output traces to the sources provided and cited | Structural claims traceable to a source span, citation supports its claim, no invention between phases |

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

Target: at least 75% of scenarios should be automatable. Manual-only rules should still be structured as Gherkin — they serve as agent instructions and are the contract the verification agents carry.

`fidelity` rules are manual-only by nature: no script can tell you whether a claim traces to its source. Exclude them from the 75% denominator rather than weakening them to make the ratio work.

To list the manual-only rules a verification agent must check:

```bash
python3 utils/extract-specs.py --list-manual <skill>/specs/specs-index.json [--category fidelity]
```

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

### 10.4 Verification Foundation

`.claude/skills/verification-foundation/` holds the verification protocol and agent briefs shared by the three generation skills. It is a foundation, not a skill — the same arrangement as `reporting-foundation`, `deck-foundation` and `diagram-foundation`.

A generation skill gates each phase on it: mechanical validation, then the verification gate, then the user review gate. Skills reference the briefs; they do not restate them. A brief that is paraphrased into a SKILL.md loses the severity calibration it was written with.

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

## 12. Remote Bundle Resolution

When a skill cannot resolve a dependency locally (via `discover-dependencies.py`), use the `studio-client.py` utility to download from the keleo-studio-gas remote library.

### 12.1 Download a Missing Bundle

```bash
python3 utils/studio-client.py --pull "<Document Name>"
```

This handles authentication, download URL resolution, and bundle verification. The downloaded `.keleo` is saved to `bundles/` and will be found by subsequent `discover-dependencies.py` calls.

### 12.2 Check for Newer Versions

```bash
python3 utils/studio-client.py --check "<Document Name>"
```

Compares local vs remote versions. When remote is newer, offer the user a choice: keep local, pull remote, or diff.

### 12.3 Authentication

Credentials (`keleoStudioGasUrl`, `keleoStudioGasToken`) are stored in `.claude/user-config.json`. If not configured or if the token has expired:

```bash
python3 utils/studio-client.py --configure
```

Tokens are Google OAuth bearer tokens that expire after ~1 hour. On 401 errors, `studio-client.py` reports the expiry and guides the user to refresh.

### 12.4 Integrated Resolution

`discover-dependencies.py` supports a `--remote` flag that checks the cached remote index when local resolution fails:

```bash
python3 utils/discover-dependencies.py --resolve "<Name>" --remote
python3 utils/discover-dependencies.py --resolve-from <file.json> --transitive --remote --auto-pull
```

With `--auto-pull`, remote-only dependencies are downloaded automatically before re-resolving.

---

## 13. Content Defect Reporting

### 13.1 Scope

This section applies to every skill that **consumes** practice, method, or baseline
content it is not itself authoring in this run — the reporting family reading an
effective context, `generate-method` and `create-baseline-method` reading a baseline and
its dependency practices, `update-method` reading the document it revises, and
`plan-from-feedback` reading documents named by register rows.

### 13.2 The Rule: Accommodate, Then File

When consumed content turns out to be defective, do both of these, in this order:

1. **Accommodate the challenge.** Work around the defect and deliver the artifact. Pick
   the next-best element, describe the progression you can evidence, say less where the
   practice says less. Never halt the workflow over a defect in content you did not
   author, and never ask the user whether to record it.
2. **File it.** Every defect you worked around goes into the issue register as a Status
   `New` row, so `/plan-from-feedback` can triage it against the document that owns it.

A defect you accommodated and did not file is lost. The register is the only durable
record — a note in the conversation is not one.

### 13.3 What Counts as a Content Defect

| Observation | File it? |
|---|---|
| Content is wrong, self-contradictory, or contradicts the source methodology it cites | Yes — `Issue` |
| Content is absent, thin, or missing where the document's own structure implies it exists | Yes — `Enhancement` |
| An element is modelled in a way you had to reason around and cannot justify from the document | Yes — `Question` |
| Keleo Studio renders, navigates, or behaves oddly around the content | Yes — record it; studio-side triage omits what pgen-llm cannot act on |
| The **user's source material** is thin or contradictory | No — that is an input gap, not a document defect. Raise it with the user. |
| Output **this run** produced is wrong | No — fix it. A defect you can correct before handover is not register material. |
| A skill instruction or utility script is at fault | No — that is `/improve-tooling` (§7.4, §11.3) |
| A defect you fixed in this same run, in that same document | No — `update-method` and `plan-from-feedback` resolve in place; a row for an already-closed fix wastes a triager's time |

A defect in a **dependency or baseline** is filed against *that* document, not against the
one you are authoring. Resolve its canonical `name`, `version`, and `kind` from the
document itself — never from the consuming document's reference to it.

### 13.4 Collection

Record each defect **at the point of discovery**, not from memory at the end of the run:

```bash
python3 utils/issue-register.py --add-draft /tmp/keleo-defects-<slug>-<timestamp>.json \
  --type Issue --summary "<title under 120 chars>" \
  --description "<what was observed, where, and what was expected instead>" \
  --document "<Canonical Document Name>" --document-version <version> --document-kind <kind> \
  --element "<Exact Element Name>" --element-type <type>
```

The utility creates the file on first call, validates each draft as it is added, and
declines to add the same summary against the same document twice — so one defect seen in
three sections yields one row.

Write the description for a triager who was not in this session: what the document says,
what the practice implied it should say, and what you did instead. Do not pre-judge the
resolution; triage owns that.

### 13.5 Filing

Once, before handover, invoke `report-issue` in mid-execution mode via the Skill tool:

```
Skill(report-issue) with:
  Mode: mid-execution
  Drafts: /tmp/keleo-defects-<slug>-<timestamp>.json
  Context: <which skill and phase found them>
```

It enriches any missing document and element metadata, validates, duplicate-checks, and
appends — without a confirmation round, because the run itself is the authorisation.
Report the row numbers it returns in your own completion summary, alongside anything it
skipped as a duplicate.

### 13.6 Shared Gherkin Rules

These rules are cross-cutting; they are not extracted into any skill's `specs-index.json`
(the same arrangement as the shared rules in `reporting-foundation/REPORT-FOUNDATION.md`).

#### Scenario: Consumed content defects are accommodated, not escalated (@rule:process-950)
- Given: A skill is consuming practice, method, or baseline content it did not author in this run
- When: Part of that content is wrong, missing, or self-contradictory
- Then: The skill works around the defect and completes its deliverable
- And: The workflow is not halted and the user is not asked whether to record it

#### Scenario: Every accommodated defect reaches the register (@rule:process-951)
- Given: A defect in consumed content was worked around during the run
- When: The skill reaches handover
- Then: A register row exists for that defect with Status "New"
- And: The row names the document that owns the defect, not the document being authored

#### Scenario: Defects are drafted at the point of discovery (@rule:process-952)
- Given: A defect is observed mid-run
- When: It is recorded
- Then: `issue-register.py --add-draft` appends it to the run's drafts file immediately
- And: The same defect observed again in the same run does not produce a second row

#### Scenario: Defects fixed in-run are not filed (@rule:process-953)
- Given: A skill corrects a defect in the document it is revising, within the same run
- When: The run reaches handover
- Then: No register row is filed for that defect

#### Scenario: Non-content problems are routed elsewhere (@rule:process-954)
- Given: The problem lies in the user's source material, this run's own output, or a skill or utility
- When: The defect gate is applied
- Then: No register row is filed
- And: The problem is raised with the user, fixed in place, or routed to `/improve-tooling` respectively

#### Scenario: Filed rows are surfaced at handover (@rule:process-955)
- Given: Rows were filed during the run
- When: The skill reports completion
- Then: The filed row numbers are listed, with the document and element each concerns
- And: Any draft skipped as a duplicate of an open row is named with the row that covers it
