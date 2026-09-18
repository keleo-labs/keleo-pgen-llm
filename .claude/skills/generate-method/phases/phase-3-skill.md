# Phase 3: JSON Generation — Subagent Skill

## Context

You are a subagent executing **Phase 3: JSON Generation** of the Practice Language code generation pipeline. You take the Phase 2 mapping guide and produce schema-compliant Practice JSON, then fix, validate, and package the output.

You operate within Claude Code and have access to Read, Write, Edit, and Bash tools. You write ONE output file — never intermediate fragments.

## Inputs (provided by orchestrator)

The orchestrator provides these in your launch prompt:

| Input | Description |
|---|---|
| `practiceName` | Name of the practice to generate |
| `practiceDir` | Directory containing `01-analysis-report.md` and `02-mapping-guide.md` |
| `effectiveContextPath` | Path to `_effective-context.json` (or leaf baseline if no dependencies) |
| `leafBaselinePath` | Path to leaf baseline JSON (for validation — NOT the effective context) |
| `schemaPath` | Path to `deps/language.schema.json` |
| `baselinePracticeName` | Value for `baselinePracticeName` property |
| `practiceDependencyNames` | Array of parent practice names (may be empty) |
| `isParentPracticeMode` | Whether extending a parent practice (affects `contributesTo`/`mapsTo` targets) |
| `hasAliasContext` | Whether effective baseline has `_aliasContext` (all structural refs must use canonical names) |

## Reading Plan

Read resources in this order. Do NOT read all at once — read each at the step that needs it.

### Step 1: Read Mapping Guide

Read `<practiceDir>/02-mapping-guide.md` in full. This is your PRIMARY source for all content. Every element in the output JSON must trace to this document.

Understand the mapping guide structure:
- **Practice skeleton** (metadata, description, keywords, tags)
- **Terminology / Aliases** section -> `practiceElementAliases` array
- **Alpha Mappings** -> `alphas` array (new alphas with `contributesTo`/`mapsTo`, redeclared alphas with enriched checklists)
- **Work Product Mappings** -> `workProducts` array
- **Persona Mappings** -> `personas` and `personaGroups` arrays
- **Activity Mappings** -> `activities` array
- **Pattern Mappings** -> `patterns` array (lifecycle orchestrations)
- **Pattern Group Mappings** -> `patternGroups` array (if present)
- **Outcome Mappings** -> `outcomes` array
- **Reference Content Mappings** -> `references` array (if present)
- **Citation Mappings** -> `citations` array
- **Acknowledgement Mappings** -> `acknowledgements` array (if present)
- **Narrative Mappings** -> `narratives` on elements and at practice level

### Step 2: Read Schema and Extract Versions

1. Read `deps/language.schema.json` — this is the **authoritative source** for ALL JSON structure questions. When uncertain about property names, types, or required fields, consult the schema directly.

2. Extract schema version and baseline version:
   ```bash
   python3 utils/extract-reference-names.py deps/language.schema.json --metadata
   python3 utils/extract-reference-names.py <leafBaselinePath> --metadata
   ```
   - `schemaVersion`: from schema `$comment` field (e.g., `"schemaVersion:2.13.0"` -> `"2.13.0"`)
   - Baseline `version`: for `dependencyVersions` caret range

3. Extract valid baseline names for competencies and narrative types:
   ```bash
   python3 utils/extract-reference-names.py <effectiveContextPath> --sections competencies narrativeTypes
   ```
   Keep these lists visible — every competency and narrative type reference in the output MUST match these exactly.

### Step 3: Read Semantic Guidance (selective)

Read only the sections relevant to your generation work:

- `references/semantics/practice-elements.md` — Section 5: checklist format rules, tagging taxonomy, Gherkin-inspired structure (background, test, examples)
- `references/semantics/execution-and-patterns.md` — Sections 8-9: activity structure, pattern view compression rules, outcome structure and forecastWeights
- `references/semantics/work-products.md` — Section 7: LOD naming conventions, `partOf`/`mapsTo` rules, `expectedMetrics`
- `references/semantics/narrative-and-assets.md` — Sections 10-11: narrative structure, citation format, asset definitions

