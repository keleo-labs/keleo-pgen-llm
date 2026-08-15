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
   Add `--fix-pattern-completeness` to add carry-forward alpha states to incomplete pattern views.
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

**Reference naming and description conventions:**

References are AlphaInstance objects — they represent the alpha (a general concern or concept) at a specific state, not the content asset itself. Names and descriptions must reflect this.

- **Name pattern:** `"Standard [Qualifier] <AlphaName>"` — "Standard" prefix indicates a reference exemplar. Optional qualifier indicates the positioning context (e.g., "Customer", "Partner", "Internal", "Engagement").
- **Description pattern:** Describe the semantic role of the reference instance in terms of the alpha's state progression, NOT what the linked content contains.

| | BAD (content-centric) | GOOD (concept-centric) |
|---|---|---|
| **Name** | "AI Platform TDP Customer Presentation" | "Standard Customer AI Platform TDP" |
| **Description** | "Customer-facing deck for the AI Platform technology decision point..." | "Reference AI Platform TDP at Positioned state with customer-facing positioning materials" |
| **Name** | "Inference at Scale Sales Tactic" | "Standard Engagement Inference at Scale" |
| **Description** | "Sales tactic guide for engaging customers on inference at scale..." | "Reference Inference at Scale at Prepared state with customer engagement materials" |

---

**Two-level link structure — alpha links vs evidence links:**

A reference can carry links at two levels, serving different purposes:

| Level | Property | Content Scope | Examples |
|---|---|---|---|
| **Alpha-level** | `links` on the AlphaInstance | Landing pages, introductory info, overview resources about the concern area | TDP hub pages, sales play landing pages, topic overviews |
| **Evidence-level** | `links` on each `evidenceBy` WorkProductInstance | Specific documents scoped to a work product's purpose | Customer decks, cheatsheets, conversation guides, templates |

A single reference can have BOTH alpha-level links (for orientation) and `evidenceBy` entries with their own links (for specific artifacts). Hub/landing pages with no specific work product scope go in alpha-level links only.

**Link naming:** All link `name` fields — at both levels — must use the **actual title of the content** being linked (the page title, document name, or resource heading). Do NOT use generic platform labels.

| BAD | GOOD |
|---|---|
| `"Sales Hub"` | `"Red Hat AI Platform Technology Decision Point — Customer Presentation"` |
| `"Google Slides (Source)"` | `"AI Platform TDP Qualification Cheatsheet"` |
| `"Sales Hub Page"` | `"AI Platform Technology Decision Point Hub"` |

Link `description` is optional but recommended when derivable from content inspection.

---

**`evidenceBy` mapping — content to work products:**

Document artifacts belong in `evidenceBy` as `WorkProductInstance` entries. Each entry maps the specific document to a work product type (from the practice or its `practiceDependencyNames` chain) at an appropriate level of detail. The property is spelled `evidenceBy` (NOT `evidencedBy`).

Each `evidenceBy` entry requires:
- `name`: Document-oriented name identifying the specific artifact
- `description`: What this work product instance represents
- `workProductName`: Must resolve to a defined work product (practice-local or from dependencies)
- `levelOfDetailName`: Must resolve to a defined LOD on that work product
- `links`: The actual document URLs with content-title names

**Content-to-work-product heuristics:**

| Content Type | Heuristic State | evidenceBy workProductName | evidenceBy LOD | Rationale |
|---|---|---|---|---|
| Hub/landing pages | Earliest (awareness) | NO evidenceBy — alpha `links` only | — | Navigation resource, not artifact |
| Cheatsheets, qualification guides | Early-mid (assessment) | TDP Positioning Brief | Credentialed | Credentialing/qualification support |
| Customer decks, pitch materials | Mid (positioning) | TDP Positioning Brief | Content-Complete | Customer-facing positioning artifact |
| Sales tactic pages/guides | Sub-alpha relevant state | Sales Tactic Conversation Guide | Deployment-Ready | Tactic engagement guidance |
| Sales play pitch decks | Mid (engagement) | Sales Play Execution Guide | Structured | Play-level customer engagement material |
| Personas and discovery docs | Mid (engagement) | Sales Play Execution Guide | Structured | Persona/discovery support |
| Templates, starter artifacts | Mid-late (execution) | (practice-specific work product) | (appropriate LOD) | Execution support |
| Case studies, reference archs | Late (evidence) | (practice-specific work product) | (advanced LOD) | Demonstrated outcomes |

