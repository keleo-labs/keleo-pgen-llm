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

**Five Update Modes (auto-detected or user-requested):**

1. **Auto-Fix** — All issues are programmatically fixable. Run fix utilities and validate. No phase re-execution needed.
2. **Remap & Regenerate** (Phase 2 → 3) — Use existing content, apply latest mapping guidance, regenerate JSON
3. **Full Reanalysis** (Phase 1 → 2 → 3) — Revisit source materials, update citations, complete rework
3B. **Light Reanalysis** (Phase 1B → 2 → 3) — Re-research specific analysis sections; preserve unchanged sections
4. **Add/Update References** — Discover and map reference content without full remap. Lightweight mode that adds curated external content (templates, case studies, reference architectures) to the `references` array.

**Mode instructions are in separate files** — read only the selected mode's file:
- Mode 1: `.claude/skills/update-method/modes/mode-1-full-reanalysis.md`
- Mode 1B: `.claude/skills/update-method/modes/mode-1b-light-reanalysis.md`
- Mode 2: `.claude/skills/update-method/modes/mode-2-remap.md`
- Mode 3: `.claude/skills/update-method/modes/mode-3-references.md`

## Input Requirements

**User must provide:**
1. **Existing JSON file(s)**: One or more practice/method/baseline JSON files to update
2. **Baseline practice** (for extension practices): Either a baseline JSON or parent practice/method
3. **Source materials** (only if full reanalysis): Original methodology documentation

---

## Execution Workflow

### Step 0: Assess and Detect Gaps

Run the consolidated assessment utility — this replaces ALL manual inspection steps:

```bash
python3 utils/assess-practice.py <file.json> --schema deps/language.schema.json
```

**Schema gap detection (optional, complements assessment):**
```bash
python3 utils/detect-schema-gaps.py <file.json>
python3 utils/detect-schema-gaps.py --dir <dir>/    # batch mode
```
Compares the practice's `schemaVersion` against the current schema and checks for missing features (outcomes, patternGroups, checklist priorities, references, acknowledgements, dependencyVersions, Gherkin structures). Outputs `suggestedUpdateMode` ("none", "auto-fix", "remap") based on gap severity.

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
   - `"light-reanalysis"` → proceed to **Step 1B** recommending Mode 1B
   - `"full-reanalysis"` → proceed to **Step 1B** recommending Mode 1

### Version Incrementing

When updating an existing document, increment its `version` based on the update mode:

| Update Mode | Version Bump | Rationale |
|---|---|---|
| **Auto-Fix** | `patch` (e.g. 1.0.0 → 1.0.1) | Structural fixes, no content changes |
| **Remap & Regenerate** | `minor` (e.g. 1.0.0 → 1.1.0) | Remapped content, new guidance applied |
| **Full Reanalysis** | `minor` (e.g. 1.0.0 → 1.1.0) | Content reworked from source materials |
| **Light Reanalysis** | `minor` (e.g. 1.0.0 → 1.1.0) | Targeted content rework from source materials |
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

**IMPORTANT — Schema version auto-detection:** Do NOT hardcode a `schemaVersion` in Phase 3 subagent prompts. Instruct subagents to read the schema's `$comment` field to extract the current version (e.g., `"schemaVersion:2.4.0"`). This prevents drift when the schema is updated between planning and execution. `apply-versioning.py --fix` also auto-corrects `schemaVersion` as a fallback.

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
   Add `--fix-self-ref-backgrounds` to remove background alphaStates that reference the owning alpha.
   Add `--fix-unknown-activity-spaces` to replace invalid activitySpaceNames with closest baseline match (requires baseline arg).
   Add `--fix-narrative-types` to replace invalid narrativeTypeName values with closest baseline match (requires baseline arg).
   Add `--fix-competency-refs` to fix invalid competency names/levels via `fix-competency-levels.py --partial` (requires baseline arg).
   Add `--all` to enable all optional fixes.