Read these for guidance — do NOT copy their content into the JSON.

## Step 4: Generate Practice JSON

Write the complete JSON to `<practiceDir>/<practiceName>.json`.

**Build in this order** to ensure dependencies are met:

### 4.1 Root Skeleton

```json
{
  "kind": "practice",
  "name": "<practiceName>",
  "description": "Single sentence from mapping guide",
  "schemaVersion": "<from Step 2>",
  "version": "1.0.0",
  "baselinePracticeName": "<baselinePracticeName>",
  "practiceDependencyNames": ["<from orchestrator>"],
  "dependencyVersions": [
    {"documentName": "<baselinePracticeName>", "versionRange": "^<baseline version>"}
  ],
  "tags": {
    "domainTags": [],
    "lifecycleTags": [],
    "organizationalTags": []
  },
  "keywords": [],
  "authors": [],
  "createdAt": "YYYY-MM-DD",
  "updatedAt": "YYYY-MM-DD"
}
```

**Versioning rules:**
- `schemaVersion`: from schema `$comment` (Step 2). Always set.
- `version`: `"1.0.0"` for new documents. Three-part semver.
- `dependencyVersions`: one entry per dependency name (`baselinePracticeName` + each `practiceDependencyNames` entry). Use caret range `^X.Y.Z` pinned to the dependency's current `version`.

**Parent practice mode:**
- `baselinePracticeName`: inherited from parent practice (NOT the parent practice name itself)
- `practiceDependencyNames`: only parent practices whose unique alphas are actually referenced (see "Determining practiceDependencyNames" section below)
- `dependencyVersions`: entries for BOTH baseline AND each practice dependency

### 4.2 Citations

```json
"citations": [
  {
    "name": "Exact source title",
    "description": "1 sentence summary",
    "authors": ["Author 1"],
    "date": "YYYY",
    "source": "Publisher",
    "url": "https://..."
  }
]
```

- `name` MUST be the **work title** (e.g., "Team Topologies"), NOT author-date format ("Skelton (2019)")
- `url` SHOULD be populated — carry forward from mapping guide
- Citations have NO `narratives` property

### 4.3 Acknowledgements (if present in mapping guide)

```json
"acknowledgements": [
  {"name": "Person or Institution", "description": "Contribution", "url": "https://..."}
]
```

### 4.4 Assets

Define font-character icons, external URL assets, or bundled files. See schema `$defs/Asset` for exact properties by type. Priorities: font-character > external URL > bundled file.

Elements reference assets via `assetNames` array of `{assetName, type}` objects.

### 4.5 Practice-Level Narratives

```json
"narratives": [
  {
    "name": "Narrative Name",
    "narrativeTypeName": "<EXACT baseline narrative type name>",
    "description": "Purpose",
    "narrativeContexts": [
      {"seq": 1, "narrativeElementName": "<element from NarrativeType>", "context": "1-2 sentences"}
    ],
    "citationNames": ["<exact citation name>"]
  }
]
```

### 4.6 Alphas

Translate each alpha from the mapping guide.

**New alphas** (specializations or variants):
- MUST have `contributesTo` (specialization — different states from parent) OR `mapsTo` (variant — exact same states as parent), or both on different targets
- MUST have `relatesTo` array with `direction` on every entry
- `mapsTo` alphas: states MUST exactly match target alpha (same names, same sequence)

**Redeclared alphas** (enriching baseline alphas):
- MUST NOT have `contributesTo`, `mapsTo`, or `relatesTo`
- MUST include ALL states from baseline — never subset to only enriched states
- Copy baseline state `name` and `description` VERBATIM — do not rephrase
- Add checklists ONLY to states the mapping guide explicitly enriches
- Unenriched states: include with empty `"checklist": []`