Work product names above are examples from the Sales Play Framework practice. For other practice families, use the practice's own work products or its dependency chain's work products.

---

**Complete structural example:**

Before (content-centric, no `evidenceBy`):
```json
{
  "name": "AI Platform TDP Customer Presentation",
  "description": "Customer-facing deck for the AI Platform technology decision point, positioning Red Hat's AI platform for enterprise AI deployment",
  "alphaName": "AI Platform",
  "stateName": "Positioned",
  "links": [
    { "name": "Sales Hub", "uri": "https://saleshub.redhat.com/Link/Content/DCPHDQgjP7JhTGcPDVmXhXF2XhJG" }
  ]
}
```

After (concept-centric, with `evidenceBy`):
```json
{
  "name": "Standard Customer AI Platform TDP",
  "description": "Reference AI Platform TDP at Positioned state with customer-facing positioning materials",
  "alphaName": "AI Platform",
  "stateName": "Positioned",
  "evidenceBy": [
    {
      "name": "AI Platform Customer Positioning Deck",
      "description": "Customer-facing slide deck for AI platform technology positioning",
      "workProductName": "TDP Positioning Brief",
      "levelOfDetailName": "Content-Complete",
      "links": [
        {
          "name": "Red Hat AI Platform Technology Decision Point — Customer Presentation",
          "description": "Slide deck covering AI platform positioning, competitive landscape, and customer value",
          "uri": "https://saleshub.redhat.com/Link/Content/DCPHDQgjP7JhTGcPDVmXhXF2XhJG"
        }
      ]
    }
  ]
}
```

Hub page reference (alpha-level links only, no `evidenceBy`):
```json
{
  "name": "Standard Discovery AI Platform TDP",
  "description": "Reference AI Platform TDP at Identified state with discovery and enablement resources",
  "alphaName": "AI Platform",
  "stateName": "Identified",
  "links": [
    {
      "name": "AI Platform Technology Decision Point Hub",
      "description": "Landing page with links to all AI Platform TDP sales enablement resources",
      "uri": "https://saleshub.redhat.com/Link/Content/DCGp7297MBFqdG2PWFCdjCgfWhcB"
    }
  ]
}
```

---

**For methods — present one consolidated mapping** covering all practices rather than prompting per-practice. Group by practice with a reference count summary:

```
=== Reference Mapping for "<method-name>" ===

Practice: "<practice-1>" (N references)
1. Standard Customer <AlphaName> → <alphaName> at <stateName>
   evidenceBy: <workProductName> at <LOD>
   links: [content title] (uri)
2. Standard Discovery <AlphaName> → <alphaName> at <stateName>
   alpha links: [content title] (uri)

Practice: "<practice-2>" (N references)
...

Total: X references across Y practices. Proceed? (yes/edit/no)
```

**Wait for user confirmation.**

**Step 3D: Update Practice JSON**

For a **single practice**, follow steps 1-6 below. For a **method** (multiple practices), see **Step 3E: Method-Level Orchestration** instead.

1. **Backup first:**
   ```bash
   python3 utils/backup-practice.py <directory>/
   ```

2. **Add references to JSON** using the patch utility:
   ```bash
   python3 utils/patch-practice-json.py <practice>.json --set-key references --patch-file _references.json
   ```
   Or to append to existing references:
   ```bash
   python3 utils/patch-practice-json.py <practice>.json --append-key references --patch-file _new-references.json
   ```

3. **Validate updated practice:**
   ```bash
   python3 utils/assess-practice.py <practice>.json --baseline <baseline>.json --schema deps/language.schema.json
   ```

4. **Bump version (patch):**
   ```bash
   python3 utils/apply-versioning.py <practice>.json --bump patch --fix
   ```

5. **Re-package into `.keleo`:**
   Follow the standard packaging process from Post-Update Packaging section.

6. **Report results:**
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