3. **For extension practices — fix remaining competency issues:**
   ```bash
   # --partial fixes what it can, reports unmapped names without failing
   python3 utils/fix-competency-levels.py <file.json> <baseline.json> --fix --partial
   ```
   If unmapped names are reported, add explicit mappings:
   ```bash
   python3 utils/fix-competency-levels.py <file.json> <baseline.json> --fix \
     --map-name "InvalidName=ValidName"
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

Recommended mode: [remap/light-reanalysis/full-reanalysis] — [modeReason from assessment]

Options:
1. Remap & Regenerate (Phase 2 → 3) — preserves existing analysis
2. Full Reanalysis (Phase 1 → 2 → 3) — revisits all source materials from scratch
2B. Light Reanalysis (Phase 1B → 2 → 3) — targeted re-research of specific analysis sections
3. Add/Update References — discover and add reference content only

Which mode?
```

**Mode 1B prerequisite:** Only offer Light Reanalysis if `01-analysis-report.md` exists in the practice/baseline directory. If it doesn't exist, omit option 2B.

**Wait for user response, then read the corresponding mode instructions file:**
- Mode 1 → Read `.claude/skills/update-method/modes/mode-1-full-reanalysis.md`
- Mode 1B → Read `.claude/skills/update-method/modes/mode-1b-light-reanalysis.md`
- Mode 2 → Read `.claude/skills/update-method/modes/mode-2-remap.md`
- Mode 3 → Read `.claude/skills/update-method/modes/mode-3-references.md`

**Pre-Flight Fix (Mode 1, 1B & 2 only):** Before entering remap or reanalysis, apply only structural schema fixes — NOT content fixes that Phase 3 will regenerate:

```bash
python3 utils/backup-practice.py <directory>/
python3 utils/fix-common-issues.py <file.json> --fix-schema --fix
```

This resolves blockers (missing `kind`, tags nesting, persona property normalization) without wasting time on content fixes (pattern completeness, narrative placement) that Phase 3 will overwrite. Do NOT use `--all` or `--fix-pattern-completeness` — those are for auto-fix mode only.

---

### Mode 1: Full Reanalysis (Phase 1 → 2 → 3)

**Read:** `.claude/skills/update-method/modes/mode-1-full-reanalysis.md` for detailed instructions.

---

### Mode 1B: Light Reanalysis (Phase 1B → 2 → 3)

**Read:** `.claude/skills/update-method/modes/mode-1b-light-reanalysis.md` for detailed instructions.

---

### Mode 2: Remap & Regenerate (Phase 2 → 3)

**Read:** `.claude/skills/update-method/modes/mode-2-remap.md` for detailed instructions.

---

### Mode 3: Add/Update References

**Read:** `.claude/skills/update-method/modes/mode-3-references.md` for detailed instructions.

---

## Handling Methods (Multiple Practices)

For methods, ask user for scope (all practices, specific practices, or method-level only). Run update workflow per selected practice. Package with `package-keleo.py`.

### Batch Update (All Practices in a Bundle)

When the user requests updating ALL practices in a method/bundle:

**Step 1: Build a Dependency DAG.** Group practices into tiers based on `practiceDependencyNames`:

| Tier | Contents | Depends On |
|---|---|---|
| 0 | Baseline | — |
| 1 | Practices with no `practiceDependencyNames` (or only baseline) | Baseline |
| 2 | Practices depending only on Tier 1 practices | Tier 1 |
| 3 | Practices depending on Tier 2 practices | Tier 2 |
| Final | Method JSON + rebundling | All tiers |

**Step 2: Execute by tier.** Within each tier, all practices can run in parallel:
- **Augmented analysis:** All practices can be analyzed in parallel (no inter-practice dependencies at analysis stage)
- **Remapping:** Run Tier 1 in parallel; Tier 2 can start as soon as its specific dependencies complete (not all of Tier 1); Tier 3 similarly
- **JSON generation:** All practices can run in parallel once all mapping guides are stable (element names finalized)
- **Validation + versioning:** Run batch `fix-common-issues.py --all --fix` across all practices, then batch `apply-versioning.py --bump minor --fix`