**Checklist items** (on alpha states AND work product LODs — same schema type):
- Objects `{name, description, seq}`, NEVER strings
- `name`: imperative verb phrase ("Define key metrics" not "Metrics defined")
- `description`: must add information beyond the name (rationale, scope, method)
- Positive/additive only — never describe absence ("Define key metrics" not "Metrics absent")
- No meta-items referencing other checklist items ("All requirements met" is circular)
- `priority` (optional): `"should"` or `"could"` per `references/semantics/practice-elements.md` §5.2.2. Omit for essential items (defaults to `"must"`). Only emit the field when the mapping guide marks an item as deferrable or supplementary.
- `test` (optional): `{name, description, given[], when[], then[]}` — completion criteria. `then` must be independently observable evidence, not the description in past tense. Omit test entirely if given/when would be empty.
- `examples` (optional): array of Test objects for concrete scenarios
- `evidencedBy` (optional): array of `{workProductName, levelOfDetailName}`

**State `background`** (optional):
- Object with optional `given[]`, `alphaStates[]`, `workProductLevels[]`
- NEVER reference previous state of the SAME alpha (sequential progression is implicit)
- NEVER reference previous LOD of the SAME work product
- Only cross-element dependencies

### 4.7 Work Products

```json
{
  "name": "Work Product Name",
  "description": "Single sentence",
  "contributesToAlphaNames": ["Alpha 1"],
  "expectedMetrics": [{"name": "metric-name", "description": "...", "unit": "USD"}],
  "partOf": "Parent WP Name",
  "mapsTo": "Parent WP Name",
  "levelsOfDetail": [
    {
      "name": "Level Name",
      "description": "Max 12 words",
      "seq": 1,
      "checklist": [{"name": "...", "description": "...", "seq": 1}],  // same Checklist rules as alpha states (§4.6) — including optional priority
      "contributesTo": [{"alphaName": "Alpha", "stateName": "State"}]
    }
  ]
}
```

- LOD names describe **document fidelity/depth** (what the artifact looks like), NOT concern lifecycle. Use `references/workproduct-assessment-rubric.csv` as the naming lens.
- NO "Level X:" prefixes on LOD names
- `contributesTo` is REQUIRED on every LOD
- `partOf` and `mapsTo` are mutually exclusive — never both on same WP
- `mapsTo` WPs: LODs MUST exactly match target (same names, same sequence)
- `expectedMetrics`: declare when outcomes reference this WP via `metricContributions`

### 4.8 Personas and Persona Groups

**Personas:**
- Property is `competencies` (NOT `requiredCompetencies`)
- Format: `{competencyName, competencyLevelName}` (NOT `{competencyName, level}`)
- Use EXACT baseline competency names and level names

**Persona Groups:**
- `personaNames`: array of persona name strings
- Include asset icons for both personas and groups

### 4.9 Activities

```json
{
  "name": "Specific Activity Name",
  "description": "Single sentence",
  "activitySpaceName": "Baseline Activity Space",
  "focusName": "Value | Solution | Endeavor",
  "contributesTo": [{"alphaName": "...", "stateName": "..."}],
  "worksOn": [{"workProductName": "...", "levelOfDetailName": "..."}],
  "requiredCompetencies": ["Competency Name"],
  "recommendedCompetencyLevels": [{"competencyName": "...", "competencyLevelName": "..."}],
  "involves": ["Persona Group Name"],
  "ledBy": "Persona Name"
}
```

- Activity `name` MUST differ from `activitySpaceName`
- BOTH `requiredCompetencies` (string[]) AND `recommendedCompetencyLevels` (object[]) are required
- `involves` is `string[]` of persona group names, NOT an array of objects
- `ledBy` is optional — single Persona.name string
- Activities do NOT have `seq` or `citationNames`
- `focusName` is required

### 4.10 Patterns

```json
{
  "name": "Pattern Name",
  "narrativeTypeName": "Hero's Journey",
  "patternViews": [
    {
      "name": "Phase Name",
      "description": "Max 12 words",
      "seq": 0,
      "alphaStates": [{"alphaName": "...", "stateName": "..."}],
      "workProductLevels": [{"workProductName": "...", "levelOfDetailName": "..."}],
      "activities": ["Activity Name"],
      "narrativeContexts": [{"seq": 1, "narrativeElementName": "...", "context": "..."}]
    }
  ]
}
```

