---
name: translate-methodology
description: Transform enterprise methodology documentation into schema-compliant Practice Language JSON using a modular two-phase workflow
triggerPatterns:
  - "translate.*methodology"
  - "generate.*practice.*json"
  - "convert.*framework.*practice"
  - "methodology.*translation"
---

# Methodology Translation Skill (Modular)

This skill transforms enterprise methodology documentation into schema-compliant Practice Language JSON using a rigorous modular workflow that handles both single practices and multi-practice methods.

## Workflow Overview

**Phase 1:** Generate modular research documents (~3K-20K words each)  
**Phase 1.5:** Assemble and validate  
**Phase 2:** Incremental JSON translation from modules (with text cleaning)  
**Phase 2.5:** Schema compliance fixing (automatic property name corrections)  
**Phase 2.6:** Baseline reference validation (competency/state/alpha validation)  
**Phase 2.7:** Internal integrity validation (cross-reference verification)

**Handles:** Single Practice OR Multi-Practice Method

---

## Critical Process: ALWAYS Use EnterPlanMode

**MANDATORY FIRST STEP:** Before generating ANY modules, you MUST use EnterPlanMode to:

1. Analyze source materials
2. Determine if this is a Practice or Method
3. Plan the module generation sequence
4. Identify potential complexity (which modules might need splitting)
5. Create execution strategy

**Do NOT proceed without planning.**

---

## Directory Structure

### For Single Practice

```
practices/
└── <practice-name>/
    ├── report-elements/
    │   ├── 00-analysis-plan.md       (~3-5K words)
    │   ├── 01-practice-details.md    (~2-3K words)
    │   ├── 02-citations.md           (~1-2K words)
    │   ├── 03-alphas.md              (~15-20K words, may split by focus)
    │   ├── 04-workproducts.md        (~10-15K words)
    │   ├── 05-activities-roles.md    (~15-20K words, largest module)
    │   ├── 06-patterns.md            (~10-15K words)
    │   └── 07-aliases.md             (~0.5-1K words or "no aliases")
    ├── research-report.md            (assembled for human review)
    ├── cross-reference-index.json    (validation index)
    └── <practice-name>.json          (final output)
```

### For Method

```
practices/
└── <method-name>/
    ├── report-elements/
    │   ├── 00-method-plan.md         (~4-6K words)
    │   ├── practice-1/
    │   │   ├── 00-analysis-plan.md
    │   │   ├── 01-practice-details.md
    │   │   ├── 02-citations.md
    │   │   ├── 03-alphas.md
    │   │   ├── 04-workproducts.md
    │   │   ├── 05-activities-roles.md
    │   │   ├── 06-patterns.md
    │   │   └── 07-aliases.md
    │   ├── practice-2/
    │   │   └── [same structure]
    │   └── 08-method-assembly.md     (~3-5K words)
    ├── research-report.md
    ├── cross-reference-index.json
    └── <method-name>.json
```

---

## Execution Workflow

### Working with Existing Output

**If picking up from a previous session with existing generated content:**

Before continuing with module generation or moving to the next phase, you can review and correct existing content to align with current skill rules and best practices.

**Review and Correction Process:**

1. **Identify existing output:**
   - Check for `practices/<name>/report-elements/` directory
   - List existing modules
   - Check for `research-report.md` or JSON files

2. **Determine what to review:**
   - **Individual modules** - Review specific Phase 1 modules for conciseness, structure, content quality
   - **Assembled report** - Review `research-report.md` if it exists
   - **JSON output** - Review generated JSON for schema compliance, baseline references, internal integrity
   - **All content** - Comprehensive review of everything generated

3. **Apply current standards:**
   - **Conciseness**: Verify all descriptions are single grammatically correct sentences
   - **Narratives**: Check that additional context is in narrative sections, not bloated descriptions
   - **Checklist criteria**: Ensure alpha state checklists have 5-7 one-sentence criteria (not 10+ or paragraph-length)
   - **Work product LODs**: Verify 3-5 one-sentence characteristics per level
   - **Narrative length**: Ensure narratives are focused (2-5 paragraphs, 2-4 sentences each)
   - **Text cleaning**: Remove all markdown syntax and practice metadata from JSON content
   - **Subject matter focus**: Ensure descriptions focus on domain concepts, not documentation structure
   - **Alpha rules**: Verify no floating alphas (all new alphas have `contributesTo`)
   - **Baseline references**: Check exact name matching for competencies, states, alphas
   - **Schema compliance**: Verify property names match schema exactly

4. **Correction approach:**
   - **Read the existing content** using the Read tool
   - **Identify deviations** from current rules
   - **Edit or rewrite** the content to align with standards
   - **For modules**: Use Edit tool to fix specific sections
   - **For large rewrites**: May regenerate entire modules using current prompts
   - **For JSON**: Run correction scripts (Phase 2.5, 2.6, 2.7) or edit directly

5. **After corrections:**
   - If correcting Phase 1 modules: Consider regenerating `research-report.md` and `cross-reference-index.json` (Phase 1.5)
   - If correcting JSON: Re-run validation scripts
   - Resume normal workflow from appropriate step

**When to use this:**

- Skill guidance has been updated since previous session
- Previous session deviated from best practices
- User wants to ensure consistency with current standards
- Preparing final deliverables and want to polish existing content

**Example user requests:**

- "Review the existing practice-1 modules and fix any descriptions that aren't single sentences"
- "Check all the generated JSON and correct any baseline reference issues"
- "Review everything in practices/aws-well-architected/ and update to current standards"

---

### Step 1: EnterPlanMode

**YOU MUST DO THIS FIRST.**

In plan mode:

1. **Analyze source materials:**
   - Read all provided files/URLs
   - Assess scope and complexity
   - Apply four-perspective framework preview

2. **Determine structure:**
   - **Practice** if: Single cohesive value stream, one use case, unified stakeholder journey
   - **Method** if: Multiple distinct value streams, different use cases, separate practices needed

