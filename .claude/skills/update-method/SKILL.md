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
  - "add.*reference"
  - "find.*reference"
  - "update.*reference"
---

# Update Method/Practice Skill

This skill updates existing Practice or Method JSON files to align with the latest generate-method skill guidance, baseline practice updates, and schema changes.

## Supporting Standards

`.claude/skills/SKILL-STANDARD.md` defines cross-cutting standards for all skills. **Do not read it upfront** — read the relevant section when a trigger fires:

| If you find yourself... | Stop and read |
|---|---|
| Writing `python3 -c`, `bash -c`, heredocs, or any ad-hoc inline script | §7 — these are prohibited; use reusable utils instead |
| Creating or extending a utility script | §7.4 — follow the Utils Self-Extension Protocol |
| Needing functionality that no existing util covers | §7.4 — create/extend, don't work around it |
| Finishing the workflow without auditing the session | §11 — Post-Completion Review is mandatory |
| Writing prose rules that have a clear pass/fail criterion | §9 — convert to Gherkin scenarios instead |
| Adding or modifying Gherkin scenarios in any SKILL.md | §1–6 — rule structure, categories, and triple-duty |
| Adding a new validation check to assess/validate scripts | §7.2 — follow the Adding New Checks protocol |

**How to read:** `Read .claude/skills/SKILL-STANDARD.md` — then navigate to the relevant `## N.` heading.

---

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

**Four Update Modes (auto-detected or user-requested):**

1. **Auto-Fix** — All issues are programmatically fixable. Run fix utilities and validate. No phase re-execution needed.
2. **Remap & Regenerate** (Phase 2 → 3) — Use existing content, apply latest mapping guidance, regenerate JSON
3. **Full Reanalysis** (Phase 1 → 2 → 3) — Revisit source materials, update citations, complete rework
4. **Add/Update References** — Discover and map reference content without full remap. Lightweight mode that adds curated external content (templates, case studies, reference architectures) to the `references` array.

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

For practices with cross-practice dependencies (alphas that `contributesTo`/`mapsTo` targets in other practices):
```bash
python3 utils/assess-practice.py <file.json> --baseline <baseline.json> --schema deps/language.schema.json \
  --parent <dependency-practice-1.json> --parent <dependency-practice-2.json>
```
The `--parent` flag merges each dependency's elements (alphas, work products, personas, personaGroups, activities, citations, narrativeTypes, competencies, activitySpaces) into the baseline for cross-reference validation, eliminating false positive errors for cross-practice references. Use one `--parent` per `practiceDependencyNames` entry.

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
- Validates reference anchors (alphaName/stateName resolution, link presence)
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

3. **Create effective context if needed:**
   - Collect all context sources (baseline, parent practices/methods, .keleo bundles):
     ```bash
     python3 utils/resolve-context.py <baseline.json> [<parent.json>] [<bundle.keleo>] --transitive -o practices/<name>/_effective-context.json
     ```
   - The effective context merges all sources with `_contributingPracticeName` provenance annotations

4. **Check assessment output** — read `recommendations.suggestedUpdateMode`:
   - `"auto-fix"` → proceed to **Step 1A: Auto-Fix**
   - `"remap"` → proceed to **Step 1B** recommending Mode 2
   - `"full-reanalysis"` → proceed to **Step 1B** recommending Mode 1

### Version Incrementing

When updating an existing document, increment its `version` based on the update mode:

| Update Mode | Version Bump | Rationale |
|---|---|---|
| **Auto-Fix** | `patch` (e.g. 1.0.0 → 1.0.1) | Structural fixes, no content changes |
| **Remap & Regenerate** | `minor` (e.g. 1.0.0 → 1.1.0) | Remapped content, new guidance applied |
| **Full Reanalysis** | `minor` (e.g. 1.0.0 → 1.1.0) | Content reworked from source materials |
| **Add/Update References** | `patch` (e.g. 1.0.0 → 1.0.1) | New reference content, no structural changes |

**Single command handles all versioning steps** (increment, schemaVersion, dependencyVersions, updatedAt):

```bash
# Auto-Fix → patch bump
python3 utils/apply-versioning.py <file>.json --bump patch --fix

# Remap or Full Reanalysis → minor bump
python3 utils/apply-versioning.py <file>.json --bump minor --fix
```

Dependency versions are auto-resolved from all project files in deps/, baselines/, practices/.

