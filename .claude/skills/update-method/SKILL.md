---
name: update-method
description: Update existing Practice/Method JSON files to align with latest generate-method guidance and baseline practice
triggerPatterns:
  - "update.*method"
  - "update.*practice"
  - "refresh.*method"
  - "refresh.*practice"
  - "rework.*method"
  - "rework.*practice"
---

# Update Method/Practice Skill

This skill updates existing Practice or Method JSON files to align with the latest generate-method skill guidance, baseline practice updates, and schema changes.

## Modularity Principle

**CRITICAL:** This skill is a wrapper around the `generate-method` skill. All phase processes, quality gates, and validation rules come directly from `.claude/skills/generate-method/SKILL.md`.

**Benefits:**
- ✅ Changes to generate-method automatically apply to update-method
- ✅ Single source of truth for all requirements
- ✅ Consistent quality across generation and updates
- ✅ No duplication of guidance

**Implementation:**
- Read generate-method SKILL.md for complete phase processes
- Reference specific line numbers for quality gates and validations
- Apply same prompts (`prompts/phase-*.md`) and reference files (`references/*.md`)
- Use same validation scripts (`utils/validate-practice-json.py`)

## Workflow Overview

**Three Update Modes (auto-detected):**

1. **Auto-Fix** — All issues are programmatically fixable. Run fix utilities and validate. No phase re-execution needed.
2. **Remap & Regenerate** (Phase 2 → 3) — Use existing content, apply latest mapping guidance, regenerate JSON
3. **Full Reanalysis** (Phase 1 → 2 → 3) — Revisit source materials, update citations, complete rework

## Input Requirements

**User must provide:**
1. **Existing JSON file(s)**: One or more practice/method/baseline JSON files to update
2. **Baseline practice** (for extension practices): Either a baseline JSON or parent practice/method
3. **Source materials** (only if full reanalysis): Original methodology documentation

---

## Execution Workflow

### Step 0: Assess (Single Command)

Run the consolidated assessment utility — this replaces ALL manual inspection steps:

```bash
python3 utils/assess-practice.py <file.json> --schema deps/language.schema.json
```

For extension practices with a baseline:
```bash
python3 utils/assess-practice.py <file.json> --baseline <baseline.json> --schema deps/language.schema.json
```

This single command:
- Detects `kind` (practice / method / practiceBaseline)
- Counts all elements
- Checks structure completeness (focuses, activitySpaces, competencies for baselines; activities, workProducts, patterns for practices)
- Validates PracticeElement name uniqueness
- Checks relationship types
- Validates competency level names against baseline
- Checks narrative citation references (narratives should link to citations via `citationNames`)
- Assesses checklist name/description quality (truncation, echo, duplication)
- Reports asset coverage by element type (NarrativeTypes, Focuses should have icon assets)
- Runs schema validation
- Produces `recommendations.suggestedUpdateMode` ("auto-fix" / "remap" / "full-reanalysis")

Add `--online` to also validate URL-based asset reachability:
```bash
python3 utils/assess-practice.py <file.json> --schema deps/language.schema.json --online
```

**Route based on `kind`:**
- `practiceBaseline` → **Baseline Update Path** (Step 0B)
- `practice` or `method` → **Extension Practice Path** (Step 0C)

### Step 0B: Baseline Update Path

**For baselines (`kind: practiceBaseline`):**

1. **Check assessment output** — read `recommendations.suggestedUpdateMode`:
   - `"auto-fix"` → proceed to **Step 1A: Auto-Fix** (no user interaction needed)
   - `"remap"` or `"full-reanalysis"` → ask user for update mode (Step 1B)

2. **Validation uses baseline-specific scripts:**
   ```bash
   python3 utils/validate-baseline-json.py <baseline.json> deps/language.schema.json
   ```

3. **Output directory:** `baselines/<name>/` (NOT `practices/`)

4. **Baseline-specific phase prompts** (if remap/reanalysis needed):
   - Phase 1: `prompts/phase-1-baseline-analysis.md`
   - Phase 1.5: `prompts/phase-1.5-baseline-distillation.md`
   - Phase 2: `prompts/phase-2-baseline-mapping.md`
   - Phase 3: `prompts/phase-3-baseline-json.md`