**Step 3: Method JSON + rebundle.** After all practices pass validation:
1. Update method JSON(s): `schemaVersion`, `version` bump, `dependencyVersions`
2. Package all `.keleo` bundles with `--verify`

**Key lessons:**
- Phase 3 agents are fully parallelizable — they read mapping guides (stable by this point) and write independent JSON files
- Single-agent generation works reliably for practices of any size (>100KB included) — the Parallel Section Strategy is optional complexity
- Use `fix-common-issues.py --all --fix` with baseline arg to catch unknown activity spaces, self-referencing backgrounds, invalid narrative types, and invalid competency refs post-generation
- Phase 3 agents should auto-detect the schema version from `deps/language.schema.json` rather than being told a specific version
- Phase 3 agents commonly invent competency names, competency levels, and narrative type names instead of using baseline values — always run `--all` post-generation to catch these
- When effective context is generated before dependency practices are regenerated, dependent practices may reference stale alpha/state names — regenerate effective context after dependencies complete

## User Interaction

- **Start:** Read existing JSON + baseline, run assessment
- **Present:** Assessment results, recommended mode, ask user to choose
- **Progress:** Brief updates during phases
- **Completion:** Comparison report (what changed, what preserved, validation summary)

**Backup:** Always run `python3 utils/backup-practice.py <directory>/` before overwriting.

---

## Post-Update Validation

### Pre-Validation Completeness Gate

Before running the eval harness, verify that Phase 3 output did not drop any element arrays. This catches output truncation issues (e.g., agent hit output limits before generating personas/personaGroups):

```bash
python3 utils/diff-practice-json.py <backup-dir>/<name>.json <dir>/<name>.json --gate
```

**If gate fails:** See the mode-specific Step 2D instructions for recovery patterns. Do NOT proceed to eval until the gate passes.

### Eval Harness

After the completeness gate passes, run the eval harness to confirm clean state:

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

### Citation URL Validation

After the eval harness passes, test citation URLs for reachability:

```bash
python3 utils/fix-citation-urls.py <dir>/<name>.json
```

**If broken URLs are found (exit code 1):**
1. Try to find a corrected URL (search for the citation title/source)
2. If a replacement exists: `python3 utils/fix-citation-urls.py <file>.json --fix --replace "old-url=new-url"`
3. If no replacement exists: `python3 utils/fix-citation-urls.py <file>.json --fix` (removes the broken URL field, preserves the citation)
4. If the citation is no longer valid at all: `python3 utils/fix-citation-urls.py <file>.json --fix --remove-citations` (removes entire citation and all citationNames references)

### ChangeRequest Generation (MANDATORY)

After any update that modifies a practice/baseline/method JSON, generate a ChangeRequest capturing the delta between the backup version and the updated version. ChangeRequests enable automatic downstream propagation of renames and structural changes via `apply-change-request.py`.

**When to generate:**
- **Mode 1 (Full Reanalysis):** Always — content is reworked from source
- **Mode 1B (Light Reanalysis):** Always — analysis content is reworked within scope
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

### Post-Update Cross-Method Sync

After version bump and rebundling, sync updated practices to all consuming methods:

```bash
# Show what would be synced (dry run)
python3 utils/sync-practices.py practices/<method>/

# Apply sync and rebuild affected bundles
python3 utils/sync-practices.py practices/<method>/ --fix --rebuild-bundles
```

This scans all `practices/*/` directories for JSON files with matching `name` fields, compares versions (semver), and copies newer files to targets — preserving target filenames (handles cases like `build-run-applications.json` → `build-and-run-applications.json`).

**Ensure versions are ahead of all copies** (e.g., after branched versions were created):
```bash
# Show current versions across all copies
python3 utils/apply-versioning.py --show --dir practices/<method>/

# Bump to be ahead of all copies
python3 utils/apply-versioning.py --dir practices/<method>/ --ahead-of-copies --fix
```