**IMPORTANT — Phase 3 subagents must NOT set version:** The generate-method skill tells Phase 3 to set `version: "1.0.0"` for new documents. When updating, this conflicts with `apply-versioning.py`. Override this in the Phase 3 subagent prompt: instruct it to **preserve the existing version** from the source JSON (or omit the version field). The `apply-versioning.py` call after Phase 3 is the sole version manager for updates.

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
   Add `--fix-narrative-placement` to move top-level narratives to matching element's narratives[].
   Add `--fix-pattern-completeness` to ensure final view completeness and compress unchanged carry-forward states.
   Add `--compress-patterns` to remove unchanged carry-forward alpha states from non-final pattern views.
   Add `--all` to enable all optional fixes.

3. **For extension practices — fix competency levels if needed:**
   ```bash
   python3 utils/fix-competency-levels.py <file.json> <baseline.json> --fix
   ```

4. **Re-assess to confirm fixes:**
   ```bash
   python3 utils/assess-practice.py <file.json> --baseline <baseline.json> --schema deps/language.schema.json \
     [--parent <dep-practice.json> ...]
   ```
   Include `--parent` for each practice dependency to avoid false positives on cross-practice alpha references.

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
3. Add/Update References — discover and add reference content only

Which mode?
```

**Wait for user response, then proceed to Mode 1, Mode 2, or Mode 3 below.**

**Pre-Flight Fix (Mode 1 & 2 only):** Before entering remap or reanalysis, apply only structural schema fixes — NOT content fixes that Phase 3 will regenerate:

```bash
python3 utils/backup-practice.py <directory>/
python3 utils/fix-common-issues.py <file.json> --fix-schema --fix
```

This resolves blockers (missing `kind`, tags nesting, persona property normalization) without wasting time on content fixes (pattern completeness, narrative placement) that Phase 3 will overwrite. Do NOT use `--all` or `--fix-pattern-completeness` — those are for auto-fix mode only.

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
- Process: See generate-method SKILL.md "Step 1: Phase 1 - Analysis" section

**Update-specific additions:**
- **Update citations:** Search for latest authoritative sources (official docs, recent editions). Enrich all citations with `url` fields — use user-provided URLs, official websites, DOI references (`https://doi.org/10.xxxx/xxxxx`), or publisher pages. Only omit when no stable link exists.
- **Output directory:** `practices/<name>/` for extension practices, `baselines/<name>/` for baselines
- **Output:** `<dir>/01-analysis-report.md` (OVERWRITE existing if present)
- **Baselines only:** Also run Phase 1.5 distillation after Phase 1 (output: `<dir>/01.5-distilled-essentials.md`)
- **Comparison:** Note major differences from existing JSON content, inform user if significant restructuring needed

**Validation:** Apply Phase 1 Validation from generate-method skill

**Step 2C: Run Phase 2 - Mapping**

**IMPORTANT:** Follow the `generate-method` skill Phase 2 process exactly as documented in `.claude/skills/generate-method/SKILL.md` (Step 2: Phase 2 - Mapping section).

**Key reference files (read from generate-method skill):**
- Phase 2 prompt: `prompts/phase-2-mapping.md`
- Semantics guide: `references/semantics.md`
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

**Output:** `practices/<name>/02-mapping-guide.md` (OVERWRITE existing)

**Validation:** Apply Phase 2 Validation from generate-method skill

**Step 2D: Run Phase 3 - JSON Generation**

**IMPORTANT:** Follow the `generate-method` skill Phase 3 process exactly as documented in `.claude/skills/generate-method/SKILL.md` (Step 3: Phase 3 - JSON Generation section).

**Key reference files (read from generate-method skill):**
- Phase 3 prompt: `prompts/phase-3-json.md`
- Schema: `deps/language.schema.json`
- Baseline: Use effective baseline for semantic context; validate against the **original** user-provided baseline (canonical names). **Parent practice mode:** Set `baselinePracticeName` to the value inherited from the parent practice. Set `practiceDependencyNames` per the "Determining practiceDependencyNames" rule in generate-method SKILL.md (only parent practices whose unique non-baseline alphas are actually referenced).
- Process: See generate-method SKILL.md "Step 3: Phase 3 - JSON Generation" section

**Apply ALL latest validations from generate-method skill:**
- Critical JSON Rules (see "Critical JSON Rules" section)
- Phase 3 Validation (see "Phase 3 Validation" section)

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

**For methods — also extract method-level narratives** for later packaging:
```bash
python3 utils/extract-practice-content.py practices/<name>/<name>.json \
  --extract-narratives practices/<name>/_method-narrative.json
```
This saves the top-level `narratives` array to a standalone JSON file compatible with `package-keleo.py --method-narrative-file`.