### Step 0C: Extension Practice Path

**For practices/methods (`kind: practice` or `method`):**

1. **Auto-discover and resolve all dependencies:**
   ```bash
   python3 utils/discover-dependencies.py --resolve-from <file.json> --transitive
   ```
   This scans `baselines/`, `practices/`, and `deps/` directories, extracts `baselinePracticeName` and `practiceDependencyNames` from the existing JSON, and recursively resolves all baseline dependencies.
   - If any dependencies are `not_found`: ask user for the file paths
   - If any are `ambiguous`: present candidates to user

2. **Confirm resolved dependencies with user:**
   Present all resolved dependencies before proceeding:
   ```
   === Dependency Resolution ===

   Practice: "<name>" (<kind>)
     Path: <file.json>

   Resolved Dependencies:
     1. [baselinePractice] "<baseline-name>"
        Path: <resolved-path>

   All dependencies resolved. Please confirm or correct:
   - "ok" to proceed
   - "1=/correct/path.json" to correct a path
   ```
   **Wait for user confirmation before proceeding.**

3. **Create effective baseline/parent if needed:**
   - If practice has parent (not just baseline) → create effective parent:
     ```bash
     python3 utils/resolve-parent-practice.py <parent.json> -o practices/<name>/_effective-parent.json
     ```
   - If baseline has transitive dependencies:
     ```bash
     python3 utils/resolve-baseline.py <baseline.json> <dep1.json> [<dep2.json> ...] -o practices/<name>/_effective-baseline.json
     ```

4. **Check assessment output** — read `recommendations.suggestedUpdateMode`:
   - `"auto-fix"` → proceed to **Step 1A: Auto-Fix**
   - `"remap"` → proceed to **Step 1B** recommending Mode 2
   - `"full-reanalysis"` → proceed to **Step 1B** recommending Mode 1

### Step 1A: Auto-Fix (No User Interaction)

**When `suggestedUpdateMode: "auto-fix"`** — all issues are programmatically fixable.

1. **Backup first:**
   ```bash
   python3 utils/backup-practice.py <directory>/
   ```

2. **Run common fix utility (baselines and extension practices):**
   ```bash
   python3 utils/fix-common-issues.py <file.json> --fix
   ```
   Add `--normalize-relationships` if relationship type warnings were detected.
   Add `--fix-truncated-names` if checklist truncation issues were detected.
   Add `--fix-schema` for schema violations (tags nesting, persona groups, persona properties, techniqueNarratives).
   Add `--fix-contributesto-arrays` to convert contributesTo arrays to strings.
   Add `--all` to enable all optional fixes.

3. **For extension practices — fix competency levels if needed:**
   ```bash
   python3 utils/fix-competency-levels.py <file.json> <baseline.json> --fix
   ```

4. **Re-assess to confirm fixes:**
   ```bash
   python3 utils/assess-practice.py <file.json> --schema deps/language.schema.json
   ```

5. **Report results** — show what was fixed, confirm 0 errors.

**If re-assessment still shows errors → fall through to Step 1B.**

### Step 1B: Choose Update Mode (User Interaction)

**Only ask user when auto-fix is insufficient.** Present the assessment results and recommended mode:

```
Assessment found issues requiring manual intervention:
[List non-auto-fixable issues from assessment]

Recommended mode: [remap/full-reanalysis] — [modeReason from assessment]

Options:
1. Remap & Regenerate (Phase 2 → 3) — preserves existing analysis
2. Full Reanalysis (Phase 1 → 2 → 3) — revisits source materials

Which mode?
```

**Wait for user response, then proceed to Mode 1 or Mode 2 below.**

---

### Mode 1: Full Reanalysis (Phase 1 → 2 → 3)

**Step 2A: Gather Source Materials**

1. **Extract citation URLs/sources from existing JSON:**
   ```bash
   python3 utils/extract-practice-content.py <file>.json
   ```
   The `citations` array in the output contains author, title, source, and date for each citation.

2. **Ask user for source materials:**
   ```
   I found the following citations in your existing practice:
   [List citations]
   
   Please provide the original source materials:
   - URLs to online documentation
   - PDF files
   - Markdown files
   - Or confirm I should use the existing citations as references
   ```

