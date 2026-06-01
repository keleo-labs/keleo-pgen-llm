---
name: translate-methodology-v2
description: Transform methodology documentation into Practice Language JSON using clean 3-phase workflow (Analysis → Mapping → JSON)
triggerPatterns:
  - "translate.*methodology.*v2"
  - "analyze.*methodology"
  - "map.*methodology"
---

# Methodology Translation Skill (3-Phase)

This skill transforms enterprise methodology documentation into schema-compliant Practice Language JSON using a clean three-phase workflow that delegates to reference documents rather than embedding knowledge.

## Workflow Overview

**Phase 1: Analysis** → Structure methodology into outcomes, concerns, activities, workflows, practices  
**Phase 2: Mapping** → Map to baseline practice using semantic guidance  
**Phase 3: JSON** → Generate schema-compliant JSON with programmatic validation

**Key Differences from v1:**
- ✓ Simpler 3-phase structure (vs 8-phase pipeline)
- ✓ Reference-driven (reads semantics.md, not embedded rules)
- ✓ User-provided baseline (not hardcoded)
- ✓ Single validation script (not 4+ separate utilities)
- ✓ Cleaner output (3 files vs 8+ modules)

---

## Critical Process: ALWAYS Use EnterPlanMode

**MANDATORY FIRST STEP:** Before starting ANY phase, you MUST use EnterPlanMode to:

1. Analyze source materials thoroughly
2. Determine if this is a Practice or Method (multiple practices)
3. Plan phase execution strategy
4. Identify baseline practice to use
5. Create execution roadmap

**Do NOT proceed without planning.**

---

## Directory Structure

### Output Location

All generated outputs for a practice go in `practices/<practice-name>/`:

```
practices/
└── <practice-name>/
    ├── 01-analysis-report.md      (Phase 1 output, ~30-50K words)
    ├── 02-mapping-guide.md         (Phase 2 output, ~40-60K words)
    └── <practice-name>.json        (Phase 3 output, schema-compliant JSON)
```

For methods with multiple practices:

```
practices/
└── <method-name>/
    ├── 01-analysis-report.md       (Covers all practices)
    ├── 02-mapping-guide.md         (Maps all practices)
    └── <method-name>.json          (Method JSON with embedded practices)
```

---

## Reference Documents

This skill relies on reference documents (READ via Read tool, NOT embedded):

### Required References
1. **references/domain-framework.md** - Four-perspective analysis framework
2. **references/semantics.md** - Practice Language semantic guidance
3. **deps/language.schema.json** - JSON Schema definition
4. **Baseline Practice JSON** - User-provided (e.g., `deps/platform-adoption-kernel.json`)

### Phase Prompts
- **prompts/phase-1-analysis.md** - Analysis phase instructions
- **prompts/phase-2-mapping.md** - Mapping phase instructions
- **prompts/phase-3-json.md** - JSON generation instructions

---

## Execution Workflow

### Step 0: EnterPlanMode (REQUIRED)

**YOU MUST DO THIS FIRST.**

In plan mode:

1. **Read source materials completely**
   - All provided PDFs, URLs, markdown files
   - Take comprehensive notes

2. **Determine structure:**
   - **Practice** if: Single cohesive value stream, one use case
   - **Method** if: Multiple distinct value streams, different use cases, separate practices

3. **Identify baseline practice:**
   - Ask user which baseline to use
   - Default suggestion: `deps/platform-adoption-kernel.json`
   - Validate baseline file exists and is valid JSON

4. **Plan execution:**
   - Practice name (kebab-case)
   - Phase execution sequence
   - Expected complexity and size
   - Potential challenges

5. **Exit plan mode** with clear execution roadmap

### Step 1: Phase 1 - Analysis

**Objective:** Extract and organize methodology into structured analysis

**Process:**

1. **Read prompt:** `prompts/phase-1-analysis.md`
   - This prompt contains complete instructions for Phase 1
   - Follow all steps exactly as specified

2. **Load domain framework:** Read `references/domain-framework.md`
   - Understand four perspectives: Business, Technology, People, Process

3. **Analyze source materials:**
   - Extract outcomes, concerns, progressive states, work products
   - Identify activities, competencies, personas, teams
   - Map workflows and patterns
   - Determine practice boundaries