**User Feedback:**
- "Extracted existing content as Phase 1 analysis report"
- "Preserved X alphas, Y work products, Z activities"

**Step 2B: Run Phase 2 - Mapping with Latest Guidance**

**IMPORTANT:** Follow the `generate-method` skill Phase 2 process exactly as documented in `.claude/skills/generate-method/SKILL.md` (Step 2: Phase 2 - Mapping section).

**Key reference files (read from generate-method skill):**
- Phase 2 prompt: `prompts/phase-2-mapping.md`
- Semantics guide: `references/semantics.md`
- Baseline: Use effective baseline from Step 0 (or original baseline if no dependencies were resolved). If the effective baseline has `_aliasContext`, use domain aliases for semantic understanding but canonical names in structural references.
- **Parent practice mode:** The effective context (`_effective-context.json`) contains ALL merged elements with `_contributingPracticeName` provenance. Use `_provenance.tiers` to distinguish baseline elements from practice elements. `contributesTo`/`mapsTo` targets should primarily reference practice-sourced alphas using canonical names. Set `practiceDependencyNames` per the "Determining practiceDependencyNames" rule in generate-method SKILL.md (only practices whose unique non-baseline alphas are actually referenced).
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

**Output:** `practices/<name>/02-mapping-guide.md` (OVERWRITE existing if present)

**Validation:** Apply Phase 2 Validation from generate-method skill

**User Feedback:**
- "Applied latest mapping guidance to existing content"
- "Updated X competency levels, added Y aliases, completed Z pattern matrices"
- "Identified primary alpha: <Alpha Name> with N related alphas"

**Step 2C: Run Phase 3 - JSON Generation**

**Size check:** If the existing practice JSON is **>100KB**, use the **Parallel Section Strategy** below instead of single-agent generation. Single-agent generation of large practices (>100KB output) can take many hours.

#### Standard Phase 3 (practices ≤100KB)

**IMPORTANT:** Follow the `generate-method` skill Phase 3 process exactly as documented in `.claude/skills/generate-method/SKILL.md` (Step 3: Phase 3 - JSON Generation section).

**Key reference files (read from generate-method skill):**
- Phase 3 prompt: `prompts/phase-3-json.md`
- Schema: `deps/language.schema.json`
- Baseline: Use effective baseline for semantic context; validate against the **original** user-provided baseline (canonical names). **Parent practice mode:** Set `baselinePracticeName` to the value inherited from the parent practice. Set `practiceDependencyNames` per the "Determining practiceDependencyNames" rule in generate-method SKILL.md (only parent practices whose unique non-baseline alphas are actually referenced).
- Process: See generate-method SKILL.md "Step 3: Phase 3 - JSON Generation" section

**Apply ALL latest validations from generate-method skill:**
- Critical JSON Rules (see "Critical JSON Rules" section)
- Phase 3 Validation (see "Phase 3 Validation" section)

**Output:** `practices/<name>/<name>.json` (OVERWRITE existing)

#### Parallel Section Strategy (practices >100KB)

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
| C: Work Products + Patterns | `workProducts` (LODs, contributesTo), `patterns` (views, alphaStates) | Mapping guide §Work Products, §Patterns |
| D: Metadata + Secondary | `narratives`, `citations`, `assets`, `practiceElementAliases`, `personas`, `personaGroups`, `keywords`, `tags` | Mapping guide §Metadata |

**Step 3: Launch parallel subagents**

Each subagent receives:
- Its section(s) of the mapping guide
- The schema (`deps/language.schema.json`) — relevant `$defs` only
- The effective context for cross-reference names (alpha names, activity space names, etc.)
- Instruction to output ONLY its assigned section(s) as a standalone JSON object

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

### Mode 3: Add/Update References

A lightweight mode that adds or updates curated reference content without requiring full remap or reanalysis. References are `AlphaInstance` objects in the `references` array — curated external content (templates, case studies, reference architectures, sample artifacts) that illustrate alphas at specific states.

**When to use:**
- Practice has no `references` array and would benefit from exemplar content
- User wants to add specific references they've found
- Practice has been through initial generation and alpha/state mappings are established
- User explicitly requests "add references" or "find references"

**Prerequisites:** The practice must already have established alpha/state/work-product mappings (i.e., Phase 2 has been completed at some point). This mode uses those mappings as the search framework.

**Step 3A: Load Practice Context**