**Step 2B: Run Phase 1 - Analysis**

**IMPORTANT:** Follow the `generate-method` skill Phase 1 process exactly as documented in `.claude/skills/generate-method/SKILL.md` (Step 1: Phase 1 - Analysis section).

**Key reference files (read from generate-method skill):**
- Phase 1 prompt: `prompts/phase-1-analysis.md`
- Domain framework: `references/domain-framework.md`
- Process: See generate-method SKILL.md "Step 1: Phase 1 - Analysis" (lines 258-340)

**Update-specific additions:**
- **Update citations:** Search for latest authoritative sources (official docs, recent editions)
- **Output directory:** `practices/<name>/` for extension practices, `baselines/<name>/` for baselines
- **Output:** `<dir>/01-analysis-report.md` (OVERWRITE existing if present)
- **Baselines only:** Also run Phase 1.5 distillation after Phase 1 (output: `<dir>/01.5-distilled-essentials.md`)
- **Comparison:** Note major differences from existing JSON content, inform user if significant restructuring needed

**Validation:** Apply Phase 1 Completion Validation from generate-method skill (lines 304-340)

**Step 2C: Run Phase 2 - Mapping**

**IMPORTANT:** Follow the `generate-method` skill Phase 2 process exactly as documented in `.claude/skills/generate-method/SKILL.md` (Step 2: Phase 2 - Mapping section).

**Key reference files (read from generate-method skill):**
- Phase 2 prompt: `prompts/phase-2-mapping.md`
- Semantics guide: `references/semantics.md`
- Baseline: Use effective baseline from Step 0 (or original baseline if no dependencies were resolved). If the effective baseline has `_aliasContext`, use domain aliases for semantic understanding but canonical names in structural references.
- **Parent practice mode:** Also read the effective parent JSON (`_effective-parent.json`). During mapping, `contributesTo` targets should primarily reference parent practice alphas using canonical names. Set `practiceDependencyNames` per the "Determining practiceDependencyNames" rule in generate-method SKILL.md (only parent practices whose unique non-baseline alphas are actually referenced).
- Process: See generate-method SKILL.md "Step 2: Phase 2 - Mapping" (lines 342-1237)

**Apply ALL latest guidance from generate-method skill:**
- Primary alpha focus strategy (lines 2092-2217)
- Competency level validation (lines 733-738)
- Terminology aliases (lines 410-728)
- Pattern completeness - FOUR-PASS construction (lines 878-1133)
- Alpha relationships and relatesTo (lines 737-763)
- All Critical Mapping Rules (lines 729-768)

**Output:** `practices/<name>/02-mapping-guide.md` (OVERWRITE existing)

**Validation:** Apply Phase 2 Completion Validation from generate-method skill (lines 1190-1263)

**Step 2D: Run Phase 3 - JSON Generation**

**IMPORTANT:** Follow the `generate-method` skill Phase 3 process exactly as documented in `.claude/skills/generate-method/SKILL.md` (Step 3: Phase 3 - JSON Generation section).

**Key reference files (read from generate-method skill):**
- Phase 3 prompt: `prompts/phase-3-json.md`
- Schema: `deps/language.schema.json`
- Baseline: Use effective baseline for semantic context; validate against the **original** user-provided baseline (canonical names). **Parent practice mode:** Set `baselinePracticeName` to the value inherited from the parent practice. Set `practiceDependencyNames` per the "Determining practiceDependencyNames" rule in generate-method SKILL.md (only parent practices whose unique non-baseline alphas are actually referenced).
- Process: See generate-method SKILL.md "Step 3: Phase 3 - JSON Generation" (lines 1265-1565)

**Apply ALL latest validations from generate-method skill:**
- Critical JSON Rules (lines 1406-1417)
- Quality Gates (lines 1419-1467)
- Phase 3 Completion Validation (lines 1461-1556)

**Output:** `practices/<name>/<name>.json` (OVERWRITE existing)

**Comparison Report:** Show what changed vs existing (see "Comparison Report" section below)

---

