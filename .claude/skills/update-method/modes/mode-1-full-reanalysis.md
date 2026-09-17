# Mode 1: Full Reanalysis (Phase 1 → 2 → 3)

## Step 2A: Gather Source Materials

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

## Step 2B: Run Phase 1 - Analysis

**IMPORTANT:** Follow the `generate-method` skill Phase 1 process exactly as documented in `.claude/skills/generate-method/SKILL.md` (Step 1: Phase 1 - Analysis section).

**Key reference files (read from generate-method skill):**
- Phase 1 prompt: `prompts/phase-1-analysis.md`
- Domain framework: `references/domain-framework.md`
- Process: See generate-method SKILL.md "Step 1: Phase 1 - Analysis" section

**Update-specific additions:**
- **Update citations:** Search for latest authoritative sources (official docs, recent editions). Enrich all citations with `url` fields — use user-provided URLs, official websites, DOI references (`https://doi.org/10.xxxx/xxxxx`), or publisher pages. Only omit when no stable link exists.
- **Output directory:** `practices/<name>/` for extension practices, `baselines/<name>/` for baselines
- **Output:** `<dir>/01-analysis-report.md` (OVERWRITE existing if present)
- **Baselines only:** Also run Phase 1.5 distillation after Phase 1 (output: `<dir>/01.5-distilled-essentials.md`)
- **Comparison:** Note major differences from existing JSON content, inform user if significant restructuring needed

**Validation:** Apply Phase 1 Validation from generate-method skill

## Step 2C: Run Phase 2 - Mapping

**IMPORTANT:** Follow the `generate-method` skill Phase 2 process exactly as documented in `.claude/skills/generate-method/SKILL.md` (Step 2: Phase 2 - Mapping section).

**Key reference files (read from generate-method skill):**
- Phase 2 prompt: `prompts/phase-2-mapping.md`
- Semantics sub-documents: `references/semantics/composition.md` (aliasing, hierarchies), `references/semantics/practice-elements.md` (elements, Gherkin), `references/semantics/alphas.md` (alpha semantics), `references/semantics/execution-and-patterns.md` (patterns, outcomes)
- Baseline: Use effective baseline from Step 0 (or original baseline if no dependencies were resolved). If the effective baseline has `_aliasContext`, use domain aliases for semantic understanding but canonical names in structural references.
- **Parent practice mode:** The effective context (`_effective-context.json`) contains ALL merged elements with `_contributingPracticeName` provenance. Use `_provenance.tiers` to distinguish baseline elements from practice elements. `contributesTo`/`mapsTo` targets should primarily reference practice-sourced alphas using canonical names. Set `practiceDependencyNames` per the "Determining practiceDependencyNames" rule in generate-method SKILL.md (only practices whose unique non-baseline alphas are actually referenced).
- Process: See generate-method SKILL.md "Step 2: Phase 2 - Mapping" section

**Apply ALL latest guidance from generate-method skill:**
- Primary alpha focus strategy (see "Practice vs Method Handling" section)
- Competency level validation (see "Feature: Alpha Relationship Integrity" @rule:semantic-006)
- Terminology aliases (see "CRITICAL: Terminology Aliasing" section)
- Pattern completeness - FOUR-PASS construction (see "Pattern Completeness Requirements" section)
- Alpha relationships and relatesTo (see "Feature: Alpha Relationship Integrity" section)
- All Critical Mapping Rules (see "Critical JSON Rules" section)

**Subagent Directives (include in every Phase 2 subagent prompt):**
- "Proceed with FULL mapping guide generation immediately. Do NOT present options, ask for confirmation, or offer partial generation."
- "Write ALL sections completely. Never use placeholder text like `[...]`, `[... continuing ...]`, or `[same as above]`. Every section must contain its full content."
- "If the mapping guide will be large, write sections incrementally using the Write tool (for the first batch) then Edit tool (to append subsequent sections). Do not attempt to output the entire guide in a single response."

**Post-Phase-2 Placeholder Check:**
After the subagent completes, verify the mapping guide has no placeholder sections:
```bash
grep -n '\[\.\.\..*\]' <dir>/02-mapping-guide*.md
```
If placeholders are found, resume the agent: "Complete all placeholder sections. Write the full content for each `[...]` block. Use the Edit tool to replace each placeholder with complete content."

**Output:** `practices/<name>/02-mapping-guide.md` (OVERWRITE existing)

**Validation:** Apply Phase 2 Validation from generate-method skill

## Step 2D: Run Phase 3 - JSON Generation

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
- "Only use competency names that exist in the baseline/effective-context. The baseline competencies are: [list them explicitly from the baseline JSON]. Do NOT invent new competency names."
- "If the JSON is large, write it incrementally: start with metadata + alphas, then append workProducts, activities, patterns, personas, personaGroups, citations, outcomes, and assets using the Edit tool."
- "Preserve the existing version from the source JSON — do NOT set version to 1.0.0."

**Post-Phase-3 Completeness Gate (MANDATORY):**

After each Phase 3 subagent completes, verify element completeness against the backup:

```bash
python3 utils/diff-practice-json.py <backup-dir>/<name>.json <name>.json --gate
```

**If gate fails (exit code 1):**
1. Identify which element arrays dropped to 0
2. Launch a targeted fix agent to recover the missing elements from the backup JSON, updating names/references to match the new practice structure
3. Re-run the gate to confirm recovery
4. Do NOT proceed to validation until the gate passes

**Common recovery patterns:**
- **personas/personaGroups dropped to 0**: Copy from backup, update any competency name references to match new baseline competency names
- **citations dropped to 0**: Reconstruct from the mapping guide's Citations section
- **outcomes missing**: Generate from the mapping guide's Outcome Mappings section

**Output:** `practices/<name>/<name>.json` (OVERWRITE existing)

**Comparison Report:** Show what changed vs existing (see "Comparison Report" section in SKILL.md)