1. **Read the existing practice JSON:**
   ```bash
   python3 utils/extract-reference-names.py <practice>.json --structure
   ```
   Review existing alphas, states, work products, and any existing references.

2. **Read the Phase 2 mapping guide** (if available):
   - `practices/<name>/02-mapping-guide.md` — contains alpha/state/work-product mappings
   - If no mapping guide exists, extract mappings from JSON:
     ```bash
     python3 utils/extract-practice-content.py <practice>.json
     ```

3. **Load baseline and dependencies:**
   ```bash
   python3 utils/discover-dependencies.py --resolve-from <practice>.json --transitive
   ```

4. **Check existing references:**
   ```bash
   python3 utils/extract-reference-names.py <practice>.json --sections references
   ```
   If references already exist, review them for gaps, outdated links, or missing alpha coverage.

**Step 3B: Discover Reference Content**

Use the established alpha/state/work-product mappings to guide discovery. Three sources, in order of priority:

1. **User-provided references:**
   - Ask user if they have specific references to add (URLs, documents, templates)
   - Map each to the appropriate alpha/state anchor

2. **Re-examine source materials:**
   - If original source materials are accessible (from citations or user), scan for:
     - Templates, starter documents, sample configurations
     - Reference architectures, design patterns with concrete examples
     - Case studies, exemplary implementations
     - Links to downloadable artifacts (repos, templates, tools)
   - Focus on content that illustrates a specific alpha at a specific state

3. **Secondary research (opt-in):**
   - Ask user whether to conduct secondary research for references
   - If approved, search for:
     - Official templates and starter kits from methodology authors
     - Community tools, reference implementations, open-source exemplars
     - Industry case studies demonstrating the methodology
   - Focus on alphas/states that have no references from other sources
   - Present findings to user for approval before including

**Step 3C: Map References to Anchors**

For each discovered reference, map to the Practice Language structure:

1. **Alpha + State anchor:** Which alpha does this reference illustrate, and at what state of maturity?
2. **Evidence (`evidenceBy`):** Map document artifacts to `WorkProductInstance` entries (see guidance below)
3. **Alpha-level links:** Landing pages, introductory or overview resources about the concern
4. **Tags (optional):** Apply domain/lifecycle/organizational tags if applicable
5. **Naming:** Follow the conventions below (concept-oriented names, not content-centric)

**Discovery principle — scope drives search:** The alpha's scope tells you what kind of content is relevant (the concern area at a state), and the work product's scope tells you which specific documents fit as evidence. When browsing a content source, use the alpha scope to identify relevant content at the right maturity level, then examine each document's purpose to determine which work product it evidences. This two-level scoping approach (alpha concern → work product artifact) naturally produces well-structured references.

---

**Reference conventions** — see `references/semantics.md` §6.6 for full naming rules, instance naming, and merge logic. Key rules:

- **Name pattern:** `"Standard [Qualifier] <AlphaName>"` — concept-centric, not content-centric
- **Description:** Semantic role in terms of alpha state progression, NOT what the linked content contains
- **Instance names scope to the example, NOT the state/LOD** — same real-world instance at different maturity levels shares ONE name
- **Two-level links:** Alpha-level `links` = navigation/overview; `evidenceBy[].links` = specific artifacts
- **Link names:** Use the actual content title, never generic platform labels
- **`evidenceBy` entries:** Each requires `name`, `description`, `workProductName`, `levelOfDetailName`, `links`. Spelled `evidenceBy` (NOT `evidencedBy`).
- **Hub/landing pages:** Alpha-level links only, no `evidenceBy`
- **For methods:** Present one consolidated mapping covering all practices; do NOT prompt per-practice. Wait for user confirmation.

**Step 3D: Update Practice JSON**

For a **single practice**, follow steps 1-5 below. For a **method** (multiple practices), see **Step 3E: Method-Level Orchestration** instead.

1. **Backup first:**
   ```bash
   python3 utils/backup-practice.py <directory>/
   ```

2. **Write a compact spec file** and apply with `build-references.py`:
   ```bash
   # Write compact spec (see build-references.py header for format)
   # Then validate + merge into practice in one step:
   python3 utils/build-references.py <practice>.json --spec refs-spec.json --fix
   ```
   The utility validates all anchors (alphaName, stateName, workProductName, levelOfDetailName) against the practice, expands compact shorthand to full AlphaInstance objects, and handles same-name merge automatically (highest state wins, links and evidenceBy aggregated).

   Link shorthand: `"https://url|Label"` expands to `{"name": "Label", "uri": "https://url"}`.

   Alternative: output expanded JSON without applying:
   ```bash
   python3 utils/build-references.py <practice>.json --spec refs-spec.json -o _references.json
   python3 utils/patch-practice-json.py <practice>.json --set-key references --patch-file _references.json
   ```