3. **Plan module generation:**
   - Estimate which modules might exceed 20K words (need splitting)
   - Identify module dependencies
   - Plan citation strategy
   - Determine alpha extension approach

4. **Create execution plan:**
   - Specific sequence of modules to generate
   - Whether to split large modules by focus
   - For Methods: list each practice and its scope

5. **Exit plan mode** with clear roadmap

### Step 2A: Generate Practice Modules (Single Practice)

**Determine practice name early** (kebab-case).

**Create directory:**

```bash
mkdir -p practices/<practice-name>/report-elements
```

**Generate modules sequentially:**

Each module references prompts in `prompts/phase-1-modules/`

1. **Module 00:** `00-analysis-plan.md`
   - **Prompt:** Read and apply `prompts/phase-1-modules/00-analysis-plan.md`
   - **Output:** `practices/<practice-name>/report-elements/00-analysis-plan.md`
   - **Creates:** Strategic plan, alpha extension decisions, activity derivation plan

2. **Module 01:** `01-practice-details.md`
   - **Prompt:** Read and apply `prompts/phase-1-modules/01-practice-details.md`
   - **Output:** `practices/<practice-name>/report-elements/01-practice-details.md`
   - **Creates:** Practice metadata, tags, overview, context narratives
   - **CRITICAL REQUIREMENT:** MUST include at least one narrative summarizing the practice's intent and objective using a baseline narrative template (STAR, Hero's Journey, Three-Act Structure & StoryBrand, ABT, Essay, Epic, Report, etc.)

3. **Module 02:** `02-citations.md`
   - **Prompt:** Read and apply `prompts/phase-1-modules/02-citations.md`
   - **Output:** `practices/<practice-name>/report-elements/02-citations.md`
   - **Creates:** 5-15 authoritative citations in APA7 format

4. **Module 03:** `03-alphas.md`
   - **Prompt:** Read and apply `prompts/phase-1-modules/03-alphas.md`
   - **Output:** `practices/<practice-name>/report-elements/03-alphas.md`
   - **Creates:** All alpha definitions, states, checklists, instances
   - **If too large:** Split into 03a-alphas-value.md, 03b-alphas-solution.md, 03c-alphas-endeavor.md

5. **Module 04:** `04-workproducts.md`
   - **Prompt:** Read and apply `prompts/phase-1-modules/04-workproducts.md`
   - **Output:** `practices/<practice-name>/report-elements/04-workproducts.md`
   - **Creates:** Work product definitions with LODs, instances

6. **Module 05:** `05-activities-roles.md`
   - **Prompt:** Read and apply `prompts/phase-1-modules/05-activities-roles.md`
   - **Output:** `practices/<practice-name>/report-elements/05-activities-roles.md`
   - **Creates:** Activities with rich technique narratives, personas, teams
   - **Note:** This is typically the largest module due to technique narratives

7. **Module 06:** `06-patterns.md`
   - **Prompt:** Read and apply `prompts/phase-1-modules/06-patterns.md`
   - **Output:** `practices/<practice-name>/report-elements/06-patterns.md`
   - **Creates:** Pattern definitions with views, instance tracking

8. **Module 07:** `07-aliases.md`
   - **Prompt:** Read and apply `prompts/phase-1-modules/07-aliases.md`
   - **Output:** `practices/<practice-name>/report-elements/07-aliases.md`
   - **Creates:** Terminology mappings or "no aliases" note

### Step 2B: Generate Method Modules (Multi-Practice)

**Determine method name early** (kebab-case).

**Create directory:**

```bash
mkdir -p practices/<method-name>/report-elements
```

**Generate method planning:**

1. **Module 00:** `00-method-plan.md`
   - **Prompt:** Read and apply `prompts/phase-1-modules/00-method-plan.md`
   - **Output:** `practices/<method-name>/report-elements/00-method-plan.md`
   - **Creates:** Method overview, practice composition plan, integration strategy

**For EACH practice:**

2. **Create practice directory:**

```bash
mkdir -p practices/<method-name>/report-elements/practice-<n>
```

3. **Generate practice modules 00-07** in `practice-<n>/` subdirectory:
   - Use same prompts as Step 2A
   - Output to practice-specific subdirectory
   - Each practice is self-contained

**After all practices:**

4. **Module 08:** `08-method-assembly.md`
   - **Prompt:** Read and apply `prompts/phase-1-modules/08-method-assembly.md`
   - **Output:** `practices/<method-name>/report-elements/08-method-assembly.md`
   - **Creates:** Integration layer, method-level patterns, adoption guidance

### Step 3: Phase 1.5 - Assembly and Validation

**Prompt:** Read and apply `prompts/phase-1-assembly.md`

**Process:**

1. Determine structure type (Practice vs Method)
2. Assemble all modules into `research-report.md`
3. Generate `cross-reference-index.json` from modules
4. Run validation checks
5. Report any critical errors

**Outputs:**
- `practices/<name>/research-report.md` - Complete human-readable report
- `practices/<name>/cross-reference-index.json` - Validation index for Phase 2

**Quality Gate:**
- If validation passes: Proceed to Phase 2
- If critical errors: Report and await fixes

### Step 4: Phase 2 - Segmented JSON Generation

**NEW APPROACH (2026-05-21):** Generate JSON in **segments** to avoid token limits, then assemble.

**Why Segmented:** Monolithic generation (100KB JSON in one go) exceeds agent token limits for large practices. Segmented approach generates one small JSON file per Phase 1 module, then assembles mechanically.

**Process:**

#### Step 4.1: Generate JSON Segments

**CRITICAL REQUIREMENT:** ALL segments MUST comply with schema specifications.

**Before generating ANY segment:**
1. Read `/deps/language.schema.json` for structure validation
2. Read `/references/semantics.md` for semantic guidance
3. Read `SEGMENT-SCHEMA-SPECS.md` (in skill directory) for complete specifications
4. Follow ALL schema requirements exactly

For each practice, generate 9 JSON segments (one per module):