4. **Generate output:** Write to `practices/<practice-name>/01-analysis-report.md`
   - Follow exact format from phase-1-analysis.md prompt
   - ~30-50K words structured markdown
   - Complete, no placeholders

**Quality Gates:**
- ✓ All four perspectives represented
- ✓ Clear traceability: Outcomes → Concerns → States → Work Products → Activities
- ✓ Progressive states reflect source's natural maturity (not forced template)
- ✓ Rich activity narratives with citations
- ✓ Clear practice boundaries justified

**User Feedback:** Brief progress updates
- "Analyzing source materials using four-perspective framework..."
- "Extracted N concerns across M perspectives..."
- "Phase 1 complete: Analysis report generated at practices/<name>/01-analysis-report.md"

### Step 2: Phase 2 - Mapping

**Objective:** Map Phase 1 analysis to baseline practice framework

**Process:**

1. **Read prompt:** `prompts/phase-2-mapping.md`
   - This prompt contains complete mapping instructions
   - Follow all steps exactly as specified

2. **Request baseline practice:**
   
   **Ask user:**
   ```
   I need the baseline practice file to proceed with mapping. Please provide:
   - File path to your baseline practice JSON
   - OR: Confirm use of the example at deps/platform-adoption-kernel.json
   
   The baseline practice defines the standardized framework (alphas, activity spaces, 
   competencies) that your source methodology will be mapped to.
   ```

   **Store:** baseline_practice_path  
   **Validate:** File exists, is valid JSON

3. **Load resources:**
   - Read `practices/<practice-name>/01-analysis-report.md`
   - Read baseline practice JSON (user-provided path)
     - **CRITICAL:** Read element DESCRIPTIONS, not just names
     - Understand semantic scope: alpha descriptions reveal full scope, state descriptions show progression
     - Competency descriptions clarify expertise range, activity space descriptions define boundaries
     - Description-level understanding is essential for accurate redeclaration vs specialization decisions
   - Read `references/semantics.md` (comprehensive semantic guidance)

4. **Map elements:**
   - Concerns → Alphas (redeclaration vs specialization decision)
   - Work Products → WorkProducts with LODs
   - Competencies → Exact baseline competency names
   - Personas → Personas with competency references
   - Teams → PersonaGroups
   - Activities → Activities with complete references
   - Workflows → Patterns with PatternViews
   - Terminology → Aliases (if needed)

5. **Generate output:** Write to `practices/<practice-name>/02-mapping-guide.md`
   - Follow exact format from phase-2-mapping.md prompt
   - ~40-60K words structured markdown
   - Complete mapping specification
   - Validation checklist satisfied

**Critical Mapping Rules:**

From `references/semantics.md`:

- **NO FLOATING ALPHAS:** All new alphas MUST have `contributesTo` (Section 4.1)
- **Exact name matching:** All baseline references are case-sensitive (Section 3)
- **Orthogonal tags:** Use {domainTags, lifecycleTags, organizationalTags} (Section 3.1.2)
- **Redeclaration vs Specialization:** Follow decision framework (Section 9.2.5)
- **Competency names:** Use EXACT baseline names, not descriptions (Section 6.2)
- **Single sentences:** Descriptions max 20 words, states/LODs max 12 (Section 3.1)

**Quality Gates:**
- ✓ All Phase 1 concerns mapped to alphas
- ✓ All new alphas have contributesTo
- ✓ All baseline references are exact canonical names
- ✓ Tags use orthogonal structure
- ✓ Validation checklist completely satisfied

**User Feedback:**
- "Reading analysis report and loading baseline practice..."
- "Mapping N concerns to alphas using redeclaration/specialization framework..."
- "Phase 2 complete: Mapping guide generated at practices/<name>/02-mapping-guide.md"

### Step 3: Phase 3 - JSON Generation

**Objective:** Generate schema-compliant Practice or Method JSON

**Process:**

1. **Read prompt:** `prompts/phase-3-json.md`
   - This prompt contains complete JSON generation instructions
   - Follow all steps exactly as specified

2. **Load resources:**
   - Read `practices/<practice-name>/02-mapping-guide.md`
   - Read `deps/language.schema.json` (schema structure)
   - Read `references/semantics.md` (JSON structure examples)
   - Read baseline practice JSON (same as Phase 2)