3. **Validate updated practice:**
   ```bash
   python3 utils/assess-practice.py <practice>.json --baseline <baseline>.json --schema deps/language.schema.json
   ```

5. **Bump version (patch):**
   ```bash
   python3 utils/apply-versioning.py <practice>.json --bump patch --fix
   ```

6. **Re-package into `.keleo`:**
   Follow the standard packaging process from Post-Update Packaging section.

7. **Report results:**
   ```
   Added N references to "<practice-name>":
   - [Reference 1]: [alphaName] at [stateName] — [link]
   - [Reference 2]: [alphaName] at [stateName] — [link]
   ...
   
   Version bumped: X.Y.Z → X.Y.(Z+1)
   Package updated: bundles/<name>.keleo
   ```

**Step 3E: Method-Level Orchestration (Mode 3)**

When adding references to a **method** with multiple constituent practices:

1. **Backup the method directory:**
   ```bash
   python3 utils/backup-practice.py practices/<method-name>/
   ```

2. **Identify all constituent practices** from the method JSON's `practiceNames` array. List them with their alpha structures so content can be mapped accurately.

3. **Batch discovery:** Browse the content source once for all practices, grouping discovered content by practice. Present a single consolidated mapping to the user for approval — do NOT prompt per-practice.

4. **Apply references to each practice** using compact specs:
   ```bash
   # Repeat for each practice with references
   python3 utils/build-references.py <practice>.json --spec <practice>-refs-spec.json --fix
   ```

5. **Batch version bump** all modified practices plus the method JSON in one command:
   ```bash
   python3 utils/apply-versioning.py --dir practices/<method-name>/ --bump patch --fix
   ```

6. **Repackage** the full method into `.keleo`:
   ```bash
   python3 utils/package-keleo.py \
     --documents <baseline>.json <practice1>.json ... <method>.json \
     --name <method-name> --version <new-version> \
     --description "..." -o bundles/<method-name>.keleo --verify
   ```

7. **Report results** with a summary table showing references per practice.

8. **Clean up** any temporary reference JSON files created during patching.

---

## Handling Methods (Multiple Practices)

For methods, ask user for scope (all practices, specific practices, or method-level only). Run update workflow per selected practice. Package with `package-keleo.py`.

## User Interaction

- **Start:** Read existing JSON + baseline, run assessment
- **Present:** Assessment results, recommended mode, ask user to choose
- **Progress:** Brief updates during phases
- **Completion:** Comparison report (what changed, what preserved, validation summary)

**Backup:** Always run `python3 utils/backup-practice.py <directory>/` before overwriting.

---

## Post-Update Validation

After any update, run the eval harness to confirm clean state:

**For extension practices:**
```bash
python3 utils/eval-skill-output.py practices/<name>/ \
  --baseline <baseline.json> --schema deps/language.schema.json --summary \
  [--parent <dep-practice.json> ...]
```
Include `--parent` for each `practiceDependencyNames` entry whose elements (alphas, work products, personas, etc.) are referenced by the practice.

**For baselines:**
```bash
python3 utils/eval-skill-output.py baselines/<name>/ --schema deps/language.schema.json --summary
```

**Expected result:** `error_pass_rate: 1.0`. Warning assertions are advisory — address where practical.

### ChangeRequest Generation (MANDATORY)

After any update that modifies a practice/baseline/method JSON, generate a ChangeRequest capturing the delta between the backup version and the updated version. ChangeRequests enable automatic downstream propagation of renames and structural changes via `apply-change-request.py`.

**When to generate:**
- **Mode 1 (Full Reanalysis):** Always — content is reworked from source
- **Mode 2 (Remap & Regenerate):** Always — mappings and structure change
- **Mode 1A (Auto-Fix):** Only if the fix introduced nameChanges (LOD renames, alpha renames, state renames). Pure structural fixes (missing `kind`, tags nesting, persona property normalization) do not need a ChangeRequest.
- **Mode 3 (Add/Update References):** Not needed — references are additive with no downstream impact