1. **01-practice-skeleton.json** (from 01-practice-details.md)
   - Practice metadata, tags, authors, version
   - ~2KB output
   - **Format:** JSON object (NOT array)

2. **02-citations.json** (from 02-citations.md)
   - Array of Citation objects
   - ~3KB output
   - **Schema:** {name, description, authors[], date, source, url}
   - **CRITICAL:** Citations do NOT have narratives (metadata only)

3. **03-alphas.json** (from 03-alphas.md)
   - Array of Alpha objects with states, checklists, narratives
   - ~20-40KB output
   - **CRITICAL:** Checklist items MUST be objects {name, description, seq}, NOT strings
   - **CRITICAL:** New alphas MUST have contributesTo array
   - **CRITICAL:** Extract ALL narratives and state checklists

4. **04-workproducts.json** (from 04-workproducts.md)
   - Array of WorkProduct objects with LODs, checklists
   - ~15-25KB output
   - **CRITICAL:** Checklist items MUST be objects {name, description, seq}, NOT strings
   - **CRITICAL:** LevelOfDetail.contributesTo is REQUIRED (array of AlphaContribution)
   - **CRITICAL:** Extract ALL LOD checklists

5. **05-activities.json** (from 05-activities-roles.md - Activities section)
   - Array of Activity objects with technique narratives
   - ~15-20KB output
   - **CRITICAL:** Use {competencyName, competencyLevelName}, NOT {competencyName, level}
   - **CRITICAL:** Include BOTH requiredCompetencies (strings) AND recommendedCompetencyLevels (objects)
   - **CRITICAL:** Extract ALL "How to Perform" narratives

6. **05-personas.json** (from 05-activities-roles.md - Personas section)
   - Array of Persona objects with competencies
   - ~3-5KB output
   - **CRITICAL:** Property name is `competencies` NOT `requiredCompetencies`
   - **CRITICAL:** Use {competencyName, competencyLevelName} format
   - **CRITICAL:** Extract ALL competency requirements

7. **05-teams.json** (from 05-activities-roles.md - Persona Groups section)
   - Array of PersonaGroup objects with persona names
   - ~2KB output
   - **CRITICAL:** Extract ALL team member lists (personas array)

8. **06-patterns.json** (from 06-patterns.md)
   - Array of Pattern objects with pattern views
   - ~10-20KB output
   - **CRITICAL:** PatternView uses `alphaStates` NOT `alphas`
   - **CRITICAL:** PatternView.seq is REQUIRED
   - **CRITICAL:** NO `workProducts` property in PatternView (not in schema)
   - **CRITICAL:** activities are string names, not objects

9. **07-aliases.json** (from 07-aliases.md)
   - Array of PracticeElementAlias objects (or empty array if no aliases)
   - ~2KB output

**Save segments to:** `json-segments/practice-N/NN-*.json`

**Validation before saving ANY segment:**
- Run `jq empty <file>` to validate JSON syntax
- Verify all schema requirements met (see SEGMENT-SCHEMA-SPECS.md)
- Verify file size is within expected range

**Segment generation can be parallelized:** Spawn 9 agents simultaneously, one per segment.

#### Step 4.2: Assemble Practice JSON

Run assembly script:
```bash
python3 assemble-practice-json.py <practice-number>
```

**What assembly does:**
- Loads all 9 JSON segments
- Extracts instances from patterns (alphaInstances, workProductInstances)
- Merges into complete practice JSON structure
- Validates completeness
- Saves `practice-N-<name>.json`

**Output:** Complete practice JSON (80-120KB)

#### Step 4.3: Assemble Method JSON (for methods)

For multi-practice methods:
```bash
python3 rebuild-method-json.py
```

Combines all practice JSONs into method JSON.

**Output:** Complete method JSON with practices array

**Schema Compliance Resources:**

Before generating segments, agents must read:
1. `/deps/language.schema.json` - Authoritative schema definition
2. `/references/semantics.md` - Semantic guidance and operational architecture
3. `.claude/skills/translate-methodology/SEGMENT-SCHEMA-SPECS.md` - Complete segment specifications
4. `.claude/skills/translate-methodology/REGENERATE-FROM-SCRATCH-RULE.md` - When to regenerate vs refine

**Common Schema Violations to Avoid:**

1. **Checklist format** - MUST be objects with {name, description, seq}, NOT strings
2. **CompetencyLevelReference** - MUST use {competencyName, competencyLevelName}, NOT {competencyName, level}
3. **Persona property** - MUST be `competencies`, NOT `requiredCompetencies`
4. **Activity competencies** - MUST have BOTH `requiredCompetencies` (strings) AND `recommendedCompetencyLevels` (objects)
5. **PatternView properties** - MUST use `alphaStates` NOT `alphas`, MUST include `seq`, NO `workProducts` property
6. **LevelOfDetail.contributesTo** - REQUIRED field on all LOD objects
7. **Floating alphas** - All new alphas MUST have `contributesTo` array

**Critical Elements Assembly Handles:**

**PracticeElementAliases** (from segment 07):
- Assembly merges into practice root: `practice.practiceElementAliases[]`

**AlphaInstances** (extracted from pattern views):
- Assembly extracts from `patternView.alphaInstances[]` and merges to practice root

**WorkProductInstances** (extracted from pattern views):
- Assembly extracts from pattern views and merges to practice root

**Output:**
- `practices/<name>/<name>.json` - Schema-compliant Practice or Method JSON with complete element coverage

### Step 4.5: Phase 2 Completeness Validation

**AUTOMATIC STEP - RUN IMMEDIATELY AFTER PHASE 2**

After initial JSON generation, validate and fix content completeness by extracting ALL rich content from Phase 1 modules that may have been missed.

**What Gets Validated/Fixed:**

1. **Alpha narratives:** Extract "Context and Rationale" sections
2. **Alpha state checklists:** Extract criteria sections into Checklist objects
3. **Work product LOD checklists:** Extract criteria sections
4. **Activity narratives:** Extract "How to Perform" sections
5. **Persona competencies:** Extract "**Competencies:**" sections
6. **Team personas:** Extract "**Team Members:**" sections
7. **Pattern view content:** Extract alphas, workProducts, activities from view sections