### Mode 2: Remap & Regenerate (Phase 2 → 3)

**Step 2A: Extract Existing Content as Phase 1 Analysis**

**Reverse-engineer JSON to analysis format using the extraction utility:**

```bash
python3 utils/extract-practice-content.py practices/<name>/<name>.json --output practices/<name>/01-analysis-report.md
```

This extracts all practice elements (metadata, alphas with states, work products with LODs, activities with competencies, personas, patterns with views, citations) and generates a Phase 1 analysis report markdown file. For methods, it merges all embedded practices into a single document.

Without `--output`, prints a structured JSON summary to stdout for review:
```bash
python3 utils/extract-practice-content.py practices/<name>/<name>.json
```

**User Feedback:**
- "Extracted existing content as Phase 1 analysis report"
- "Preserved X alphas, Y work products, Z activities"

**Step 2B: Run Phase 2 - Mapping with Latest Guidance**

**IMPORTANT:** Follow the `generate-method` skill Phase 2 process exactly as documented in `.claude/skills/generate-method/SKILL.md` (Step 2: Phase 2 - Mapping section).

**Key reference files (read from generate-method skill):**
- Phase 2 prompt: `prompts/phase-2-mapping.md`
- Semantics guide: `references/semantics.md`
- Baseline: Use effective baseline from Step 0 (or original baseline if no dependencies were resolved). If the effective baseline has `_aliasContext`, use domain aliases for semantic understanding but canonical names in structural references.
- **Parent practice mode:** Also read the effective parent JSON (`_effective-parent.json`). During mapping, `contributesTo` targets should primarily reference parent practice alphas using canonical names. Set `practiceDependencyNames` per the "Determining practiceDependencyNames" rule in generate-method SKILL.md (only parent practices whose unique non-baseline alphas are actually referenced).
- Process: See generate-method SKILL.md "Step 2: Phase 2 - Mapping" (lines 342-1237)

**Apply ALL latest guidance from generate-method skill to extracted content:**
- Primary alpha focus strategy (lines 2092-2217)
- Competency level validation (lines 733-738, 1220-1237)
- Terminology aliases (lines 410-728)
- Pattern completeness - FOUR-PASS construction (lines 878-1133)
- Alpha relationships and relatesTo (lines 737-763)
- All Critical Mapping Rules (lines 729-768)

**Mode 2 specific approach:**
- Start with existing content as base
- Apply latest guidance to refine/fix/enhance
- Preserve valid existing mappings
- Document changes made

**Output:** `practices/<name>/02-mapping-guide.md` (OVERWRITE existing if present)

**Validation:** Apply Phase 2 Completion Validation from generate-method skill (lines 1190-1263)

**User Feedback:**
- "Applied latest mapping guidance to existing content"
- "Updated X competency levels, added Y aliases, completed Z pattern matrices"
- "Identified primary alpha: <Alpha Name> with N related alphas"

**Step 2C: Run Phase 3 - JSON Generation**

**IMPORTANT:** Follow the `generate-method` skill Phase 3 process exactly as documented in `.claude/skills/generate-method/SKILL.md` (Step 3: Phase 3 - JSON Generation section).

**Key reference files (read from generate-method skill):**
- Phase 3 prompt: `prompts/phase-3-json.md`
- Schema: `deps/language.schema.json`
- Baseline: Use effective baseline for semantic context; validate against the **original** user-provided baseline (canonical names). **Parent practice mode:** Set `baselinePracticeName` to the value inherited from the parent practice. Set `practiceDependencyNames` per the "Determining practiceDependencyNames" rule in generate-method SKILL.md (only parent practices whose unique non-baseline alphas are actually referenced).
- Process: See generate-method SKILL.md "Step 3: Phase 3 - JSON Generation" (lines 1265-1565)

**Apply ALL latest validations from generate-method skill:**
- Critical JSON Rules (lines 1406-1417)
- Quality Gates (lines 1419-1467)
- Phase 3 Completion Validation (lines 1461-1556)

**Output:** `practices/<name>/<name>.json` (OVERWRITE existing)

**Comparison Report:**

Generate a structured diff showing changes:

```bash
python3 utils/diff-practice-json.py <old-file>.json <new-file>.json --json
```