4. **Patch all practices:** Create one reference JSON per practice and patch each:
   ```bash
   # Repeat for each practice with references
   python3 utils/patch-practice-json.py <practice>.json --set-key references --patch-file <refs>.json
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

**For Method JSON files:**

1. **Ask user for scope:**
   ```
   This is a Method with N practices. Which practices would you like to update?
   - All practices (full method update)
   - Specific practices: [list practice names]
   - Method-level only (narratives, citations, patterns)
   ```

2. **For each selected practice:**
   - Run update workflow (Mode 1, Mode 2, or Mode 3) per practice
   - Generate individual practice JSON or mapping sections

3. **Package Method into `.keleo`:**
   - Package updated practices + baseline into `.keleo` archive using `package-keleo.py`
   - The packager generates an externalized method JSON with `practiceNames` references
   - Method-level narratives and merged citations are included automatically
   - Validate individual practice JSONs before packaging

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
3. Add/Update References - Add curated external content without full remap

Which mode would you like to use?"

### During Update

Provide progress updates:

- "Extracting existing content as Phase 1 analysis..."
- "Applying latest mapping guidance: primary alpha focus, competency validation..."
- "Generating updated JSON with latest schema requirements..."
- "Packaging into .keleo archive..."
- "Validation passed! Updated practice packaged at bundles/<name>.keleo"

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
  --baseline <baseline.json> --schema deps/language.schema.json --summary \
  [--parent <dep-practice.json> ...]
```
Include `--parent` for each `practiceDependencyNames` entry whose elements (alphas, work products, personas, etc.) are referenced by the practice.

**For baselines:**
```bash
python3 utils/eval-skill-output.py baselines/<name>/ --schema deps/language.schema.json --summary
```

**Expected result:** `error_pass_rate: 1.0`. Warning assertions are advisory — address where practical.

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

### Scenario 7: Add Gherkin-Inspired Structured Guidance

**Symptoms:**
- Practice/baseline lacks `background`, `test`, or `examples` properties
- States have complex prerequisites not captured structurally
- Checklist items need verification scenarios
- Activities have non-obvious triggers or decision points

**Update Mode:** Remap & Regenerate (Mode 2)

**Process:**
1. Read `references/semantics.md` Section 5.3 (Gherkin-Inspired Test Model) and Section 8.1.1 (Gherkin on Activities)
2. Review existing states for complex prerequisites → add `background` with `given`, `alphaStates`, `workProductLevels`
3. Review checklist items for verification logic → add `test` (Given/When/Then) and `examples` (concrete scenarios)
4. Review activities for triggers/decision points → add `test.when` and `test.then` (complementing structural `contributesTo`/`worksOn`)
5. For baselines: use sparingly — practice layer is the natural place for detailed Gherkin
6. For LODs: add `background` where work product maturity depends on alpha state prerequisites
7. Regenerate JSON and validate

**Key Rules:**
- `test` extends PracticeElement — requires `name` and `description` fields
- `examples` is an array of Test objects (not strings)
- `background` is an object (not string/array) with optional `given`, `alphaStates`, `workProductLevels`
- `test.then` should complement (not duplicate) structural `contributesTo`/`worksOn`
- Incremental adoption is valid — any combination of background/test/examples can be used independently

### Scenario 8: Convert Existing Output to `.keleo` Package

**Symptoms:**
- Existing practice/baseline/method JSON files without `.keleo` packaging
- Embedded method JSON that should use externalized `practiceNames` references
- Need to bundle practice + baseline into a distributable package

**Update Mode:** No phase re-execution needed — packaging only

**Process for embedded method JSON:**
```bash
python3 utils/package-keleo.py \
  --from-embedded <method>.json \
  --baseline <baseline>.json \
  -o bundles/<method-name>.keleo --verify
```
This extracts embedded practices into separate documents, creates an externalized method JSON with `practiceNames` string references, and bundles everything into a `.keleo` archive.

**Process for standalone practice + baseline:**
First resolve transitive dependencies (`python3 utils/discover-dependencies.py --resolve-from <practice>.json --transitive`), then include all resolved documents:
```bash
python3 utils/package-keleo.py \
  --name "<practice-name>" --version "1.0.0" \
  --description "<description>" \
  --documents <baseline>.json [<transitive-deps>.json ...] <practice>.json \
  -o bundles/<practice-name>.keleo --verify
```

**Process for standalone baseline:**
If the baseline has `baselinePracticeName`, include the parent baseline:
```bash
python3 utils/package-keleo.py \
  --name "<baseline-name>" --version "1.0.0" \
  --description "<description>" \
  --documents [<parent-baseline>.json] <baseline>.json \
  -o bundles/<baseline-name>.keleo --verify
```

### Scenario 9: Add/Update Reference Content

**Symptoms:**
- Practice has no `references` array or sparse references
- User has found exemplar content (templates, case studies, reference architectures) to add
- Practice would benefit from curated external content illustrating alphas at specific states
- User explicitly requests reference discovery

**Update Mode:** Add/Update References (Mode 3)