**Process:**

1. **Run completeness fix script** in practice directory:
   ```bash
   python3 comprehensive-content-fix.py
   ```

2. **For Methods:** Rebuild after fixes:
   ```bash
   python3 rebuild-method-json.py
   ```

3. **Verify completeness:**
   ```bash
   jq '.alphas[0] | {name, hasNarrative: (.narratives | length > 0)}' <practice>.json
   jq '.activities[0] | {name, hasNarrative: (.narratives | length > 0)}' <practice>.json
   jq '.personas[0] | {name, hasCompetencies: (.requiredCompetencies | length > 0)}' <practice>.json
   ```

**Why This Step:**

Phase 2 translation focuses on structural extraction (names, descriptions, references). The comprehensive-content-fix.py script ensures NO rich content is missed by re-parsing modules specifically for:
- Narratives (Context, Rationale, How-To sections)
- Checklists (state criteria, LOD characteristics)
- Competencies (persona requirements)
- Team composition (persona memberships)
- Pattern orchestration (activities, alphas, work products per view)

**Quality Gate:**
- If script reports 0 changes: Phase 2 was complete
- If script reports changes: Review and apply fixes, then proceed
- Proceed to schema compliance fixing

**See Also:** `PHASE-2-COMPLETENESS-FIX.md` for detailed issue description and solution

### Step 5: Phase 2.5 - Schema Compliance Fixing

**AUTOMATIC STEP - RUN IMMEDIATELY AFTER COMPLETENESS VALIDATION**

After JSON generation, automatically fix property name mismatches to ensure schema compliance.

**Common Property Name Issues:**

Activities:
- `outcomes` → `contributesTo`
- `focus` → `focusName`
- `competencies` → `recommendedCompetencyLevels` + `requiredCompetencies`
- `personas` → `involves`
- `workProductsUsed` → `worksOn`

Patterns:
- `views` → `patternViews`
- `narrativeFramework` → `narrativeTypeName`
- Remove `type` (not in schema)

PatternViews:
- `activitiesEmphasized` → `activities`

**Process:**

1. **Create fix script** in the practice directory:
   - Copy `utils/fix-property-names.py` template to practice directory
   - OR use inline Python code to fix property names

2. **Run fixes** on individual practice files:
   ```bash
   python3 fix-property-names.py
   ```

3. **For Methods:** Rebuild method JSON after fixing practice files:
   ```bash
   python3 rebuild-method-json.py
   ```

4. **Verify fixes** by checking a few key properties:
   ```bash
   jq '.activities[0] | keys' <practice>.json  # Should show contributesTo, focusName, etc.
   jq '.patterns[0] | keys' <practice>.json    # Should show patternViews, narrativeTypeName
   ```

**Why This Step:**

The Phase 2 prompts may occasionally generate property names that don't exactly match the schema (e.g., using intuitive names like `outcomes` instead of the schema's `contributesTo`). This automated fix step ensures 100% schema compliance by:

1. Correcting all property names to match `deps/language.schema.json`
2. Adding required fields (like `requiredCompetencies`) that are derived from other fields
3. Removing non-schema fields (like `type` on Patterns)
4. Ensuring consistent naming across all generated JSON files

**Quality Gate:**
- Verify JSON syntax is still valid after fixes
- Spot-check that property names match schema
- Proceed to baseline validation

### Step 6: Phase 2.6 - Baseline Reference Validation

**AUTOMATIC STEP - RUN IMMEDIATELY AFTER PHASE 2.5**

After schema compliance fixes, validate all baseline practice references against `deps/platform-adoption-kernel.json` and fix incorrect references.

**What Gets Validated:**

1. **Competency Names** (8 canonical):
   - Analysis, Engineering, Leadership, Management
   - Platform Security And Compliance Enforcement
   - Platform Strategic Alignment
   - Site Reliability, Stakeholder Representation

2. **Alpha Names** (13 baseline + practice-defined)
   - Validates references in `contributesTo`
   - Allows practice-defined alphas

3. **State Names** (per alpha)
   - Validates state references against alpha definitions
   - Merges baseline + practice-defined states

4. **Focus Names** (3): Value, Solution, Endeavor

5. **ActivitySpace Names** (20 baseline)

**Common Issues Fixed:**

**Competency Descriptions → Names:**
- `"Machine Learning (model development...)"` → `"Engineering"`
- `"Model Risk Management (...)"` → `"Management"`
- `"Data Governance (...)"` → `"Management"`
- `"Regulatory Compliance (...)"` → `"Platform Security And Compliance Enforcement"`

**Invalid State Names:**
- `"Provisioned"` → `"Configured"` (Serving Runtime)
- `"Provisioned"` → `"Prepared"` (Work)
- `"In Use"` → `"Performing"` (Team)
- `"In Use"` → `"Satisfied in Use"` (Stakeholders)
- `"In Use"` → `"Available"` (Inference Endpoint)

**Process:**

1. **Copy validation script** to practice directory:
   ```bash
   cp ../../utils/validate-baseline-references.py .
   ```

2. **Run validation** on all practice files:
   ```bash
   python3 validate-baseline-references.py
   ```

3. **For Methods:** Rebuild after validation fixes:
   ```bash
   python3 rebuild-method-json.py
   ```

4. **Verify** all practices pass:
   ```bash
   python3 validate-baseline-references.py  # Should show 0 errors
   ```

**Why This Step:**

Phase 2 translation may generate:
- Competency descriptions instead of canonical names (from persona sections)
- State names that don't match alpha state definitions
- References using intuitive but non-canonical names

This step ensures 100% baseline compliance by:
1. Mapping competency descriptions to canonical names
2. Correcting state references to valid states
3. Validating all symbolic references are exact matches
4. Preserving practice-defined alpha extensions

