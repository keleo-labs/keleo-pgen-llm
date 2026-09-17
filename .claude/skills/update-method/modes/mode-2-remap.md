# Mode 2: Remap & Regenerate (Phase 2 → 3)

## Step 2A: Extract Existing Content as Phase 1 Analysis

**Reverse-engineer JSON to analysis format using the extraction utility:**

```bash
python3 utils/extract-practice-content.py practices/<name>/<name>.json --output practices/<name>/01-analysis-report.md
```

This extracts all practice elements (metadata, alphas with states, work products with LODs, activities with competencies, personas, patterns with views, citations) and generates a Phase 1 analysis report markdown file. For methods, it merges all embedded practices into a single document.

Without `--output`, prints a structured JSON summary to stdout for review:
```bash
python3 utils/extract-practice-content.py practices/<name>/<name>.json
```

**For methods — also extract method-level narratives** for later packaging:
```bash
python3 utils/extract-practice-content.py practices/<name>/<name>.json \
  --extract-narratives practices/<name>/_method-narrative.json
```
This saves the top-level `narratives` array to a standalone JSON file compatible with `package-keleo.py --method-narrative-file`.

**User Feedback:**
- "Extracted existing content as Phase 1 analysis report"
- "Preserved X alphas, Y work products, Z activities"

## Step 2A.5: Generate Practice Summaries (Batch Updates)

When updating multiple practices in a method, generate structural summaries for subagent prompt construction:

```bash
# Generate summaries for all practices in the method directory
for f in practices/<method>/*.json; do
  [[ "$(basename "$f")" == _* || "$(basename "$f")" == change-request* ]] && continue
  python3 utils/practice-summary.py "$f" --baseline <baseline>.json --json > "practices/<method>/_summary-$(basename "$f")"
done
```

Each summary contains: metadata, alphas (with relationship types, targets, states, priority distribution), patterns (with view names), patternGroups, outcomes (with forecastWeights), work products, activities, and schema feature coverage flags. Use these summaries in Phase 2/3 subagent prompts instead of ad hoc structural inspection.

**Determine parallelization strategy using dependency tiers:**
```bash
python3 utils/discover-dependencies.py --tiers practices/<method>/<method>.json
```

This classifies practices into Tier 1 (baseline-only, can run in parallel) and Tier 2 (depends on other practices, run after Tier 1).

## Step 2B: Run Phase 2 - Mapping with Latest Guidance

**IMPORTANT:** Follow the `generate-method` skill Phase 2 process exactly as documented in `.claude/skills/generate-method/SKILL.md` (Step 2: Phase 2 - Mapping section).

**Key reference files (read from generate-method skill):**
- Phase 2 prompt: `prompts/phase-2-mapping.md`
- Semantics sub-documents: `references/semantics/composition.md` (aliasing, hierarchies), `references/semantics/practice-elements.md` (elements, Gherkin), `references/semantics/alphas.md` (alpha semantics), `references/semantics/execution-and-patterns.md` (patterns, outcomes)
- Baseline: Use effective baseline from Step 0 (or original baseline if no dependencies were resolved). If the effective baseline has `_aliasContext`, use domain aliases for semantic understanding but canonical names in structural references.
- **Parent practice mode:** The effective context (`_effective-context.json`) contains ALL merged elements with `_contributingPracticeName` provenance. Use `_provenance.tiers` to distinguish baseline elements from practice elements. `contributesTo`/`mapsTo` targets should primarily reference practice-sourced alphas using canonical names. Set `practiceDependencyNames` per the "Determining practiceDependencyNames" rule in generate-method SKILL.md (only practices whose unique non-baseline alphas are actually referenced).
- **Practice summary context:** If practice summaries were generated (Step 2A.5), include the JSON summary in each subagent prompt. This provides alpha names, pattern views, outcomes, dependencies without requiring ad hoc inspection.
- Process: See generate-method SKILL.md "Step 2: Phase 2 - Mapping" section

**Apply ALL latest guidance from generate-method skill to extracted content:**
- Primary alpha focus strategy (see "Practice vs Method Handling" section)
- Competency level validation (see "Feature: Alpha Relationship Integrity" @rule:semantic-006)
- Terminology aliases (see "CRITICAL: Terminology Aliasing" section)
- Pattern completeness - FOUR-PASS construction (see "Pattern Completeness Requirements" section)
- Alpha relationships and relatesTo (see "Feature: Alpha Relationship Integrity" section)
- All Critical Mapping Rules (see "Critical JSON Rules" section)

**Mode 2 specific approach:**
- Start with existing content as base
- Apply latest guidance to refine/fix/enhance
- Preserve valid existing mappings
- Document changes made