**Process:**
1. Load existing practice JSON and review alpha/state/work-product mappings
2. Check for existing references and identify coverage gaps
3. Discover new references from source materials, secondary research, or user-provided content
4. Map each reference to alpha + state anchor with at least one `links` entry (URI)
5. Present mapped references to user for approval
6. Patch references into practice JSON, validate, version bump (patch), and re-package

**Key Rules:**
- Every reference MUST have at least one `links` entry with a valid URI
- `alphaName` and `stateName` must match defined elements in practice or baseline
- `evidenceBy` entries (if present) must reference defined work products and LODs
- Follow naming conventions from `references/semantics.md` §6.6
- References are `AlphaInstance` objects — they illustrate an alpha at a specific state of maturity

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
   - Assessment with parent: `python3 utils/assess-practice.py <file>.json --baseline <baseline>.json --parent <parent>.json` (merges parent's alphas, work products, personas, activities, etc. into baseline for cross-reference validation)
   - Assessment summary: `python3 utils/assess-practice.py <file>.json --summary` (counts by severity/category, suggested mode)
   - Extract method narratives: `python3 utils/extract-practice-content.py <method>.json --extract-narratives <output>.json` (for package-keleo.py --method-narrative-file)
   - Errors-only assessment: `python3 utils/assess-practice.py <file>.json --errors-only` (filter to only severity=error issues)
   - Top-level structure overview: `python3 utils/extract-reference-names.py <file>.json --structure` (type and count/length for each key)
   - Cross-practice method audit: `python3 utils/audit-method-references.py <method>.json --baseline <baseline>.json` (alpha refs, duplicates, persona consistency)
   - Add missing alpha redeclaration: `python3 utils/fix-alpha-refs.py <practice>.json <baseline>.json --add-redeclaration "Alpha Name" [--fix]`
   - Remap alpha references: `python3 utils/fix-alpha-refs.py <practice>.json <baseline>.json --remap "Old Alpha" "New Alpha" --state-map '{"OldState":"NewState"}' [--fix]`
   - Remove alpha and references: `python3 utils/fix-alpha-refs.py <practice>.json <baseline>.json --remove-alpha "Alpha Name" [--fix]`
   - Batch alpha transform (dry-run): `python3 utils/transform-alphas.py <practice>.json --spec '[{"alpha":"Old","rename":"New","setMapsTo":"Parent","stateMap":{"S1":"T1"}}]'`
   - Batch alpha transform (apply): `python3 utils/transform-alphas.py <practice>.json --spec-file transforms.json --fix`
   - Transform spec supports: `rename`, `setMapsTo`, `setContributesTo`, `stateMap` (1:1 or many:1 merge), `addStates` (new states with checklist)
   - Resolve transitive deps: `python3 utils/discover-dependencies.py --resolve-from <file>.json --transitive` (find all baselines + practices in dependency tree)
   - Package into .keleo: `python3 utils/package-keleo.py --name "name" --version "1.0.0" --description "..." --documents baseline.json [transitive-deps.json ...] p1.json p2.json --method-name "Method Name" -o bundles/name.keleo --verify` (list ALL transitive deps, never use `_effective-context.json`)
   - Convert embedded method to .keleo: `python3 utils/package-keleo.py --from-embedded method.json --baseline baseline.json -o bundles/method.keleo --verify`
   - Verify existing package: `python3 utils/package-keleo.py --verify-only bundles/name.keleo`
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
   - These commands work on ANY JSON file — practice, method, baseline, `_effective-context.json`
   - Bump version (patch): `python3 utils/apply-versioning.py <file>.json --bump patch --fix` (increments version, refreshes schemaVersion, dependencyVersions, updatedAt)
   - Bump version (minor): `python3 utils/apply-versioning.py <file>.json --bump minor --fix` (for remap/reanalysis updates)
   - Normalize versioning: `python3 utils/apply-versioning.py <file>.json --fix` (add schemaVersion, normalize version, populate dependencyVersions)
   - Batch versioning: `python3 utils/apply-versioning.py --all --fix` (process all docs in dependency order)
3. **Preserve Content** — Retain all valuable analysis, activities, narratives unless superseded.
4. **Backup First** — Never overwrite without running `utils/backup-practice.py` first.
5. **Validate Rigorously** — Re-run `assess-practice.py` after every fix to confirm clean state.
6. **Report Changes** — Show what was fixed and what remains.

---

## Post-Completion Review (MANDATORY)

**After completing the skill workflow OR after completing planning**, review the session for optimisation opportunities:

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