**Step 1: Generate ChangeRequest from diff:**
```bash
python3 utils/generate-change-request.py \
  <backup-dir>/<old-file>.json <updated-file>.json \
  --author "<git user>" \
  --status accepted \
  --note "Mode N update: <brief description of changes>" \
  -o <practice-dir>/<name>.changerequest.json
```

The utility compares old and new JSON, detects element renames (alphas, states, LODs, competencies, focuses, activity spaces, work products, narrative types), and generates a schema-compliant ChangeRequest with `operations` and `nameChanges` arrays.

**Step 2: Discover downstream dependents and present impact report:**
```bash
python3 utils/discover-dependencies.py --dependents "<Document Name>"
```

**MANDATORY: Present a Downstream Impact Report to the user.** Combine the ChangeRequest output with the dependents list to show which practices need updating:

```
=== Downstream Impact Report ===

ChangeRequest: <changeId>
Target: "<Document Name>" (<kind>)
Operations: N total (X modify, Y add, Z remove)
NameChanges: M renames requiring downstream propagation

Affected practices:
  1. "<Dependent Name>" (practices/<path>.json)
     Role: <practiceDependency|baselinePractice>
     Impact: <auto-propagatable|manual remap needed>
     Affected nameChanges:
       - <ElementType>: "<fromName>" → "<toName>"
       - ...

  2. "<Dependent Name>" (practices/<path>.json)
     ...

No dependents found.  (if none)

Actions needed:
  - Auto-propagatable: Run apply-change-request.py to update references
  - Manual remap needed: Run /update-method on affected practices
```

**Impact classification:**
- **Auto-propagatable:** The ChangeRequest contains `nameChanges` that `apply-change-request.py` can cascade automatically (element renames, state renames, LOD renames). These are safe to apply programmatically.
- **Manual remap needed:** The ChangeRequest contains structural changes (new alphas, removed alphas, changed contributesTo targets, new activity spaces) that require the dependent practice to be remapped via `/update-method`. Flag these for the user.

**Step 3: Propagate auto-fixable changes (dry-run first):**

If the ChangeRequest has `nameChanges` and dependents were found:
```bash
# Preview changes
python3 utils/apply-change-request.py <changerequest>.json <downstream1>.json <downstream2>.json

# Apply after user confirms
python3 utils/apply-change-request.py <changerequest>.json <downstream1>.json <downstream2>.json --fix
```

Show the dry-run output to the user before applying. Wait for user confirmation. The `nameChanges` array drives automatic reference updates in downstream files -- alpha name references, state references, competency names, LOD names, and all cascading structural references are updated in a single pass.

**Step 4: Re-validate downstream files** after applying changes:
```bash
python3 utils/assess-practice.py <downstream>.json --baseline <baseline>.json --errors-only
```

**Step 5: Report remaining manual work** to the user. List any dependents that need a full `/update-method` remap due to structural changes that cannot be auto-propagated.

### Post-Update Packaging

After validation passes, resolve transitive dependencies and package the updated output into a `.keleo` archive. **Never use `_effective-context.json` as a document** — it is a build artifact for semantic context during generation, not a distributable document.

**Step 1: Resolve transitive dependencies:**
```bash
python3 utils/discover-dependencies.py --resolve-from <practice-or-baseline>.json --transitive
```
Resolve any ambiguous dependencies (prefer `deps/`, `baselines/`, or `practices/` paths over `.keleo`-embedded copies). Collect all resolved file paths.

**Step 2: Package with all dependencies in topological order** (baselines first, then practices in dependency order, entry-point last):

**For extension practices:**
```bash
python3 utils/package-keleo.py \
  --name "<practice-name>" --version "1.0.0" \
  --description "<practice description>" \
  --documents <baseline>.json [<transitive-dep>.json ...] practices/<name>/<name>.json \
  -o bundles/<name>.keleo --verify
```

**For methods (multiple practices):**
```bash
python3 utils/package-keleo.py \
  --name "<method-name>" --version "1.0.0" \
  --description "<method description>" \
  --documents <baseline>.json [<transitive-dep>.json ...] \
              practices/<method-name>/practice-1.json \
              practices/<method-name>/practice-2.json \
  --method-name "<Method Name>" \
  --method-description "<method description>" \
  --method-narrative-file practices/<method-name>/_method-narrative.json \
  -o bundles/<method-name>.keleo --verify
```

**For baselines (with parent baseline):**
```bash
python3 utils/package-keleo.py \
  --name "<baseline-name>" --version "1.0.0" \
  --description "<baseline description>" \
  --documents [<parent-baseline>.json] baselines/<name>/<name>.json \
  -o bundles/<name>.keleo --verify
```