**Find which methods consume a specific practice:**
```bash
python3 utils/discover-dependencies.py --consumers "Practice Name"
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
| 7 | Add Gherkin guidance | Remap (Mode 2) | Read semantics/practice-elements.md §5.3, semantics/execution-and-patterns.md §8.1.1; add background/test/examples |
| 8 | Convert to .keleo package | Packaging only | `package-keleo.py --from-embedded` or `--documents` |
| 9 | Add/update references | Mode 3 | Map to alpha+state, require ≥1 link per reference |
| 10 | Add/convert WP partOf/mapsTo | Targeted transform | `transform-workproducts.py --spec '[...]' --fix` |
| 11 | Batch WP partOf→mapsTo | Targeted transform | `transform-workproducts.py` — set `setMapsTo`, `lodMap`, `rename` |
| 12 | Add/update outcomes | Remap (Mode 2) | Add 1-3 outcomes with measureDescription + metricContributions or objectiveContributions |
| 13 | Criteria-style checklists | Remap (Mode 2) | Rewrite checklist names from past-participle criteria to imperative verb phrases; add test completion criteria where missing |
| 14 | Source material updated (specific chapter/edition) | Light Reanalysis (Mode 1B) | Scope to affected sections, provide updated source URLs |
| 15 | Skill/language changes affecting specific elements | Light Reanalysis (Mode 1B) | Scope to affected element types (concerns, activities, etc.) |
| 16 | User-identified gaps in analysis quality | Light Reanalysis (Mode 1B) | Scope to weak sections, describe what's missing |

**Scenario 8 details** (packaging-only — most common standalone use):
- Embedded method: `package-keleo.py --from-embedded <method>.json --baseline <baseline>.json -o bundles/<name>.keleo --verify`
- Standalone practice: resolve deps first (`discover-dependencies.py --resolve-from <practice>.json --transitive`), then `package-keleo.py --documents <baseline>.json [<deps>...] <practice>.json -o bundles/<name>.keleo --verify`

**Scenario 10/11 key rules**: `mapsTo` and `partOf` are mutually exclusive. `mapsTo` requires identical LOD names. `mapsTo` variant names omit parent type.

---

---

## Feature: Update Process Integrity

Validates that the update workflow follows correct assessment-first, backup-safe patterns.

### Scenario: Assessment before update (@rule:process-401)
- Given: An existing JSON file is provided for update
- When: The update workflow begins
- Then: assess-practice.py is run first to determine suggestedUpdateMode
- And: The update mode is auto-fix, remap, light-reanalysis, or full-reanalysis based on assessment output

### Scenario: Backup before overwrite (@rule:process-402)
- Given: The update will overwrite existing files
- When: Any mode (auto-fix, remap, light-reanalysis, or full-reanalysis) begins
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
- Given: A remap, light-reanalysis, or full-reanalysis update has completed
- When: The new JSON is generated
- Then: diff-practice-json.py shows what changed vs the original
- And: The user sees added, removed, and modified elements

### Scenario: User confirms update mode when auto-fix insufficient (@rule:process-408)
- Given: Assessment shows non-auto-fixable issues
- When: Step 1B presents mode options
- Then: The user is asked to choose between remap, light-reanalysis, and full-reanalysis
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

### Scenario: Content preservation during light reanalysis (@rule:process-412)
- Given: The update uses light reanalysis mode (Phase 1B → 2 → 3)
- When: Sections are classified as PRESERVE or UPDATE based on user scope
- Then: PRESERVE sections appear verbatim in the updated analysis report
- And: UPDATE sections retain valid existing entries as baseline
- And: New content is traceable to source materials or the stated change context

## Key Principles

1. **Automate First** — Use `assess-practice.py` and fix utilities before asking the user anything. Only prompt when auto-fix is insufficient.
2. **No Inline Scripts** — All programmatic actions use reusable scripts in `utils/`, never `python3 -c` or `bash -c`. **Canonical registry:** `utils/README.md` — read this for the full, current list of all utilities. Run `python3 utils/<script>.py --help` for detailed usage.
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