**Quality Gate:**
- All competency references use canonical baseline names
- All state references exist in their target alphas
- All alpha/focus/activitySpace references are valid
- Proceed to internal integrity validation

### Step 7: Phase 2.7 - Internal Integrity Validation

**AUTOMATIC STEP - RUN IMMEDIATELY AFTER PHASE 2.6**

After baseline validation, verify all internal cross-references within the practice/method are valid.

**What Gets Validated:**

1. **Activity → Alpha/State References**
   - All `contributesTo` references point to existing alphas
   - All state names exist in their target alpha
   - Validates across all practices in a method

2. **Activity → Work Product References**
   - All `worksOn` references point to existing work products
   - Can reference work products from other practices

3. **Pattern View → Activity References**
   - All activities referenced in pattern views exist
   - Can reference activities from other practices

4. **Pattern View → Alpha/State References**
   - All alpha states in pattern views are valid
   - Validates against merged alpha definitions

**Element Index Built:**
- All alphas: baseline + practice-defined (with merged states)
- All work products across all practices
- All activities across all practices
- All patterns, personas, teams

**Process:**

1. **Copy validation script** to practice directory:
   ```bash
   cp ../../utils/validate-internal-integrity.py .
   ```

2. **Run validation** on method JSON:
   ```bash
   python3 validate-internal-integrity.py
   ```

3. **Review results:**
   - If 0 issues: Proceed to schema validation
   - If issues found: Review `INTERNAL-INTEGRITY-REPORT.md` and fix manually

**Why This Step:**

Phase 2 translation generates practices independently, which can result in:
- Activities referencing work products that don't exist
- Pattern views referencing activities from wrong practice names
- Broken cross-practice references in methods
- Invalid alpha/state references due to typos

This step ensures 100% internal consistency by:
1. Building complete element index across all practices
2. Validating every symbolic reference
3. Detecting broken cross-references
4. Generating detailed inventory report

**Quality Gate:**
- All activity → alpha/state references valid
- All activity → work product references valid
- All pattern view → activity references valid
- All pattern view → alpha/state references valid
- Proceed to schema validation

**Note on Fixing:**

Unlike Phases 2.5 and 2.6, internal integrity issues typically require manual review because:
- Missing work products may need to be created
- Wrong activity references need domain knowledge to correct
- Cross-practice references may indicate structural issues

The validation report provides detailed diagnostics to guide manual fixes.

---

## Python Utilities Reference

The translation workflow relies on these utilities in `utils/`:

### Core Validators (Run in Sequence)

**These utilities MUST be run in sequence - do not skip steps:**

1. **fix-property-names.py** - Auto-correct schema property names
   - **Phase:** 2.5
   - **Purpose:** Correct property name mismatches (e.g., `outcomes` → `contributesTo`)
   - **Usage:** `python3 fix-property-names.py` (auto-discovers JSON files)
   - **When:** Immediately after JSON generation

2. **rebuild-method-json.py** - Assemble method from practices (methods only)
   - **Phase:** 2.5b
   - **Purpose:** Combine individual practice JSON files into complete Method JSON
   - **Usage:** `python3 rebuild-method-json.py`
   - **When:** After Phase 2.5 fixes, before Phase 2.6 (methods only)

3. **validate-baseline-references.py** - Validate baseline references
   - **Phase:** 2.6
   - **Purpose:** Validate and auto-fix competency names, state names, alpha references
   - **Usage:** `python3 validate-baseline-references.py` (auto-discovers JSON files)
   - **When:** After Phase 2.5/2.5b, before Phase 2.7

4. **validate-internal-integrity.py** - Validate cross-references
   - **Phase:** 2.7
   - **Purpose:** Validate all internal cross-references, generate integrity report
   - **Usage:** `python3 validate-internal-integrity.py`
   - **When:** After Phase 2.6, before Phase 2.8
   - **Output:** `INTERNAL-INTEGRITY-REPORT.md` with detailed diagnostics

### QA Checkers (Run Before Finalization)

5. **check-floating-alphas.py** - Enforce contributesTo rule
   - **Purpose:** Ensure all new alphas have `contributesTo` relationships
   - **Usage:** `python3 check-floating-alphas.py <practice-or-method-file.json>`
   - **When:** Quality assurance check before publication
   - **Critical:** Floating alphas violate Practice Language semantics

6. **validate-cross-practice-integrity.py** - Multi-practice validation (methods)
   - **Purpose:** Validate cross-practice references in multi-practice methods
   - **Usage:** Run from method directory or repo root
   - **When:** For methods with multiple practices
   - **Differs from validate-internal-integrity.py:** Works with separate practice files

### Support Utilities

7. **module_validator.py** - Check module sizes for splitting
   - **Purpose:** Monitor module word counts, recommend splits
   - **Usage:** `python -m utils.module_validator`
   - **When:** After generating Phase 1 modules

8. **session_manager.py** - Checkpoint/resume support
   - **Purpose:** Save and restore translation progress
   - **When:** Long-running translations, recovery from interruptions

9. **citation_parser.py** - Parse citations from modules
   - **Purpose:** Extract citation metadata from Module 02
   - **Used by:** Phase 2 parsers during JSON translation

### Phase 2 Parsers (utils/phase2-parsers/)

**Modular Python parsers for translating Phase 1 markdown to JSON:**

- **alpha_parser.py** - Extract alphas, states, checklists
- **workproduct_parser.py** - Extract work products, LODs
- **activity_parser.py** - Extract activities, personas, teams
- **pattern_parser.py** - Extract patterns, views
- **alias_parser.py** - Extract terminology aliases
- **translate_practice.py** - Orchestrator script that uses all parsers

**Example usage:**
```bash
python translate_practice.py \
  ../../practices/my-practice/report-elements/ \
  ../../deps/platform-adoption-kernel.json \
  ../../practices/my-practice/practice.json
```

### Complete Documentation

See [utils/README.md](../../utils/README.md) for comprehensive documentation of all utilities, usage patterns, and troubleshooting guides.

### Typical Workflow Summary