3. **Generate JSON incrementally:**
   - Practice/Method skeleton (metadata, tags, keywords)
   - Citations (metadata only, NO narratives property)
   - Narratives (practice/method level)
   - Alphas (with states, checklists, narratives)
   - Alpha Instances
   - Work Products (with LODs, checklists, contributesTo)
   - Work Product Instances
   - Personas (competencies property, NOT requiredCompetencies)
   - Persona Groups (personaNames array)
   - Activities (BOTH requiredCompetencies AND recommendedCompetencyLevels)
   - Patterns (patternViews, alphaStates properties)
   - Practice Element Aliases (if applicable)

4. **Validate JSON syntax:**
   ```bash
   jq empty practices/<name>/<name>.json
   ```

5. **Run validation script:**
   ```bash
   python3 utils/validate-practice-json.py \
     practices/<name>/<name>.json \
     <baseline-practice-path> \
     deps/language.schema.json
   ```

6. **Interpret validation results:**
   - Read JSON output from validation script
   - Categorize errors: schema / baseline / integrity
   - Determine fix strategy for each error category

7. **Apply fixes:**
   - **Schema violations:** Edit JSON to correct property names, types, structure
   - **Baseline mismatches:** Use exact baseline names, add contributesTo
   - **Integrity errors:** Create missing elements or fix references

8. **Iterate until clean:**
   - Re-run validation after each fix batch
   - Continue until 0 errors

9. **Final quality check:**
   - All Phase 2 mappings present in JSON
   - No content omissions
   - All narratives and checklists complete
   - JSON well-formatted and readable

**Critical JSON Rules:**

From `deps/language.schema.json`:

- **Checklist format:** Objects {name, description, seq}, NOT strings
- **Competency references:** {competencyName, competencyLevelName}, NOT {competencyName, level}
- **Persona property:** `competencies`, NOT `requiredCompetencies`
- **Activity competencies:** BOTH `requiredCompetencies` (strings) AND `recommendedCompetencyLevels` (objects)
- **PatternView properties:** `alphaStates` NOT `alphas`, `patternViews` NOT `views`, NO `workProducts`
- **LOD contributesTo:** REQUIRED on every LevelOfDetail
- **Tags structure:** Nested object {domainTags, lifecycleTags, organizationalTags}, NOT flat array

**Quality Gates:**
- ✓ Valid JSON syntax (jq empty passes)
- ✓ Schema validation: 0 errors
- ✓ Baseline validation: 0 errors
- ✓ Internal integrity: 0 errors
- ✓ All Phase 2 content in JSON
- ✓ No floating alphas

**User Feedback:**
- "Generating JSON from mapping guide..."
- "Running validation (schema, baseline, integrity)..."
- "Found N errors in category X, applying fixes..."
- "Validation passed! Generated schema-compliant JSON at practices/<name>/<name>.json"

---

## Validation Script

**Location:** `utils/validate-practice-json.py`

**Purpose:** Comprehensive validation combining:
1. JSON Schema compliance
2. Baseline practice reference checking
3. Internal cross-reference integrity

**Usage:**
```bash
python3 utils/validate-practice-json.py \
  <practice-or-method.json> \
  <baseline-practice.json> \
  <language-schema.json>
```

**Output:** JSON report with categorized errors:
```json
{
  "valid": false,
  "error_count": 5,
  "summary": {
    "schema": 2,
    "baseline": 2,
    "integrity": 1
  },
  "errors": [
    {
      "category": "schema",
      "severity": "error",
      "path": "alphas[0].states[0].checklist[0]",
      "issue": "Expected object, got string",
      "expected": "{name, description, seq}",
      "actual": "Checklist item",
      "suggestion": "Convert to object format"
    }
  ]
}
```

**Error Categories:**

- **schema:** Property name mismatches, type errors, missing required fields
- **baseline:** Invalid competency/alpha/state references against baseline
- **integrity:** Broken cross-references within practice/method

**Skill Response to Errors:**

Read validation output and apply fixes:

1. **Schema errors:**
   - Correct property names (e.g., `outcomes` → `contributesTo`)
   - Fix data types (e.g., string checklist → object checklist)
   - Add missing required fields (e.g., contributesTo on LODs)

2. **Baseline errors:**
   - Map competency descriptions to exact baseline names
   - Correct state names to match alpha definitions
   - Add contributesTo to floating alphas
   - Use exact case-sensitive baseline references