This compares scalar fields, element counts across all sections, diffs competency level names, lists aliases, and reports added/removed elements by name. Use `--changes-only` for human-readable output showing only changed sections.

---

## Handling Methods (Multiple Practices)

**For Method JSON files:**

1. **Ask user for scope:**
   ```
   This is a Method with N practices. Which practices would you like to update?
   - All practices (full method update)
   - Specific practices: [list practice names]
   - Method-level only (narratives, citations, patterns)
   ```

2. **For each selected practice:**
   - Run update workflow (Mode 1 or Mode 2) per practice
   - Generate individual practice JSON or mapping sections

3. **Reassemble Method JSON:**
   - Combine updated practices into method structure
   - Update method-level narratives if needed
   - Merge citations (deduplicate)
   - Validate method JSON

---

## Key Changes to Apply

**IMPORTANT:** All requirements come from the `generate-method` skill. Read `.claude/skills/generate-method/SKILL.md` for complete details.

**When updating practices, ensure these latest requirements from generate-method are met:**

### Quality Requirements

All quality requirements from the `generate-method` skill apply. Use the eval harness to validate rather than manual checklists — see Post-Update Validation below.

---

## User Interaction Patterns

### Initial Request

When user provides existing JSON:

"I'll update this practice/method to align with the latest guidance. Let me first read the existing content and identify what needs updating."

**Then:** Read existing JSON and baseline practice

### After Reading Existing Content

Present update mode choice:

"I've analyzed the existing practice. Here's what I found:
- Current structure: [Practice/Method with N practices]
- Primary alpha: [Identified or 'Not clearly defined']
- Potential updates needed: [List key issues]

Please select an update mode:
1. Full Reanalysis (Phase 1 → 2 → 3) - Recommended if source materials available
2. Remap & Regenerate (Phase 2 → 3) - Faster, preserves existing analysis

Which mode would you like to use?"

### During Update

Provide progress updates:

- "Extracting existing content as Phase 1 analysis..."
- "Applying latest mapping guidance: primary alpha focus, competency validation..."
- "Generating updated JSON with latest schema requirements..."
- "Validation passed! Updated practice generated at practices/<name>/<name>.json"

### Completion Report

Provide comparison summary:

"Update complete! Here's what changed:
- Primary alpha: <Alpha Name> (focused practice around this alpha)
- Competency levels: Updated X invalid names to baseline names
- Aliases: Added Y canonical term aliases
- Patterns: Completed Z pattern matrices (N×M entries)
- Schema: Fixed [list fixes]

Preserved content:
- W activities
- X work products
- Y narratives
- Z citations

The updated JSON is schema-compliant and ready for use."

---

## Backup Strategy

**IMPORTANT:** Before overwriting existing files, create backups:

```bash
python3 utils/backup-practice.py <directory>/
```

This creates a `backup-YYYYMMDD-HHMMSS/` directory inside the practice/baseline folder and copies all JSON and markdown files. Output is structured JSON reporting the backup location and files copied.

---

## Post-Update Validation

After any update, run the eval harness to confirm clean state:

**For extension practices:**
```bash
python3 utils/eval-skill-output.py practices/<name>/ \
  --baseline <baseline.json> --schema deps/language.schema.json --summary
```

**For baselines:**
```bash
python3 utils/eval-skill-output.py baselines/<name>/ --schema deps/language.schema.json --summary
```

**Expected result:** `error_pass_rate: 1.0`. Warning assertions are advisory — address where practical.

---

## Common Update Scenarios

### Scenario 1: Baseline Practice Updated

**Symptoms:**
- New alphas in baseline
- Changed competency levels
- Updated relationships

**Update Mode:** Remap & Regenerate (Mode 2)

**Process:**
1. Extract existing content
2. Map to new baseline alphas
3. Update competency level names
4. Add new relationships
5. Regenerate JSON

### Scenario 2: Citations Outdated

**Symptoms:**
- Old methodology versions
- Broken URLs
- Newer editions available

**Update Mode:** Full Reanalysis (Mode 1)

**Process:**
1. Gather updated source materials
2. Research latest authoritative sources
3. Update citations in Phase 1
4. Remap with latest content
5. Regenerate JSON