**Subagent Directives (include in every Phase 2 subagent prompt):**
- "Proceed with FULL mapping guide generation immediately. Do NOT present options, ask for confirmation, or offer partial generation."
- "Write ALL sections completely. Never use placeholder text like `[...]`, `[... continuing ...]`, or `[same as above]`. Every section must contain its full content."
- "If the mapping guide will be large, write sections incrementally using the Write tool (for the first batch) then Edit tool (to append subsequent sections)."

**Post-Phase-2 Placeholder Check:**
After the subagent completes, verify the mapping guide has no placeholder sections:
```bash
grep -n '\[\.\.\..*\]' <dir>/02-mapping-guide*.md
```
If placeholders are found, resume the agent: "Complete all placeholder sections. Write the full content for each `[...]` block."

**Output:** `practices/<name>/02-mapping-guide.md` (OVERWRITE existing if present)

**Validation:** Apply Phase 2 Validation from generate-method skill

**User Feedback:**
- "Applied latest mapping guidance to existing content"
- "Updated X competency levels, added Y aliases, completed Z pattern matrices"
- "Identified primary alpha: <Alpha Name> with N related alphas"

## Step 2C: Run Phase 3 - JSON Generation

**Size note:** Single-agent generation works reliably for practices of any size (300KB+ tested successfully). The **Parallel Section Strategy** below is available as an optional optimization for very large practices but is not required.

### Standard Phase 3 (all practices)

**IMPORTANT:** Follow the `generate-method` skill Phase 3 process exactly as documented in `.claude/skills/generate-method/SKILL.md` (Step 3: Phase 3 - JSON Generation section).

**Key reference files (read from generate-method skill):**
- Phase 3 prompt: `prompts/phase-3-json.md`
- Schema: `deps/language.schema.json`
- Baseline: Use effective baseline for semantic context; validate against the **original** user-provided baseline (canonical names). **Parent practice mode:** Set `baselinePracticeName` to the value inherited from the parent practice. Set `practiceDependencyNames` per the "Determining practiceDependencyNames" rule in generate-method SKILL.md (only parent practices whose unique non-baseline alphas are actually referenced).
- Process: See generate-method SKILL.md "Step 3: Phase 3 - JSON Generation" section

**Apply ALL latest validations from generate-method skill:**
- Critical JSON Rules (see "Critical JSON Rules" section)
- Phase 3 Validation (see "Phase 3 Validation" section)

**Subagent Directives (include in every Phase 3 subagent prompt):**
- "Generate the COMPLETE practice JSON. You MUST include ALL element arrays: alphas, workProducts, activities, patterns, personas, personaGroups, citations, outcomes, assets, and narratives."
- "Only use competency names that exist in the baseline/effective-context. Do NOT invent new competency names."
- "Preserve the existing version from the source JSON — do NOT set version to 1.0.0."

**Post-Phase-3 Completeness Gate (MANDATORY):**
After each Phase 3 subagent completes, verify element completeness against the backup:
```bash
python3 utils/diff-practice-json.py <backup-dir>/<name>.json <name>.json --gate
```
If the gate fails (exit code 1), recover missing elements from the backup and re-run the gate. See Mode 1's Step 2D for detailed recovery patterns.

**Output:** `practices/<name>/<name>.json` (OVERWRITE existing)

### Parallel Section Strategy (practices >100KB)

For large practices, split Phase 3 into parallel subagents that each generate one JSON section. This reduces per-agent output from ~200KB to ~30-50KB and enables parallel execution.

**Step 1: Create scaffold from existing JSON**

Copy the existing JSON as the base. The subagents will generate replacement sections:
```bash
cp practices/<name>/<name>.json practices/<name>/<name>.json.bak
```

**Step 2: Extract section assignments from mapping guide**

The mapping guide has clear section headers. Assign sections to parallel subagents:

| Subagent | Sections | Key Reference |
|----------|----------|---------------|
| A: Alphas | `alphas` (states, checklists, narratives, relatesTo/contributesTo) | Mapping guide §Alpha Definitions |
| B: Activities | `activities` (contributesTo, worksOn, competencies, narratives) | Mapping guide §Activity Definitions |
| C: Work Products + Patterns | `workProducts` (LODs, contributesTo, contributesToAlphaNames), `patterns` (views, alphaStates), `patternGroups` (entries, narratives) | Mapping guide §Work Products, §Patterns, §Pattern Groups |
| D: Metadata + Secondary | `narratives`, `citations`, `assets`, `practiceElementAliases`, `personas`, `personaGroups`, `keywords`, `tags` | Mapping guide §Metadata |

**Step 3: Launch parallel subagents**

Each subagent receives:
- Its section(s) of the mapping guide
- The schema (`deps/language.schema.json`) — relevant `$defs` only
- The effective context for cross-reference names (alpha names, activity space names, etc.)
- Instruction to output ONLY its assigned section(s) as a standalone JSON object
- **Subagent C (patternGroups):** Must load the baseline's `patternGroups` and adopt existing baseline group names. Novel groups require justification. Use exact baseline group names — they are the merge key for cross-practice composition.