3. **Integrity errors:**
   - Create missing work products, activities, alphas
   - Fix broken symbolic references
   - Correct cross-practice references (for methods)

**Auto-fixable vs Manual:**

- **Auto-fix:** Schema violations, baseline reference corrections
- **Ask user:** Structural ambiguities, missing elements that need domain knowledge

---

## Key Principles

### Reference-Driven Architecture

This skill does NOT embed knowledge. Instead:

- **Phase 1:** Reads `references/domain-framework.md` for perspectives
- **Phase 2:** Reads `references/semantics.md` for mapping rules
- **Phase 3:** Reads `deps/language.schema.json` for structure
- **All phases:** Use prompts in `prompts/` directory for instructions

**Benefits:**
- Skill stays thin (orchestration only)
- Reference docs are single source of truth
- Updates to semantics don't require skill changes
- Clear separation of concerns

### User-Provided Baseline

The skill does NOT assume a specific baseline practice. Instead:

- User provides baseline practice file path
- Example provided: `deps/platform-adoption-kernel.json`
- Validation script validates against provided baseline
- Works with any baseline following Practice Language schema

**Benefits:**
- Flexibility to use different baselines
- No hardcoded assumptions
- Baseline can evolve independently

### Clean Three-Phase Structure

Unlike the complex v1 pipeline (Phase 1 → 1.5 → 2 → 2.5 → 2.6 → 2.7 → 2.8), this uses:

**Phase 1: Analysis** (one step)
- Organize methodology into structured analysis
- Output: Single markdown file

**Phase 2: Mapping** (one step)
- Map analysis to baseline using semantics
- Output: Single markdown file

**Phase 3: JSON** (one step with iterative validation)
- Generate JSON, validate, fix, repeat until clean
- Output: Schema-compliant JSON

**Benefits:**
- Easier to understand and explain
- Clear phase boundaries
- Simpler resumption if interrupted

### Programmatic Validation

Single validation script replaces multiple utilities:

**Old approach (v1):**
- fix-property-names.py
- validate-baseline-references.py
- validate-internal-integrity.py
- Manual review and iteration

**New approach (v2):**
- validate-practice-json.py (all-in-one)
- Skill interprets results and applies fixes
- Automated iteration until clean

**Benefits:**
- Single command validates everything
- Structured JSON output for skill consumption
- Clear error categorization and suggestions

---

## Common Pitfalls to Avoid

### Phase 1 Pitfalls
- ❌ Skipping EnterPlanMode
- ❌ Not reading domain-framework.md before analyzing
- ❌ Forcing template patterns instead of discovering source's natural progression
- ❌ Multi-sentence descriptions (violates conciseness standards)
- ❌ Insufficient citations (need 5-15 authoritative sources)

### Phase 2 Pitfalls
- ❌ Not reading semantics.md before mapping
- ❌ Creating floating alphas (missing contributesTo)
- ❌ Using competency descriptions instead of exact baseline names
- ❌ Using alias names in structural references (use canonical names)
- ❌ Wrong alpha approach (should use redeclaration vs specialization framework)
- ❌ Flat tags array instead of orthogonal structure

### Phase 3 Pitfalls
- ❌ Not reading language.schema.json before generating
- ❌ Checklist items as strings instead of objects
- ❌ Wrong competency reference format ({competencyName, level} instead of {competencyName, competencyLevelName})
- ❌ Using `requiredCompetencies` on personas (should be `competencies`)
- ❌ Missing BOTH `requiredCompetencies` AND `recommendedCompetencyLevels` on activities
- ❌ Wrong PatternView property names (`alphas` instead of `alphaStates`, `views` instead of `patternViews`)
- ❌ Missing contributesTo on LODs
- ❌ Markdown or metadata in JSON strings

---

## Practice vs Method Handling

### Practice (Single Value Stream)

**When:** Single cohesive value stream, one use case, unified stakeholder journey

**Structure:**
- One analysis report (covers entire practice)
- One mapping guide (maps to baseline)
- One Practice JSON

**Example:** "Team Topologies" as single practice

### Method (Multiple Practices)

**When:** Multiple distinct value streams, different use cases, separate practices