### Scenario 3: Schema/Guidance Updated

**Symptoms:**
- Missing discriminator property
- Invalid competency level names
- Incomplete pattern matrices
- Missing aliases

**Update Mode:** Remap & Regenerate (Mode 2)

**Process:**
1. Extract existing content
2. Apply latest guidance
3. Fix schema issues
4. Regenerate JSON

### Scenario 4: Practice Needs Restructuring

**Symptoms:**
- No clear primary alpha
- Too broad coverage (8+ unrelated alphas)
- "Everything else" catch-all structure

**Update Mode:** Full Reanalysis (Mode 1)

**Process:**
1. Revisit source materials
2. Identify primary alphas
3. Split into multiple focused practices
4. Create orchestration practice if needed
5. Generate separate practice JSONs

### Scenario 5: Quality Improvements (Checklist Names, Asset Coverage, Citations)

**Symptoms:**
- Checklist names are sentence fragments or truncated at 50 characters
- NarrativeTypes/Focuses lack icon assets
- Narratives don't reference citations via `citationNames`

**Update Mode:** Auto-fix first (citations, truncation stopgap), then Remap if quality issues remain

**Process:**
1. Run assessment — detects quality issues
2. Auto-fix: narrative citations linked, truncated names expanded
3. Re-assess: if echo/duplicate names or asset gaps remain → remap
4. Remap: rewrite checklist names as noun phrases, add Font Awesome icons
5. Re-assess to confirm clean state

### Scenario 6: Citation Name Format (Author-Date → Work Title)

**Symptoms:**
- Assessment flags `citation-name-format` warnings
- Citation names use author-date shorthand (e.g., `"Teece (2007)"`) instead of work titles

**Update Mode:** Auto-fix using existing utilities (no remap needed)

**Process:**
1. Inspect citation metadata to determine correct titles:
   ```bash
   python3 utils/extract-reference-names.py <file.json> --sections citations --citation-details
   ```
2. For each flagged citation, determine the correct work title from the `description` and `source` fields
3. Apply renames using `fix-citation-names.py`:
   ```bash
   python3 utils/fix-citation-names.py <file.json> --rename "Teece (2007)=Dynamic Capabilities and Strategic Management" --rename "Osterwalder (2010)=Business Model Generation"
   ```
   Or for many renames, create a rename map JSON file and use `--map`:
   ```bash
   python3 utils/fix-citation-names.py <file.json> --map <rename-map.json>
   ```
   Rename map format: `{"renames": [{"old": "Author (Year)", "new": "Work Title"}, ...]}`
4. Re-assess to confirm `citation-name-format` warnings are resolved

---

## Remap Phase: Checklist Name Quality

When assessment flags `checklist-quality` issues with names that echo or duplicate their descriptions, the remap phase must rewrite checklist names to proper noun-phrase labels.

**Current (bad) patterns:**
- Sentence fragment: `"Pests and diseases identified accurately using field guides"`
- Truncated at 50 chars: `"Surveillance protocols established for high-risk p"`
- Duplicate of description: name == description verbatim

**Target pattern:**
- Short Title Case noun phrase: `"Pest & Disease Identification Accuracy"`

**Rules for checklist name rewriting:**
1. Names MUST be short noun phrases in Title Case (3-8 words)
2. Names MUST NOT be sentences or verb-led phrases
3. Names MUST NOT duplicate or echo the description
4. Names SHOULD capture WHAT is being checked, not HOW
5. Descriptions remain as full sentences explaining the criterion — do not modify descriptions

**Transformation examples:**

| Original Name | Rewritten Name |
|---|---|
| Taxonomic keys used correctly | Taxonomic Key Accuracy |
| Cultivar authenticity verified | Cultivar Authenticity Verification |
| Light-photosynthesis relationship understood | Light-Photosynthesis Competency |
| Populations quantified using standard metrics | Population Quantification Standards |
| Structural load analysis completed | Structural Load Analysis |
| Inspections scheduled weekly or more frequently du... | Inspection Scheduling Frequency |
| Surveillance protocols established for high-risk p... | High-Risk Pathway Surveillance |