**For Single Practice:**
1. Generate Phase 1 modules → Phase 2 JSON
2. Run `fix-property-names.py` (Phase 2.5)
3. Run `validate-baseline-references.py` (Phase 2.6)
4. Run `validate-internal-integrity.py` (Phase 2.7)
5. Review integrity report, fix any issues
6. Run `check-floating-alphas.py` (QA)
7. Run schema validation (Phase 2.8)

**For Method (Multiple Practices):**
1. Generate Phase 1 modules → Phase 2 JSON for each practice
2. Run `fix-property-names.py` on all practice files (Phase 2.5)
3. Run `rebuild-method-json.py` to assemble (Phase 2.5b)
4. Run `validate-baseline-references.py` (Phase 2.6)
5. Run `rebuild-method-json.py` again (re-assemble after fixes)
6. Run `validate-internal-integrity.py` (Phase 2.7)
7. Review integrity report, fix any issues
8. Run `check-floating-alphas.py` (QA)
9. Run schema validation (Phase 2.8)

**Note:** Phases 2.5, 2.6, 2.7 should run automatically without user intervention when possible. Only Phase 2.7 typically requires manual review of the integrity report.

---

### Step 8: Phase 2.8 - Schema Validation (MANDATORY)

**REQUIRED STEP - RUN AFTER ALL FIXES**

After all previous validation and fix steps, validate the complete JSON against the authoritative schema to catch any remaining violations.

**Process:**

1. **Run schema validation** on practice or method JSON:
   ```bash
   node ../../utils/validate-json-schema.js <practice-name>.json
   ```

2. **Review validation results:**
   - ✓ If **0 errors**: Schema compliance confirmed, proceed to final delivery
   - ✗ If **errors found**: Review error report and apply fixes (see below)

**Common Schema Violations:**

Based on validation of red-hat-ai-3 Practice 1 (documented in `prompts/reference/schema-violations-complete.md`):

1. **Narrative Structure** - Narratives must have `name`, `description`, `narrativeTypeName`, `narrativeContexts`
   - Wrong: `{narrativeName, narrativeTypeName, narrativeContexts}`
   - Right: `{name, description, narrativeTypeName, narrativeContexts}`

2. **Activity Narratives Property** - Activities use `narratives` not `techniqueNarratives`
   - Wrong: `activity.techniqueNarratives`
   - Right: `activity.narratives` (with name/description on each narrative)

3. **Practice Tags Structure** - Tags must be nested in `tags` object
   - Wrong: `{domainTags: [...], lifecycleTags: [...], organizationalTags: [...]}`
   - Right: `{tags: {domainTags: [...], lifecycleTags: [...], organizationalTags: [...]}}`

4. **PersonaGroups Property** - Practice uses `personaGroups` not `teams`
   - Wrong: `practice.teams`
   - Right: `practice.personaGroups`

**Fixing Validation Errors:**

1. **Read the error report** - Validator shows path, issue, and schema location for each error
2. **Consult prompts/reference/schema-violations-complete.md** - Detailed examples and fixes
3. **Update affected segments or assembly script** - Fix root cause
4. **Regenerate or manually fix JSON** - Depending on error type
5. **Re-run validation** - Confirm all errors resolved

**Why This Step is Mandatory:**

The schema is the authoritative contract for Practice Language JSON. All other validation steps (property names, baseline references, internal integrity) are helpers that catch common issues. This final schema validation ensures:

1. **Complete compliance** - No unevaluated properties, all required fields present
2. **Type safety** - All values match expected types and formats
3. **Structural correctness** - Nested objects follow schema definitions exactly
4. **Deliverability** - JSON can be consumed by downstream tools and platforms

**Quality Gate:**

- **PASS:** 0 schema validation errors → JSON is ready for delivery
- **FAIL:** Any schema errors → Must fix before proceeding

**Output Location:**

- Validation errors displayed in terminal
- Reference: `prompts/reference/schema-violations-complete.md` for detailed error catalog
- Tool: `utils/validate-json-schema.js` (requires Node.js, ajv packages)

---

## Module Size Management

### When to Split Modules

**Module 03 (Alphas):**
- If methodology has extensive alpha content across all three focuses
- Estimated >20,000 words
- **Split into:** 03a-alphas-value.md, 03b-alphas-solution.md, 03c-alphas-endeavor.md

**Module 04 (Work Products):**
- If methodology defines >8 work products with extensive LODs
- Estimated >20,000 words
- **Split into:** 04a-workproducts-value.md, 04b-workproducts-solution.md, 04c-workproducts-endeavor.md

**Module 05 (Activities & Roles):**
- If methodology has >15 activities with rich technique narratives
- Estimated >25,000 words
- **Split into:** 05a-activities.md, 05b-personas-teams.md
- OR: 05a-activities-value.md, 05b-activities-solution.md, 05c-activities-endeavor.md, 05d-personas-teams.md

**Decision Point:** Make splitting decision in Step 1 (Plan Mode) based on source material assessment.

---

## Centralized Writing Standards (Referenced by All Module Prompts)

All Phase 1 module prompts reference these centralized standards to avoid duplication.

### Conciseness Standards

**Golden Rule: All descriptions MUST be single grammatically correct sentences. Use narratives for additional context.**

#### Descriptions: Single Sentence Rule

Every description field (alpha, state, activity, work product, pattern, persona, team, etc.) MUST be:

- **One sentence** - period at the end, no continuation
- **Grammatically complete** - subject, verb, object structure
- **Essence only** - the core purpose or concept, nothing more
- **Self-contained** - understandable without reading other text

**Examples:**

- ✅ Good: "Ensures infrastructure components are secure, compliant, and meet organizational standards."
- ❌ Bad: "This activity ensures that infrastructure components are secure and compliant with organizational standards by implementing security controls, conducting audits, and ensuring that all systems meet the required compliance frameworks and policies."
- ✅ Good: "The team responsible for building and maintaining the platform infrastructure."
- ❌ Bad: "This team is responsible for designing, implementing, and maintaining the platform infrastructure, including cloud resources, networking, storage, and compute capabilities, working closely with security and operations teams."