**Structure:**
- One analysis report (covers all practices with clear boundaries)
- One mapping guide (maps each practice separately + method integration)
- One Method JSON with embedded practices array

**Example:** "AWS Well-Architected Framework" as method with 6 pillar practices

**Decision Heuristics:**
- Different use-cases (greenfield vs brownfield) → Method
- Different value-streams (platform building vs consuming) → Method
- Different stakeholder journeys (builders vs consumers) → Method
- Different capability domains (security, observability, deployment) → Method

---

## User Interaction Patterns

### Initial Request

When user provides source materials:

"I'll translate this methodology using a three-phase workflow (Analysis → Mapping → JSON). Let me first analyze the source materials and create an execution plan."

**Then:** EnterPlanMode

### Before Phase 2

Request baseline practice:

"I need the baseline practice file to proceed with Phase 2 mapping. Please provide:
- File path to your baseline practice JSON
- OR: Confirm use of the example at deps/platform-adoption-kernel.json

The baseline defines the standardized framework (alphas, activity spaces, competencies) that your methodology will be mapped to."

### During Phases

Provide brief progress updates:
- "Phase 1: Analyzing source using four-perspective framework..."
- "Phase 2: Mapping concerns to alphas using semantic guidance..."
- "Phase 3: Generating JSON and running validation..."

### After Validation Errors

Report findings and fixes:
- "Validation found 5 schema errors, 3 baseline mismatches. Applying fixes..."
- "Re-running validation... 0 errors. JSON is schema-compliant!"

### Final Output

Report completion with file paths:

"Translation complete! Generated files:
 ✓ practices/<name>/01-analysis-report.md (~40K words)
 ✓ practices/<name>/02-mapping-guide.md (~50K words)
 ✓ practices/<name>/<name>.json (schema-compliant)

Validation summary:
 ✓ Schema compliance: PASS
 ✓ Baseline references: PASS
 ✓ Internal integrity: PASS

JSON is ready for use in Practice Language consuming systems."

---

## Troubleshooting

### If Phase 1 fails:
- Check that domain-framework.md is accessible
- Verify source materials are readable
- Ensure sufficient context for large documents
- Review for extremely complex methodologies (may need chunking)

### If Phase 2 fails:
- Verify baseline practice file exists and is valid JSON
- Check that semantics.md is accessible
- Review for missing content in Phase 1 analysis
- Ensure mapping decisions follow semantic guidance

### If Phase 3 validation fails repeatedly:
- Re-read schema.json to understand exact structure
- Check validation error suggestions carefully
- Review common schema violations in phase-3-json.md prompt
- Consider regenerating problematic sections from Phase 2 mapping

### If validation script errors:
- Ensure Python 3.8+ installed
- Install jsonschema: `pip install jsonschema`
- Check file paths are correct (absolute or relative to working directory)
- Verify all three files (practice, baseline, schema) are valid JSON

---

## Final Deliverables

For successful translation, user receives:

1. **`practices/<name>/01-analysis-report.md`**
   - Complete structured analysis (~30-50K words)
   - Human-readable, organized by perspectives

2. **`practices/<name>/02-mapping-guide.md`**
   - Complete mapping specification (~40-60K words)
   - Human-readable, ready for review

3. **`practices/<name>/<name>.json`**
   - Schema-compliant Practice or Method JSON
   - Validated against schema, baseline, internal integrity
   - Ready for consumption by Practice Language tools

Users can:
- Review and edit phase outputs
- Regenerate specific phases if source changes
- Use analysis and mapping as methodology documentation
- Use JSON in tooling that consumes Practice Language
- Share JSON with teams and tools

---

## Success Metrics

A successful translation achieves:

1. ✓ All three phases complete without errors
2. ✓ Validation passes with 0 schema violations
3. ✓ Validation passes with 0 baseline reference errors
4. ✓ Validation passes with 0 internal integrity errors
5. ✓ All source methodology content mapped (no omissions)
6. ✓ Clear traceability from source → analysis → mapping → JSON
7. ✓ JSON is well-formatted, readable, and usable

Quality indicators:
- Rich narratives with citations (not sparse)
- Complete checklists (5-7 per state, 3-5 per LOD)
- Exact baseline references (case-sensitive matches)
- No floating alphas (all new alphas have contributesTo)
- Orthogonal tags throughout
- Single-sentence descriptions