**Process during remap:**
1. Read all checklist items across all alphas and states
2. For each item where name echoes/duplicates description: rewrite name as a Title Case noun phrase
3. Ensure names remain unique within each state's checklist
4. Preserve descriptions unchanged (they provide the detailed criterion)
5. Apply consistently across all alphas — don't fix some and leave others

---

## Remap Phase: Asset Coverage

When assessment flags `asset-coverage` issues, the remap phase must add icon assets for element types with coverage gaps (typically NarrativeTypes and Focuses).

**Font Awesome 6 Free icon selection guidance:**

All icons use these standard fields:
- `fontFamily`: `"Font Awesome 6 Free"`
- `fontWeight`: `"900"` (solid style)
- Asset `type`: `"font-character"`
- Naming convention: `<kebab-case-element-name>-icon`

**AssetReference on elements:**
```json
"assetNames": [{"assetName": "<asset-name>-icon", "type": "icon"}]
```

**Process during remap:**
1. For each NarrativeType without `assetNames`:
   a. Choose an appropriate Font Awesome icon based on the narrative type's name/purpose
   b. Create an Asset definition in the top-level `assets[]` array
   c. Add `assetNames` to the NarrativeType element
2. Repeat for each Focus without `assetNames`
3. Verify all `assetName` references resolve to entries in `assets[]`

**Common icon suggestions (adapt to domain):**

| Element Type / Name | Suggested `fontCharacter` |
|---|---|
| NarrativeType "Hero's Journey" | `fa-route` |
| NarrativeType "STAR" | `fa-star` |
| NarrativeType "Three-Act Structure" | `fa-theater-masks` |
| NarrativeType "StoryBrand" | `fa-bullhorn` |
| NarrativeType "Seasonal Progression" | `fa-calendar-alt` |
| NarrativeType "Citation Standard" | `fa-quote-right` |
| Focus "Value" / business-oriented | `fa-chart-line` |
| Focus "Solution" / technical | `fa-cogs` |
| Focus "Endeavor" / organizational | `fa-people-group` |
| Focus (biological/natural) | `fa-dna` |
| Focus (operations/production) | `fa-industry` |
| Focus (professional/practice) | `fa-user-tie` |

**Asset definition example:**
```json
{
  "name": "heros-journey-narrative-type-icon",
  "type": "font-character",
  "description": "Hero's Journey narrative type icon",
  "fontFamily": "Font Awesome 6 Free",
  "fontCharacter": "fa-route",
  "fontWeight": "900"
}
```

---

## Key Principles