---

## Common Update Scenarios

| # | Trigger | Mode | Key Command / Notes |
|---|---|---|---|
| 1 | Baseline updated | Remap (Mode 2) | Map to new alphas, update competency levels |
| 2 | Citations outdated | Full Reanalysis (Mode 1) | Gather updated sources, research latest editions |
| 3 | Schema/guidance updated | Remap (Mode 2) | Apply latest guidance, fix schema issues |
| 4 | Practice needs restructuring | Full Reanalysis (Mode 1) | Identify primary alphas, split practices |
| 5 | Quality issues (names, assets, citations) | Auto-fix → Remap | `fix-common-issues.py --fix --all`, then remap for remaining |
| 6 | Citation name format (Author-Date → Title) | Auto-fix | `fix-citation-names.py --rename "Old=New"` or `--map renames.json` |
| 7 | Add Gherkin guidance | Remap (Mode 2) | Read semantics.md §5.3, §8.1.1; add background/test/examples |
| 8 | Convert to .keleo package | Packaging only | `package-keleo.py --from-embedded` or `--documents` |
| 9 | Add/update references | Mode 3 | Map to alpha+state, require ≥1 link per reference |
| 10 | Add/convert WP partOf/mapsTo | Targeted transform | `transform-workproducts.py --spec '[...]' --fix` |
| 11 | Batch WP partOf→mapsTo | Targeted transform | `transform-workproducts.py` — set `setMapsTo`, `lodMap`, `rename` |

**Scenario 8 details** (packaging-only — most common standalone use):
- Embedded method: `package-keleo.py --from-embedded <method>.json --baseline <baseline>.json -o bundles/<name>.keleo --verify`
- Standalone practice: resolve deps first (`discover-dependencies.py --resolve-from <practice>.json --transitive`), then `package-keleo.py --documents <baseline>.json [<deps>...] <practice>.json -o bundles/<name>.keleo --verify`

**Scenario 10/11 key rules**: `mapsTo` and `partOf` are mutually exclusive. `mapsTo` requires identical LOD names. `mapsTo` variant names omit parent type.

---

## Remap Phase: Quality Fixes

### Checklist Name Quality
When assessment flags `checklist-quality` issues, rewrite names as short Title Case noun phrases (3-8 words) capturing WHAT is checked, not HOW. Names must not echo descriptions. Apply consistently across all alphas.

### Asset Coverage
When assessment flags `asset-coverage` gaps, add Font Awesome 6 Free icons (`fontWeight: "900"`, naming: `<kebab-case>-icon`). Every NarrativeType and Focus needs an icon. See generate-method SKILL.md Assets section for icon suggestions and JSON structure.

---

## Feature: Update Process Integrity

Validates that the update workflow follows correct assessment-first, backup-safe patterns.

### Scenario: Assessment before update (@rule:process-401)
- Given: An existing JSON file is provided for update
- When: The update workflow begins
- Then: assess-practice.py is run first to determine suggestedUpdateMode
- And: The update mode is auto-fix, remap, or full-reanalysis based on assessment output

### Scenario: Backup before overwrite (@rule:process-402)
- Given: The update will overwrite existing files
- When: Any mode (auto-fix, remap, or full-reanalysis) begins
- Then: backup-practice.py has created a timestamped backup of the directory
- And: The backup contains all JSON and markdown files

### Scenario: Auto-fix mode applied when sufficient (@rule:process-403)
- Given: Assessment output shows suggestedUpdateMode is "auto-fix"
- When: The update mode is determined
- Then: Fix utilities are run without user interaction
- And: Re-assessment confirms 0 errors before reporting success

### Scenario: Dependency resolution before update (@rule:process-404)
- Given: An extension practice is being updated
- When: Step 0C begins
- Then: discover-dependencies.py resolves all baselinePracticeName and practiceDependencyNames
- And: Resolved dependencies are confirmed with the user before proceeding

### Scenario: Content preservation during remap (@rule:process-405)
- Given: The update uses remap mode (Phase 2 → 3)
- When: Existing content is extracted and remapped
- Then: All valid existing alphas, activities, work products, and narratives are preserved
- And: Only superseded or invalid content is replaced

### Scenario: Post-update validation required (@rule:process-406)
- Given: An update has completed (any mode)
- When: The workflow is finishing
- Then: eval-skill-output.py is run with error_pass_rate checked
- And: The result is reported to the user with any remaining warnings