Example subagent output for Subagent A:
```json
{"alphas": [...]}
```

**Step 4: Merge sections into base JSON**

Use `patch-practice-json.py` to merge each section into the base:
```bash
python3 utils/patch-practice-json.py practices/<name>/<name>.json --set-key alphas --patch-file _section-alphas.json
python3 utils/patch-practice-json.py practices/<name>/<name>.json --set-key activities --patch-file _section-activities.json
python3 utils/patch-practice-json.py practices/<name>/<name>.json --set-key workProducts --patch-file _section-workproducts.json
python3 utils/patch-practice-json.py practices/<name>/<name>.json --set-key patterns --patch-file _section-patterns.json
# ... metadata sections
```

**Step 5: Run auto-fix + validation**

After merging, run `fix-common-issues.py --all --fix` and validate as normal. The merged JSON may need element-kind discriminators and pattern completeness fixes.

**Comparison Report:**

Generate a structured diff showing changes:

```bash
python3 utils/diff-practice-json.py <old-file>.json <new-file>.json --json
```

This compares scalar fields, element counts across all sections, diffs competency level names, lists aliases, and reports added/removed elements by name. Use `--changes-only` for human-readable output showing only changed sections.

---

## Quality Fixes

### Checklist Name Quality
When assessment flags `checklist-quality` issues, rewrite names as imperative verb phrases (3-8 words) describing WHAT to do, not what condition exists. Names must not echo descriptions. Apply consistently across all alphas and work product LODs.

When assessment flags `checklist-polarity` issues, rewrite items to be positive and additive — describing an action to perform, not the absence or lack of something. For example, "Metrics absent" → "Define Key Metrics". Use the state/LOD description and narratives to characterize level qualities including limitations.

### Checklist Style Modernization
When assessment flags `checklist-style` issues, rewrite checklist items from criteria-style (past-participle conditions) to action-oriented (imperative verb phrases):

**Name transformation**: Convert past-participle names to imperative verb phrases.
- "Architecture documented" → "Document the Architecture"
- "Security review completed" → "Complete Security Review"
- "Cost model validated" → "Validate Cost Model"
- "SLOs defined and monitored" → "Define and Monitor SLOs"

**Description enrichment**: After transforming names, verify descriptions carry information beyond them. If a description merely restates the name as a sentence, rewrite to add rationale, scope, method, or context. Do NOT mechanically transform old descriptions into sentences that echo the new name.
- Anti-pattern: name "Document the Architecture" + description "Document the architecture approach." (echo — adds nothing)
- Correct: name "Document the Architecture" + description "Create a reference architecture capturing technology stack decisions, rationale, and alternatives considered."

**Test enrichment (not test promotion)**: Do NOT mechanically create tests from descriptions. Only create or retain a test when you can populate `given` with meaningful preconditions, `when` with a meaningful trigger, and `then` with independently observable evidence beyond the description. A test with empty `given`/`when` and `then` that restates the description in past tense is a skeleton test — it adds no verification value.

**Skeleton test cleanup**: When assessment flags `checklist-skeleton-test` or `checklist-echo` issues, or when encountering tests where `test.description` is literally "Definition of done.", `given` and `when` are both empty, and `then` echoes the description — either enrich the test with real preconditions, triggers, and independently verifiable evidence, or remove the test entirely. Removal is preferred when the checklist item is straightforward enough that name + description are self-sufficient.

Apply consistently across all alphas and work product LODs.

### Asset Coverage
When assessment flags `asset-coverage` gaps, add Font Awesome 6 Free icons (`fontWeight: "900"`, naming: `<kebab-case>-icon`). Every NarrativeType and Focus needs an icon. See generate-method SKILL.md Assets section for icon suggestions and JSON structure.

### Outcomes
When assessment flags `outcomes` warnings (missing outcomes) or `outcome-refs` errors (broken cross-references):
- Add 1-3 outcomes with `measureDescription` (always required)
- Each outcome should have `metricContributions` or `objectiveContributions` (never neither)
- Bias toward at least one objective-based outcome tied to the main lifecycle pattern (broadest alpha coverage)
- Validate `alphaName`/`stateName` references in metricContributions resolve to defined alphas/states
- Optional `workProductName` on a metricContribution must match a WorkProduct.name; declare that `metricName` on the work product's `expectedMetrics`
- Every objectiveContribution MUST include `patternName` (scopes view references to that pattern)
- Validate `recognizedAtPatternViewName` in objectiveContributions resolves to a view within the named pattern
- See generate-method SKILL.md @rule:outcome-001 through @rule:outcome-004