1. **Automate First** — Use `assess-practice.py` and fix utilities before asking the user anything. Only prompt when auto-fix is insufficient.
2. **No Inline Scripts** — All programmatic actions use reusable scripts in `utils/`, never `python3 -c` or `bash -c`.
   - Discover dependency by name: `python3 utils/discover-dependencies.py --resolve "Practice Name"` (find file path by name)
   - Resolve all dependencies: `python3 utils/discover-dependencies.py --resolve-from <file>.json --transitive` (extract and resolve all deps recursively)
   - List available files: `python3 utils/discover-dependencies.py --list` (index all JSON files in baselines/, practices/, deps/)
   - Narrative inspection: `python3 utils/extract-reference-names.py <file>.json --sections narratives` (top-level) or `--narrative-placement` (all elements) or `--narrative-content` (with descriptions and first context)
   - Aliases/citations/types: `python3 utils/extract-reference-names.py <file>.json --sections aliases narrativeTypes citations`
   - Baseline/parent narrative types and elements: `python3 utils/extract-reference-names.py <baseline-or-parent>.json --sections narrativeTypes` (shows type names with their narrative elements)
   - Specific narrative type definitions (full JSON): `python3 utils/extract-reference-names.py <file>.json --sections narrativeTypes --narrative-type-names "STAR" "Technique"` (dumps complete JSON for named types)
   - Find all references to an element: `python3 utils/extract-reference-names.py <file>.json --find-refs "Platform"` (searches alphas, activities, workProducts, patterns, aliases)
   - Narrative contexts by element: `python3 utils/extract-reference-names.py <file>.json --context-element "Common Pitfalls"` (all contexts for a specific narrative element)
   - Long narrative contexts: `python3 utils/extract-reference-names.py <file>.json --long-contexts` (contexts exceeding 3 sentences, truncated)
   - Long contexts with full text: `python3 utils/extract-reference-names.py <file>.json --long-contexts --full-text` (full context text, no truncation)
   - Context element with full text: `python3 utils/extract-reference-names.py <file>.json --context-element "Common Pitfalls" --full-text` (full text, no truncation)
   - Parent practice activity narratives: `python3 utils/extract-reference-names.py <parent>.json --sections activities --activity-details` (shows narrative types and elements per activity)
   - Full assessment: `python3 utils/assess-practice.py <file>.json [--baseline <baseline>.json]`
   - Compare two versions: `python3 utils/diff-practice-json.py old.json new.json` (structural diff: count deltas, added/removed elements)
   - Compare (changes only): `python3 utils/diff-practice-json.py old.json new.json --changes-only`
   - Assessment with parent: `python3 utils/assess-practice.py <file>.json --baseline <baseline>.json --parent <parent>.json` (merges parent elements into baseline for validation)
   - Assessment summary: `python3 utils/assess-practice.py <file>.json --summary` (counts by severity/category, suggested mode)
   - Errors-only assessment: `python3 utils/assess-practice.py <file>.json --errors-only` (filter to only severity=error issues)
   - Top-level structure overview: `python3 utils/extract-reference-names.py <file>.json --structure` (type and count/length for each key)
   - Cross-practice method audit: `python3 utils/audit-method-references.py <method>.json --baseline <baseline>.json` (alpha refs, duplicates, persona consistency)
   - Add missing alpha redeclaration: `python3 utils/fix-alpha-refs.py <practice>.json <baseline>.json --add-redeclaration "Alpha Name" [--fix]`
   - Remap alpha references: `python3 utils/fix-alpha-refs.py <practice>.json <baseline>.json --remap "Old Alpha" "New Alpha" --state-map '{"OldState":"NewState"}' [--fix]`
   - Remove alpha and references: `python3 utils/fix-alpha-refs.py <practice>.json <baseline>.json --remove-alpha "Alpha Name" [--fix]`
   - Assemble method with merged assets: `python3 utils/assemble-method-json.py --name "Name" --baseline-name "Baseline" --practices p1.json p2.json -o method.json --merge-assets`
   - JSON patching — set key: `python3 utils/patch-practice-json.py <target>.json --set-key assets --patch-file assets.json`
   - JSON patching — merge at root: `python3 utils/patch-practice-json.py <target>.json --patch-file patch.json`
   - JSON patching — append to array: `python3 utils/patch-practice-json.py <target>.json --append-key assets --patch-file more-assets.json`
   - JSON patching — named element: `python3 utils/patch-practice-json.py <target>.json --element-path "alphas[Platform]" --patch-file patch.json`
   - JSON patching — field match: `python3 utils/patch-practice-json.py <target>.json --element-path "activities[My Activity].narratives[0].narrativeContexts[narrativeElementName=Common Pitfalls]" --patch-file patch.json`
   - JSON patching — create new: `python3 utils/patch-practice-json.py <new>.json --patch-file skeleton.json --create`
   - JSON patching — delete key: `python3 utils/patch-practice-json.py <target>.json --delete-key kind`
   - JSON patching — deep replace: `python3 utils/patch-practice-json.py <target>.json --replace "old text" "new text"`
   - JSON patching — bulk replace: `python3 utils/patch-practice-json.py <target>.json --replace-file replacements.json` (JSON array of `["old", "new"]` pairs)
   - JSON patching — preview: add `--dry-run` to any patch command
   - These commands work on ANY JSON file — practice, method, baseline, `_effective-baseline.json`, or `_effective-parent.json`
3. **Preserve Content** — Retain all valuable analysis, activities, narratives unless superseded.
4. **Backup First** — Never overwrite without running `utils/backup-practice.py` first.
5. **Validate Rigorously** — Re-run `assess-practice.py` after every fix to confirm clean state.
6. **Report Changes** — Show what was fixed and what remains.