- Use `patternViews` NOT `views`
- Use `alphaStates` NOT `alphas`
- NO `workProducts` property on PatternView — use `workProductLevels`
- `activities` are string names, not objects
- Each alpha at most 1 state per PatternView — split to sub-views if needed
- **State compression:** Non-final views include ONLY alpha states that CHANGE from previous view. FINAL view MUST include ALL alphas as complete end-state snapshot.
- `PatternView.seq` is REQUIRED (0 for prerequisites, 1+ for main phases)

### 4.11 Pattern Groups (if present in mapping guide)

- Use exact baseline group name as merge key
- Only emit groups with patterns assigned (not empty baseline groups)
- `patternName` must match a defined Pattern.name exactly
- Include narratives when mapping guide provides group-level rationale

### 4.12 Outcomes

```json
{
  "name": "Outcome Name",
  "description": "Value this practice delivers",
  "measureDescription": "How success is measured",
  "metricContributions": [...],
  "objectiveContributions": [
    {
      "patternName": "Pattern Name",
      "recognizedAtPatternViewName": "Final View",
      "forecastWeights": [
        {"patternViewName": "Foundation", "weight": 0.25},
        {"patternViewName": "Final View", "weight": 1.0}
      ]
    }
  ]
}
```

- 1-3 outcomes per practice
- Every outcome MUST have at least one of `metricContributions` or `objectiveContributions`
- `measureDescription` is always required
- Every `objectiveContribution` MUST have `patternName`
- `recognizedAt` entry MUST have weight 1.0 in forecastWeights
- Omit empty arrays entirely (not `"metricContributions": []`)
- At least one outcome SHOULD use `objectiveContributions` tied to the main lifecycle pattern

### 4.13 References (if "Reference Content Mappings" section exists in mapping guide)

Each reference is an `AlphaInstance` with at least one `links` entry. References must be actionable (templates, examples, artifacts) — not documentation.

- Every reference MUST have at least one `links` entry with valid `uri`
- Use `pages` on links when content is at a specific location within a larger document
- `evidenceBy` entries are full WorkProductInstance objects with `name`, `description`, `workProductName`, `levelOfDetailName`, and `links`
- Same-name instances at different states/LODs: merge (keep highest, aggregate links)

### 4.14 Aliases

```json
"practiceElementAliases": [
  {
    "practiceElementType": "Alpha",
    "practiceElementName": "Canonical Name",
    "aliasName": "Source Term"
  }
]
```

- Do NOT re-declare aliases from parent/dependency practices
- Do NOT reuse a dependency alias name for a different target
- Only create aliases for elements this practice defines or redefines

### 4.15 Method Packaging (methods only)

For methods with multiple practices:

1. Generate each practice as a standalone JSON file with `"kind": "practice"`
2. The method uses externalized references:
   ```json
   {
     "kind": "method",
     "name": "Method Name",
     "baselinePracticeName": "...",
     "practiceNames": ["Practice 1", "Practice 2"],
     "citations": [],
     "narratives": []
   }
   ```
3. `practiceNames` and `baselinePracticeName` are strings, not embedded objects
4. Method packaging is handled by `utils/package-keleo.py` with `--method-name` flag

### 4.16 Completeness Check

Before proceeding to fix/validate, verify ALL sections are present:

- `kind`, metadata, tags, keywords
- `citations` array
- `narratives` (practice-level)
- `alphas` array
- `workProducts` array
- `personas` array
- **`personaGroups` array** (often missed)
- `activities` array
- `patterns` array (minimum 1 pattern, 2+ views)
- `outcomes` array (1-3)
- `references` array (if mapping guide has Reference Content Mappings)
- `practiceElementAliases` array
- `acknowledgements` (if mapping guide has them)
- `assets` array

Empty arrays `[]` are valid except: patterns MUST have minimum 1 pattern.

## Step 5: Fix and Validate

### 5.1 Unified Lint Pipeline (preferred)

```bash
python3 utils/lint-practice.py <practice>.json [<leafBaseline>.json] [<schema>.json] --fix
```

This runs the full fix-then-validate pipeline in one command.

### 5.2 Individual Fix Tools (when targeted intervention is needed)

Run auto-fixers first, then validate:

```bash
# Fix common structural issues (assets, pattern compression, narrative structure)
python3 utils/fix-common-issues.py <practice>.json <leafBaseline>.json --fix --all

# Fix competency name/level mismatches against baseline
python3 utils/fix-competency-levels.py <practice>.json <leafBaseline>.json --fix

# Validate (always pass leaf baseline, NOT effective context)
python3 utils/validate-practice-json.py <practice>.json <leafBaseline>.json deps/language.schema.json
```

The validator auto-discovers `_effective-context.json` in the practice directory for cross-practice element resolution.

### 5.3 Targeted Alpha Fixes

```bash
# Add missing baseline alpha redeclaration
python3 utils/fix-alpha-refs.py <practice>.json <leafBaseline>.json --add-redeclaration "Alpha Name" --fix

# Remap references from one alpha to another
python3 utils/fix-alpha-refs.py <practice>.json <leafBaseline>.json --remap "Old" "New" --state-map '{"OldState":"NewState"}' --fix
```

### 5.4 Quick Assessment

```bash
# Quick error check (add --parent for each practiceDependencyNames entry)
python3 utils/assess-practice.py <practice>.json --baseline <leafBaseline>.json --errors-only [--parent <dep>.json ...]
```

### 5.5 Iterate Until Clean

1. Read validation output — categorize errors as schema, baseline, or integrity
2. Apply fixes (schema violations and baseline references are often auto-fixed)
3. Re-validate
4. Repeat until 0 errors

**NEVER re-run `resolve-context.py` during fix iterations** — the `_effective-context.json` was generated once by the orchestrator in Step 0.5. Re-running it after the practice JSON exists may include the practice itself, corrupting the context.

### 5.6 Validation Error Guide

| Category | Examples | Fix Approach |
|---|---|---|
| **Schema** | Wrong property names, type errors, missing required fields, unevaluated properties | Edit JSON directly; often auto-fixed by `fix-common-issues.py` |
| **Baseline** | Invalid competency names, invalid state names, floating alphas | Use exact baseline names from Step 2 extraction; add `contributesTo`/`mapsTo` |
| **Integrity** | Broken WP/activity/alpha cross-references | Fix symbolic references to match defined element names |

## Step 6: Package

### 6.1 Resolve Transitive Dependencies

```bash
python3 utils/discover-dependencies.py --resolve-from <practiceDir>/<practiceName>.json --transitive
```

Collect the full list of resolved dependency file paths.

### 6.2 Package into .keleo

```bash
python3 utils/package-keleo.py \
  --name "<practiceName>" \
  --version "1.0.0" \
  --description "<practice description>" \
  --documents <leafBaseline>.json \
              [<transitive-dep-1>.json] \
              [<transitive-dep-2>.json] \
              <practiceDir>/<practiceName>.json \
  -o bundles/<practiceName>.keleo \
  --verify
```

- List dependencies in topological order (baselines first, practices in dependency order, entry-point practice last)
- NEVER use `_effective-context.json` as a document — it is a build artifact, not a distributable document
- The `--verify` flag lists package contents inline
- The packager auto-reads `schemaVersion` from schema and auto-builds package dependencies from document `dependencyVersions`

### 6.3 Method Packaging (methods only)

```bash
python3 utils/package-keleo.py \
  --name "<methodName>" \
  --version "1.0.0" \
  --description "<method description>" \
  --documents <baseline>.json \
              [<deps>...] \
              <practiceDir>/practice-1.json \
              <practiceDir>/practice-2.json \
  --method-name "<Method Name>" \
  --method-description "<method description>" \
  --method-narrative-file <practiceDir>/_method-narrative.json \
  -o bundles/<methodName>.keleo \
  --verify
```

## Determining practiceDependencyNames

**Rule:** Declare a dependency on a parent practice ONLY when the generated practice references alphas that originate from that parent practice (not from the baseline).

**Algorithm (after JSON generation):**

1. **Collect all alpha references:**
   - `contributesTo`/`mapsTo` targets from new alphas
   - Names of all redeclared alphas (alphas without `contributesTo`/`mapsTo`)
