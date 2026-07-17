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

**Two Update Modes:**

1. **Full Reanalysis** (Phase 1 → 2 → 3): Revisit source materials, update citations, complete rework
2. **Remap & Regenerate** (Phase 2 → 3): Use existing content, apply latest mapping guidance, regenerate JSON

## Critical Process: Ask User for Update Mode

**MANDATORY FIRST STEP:** After reading existing JSON, ask the user which update mode to use:

**Option 1: Full Reanalysis**
- Revisit original source materials
- Update citations to latest authoritative sources
- Complete Phase 1 analysis with latest domain framework
- Apply latest Phase 2 mapping guidance (primary alpha focus, competency levels, etc.)
- Generate fresh JSON with all fixes

**Option 2: Remap & Regenerate**
- Extract existing content as Phase 1 analysis
- Apply latest Phase 2 mapping guidance without revisiting sources
- Generate updated JSON with latest schema/baseline

**When to recommend each:**
- **Full Reanalysis**: Baseline practice changed significantly, citations are outdated, or major structural changes needed
- **Remap & Regenerate**: Minor fixes (competency levels, aliases, pattern completeness), schema updates, baseline refinements

---

## Input Requirements

**User must provide:**
1. **Existing JSON file(s)**: One or more practice/method JSON files to update
2. **Baseline practice OR parent practice/method**: Either a baseline practice JSON (e.g., `deps/platform-adoption-kernel.json`) or an existing practice/method to extend (see "Parent Practice Mode" below)
3. **Update mode**: Full reanalysis OR remap & regenerate
4. **Source materials** (if full reanalysis): Original methodology documentation

---

## Execution Workflow

### Step 0: Read Existing Content

1. **Read existing JSON file(s) and analyze structure:**
   ```bash
   python3 utils/inspect-practice-json.py practices/<name>/<name>.json
   ```

2. **Analyze current structure:**
   - Is this a Practice or Method?
   - What alphas are covered?
   - What is the primary alpha? (may not be explicit in older versions)
   - How many practices (if Method)?
   - What citations exist?

3. **Read current baseline or parent practice:**
   - Validate file exists and is valid JSON
   - **Detect input type:**
     ```bash
     python3 utils/resolve-parent-practice.py <file.json> --check-only
     ```
     - If `inputKind: "practiceBaseline"` → Standard baseline flow (proceed to step 4)
     - If `inputKind: "practice"` or `"method"` → **Parent practice mode** (proceed to step 3.5)

3.5. **Parent Practice Resolution (parent practice mode only):**
   - Extract `baselinePracticeName` from the check-only output
   - Locate the actual baseline file (ask user if needed)
   - Create effective parent:
     ```bash
     python3 utils/resolve-parent-practice.py <parent.json> -o practices/<name>/_effective-parent.json
     ```
   - Record: `parentPracticePath`, `effectiveParentPath`, `parentPracticeNames`, `actualBaselinePath`
   - Report detected mode and parent practice details to user
   - Continue to step 4 using `actualBaselinePath` as the baseline

4. **Check baseline for dependencies and resolve:**
   ```bash
   python3 utils/resolve-baseline.py <baseline-practice.json> --check-only -o /dev/null
   ```
   **Note:** In parent practice mode, operate on `actualBaselinePath` (the baseline referenced by the parent practice), not the user-provided file.
   
   If `hasDependencies: true`: 
   - Report dependency names to user and ask for file paths
   - Recursively check transitive dependencies
   - Create effective baseline:
     ```bash
     python3 utils/resolve-baseline.py \
       <baseline-practice.json> \
       <dependency-1.json> [<dependency-2.json> ...] \
       -o practices/<name>/_effective-baseline.json
     ```
   - Use `_effective-baseline.json` for all analysis/mapping phases
   - Use the **original** baseline for validation
   
   If `hasDependencies: false`: use the baseline file directly.

5. **Identify what has changed since original generation:**
   - New baseline alphas or relationships?
   - New competency levels?
   - Schema property changes?
   - New semantic requirements (primary alpha focus, aliases, pattern completeness)?
   - Baseline dependencies: [list if `baselinePracticeNames` present, "none" otherwise]