**Word Count Limits:**
- Practice/Alpha/Work Product/Activity/Persona/Pattern descriptions: **Maximum 20 words**
- State/LOD/PatternView descriptions: **Maximum 12 words**
- Checklist criteria: No limit (detail needed for verification)

### Citation Standards

- Citations are bibliographic references: name, description, authors, date, source, url
- **NO narratives on Citation objects** (narratives reference citations, not vice versa)
- Citation names use exact source titles for readability (e.g., "Team topologies: Organizing business and technology teams for fast flow")
- 5-15 authoritative sources per practice
- Additional context about sources belongs in practice/alpha/activity narratives that cite them

### Narrative Standards

- **Narrative contexts:** 1-3 sentences per element (not multi-paragraph blocks)
- Each context conveys ONE specific point, observation, or step
- **Bullet-point mentality:** Key insights, not comprehensive essays
- Use citationNames for further reading (direct readers to comprehensive source material)
- Multiple focused narratives better than one bloated narrative

**Anti-patterns to avoid:**
- ❌ Multi-paragraph context elements (3+ sentences per element)
- ❌ Comprehensive background exposition
- ❌ Repeating source material verbatim
- ❌ Generic statements without specific claims

**Good pattern:**
- ✅ Specific research finding or principle (1-2 sentences)
- ✅ Practical observation or pattern (1-2 sentences)
- ✅ Clear connection to practice domain (1-2 sentences)
- ✅ Citation for deeper reading

**Remember:** Contexts are signposts pointing to insights. Citations provide the full journey.

### Checklist Standards

- Alpha state checklists: 5-7 criteria per state (not 10+)
- Work product LOD checklists: 3-5 criteria per level
- Each criterion: **One sentence** explaining what must be verified
- Avoid multi-sentence or paragraph-length criteria

### Naming Standards

- **Activity names:** Specific (verb + specific subject), never duplicate ActivitySpace name
- **Work product LOD names:** Descriptive only, **NO "Level X:" prefix** (e.g., "Basic" not "Level 1: Basic")
- **Alpha instance names:** Specific qualifier + base alpha name
- **Persona names:** Role-descriptive, clear differentiation
- **Citation names:** Exact source titles (readable, not code-like)

### Alpha Decision: Redeclaration vs. Specialization

When enriching baseline alphas, test if additions are generally applicable or practice-specific:

**Generally Applicable → Redeclaration:**
- Universal verification criteria
- Industry-standard checklists
- Widely-recognized best practices
- Any practice in domain would benefit

**Practice-Specific → Specialization:**
- Methodology-specific concepts
- Practice-specific techniques
- Specialized patterns unique to this approach
- Create new alpha with contributesTo

**When in doubt:** Default to specialization to preserve baseline reusability.

---

## Key Principles

### Modular Benefits

1. **Manageable Size:** Each module 1K-20K words (no 80K monoliths)
2. **Incremental Progress:** Generate and validate one section at a time
3. **Iteration-Friendly:** Re-generate single modules without redoing everything
4. **Parallel Potential:** Different modules could be delegated to subagents
5. **Clear Dependencies:** Each module knows which previous modules to read

### Quality Standards