### Scenario: Comparison report after update (@rule:process-407)
- Given: A remap or full-reanalysis update has completed
- When: The new JSON is generated
- Then: diff-practice-json.py shows what changed vs the original
- And: The user sees added, removed, and modified elements

### Scenario: User confirms update mode when auto-fix insufficient (@rule:process-408)
- Given: Assessment shows non-auto-fixable issues
- When: Step 1B presents mode options
- Then: The user is asked to choose between remap and full-reanalysis
- And: The recommended mode and reason from assessment are presented

### Scenario: ChangeRequest generated after update (@rule:process-409)
- Given: An update has modified an existing practice/baseline/method JSON
- When: The updated JSON differs from the backup version
- Then: generate-change-request.py produces a ChangeRequest JSON
- And: The ChangeRequest is written to the practice directory
- And: A Downstream Impact Report is presented to the user listing affected practices

### Scenario: Downstream impact report presented (@rule:process-410)
- Given: A ChangeRequest has been generated with operations and nameChanges
- When: discover-dependencies.py --dependents finds downstream practices
- Then: The user is shown each dependent practice name, path, and role
- And: Each nameChange affecting that dependent is listed
- And: Each dependent is classified as auto-propagatable or manual remap needed
- And: The user is told which practices need /update-method remap vs auto-fix

### Scenario: Downstream auto-propagation requires confirmation (@rule:process-411)
- Given: Downstream dependents have auto-propagatable nameChanges
- When: apply-change-request.py is invoked
- Then: A dry-run is shown to the user first
- And: Changes are only applied after user confirms

## Key Principles

1. **Automate First** — Use `assess-practice.py` and fix utilities before asking the user anything. Only prompt when auto-fix is insufficient.
2. **No Inline Scripts** — All programmatic actions use reusable scripts in `utils/`, never `python3 -c` or `bash -c`. See generate-method SKILL.md "Key Utilities" table for the full utility reference. Run `python3 utils/<script>.py --help` for detailed usage. Additional update-specific utilities:
   - `transform-alphas.py` — Batch alpha transforms: `rename`, `setMapsTo`, `setContributesTo`, `stateMap`, `addStates`
   - `transform-workproducts.py` — Batch WP transforms: `rename`, `setMapsTo`, `setPartOf`, `lodMap`, `addLods`
   - `build-references.py` — Validate and expand reference specs into AlphaInstance JSON (`--spec`, `--fix`)
   - `fix-citation-names.py` — Rename citation names (`--rename "Old=New"` or `--map renames.json`)
   - `apply-versioning.py` — Stamp versions (`--bump patch|minor --fix` or `--all --fix` for batch)
   - `generate-change-request.py` — Generate ChangeRequest JSON from old/new diff (`<old>.json <new>.json --author --status -o`)
   - `apply-change-request.py` — Apply ChangeRequest nameChanges/removals to downstream JSON (`<cr>.json <target>.json [--fix]`)
3. **Preserve Content** — Retain all valuable analysis, activities, narratives unless superseded.
4. **Backup First** — Never overwrite without running `utils/backup-practice.py` first.
5. **Validate Rigorously** — Re-run `assess-practice.py` after every fix to confirm clean state.
6. **Report Changes** — Show what was fixed and what remains.

---

## Post-Completion Review (MANDATORY)

**After completing the skill workflow OR after completing planning**, read `.claude/skills/SKILL-STANDARD.md` §11 for the full Post-Completion Review protocol, then review the session for optimisation opportunities:

1. **Audit ad-hoc commands**: Did the user have to confirm execution of any commands or scripts that weren't auto-approved? Look for:
   - Permission prompts for Bash commands not in the project's `.claude/settings.json` allow list
   - Inline `python3 -c` or `bash -c` scripts that should have been reusable utils
   - Shell patterns (heredocs, loops, process substitution) that triggered prompts
   - External tool calls (e.g., `unzip`, `zip`, `curl`) that could be absorbed into existing utils

2. **Identify missing utils**: Did you have to write any ad-hoc logic that could be generalised into a reusable utility script in `utils/`?

3. **Propose fixes** (present to user, don't apply unilaterally):
   - **Permission gaps**: Suggest adding auto-allow entries to `.claude/settings.json`
   - **Missing utils**: Propose new utility scripts or extensions to existing ones
   - **Skill improvements**: Suggest skill instruction updates to prevent the ad-hoc pattern in future runs

4. **Report**: Briefly tell the user what you found and what you'd recommend changing. If nothing was found, say so — a clean session is a good signal.