2. **Filter out practice-local targets** (alphas defined within the same practice)
3. **For each remaining reference**, classify using `_effective-context.json`:
   - Check the alpha's `_contributingPracticeName` against `_provenance.tiers`
   - **Baseline alpha** (source in `tiers.baselines`): no dependency created
   - **Practice-only alpha** (source in `tiers.practices`): creates dependency on that contributing practice
4. **Set `practiceDependencyNames`** to the deduplicated list of contributing practices. If all referenced alphas trace to baselines, set to `[]`.

**Verification:**
```bash
python3 utils/resolve-practice-dependencies.py \
  --parent _effective-context.json \
  --baseline <leafBaseline>.json \
  --practice <practice>.json \
  --per-alpha
```

**Why this matters:** Blindly including all parent practice names inflates the dependency graph. A practice that only contributes to baseline alphas has no structural dependency on parent practices that merely redeclare those same alphas.

## Output Format

| Output | Path | Description |
|---|---|---|
| Practice JSON | `<practiceDir>/<practiceName>.json` | Intermediate — complete schema-compliant JSON |
| `.keleo` package | `bundles/<practiceName>.keleo` | Primary deliverable — ZIP with manifest + documents |

Write ONE output JSON file. Never create intermediate fragment files (e.g., `_part1.json`).

## Common Mistakes

These are experience-based gotchas — the most frequent errors observed in Phase 3 output. Consult the schema for authoritative rules.

| # | Mistake | Correct Form |
|---|---|---|
| 1 | Missing `"kind": "practice"` at root | Always include the discriminator property |
| 2 | Checklist items as strings | Objects `{name, description, seq}` with optional `priority` |
| 3 | Competency refs as `{competencyName, level}` | `{competencyName, competencyLevelName}` — use baseline names exactly |
| 4 | `views` / `alphas` / `workProducts` on patterns | `patternViews` / `alphaStates` / `workProductLevels` |
| 5 | Missing `contributesTo` on LevelOfDetail | Required on every LOD |
| 6 | Pattern final view missing alphas from earlier views | Final view = complete end-state snapshot of ALL alphas |
| 7 | Inventing competency names not in baseline | Extract from baseline with `extract-reference-names.py --sections competencies` |
| 8 | Inventing narrative types not in baseline | Extract from baseline with `extract-reference-names.py --sections narrativeTypes` |
| 9 | Tags as flat array | Nested object `{domainTags, lifecycleTags, organizationalTags}` |
| 10 | `involves` as object array | `string[]` of persona group names |
| 11 | Negative/absence framing in checklists | Must be positive/additive achievements |
| 12 | Multiple output fragment files | Write ONE complete JSON file |
| 13 | Persona property `requiredCompetencies` | Property name is `competencies` |
| 14 | Missing `focusName` on activities | Required — derive from activity space focus |
| 15 | `assetNames` as singular string | Array of `{assetName, type}` objects |
| 16 | Redeclared alpha missing baseline states | Include ALL states, empty checklist for unenriched |
| 17 | Rephrasing baseline state descriptions | Copy baseline state `name` and `description` VERBATIM |
| 18 | `relatesTo` on redeclared alphas | Only new alphas get `relatesTo` — redeclarations inherit from baseline |
| 19 | Outcome without any contribution mechanism | Every outcome needs `metricContributions` or `objectiveContributions` |
| 20 | `objectiveContribution` missing `patternName` | Required — scopes view references to that pattern |
| 21 | Name collisions across element types | Names must be globally unique — disambiguate with suffixes |
| 22 | `background` referencing previous state of same alpha | Sequential progression is implicit — only cross-element deps |

## Tool Call Guidelines

- Use simple single-command Bash calls matching auto-approved patterns (`grep`, `wc`, `head`, `python3 utils/...`)
- Do NOT combine commands using variable assignments (`TARGET="..." && grep ...`) or shell loops
- NEVER use inline `python3 -c` scripts — use utility scripts only
- Make separate tool calls instead of compound commands

## Success Criteria

- Valid JSON syntax
- Schema validation: 0 errors
- Baseline validation: 0 errors
- Internal integrity: 0 errors
- All Phase 2 mappings present in JSON
- No floating alphas
- All symbolic references are exact case-sensitive matches
- No markdown or metadata in JSON strings
- `.keleo` package produced in `bundles/`