1. **Natural Prose:** Modules use human-readable prose, not pseudo-JSON
2. **Complete Content:** No placeholders, no "etc.", capture everything
3. **Exact Names:** Use exact baseline element names (case-sensitive)
4. **Rich Narratives:** Especially in Module 05 (technique narratives)
5. **Comprehensive Citations:** 5-15 authoritative sources (Module 02)
6. **Clean JSON Text:** All markdown syntax and practice metadata removed from final JSON
7. **Subject Matter Focus:** Descriptions and narratives focus on domain concepts, not documentation structure
8. **Required Practice Intent Narrative:** Every practice and method MUST include at least one narrative summarizing the intent and objective using a provided narrative template (STAR, Hero's Journey, Three-Act Structure & StoryBrand, ABT, Essay, Epic, Report, etc.)

### Writing Conciseness Guidelines

**See "Centralized Writing Standards" section above for complete guidelines.**

All Phase 1 modules reference the centralized standards for:
- Description conciseness (single sentence, max 20 words)
- Narrative context length (1-3 sentences per element)
- Checklist criteria (5-7 per state, 3-5 per LOD, one sentence each)
- Citation standards (metadata only, no narratives)
- Naming conventions (LODs, activities, alphas, citations)
- Alpha decision tree (redeclaration vs. specialization)

**Key Principles:**
- **Essence → Descriptions** (single sentence)
- **Context → Narratives** (1-3 sentences per element)
- **Citations → Further Reading** (reference via citationNames)

**The goal is high-quality, readable, focused content that captures the methodology's unique value proposition—not a reproduction of the source materials.**

### Maturity Progression Discovery

**CRITICAL: Let the SOURCE CONTENT drive progression, not templates.**

The `references/workproduct-assessment-rubric.csv` is **GUIDANCE for recognizing patterns**, not a template to impose.

**Approach for Alpha States:**
1. **Read the source methodology** for how it describes progression, maturity, or evolution
2. **Identify natural waypoints** the methodology itself describes (e.g., "initial setup" → "production ready" → "optimized")
3. **Use the rubric as a lens** to help recognize Business/Technology/People/Process patterns in those waypoints
4. **Create states that reflect the source**, not force-fit source content into rubric categories
5. **Minimum 3 states required**, but use more (4-7) if the source naturally expresses them

**Approach for Work Product Levels of Detail:**
1. **Look for natural maturity expressions** in the source (e.g., "basic configuration" → "comprehensive setup" → "automated deployment")
2. **Use the rubric to identify patterns** (descriptive → logical → behavioral → automated) but don't force all 5 levels
3. **Create LODs matching source progressions**, using rubric terms where they fit naturally
4. **Minimum 3 levels required**, but use 4-5 if the source clearly describes them
5. **Level 0 (Non-Existent) is usually appropriate** as baseline, but not mandatory

**Examples:**
- ✅ Good: Source describes "manual configuration → scripted deployment → CI/CD automation" → Create 3-4 LODs matching these
- ❌ Bad: Forcing 5 levels from rubric when source only describes 3 maturity stages
- ✅ Good: Alpha states named from methodology's own lifecycle phases
- ❌ Bad: Alpha states using generic rubric language that doesn't match source terminology

**The rubric helps you SEE patterns, but the source content DEFINES the actual progression.**

### Common Pitfalls to Avoid

- **Skipping EnterPlanMode:** Always plan first
- **Missing practice intent narrative:** EVERY practice and method MUST have at least one narrative summarizing intent/objective using a baseline narrative template (Module 01)
- **Multi-sentence descriptions:** All descriptions must be single grammatically correct sentences
- **Bloated descriptions:** Move additional context to narratives, not description fields
- **Paragraph-length checklist criteria:** Each criterion should be one sentence
- **Multi-paragraph narrative contexts:** Each context element should be 1-3 sentences maximum
- **"Level X:" in LOD names:** Use descriptive names only (e.g., "Basic" not "Level 1: Basic")
- **Narratives on Citations:** Citations are metadata only (no narratives property)
- **Wrong alpha approach:** Test redeclaration vs. specialization (practice-specific → specialization)
- **Markdown in JSON:** Remove all markdown syntax from text before inserting into JSON
- **Practice metadata in JSON:** Descriptions should focus on subject matter, not the practice's documentation of it
- **Not splitting large modules:** Monitor estimated sizes, split if needed
- **Fuzzy name matching:** All baseline references must be exact
- **Activity naming:** Never duplicate ActivitySpace names
- **Missing technique narratives:** Module 05 should have rich "How to Perform" sections
- **Insufficient citations:** Module 02 needs 5-15 authoritative sources
- **Forgetting method assembly:** Methods need Module 08
- **Not reviewing previous session output:** When picking up existing work, review for compliance with current standards

---

## Troubleshooting

### If module generation fails:

1. Check that previous dependent modules were generated
2. Verify source materials are accessible
3. Ensure directory structure exists
4. Check for extremely large content (may need splitting)

### If validation fails:

1. Review cross-reference-index.json
2. Check for name mismatches (case-sensitive)
3. Verify all references exist
4. Re-generate specific problematic modules

### If Phase 2 translation fails:

1. Verify cross-reference-index.json exists and is valid
2. Check that all expected modules exist
3. Verify baseline framework is accessible
4. Check for malformed module content

---

## User Interaction

### Reviewing Existing Content

When user asks to review or fix existing output from a previous session:

"I'll review the existing content in practices/<name>/ and update it to align with current standards. Let me check what's been generated so far."

**Process:**

1. List existing files to understand what's been completed
2. Identify specific deviations from current rules (descriptions, narratives, references, etc.)
3. Report findings briefly: "Found X modules with overly verbose descriptions, Y instances of multi-sentence criteria"
4. Correct the issues using Edit tool or regeneration as appropriate
5. Report completion: "Updated N files to align with current standards: single-sentence descriptions, focused narratives, corrected baseline references"

### Initial Request

When user provides source materials, start with:

"I'll translate this methodology using a modular workflow. First, let me analyze the source materials and create an execution plan."

**Then:** EnterPlanMode

### During Module Generation

Provide brief updates:

"Generating Module 01 (Practice Details)..."
"Generating Module 03 (Alphas) - this may take a few minutes due to complexity..."

### After Phase 1.5

Report validation results:

"Phase 1 complete. Generated 8 modules, assembled into research report. Validation: X/Y checks passed."

### After Phase 2

Report translation status:

"Phase 2 complete. Generated JSON files. Running schema compliance fixes..."

### After Phase 2.5 (Schema Compliance)

Report progress:

"Phase 2.5 complete. Property names corrected. Running baseline reference validation..."

### After Phase 2.6 (Baseline Validation)

Report progress:

"Phase 2.6 complete. Baseline references validated. Running internal integrity validation..."

### After Phase 2.7 (Internal Integrity)

Report final output:

**If 0 issues found:**
"Translation complete! Generated fully validated JSON at practices/<name>/<name>.json
 ✓ Property names validated and corrected
 ✓ Baseline references validated (competencies, states, alphas)
 ✓ Internal integrity verified (all cross-references valid)
 ✓ All files ready for use"

**If issues found:**
"Translation complete with validation warnings.
 ✓ Property names validated and corrected
 ✓ Baseline references validated
 ⚠ Internal integrity issues found: X issues
 
 Review INTERNAL-INTEGRITY-REPORT.md for details.
 Common issues:
 - Activities referencing non-existent work products
 - Pattern views referencing wrong activity names
 - Cross-practice reference mismatches
 
 Fix issues and re-run: python3 validate-internal-integrity.py"

---

## Final Deliverables

For successful translation, user receives:

1. **`report-elements/` directory:** All modular markdown files (human-editable)
2. **`research-report.md`:** Complete assembled documentation (~50-80K words)
3. **`cross-reference-index.json`:** Validation index
4. **`<name>.json`:** Fully validated Practice or Method JSON (schema-compliant + baseline-validated)
5. **Utility scripts** (in practice directory):
   - `fix-property-names.py` - Schema compliance fixer
   - `validate-baseline-references.py` - Baseline reference validator and fixer
   - `validate-internal-integrity.py` - Internal cross-reference validator
   - `rebuild-method-json.py` - Method assembly script (for methods only)

Users can:
- Review and edit individual modules
- Re-generate specific modules if needed
- Use research-report.md as methodology documentation
- Use <name>.json in tooling that consumes Practice Language
- Re-run validation and fixes if manual edits are made:
  ```bash
  cd practices/<name>
  python3 fix-property-names.py
  python3 validate-baseline-references.py
  python3 rebuild-method-json.py  # Methods only
  ```