### Step 1: Ask User for Update Mode

**Present options to user:**

```
I've read the existing practice/method JSON. Please select an update mode:

**Option 1: Full Reanalysis**
- I'll revisit the original source materials
- Update citations to latest authoritative sources
- Complete fresh Phase 1 analysis
- Apply latest mapping guidance (primary alpha focus, competency validation, etc.)
- Generate completely refreshed JSON

**Recommended when:**
- Baseline practice has changed significantly
- Citations are outdated
- Major structural changes needed (e.g., practice splitting, primary alpha refocus)
- Source materials available

**Option 2: Remap & Regenerate**
- I'll extract existing content as Phase 1 analysis
- Apply latest Phase 2 mapping guidance
- Regenerate JSON with latest schema/baseline requirements

**Recommended when:**
- Minor fixes needed (competency levels, aliases, pattern matrices)
- Schema or baseline refinements
- Source materials not available
- Preserving existing analysis is priority

Which update mode would you like to use?
```

**Wait for user response before proceeding.**

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
- **Output:** `practices/<name>/01-analysis-report.md` (OVERWRITE existing if present)
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
python3 utils/compare-practice-json.py <old-file>.json <new-file>.json
```

This compares element counts (alphas, workProducts, activities, patterns, citations, personas, assets), diffs competency level names, lists aliases in the new file, and reports added/removed elements by name. Output is structured JSON.

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

### Reference: generate-method Quality Gates

**Apply ALL quality gates and validation checks from generate-method skill:**

- **Primary Alpha Focus** (generate-method lines 2092-2217, CLAUDE.md lines 150-192)
  - See "Practice vs Method Handling" section in generate-method skill
  
- **Competency Level Validation** (generate-method lines 733-738, 1220-1237, 1461-1556)
  - See "Critical Mapping Rules" in generate-method skill
  
- **Terminology Aliases** (generate-method lines 410-728)
  - See "Terminology Aliasing" section in generate-method skill
  
- **Pattern Completeness** (generate-method lines 878-1133)
  - See "Pattern Completeness Requirements" section in generate-method skill
  
- **Alpha Relationships** (generate-method lines 737-763)
  - See "Semantic Relationships" in Critical Mapping Rules
  
- **Discriminator Property** (generate-method lines 1406, 1421-1424)
  - See "Critical JSON Rules" in generate-method skill
  
- **PracticeElement Name Uniqueness** (generate-method lines 1430-1440, 1502-1506)
  - See "Quality Gates" in generate-method skill
  
- **Schema Compliance** (generate-method lines 1419-1467)
  - See "Quality Gates" and validation checklist in generate-method skill

**Complete Checklist:** Use generate-method Phase 2 Quality Gates (lines 1135-1183) and Phase 3 Quality Gates (lines 1419-1467)

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
python3 utils/backup-practice.py practices/<name>/
```

This creates a `backup-YYYYMMDD-HHMMSS/` directory inside the practice folder and copies all JSON and markdown files. Output is structured JSON reporting the backup location and files copied.

**Tell user about backup location** before starting update process.

---

## Validation Checklist

After update, verify:

- [ ] Discriminator property present (`kind`)
- [ ] Primary alpha identified and documented
- [ ] Competency level names match baseline
- [ ] Aliases array populated (3-8 entries)
- [ ] Pattern matrices complete (N×M)
- [ ] PracticeElement names globally unique
- [ ] Schema validation: 0 errors
- [ ] Baseline validation: 0 errors
- [ ] Internal integrity: 0 errors
- [ ] Comparison report generated

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

---

## Key Principles

1. **Preserve Content** - Retain all valuable analysis, activities, narratives unless superseded
2. **Apply Latest Guidance** - Use current generate-method best practices
3. **Validate Rigorously** - Ensure schema, baseline, and internal integrity
4. **Report Changes** - Show user what was updated and why
5. **Backup First** - Never overwrite without backup
6. **User Choice** - Let user decide between full reanalysis and remap/regenerate
