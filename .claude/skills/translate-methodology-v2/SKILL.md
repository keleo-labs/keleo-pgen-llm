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

```text
practices/
└── <practice-name>/
    ├── 01-analysis-report.md      (Phase 1 output, ~30-50K words)
    ├── 02-mapping-guide.md         (Phase 2 output, ~40-60K words)
    └── <practice-name>.json        (Phase 3 output, schema-compliant JSON)
```

For methods with multiple practices:

```text
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

---

## Token Budget Management: Phase Compaction Pattern

**CRITICAL:** To avoid token budget exhaustion during long translations, use conversation compaction between phases.

### When to Compact

**Inter-phase compaction** (between major phases):

1. **After Planning (before Phase 1):** Compact to clear planning discussion
2. **After Phase 1 (before Phase 2):** Compact to clear analysis generation
3. **After Phase 2 (before Phase 3):** Compact to clear mapping generation

**Multi-agent approach** (for multi-practice methods - RECOMMENDED):

4. **Use Agent tool for parallelism** (for methods with 2+ practices):
   - **Phase 2**: Launch one agent per practice (parallel execution)
     - Each agent reads: analysis report, baseline JSON, semantics.md
     - Each agent generates: complete practice mapping (alphas + work products + activities)
     - Write to separate files or sections
     - Agents run concurrently (no token budget sharing)
   - **Phase 3**: Launch one agent per practice (parallel execution)
     - Each agent reads: practice mapping section, baseline JSON, schema
     - Each agent generates: practice JSON (standalone, not method JSON)
     - Agents run concurrently
   - **Phase 3.5**: Assembly and validation
     - Combine practice JSONs into method structure
     - Validate method JSON against schema
     - Fix any cross-practice reference issues
   - **Benefits**: No token limits, no degeneration, concurrent execution, quality consistency

### How to Implement Multi-Agent Approach

**For Single-Practice translations:**
- User can manually compact between phases
- Tell user: "Phase N complete. [Optional: Compact before Phase N+1 for optimal token budget]"
- Don't wait - continue working

**For Multi-Practice methods (2+ practices):**
- **Always use Agent tool** (don't ask user to compact)
- Launch agents in parallel using single message with multiple Agent tool calls
- Each agent is self-contained with complete prompt and file paths

**Example: Phase 2 with 4 practices**
```
Send single message with 4 Agent tool calls:
- Agent 1: Generate Practice 1 mapping
- Agent 2: Generate Practice 2 mapping  
- Agent 3: Generate Practice 3 mapping
- Agent 4: Generate Practice 4 mapping
All run concurrently, no shared token budget
```

**Example: Phase 3 with 4 practices**
```
Send single message with 4 Agent tool calls:
- Agent 1: Generate Practice 1 JSON
- Agent 2: Generate Practice 2 JSON
- Agent 3: Generate Practice 3 JSON
- Agent 4: Generate Practice 4 JSON
Then combine into method JSON and validate
```

### Why This Works

Each phase is designed to be **stateless** and **file-driven**:

- Phase 1 reads: source materials, domain-framework.md
- Phase 2 reads: 01-analysis-report.md, baseline JSON, semantics.md
- Phase 3 reads: 02-mapping-guide.md, baseline JSON, language.schema.json

No conversational context is required - only file contents.

### Example Flow: Single Practice

```text
[Planning complete]
→ Compact conversation
→ Phase 1: Read prompts/phase-1-analysis.md, generate 01-analysis-report.md
[Phase 1 complete]
→ Compact conversation  
→ Phase 2: Read prompts/phase-2-mapping.md + 01-analysis-report.md, generate 02-mapping-guide.md
[Phase 2 complete]
→ Compact conversation
→ Phase 3: Read prompts/phase-3-json.md + 02-mapping-guide.md, generate JSON
[Phase 3 complete]
```

### Example Flow: Multi-Practice Method (4 practices) - Multi-Agent Approach

```text
[Planning complete]
→ Phase 1: Generate 01-analysis-report.md (covers all 4 practices)
[Phase 1 complete]

→ Phase 2: Launch 4 parallel agents in single message
  - Agent 1: Generate Practice 1 mapping (alphas + work products + activities)
  - Agent 2: Generate Practice 2 mapping (alphas + work products + activities)
  - Agent 3: Generate Practice 3 mapping (alphas + work products + activities)
  - Agent 4: Generate Practice 4 mapping (alphas + work products + activities)
  [All agents run concurrently]
→ Combine practice mappings into 02-mapping-guide.md
[Phase 2 complete]

→ Phase 3A: Launch 4 parallel agents in single message
  - Agent 1: Generate practice-1.json
  - Agent 2: Generate practice-2.json
  - Agent 3: Generate practice-3.json
  - Agent 4: Generate practice-4.json
  [All agents run concurrently]
→ Phase 3B: Assemble method JSON
  - Combine 4 practice JSONs into method structure
  - Merge citations
  - Write method-name.json
→ Phase 3C: Validate and fix
  - Run validation script
  - Fix errors until 0 errors
[Phase 3 complete]
```

**Benefits of Multi-Agent Approach:**
- ✅ **No token budget issues** (each agent has independent budget)
- ✅ **No quality degeneration** (Practice 4 gets same quality as Practice 1)
- ✅ **4x faster** (concurrent execution vs sequential)
- ✅ **Simpler prompts** (each agent focuses on one practice)
- ✅ **No manual compaction needed** (agents handle it automatically)

---

### Step 1: Phase 1 - Analysis

**Objective:** Extract and organize methodology into structured analysis

**BEFORE STARTING:** Consider compacting conversation if context is large (see Token Budget Management above).

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

**APPROACH DECISION:**

- **Single Practice**: Generate mapping guide directly (one step)
- **Multi-Practice Method (2+ practices)**: Use parallel Agent tool approach

**Process for Single Practice:**

1. Read `prompts/phase-2-mapping.md`, analysis report, baseline JSON, semantics.md
2. Generate complete `02-mapping-guide.md` with all alphas, work products, activities, patterns

**Process for Multi-Practice Method:**

1. **Launch parallel agents** (one per practice) in single message:
   
   ```
   Agent(description="Map Practice 1", prompt="...")
   Agent(description="Map Practice 2", prompt="...")  
   Agent(description="Map Practice 3", prompt="...")
   Agent(description="Map Practice 4", prompt="...")
   ```

2. **Each agent prompt must include:**
   - File paths to read: `practices/<method-name>/01-analysis-report.md` (practice-specific section), `deps/platform-adoption-kernel.json`, `references/semantics.md`
   - What to generate: Complete practice mapping with metadata, alphas, work products, activities, patterns
   - Output location: Write to `practices/<method-name>/02-mapping-guide-practice-N.md` OR append to shared file with clear section markers
   - Explicit instruction: "Generate COMPLETE mapping including alphas (if any), work products, activities, AND PATTERNS. CRITICAL: Every practice MUST have at least ONE pattern coordinating multiple alphas/concerns (see semantics.md Section 8.1.1). Patterns are REQUIRED for multi-alpha practices."

3. **After all agents complete:**
   - Combine practice mapping files into single `02-mapping-guide.md` (if using separate files)
   - Add method-level metadata (citations, method narrative)
   - Validate completeness: every practice has alphas + work products + activities

**Critical: Multi-Agent Benefits**
- ✅ No token budget sharing between agents
- ✅ Concurrent execution (4 practices finish in time of 1)
- ✅ No quality degeneration (Practice 4 gets same quality as Practice 1)
- ✅ Each agent focuses on single practice (cleaner, more focused)
   - Complete mapping specification
   - Validation checklist satisfied

**Critical Mapping Rules:**

From `references/semantics.md`:

- **NO FLOATING ALPHAS:** All new alphas MUST have `contributesTo` (Section 4.1)
  - Valid targets: baseline alphas, practice-local alphas (internal hierarchy), or external practice alphas (creates dependency)
  - Practice-local references create multi-level specialization chains (Alpha C → B → A → Baseline)
  - External practice references require explicit practice dependency declaration
- **SEMANTIC RELATIONSHIPS:** Use baseline `relatesTo` for analysis; define new relationships for new alphas (Section 4.1 - Semantic Relationships)
  - **For baseline alpha analysis**: Read existing `relatesTo` relationships from baseline and dependent practices to understand how the alpha functions within the framework
  - **For new alphas ONLY**: Define domain-specific `relatesTo` relationships using appropriate relationship verbs
  - **Do NOT** add `relatesTo` to redeclarations - these inherit baseline relationships
  - Relationship types: dependency ("depends on", "requires"), production ("produces", "built by"), guidance ("guides", "constrains"), information flow ("provides", "validates"), enabling ("enables", "supports"), impact ("influences", "justifies"), consumption ("consumes", "hosts")
- **Exact name matching:** All baseline references are case-sensitive (Section 3)
- **Orthogonal tags:** Use {domainTags, lifecycleTags, organizationalTags} (Section 3.1.2)
- **Redeclaration vs Specialization:** Follow decision framework (Section 9.2.5)
- **Competency names:** Use EXACT baseline names, not descriptions (Section 6.2)
- **Single sentences:** Descriptions max 20 words, states/LODs max 12 (Section 3.1)

**CRITICAL: Narrative Structure Requirements**

**ALL narratives MUST be structured objects with narrativeTypeName and narrativeContexts arrays. NEVER use prose paragraphs.**

From `prompts/phase-2-mapping.md` (lines 87-89, 525-530):

1. **Practice/Method Narratives** - REQUIRED structured format:
   ```
   Practice Narrative:
   - Narrative Type Name: STAR | Hero's Journey | Three-Act Structure | Essay
   - Narrative Contexts:
     - Seq: 1, Narrative Element Name: [Situation], Context: [1-3 sentences]
     - Seq: 2, Narrative Element Name: [Task], Context: [1-3 sentences]
     - Seq: 3, Narrative Element Name: [Action], Context: [1-3 sentences]
     - Seq: 4, Narrative Element Name: [Result], Context: [1-3 sentences]
   ```

2. **Alpha Narratives** - REQUIRED for new alphas, RECOMMENDED for redeclarations:
   ```
   Narrative:
   - Narrative Type Name: Essay
   - Narrative Contexts:
     - Seq: 1, Narrative Element Name: Introduction, Context: Why this alpha matters
     - Seq: 2, Narrative Element Name: Body, Context: Key considerations and relationships
     - Seq: 3, Narrative Element Name: Conclusion, Context: Success factors
   - Citation Names: [citation references]
   ```

3. **Activity Narratives** - REQUIRED for all activities:
   ```
   Narrative:
   - Narrative Type Name: Technique
   - Narrative Contexts:
     - Seq: 1, Narrative Element Name: Overview, Context: What this activity accomplishes
     - Seq: 2, Narrative Element Name: Technique, Context: Step-by-step how-to guidance
     - Seq: 3, Narrative Element Name: Common Pitfalls, Context: What to avoid
   - Citation Names: [authoritative source references]
   ```

4. **Pattern Narratives** - Already structured in pattern views (keep as-is)

5. **Work Product Narratives** - OPTIONAL but recommended for complex work products

**WRONG (Prose Paragraph):**
```
Practice Narrative:
OpenShift Administration addresses the foundational infrastructure and operational 
concerns for enterprise container platforms. Organizations adopting OpenShift must...
```

**CORRECT (Structured Object):**
```
Practice Narrative:
- Narrative Type Name: STAR
- Narrative Contexts:
  - Seq: 1
    Narrative Element Name: Situation
    Context: Organizations face infrastructure challenges requiring enterprise container platforms.
  - Seq: 2
    Narrative Element Name: Task
    Context: Platform teams must establish secure, resilient OpenShift infrastructure.
  - Seq: 3
    Narrative Element Name: Action
    Context: Implement progressive maturity states from architecture to automated compliance.
  - Seq: 4
    Narrative Element Name: Result
    Context: Secure self-service container infrastructure delivered to development teams.
```

**Quality Check During Mapping:**
- [ ] Practice narrative uses structured format (NOT prose)
- [ ] Method narrative uses structured format (NOT prose)
- [ ] All new alphas have narrative objects with narrativeTypeName
- [ ] All activities have Technique narrative objects
- [ ] All narrative contexts are 1-3 sentences (NOT paragraphs)
- [ ] Citations referenced in citationNames arrays

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

**APPROACH DECISION:**

- **Single Practice**: Generate JSON directly (one step)
- **Multi-Practice Method (2+ practices)**: Use parallel Agent tool approach + assembly

**Process for Single Practice:**

1. Read `prompts/phase-3-json.md`, mapping guide, schema, baseline JSON
2. Generate complete practice JSON
3. Validate and fix until 0 errors

**Process for Multi-Practice Method:**

**Step 3A: Parallel Practice JSON Generation**

1. **Launch parallel agents** (one per practice) in single message:
   
   ```
   Agent(description="Generate Practice 1 JSON", prompt="...")
   Agent(description="Generate Practice 2 JSON", prompt="...")
   Agent(description="Generate Practice 3 JSON", prompt="...")
   Agent(description="Generate Practice 4 JSON", prompt="...")
   ```

2. **Each agent prompt must include:**
   - File paths: `practices/<method-name>/02-mapping-guide.md` (practice section), `deps/language.schema.json`, `deps/platform-adoption-kernel.json`
   - What to generate: **Practice JSON** (NOT method JSON) - single practice object with kind="practice"
   - Output location: `practices/<method-name>/<practice-name>.json`
   - Schema compliance: all required properties (alphas, activities, work products, **patterns**, etc.)
   - Explicit instruction: "Generate STANDALONE practice JSON, not embedded in method. CRITICAL: MUST include patterns array from mapping guide - minimum 1 pattern per practice with 2+ PatternViews showing alpha progression."

3. **Agents run concurrently**, each producing one practice JSON file

**Step 3B: Method Assembly**

4. **After all practice JSONs complete:**
   - Read all 4 practice JSON files
   - Create method structure:
     ```json
     {
       "kind": "method",
       "name": "Method Name",
       "description": "...",
       "baselinePracticeName": "Platform Adoption Essentials",
       "tags": {...},
       "narratives": [...],
       "citations": [...],
       "practices": [
         <practice-1-json-content>,
         <practice-2-json-content>,
         <practice-3-json-content>,
         <practice-4-json-content>
       ]
     }
     ```
   - Merge citations from all practices (deduplicate)
   - Ensure each embedded practice has `kind: "practice"`

**Step 3C: Validation and Fixes**

5. **Validate method JSON:**
   ```bash
   python3 utils/validate-practice-json.py \
     practices/<method-name>/<method-name>.json \
     deps/platform-adoption-kernel.json \
     deps/language.schema.json
   ```

6. **Fix errors:**
   - Schema violations (property names, types)
   - Cross-practice references (if any)
   - Missing properties
   - Iterate until 0 errors

**Critical: Multi-Agent Benefits for Phase 3**
- ✅ Each practice generated independently (no shared token budget)
- ✅ Concurrent execution (4x faster)
- ✅ Simpler prompts (each agent focuses on one practice)
- ✅ Easier debugging (one practice per file initially)
- ✅ Clean assembly step combines everything

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

### General Workflow Pitfalls

- ❌ **Not compacting between phases** (leads to token budget exhaustion and incomplete content)
- ❌ **Generating "example" or partial content** (all activities, alphas, patterns must be complete)
- ❌ Skipping phases or combining them (each phase has distinct purpose)

### Phase 1 Pitfalls
- ❌ Skipping EnterPlanMode
- ❌ Not reading domain-framework.md before analyzing
- ❌ Forcing template patterns instead of discovering source's natural progression
- ❌ Multi-sentence descriptions (violates conciseness standards)
- ❌ Insufficient citations (need 5-15 authoritative sources)
- ❌ **Incomplete activity coverage** (must include ALL activities identified, not just 1-2 examples)

### Phase 2 Pitfalls

- ❌ Not reading semantics.md before mapping
- ❌ Creating floating alphas (missing contributesTo)
- ❌ **CRITICAL: contributesTo only references baseline** - Forgetting that contributesTo can reference practice-local alphas (internal hierarchy) or external practice alphas (cross-practice dependency)
  - **Fix:** Consider all three contributesTo options: baseline, practice-local, external practice
  - Use State Alignment Heuristic to find best parent across all three sources
  - Document practice dependencies when using external practice references
- ❌ **Not using baseline relatesTo for alpha analysis** - Ignoring existing semantic relationships when analyzing baseline alphas
  - **Fix:** Read baseline alpha's `relatesTo` array to understand dependencies, production, governance patterns
  - Use relationships to inform how the alpha fits in the practice's value stream
  - Example: "Platform" is "governed by" Platform Governance → include governance activities in practice
- ❌ **Adding relatesTo to redeclarations** - Enriching baseline alphas should NOT add new relationships
  - **Fix:** Only define `relatesTo` on NEW alphas (specializations), not redeclarations
  - Redeclarations inherit baseline relationships automatically
- ❌ **Missing relatesTo on new alphas** - New specialized alphas lack semantic relationships to peer alphas
  - **Fix:** Define domain-specific relationships using appropriate verbs from semantics.md Section 4.1
  - Example: New alpha "Platform Capability" should relate to "Platform Asset" (produces), "Requirements" (validates), etc.
- ❌ **Using vague relationship verbs** - Generic "relates to" instead of specific relationship types
  - **Fix:** Use domain-appropriate verbs: "depends on", "produces", "guides", "validates", "enables", "constrains"
- ❌ Using competency descriptions instead of exact baseline names
- ❌ Using alias names in structural references (use canonical names)
- ❌ Wrong alpha approach (should use redeclaration vs specialization framework)
- ❌ Flat tags array instead of orthogonal structure
- ❌ **CRITICAL: Writing prose paragraphs instead of structured narrative objects**
- ❌ **Missing narrativeTypeName and narrativeContexts in narratives**
- ❌ **Omitting alpha narratives (required for new alphas)**
- ❌ **Omitting activity narratives (required for all activities)**
- ❌ **CRITICAL: Degeneration in multi-practice methods** - Practice 1 gets full alpha/work product/activity coverage, but later practices only get activities (missing alphas and work products)
  - **Fix:** Use multi-agent approach (Phase 2 and Phase 3)
  - Each practice MUST have: metadata, alphas (if any), work products, activities, **patterns**
  - Don't skip alpha/work product/pattern sections just because you're on Practice 3 or 4
- ❌ **Missing patterns** - Practices have 2+ alphas but no pattern coordinating them
  - **Fix:** Every multi-alpha practice MUST have at least one pattern
  - Pattern should have 3-5 PatternViews showing how alphas progress together
  - Use external lifecycle narratives (SDLC, PDCA, etc.) when appropriate

### Phase 3 Pitfalls

- ❌ Not reading language.schema.json before generating
- ❌ Checklist items as strings instead of objects
- ❌ Wrong competency reference format ({competencyName, level} instead of {competencyName, competencyLevelName})
- ❌ Using `requiredCompetencies` on personas (should be `competencies`)
- ❌ Missing BOTH `requiredCompetencies` AND `recommendedCompetencyLevels` on activities
- ❌ **Missing `activitySpaceName` property on activities** (required for flat Practice.activities)
- ❌ **Missing `kind` property** (required on Method, Practice, and all PracticeElements for type discrimination)
- ❌ Wrong PatternView property names (`alphas` instead of `alphaStates`, `views` instead of `patternViews`)
- ❌ Missing contributesTo on LODs
- ❌ **Adding relatesTo to redeclarations** - JSON includes relatesTo on baseline alpha redeclarations
  - **Fix:** Remove relatesTo from any alpha that is a redeclaration (same name as baseline alpha)
  - Only include relatesTo on NEW alphas (those with contributesTo to baseline)
- ❌ **Invalid alphaName in relatesTo** - Relationship references non-existent alpha
  - **Fix:** Validate every relatesTo.alphaName against defined alphas in baseline and practice
  - Use exact, case-sensitive alpha names
- ❌ **Missing relatesTo on new alphas from mapping guide** - Mapping specifies relationships but JSON omits them
  - **Fix:** Copy relatesTo array from mapping guide to JSON for all new alphas
- ❌ Markdown or metadata in JSON strings
- ❌ **Generating only 1-2 example activities** (must generate ALL activities from mapping guide)
- ❌ **Empty patterns array** when mapping guide has patterns
  - **Fix:** Verify patterns array populated with minimum 1 pattern per practice
  - Each pattern must have 2+ PatternViews with alphaStates showing progression

---

## Cross-Practice Dependencies and Alpha Hierarchies

### Internal Alpha Hierarchies (Practice-Local)

Practices can create multi-level alpha specialization chains where new alphas contribute to other new alphas within the same practice:

**Example:**

```text
Platform Service → Platform Capability → Platform (baseline)
```

**Requirements:**

- Referenced alpha must be defined EARLIER in the mapping guide
- Referenced alpha must have its own valid contributesTo chain
- Creates hierarchical rollup: child states influence parent progression

**Use When:**

- Building domain-specific maturity models with multiple specialization levels
- Source methodology has nested concern hierarchies
- Need fine-grained tracking at multiple abstraction levels

### External Practice Dependencies (Cross-Practice)

Practices can reference alphas from other practices, creating explicit dependencies:

**Example:**
```json
{
  "name": "Platform Team Topology",
  "contributesTo": "Team Interaction",  // from Team Topologies practice
  "dependencies": [
    {
      "practiceName": "Team Topologies",
      "reason": "Extends team interaction patterns for platform context"
    }
  ]
}
```

**Requirements:**

- **Phase 2:** Document dependency in practice metadata section of mapping guide
- **Phase 3:** Add to JSON `dependencies` array with practiceName and reason
- External practice must be available for validation (or validation must skip external references)
- Reference must use exact, case-sensitive alpha name from external practice

**Use When:**

- Source methodology builds on concepts from another well-known practice
- Avoiding duplication of alphas already defined elsewhere
- Creating practice compositions (e.g., Platform Engineering practice depends on Team Topologies)

**Validation Considerations:**

1. **During Phase 2 Mapping:**
   - Identify external practice references
   - Read external practice JSON if available to verify alpha exists
   - Document dependency rationale in mapping guide
   - Use State Alignment Heuristic to validate semantic fit

2. **During Phase 3 JSON Generation:**
   - Populate dependencies array with all external practices referenced
   - Ensure contributesTo references are exact matches (case-sensitive)
   - Document in practice description or narrative that it extends another practice

3. **During Validation:**
   - If external practice JSON is available: validate alpha name exists
   - If external practice JSON is NOT available: document assumption that reference will be resolved at runtime
   - Check for circular dependencies (Practice A → Practice B → Practice A)

**Multi-Practice Method Considerations:**

When generating a method with multiple practices:

- Practices within the method can reference each other's alphas
- These are still "external" references requiring dependency declarations
- Method assembly (Phase 3B) should validate cross-practice references across embedded practices

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
   - Includes assets section identifying visual artifacts

3. **`practices/<name>/<name>.json`**
   - Schema-compliant Practice or Method JSON
   - Validated against schema, baseline, internal integrity
   - Ready for consumption by Practice Language tools
   - Includes `assets` array if visual artifacts identified

4. **`practices/<name>/assets/`** (optional, if visual artifacts present)
   - Diagrams, templates, charts extracted from source materials
   - Organized by type: diagrams/, templates/, icons/
   - Referenced by JSON via relative paths

### Asset Bundling and Distribution

**Practices with Visual Artifacts:**

When Phase 2 identifies visual artifacts in source materials (diagrams, architecture visualizations, templates), the practice should be distributed as a bundle:

**Bundle Structure:**

```text
practice-name.bundle/
├── practice-name.json          # Main JSON with assets array
├── assets/
│   ├── diagrams/
│   │   ├── pattern-lifecycle.svg
│   │   ├── alpha-platform-states.png
│   │   └── architecture-reference.svg
│   ├── templates/
│   │   └── architecture-doc-template.pdf
│   └── icons/
│       └── practice-icon.svg
└── manifest.json               # Bundle metadata (optional)
```

**Manifest Format (Optional):**

```json
{
  "practiceName": "Practice Name",
  "version": "1.0.0",
  "created": "2026-06-10",
  "files": [
    {"path": "practice-name.json", "checksum": "sha256:..."},
    {"path": "assets/diagrams/pattern-lifecycle.svg", "checksum": "sha256:..."}
  ]
}
```

**Asset Workflow:**

1. **Phase 2 (Mapping)**: Identify and document visual artifacts in mapping guide
   - List asset name, description, proposed path, MIME type
   - Note which elements should reference each asset

2. **Phase 3 (JSON Generation)**: Populate `assets` array and `assetNames` properties
   - Add assets array to practice/method JSON
   - Link elements to assets via `assetNames` property
   - Use placeholder checksums (`sha256:tbd`)

3. **Post-Generation (Manual)**: Extract and organize asset files
   - Create `assets/` directory structure
   - Extract diagrams from source PDFs/docs
   - Save to paths specified in JSON
   - Compute real SHA-256 checksums
   - Update JSON with actual checksums

4. **Distribution**: Package as archive
   - Zip or tar the practice directory
   - Distribute as `.bundle.zip` or `.bundle.tar.gz`

**Asset Extraction Tools:**

Common tools for extracting assets from source materials:

- **PDFs**: `pdfimages`, Adobe Acrobat export
- **Web pages**: Browser "Save image as"
- **Screenshots**: Manual capture, annotation tools
- **Diagrams**: Export from source tools (draw.io, PlantUML, Visio)

**Asset Format Recommendations:**

- **Diagrams/Charts**: SVG (preferred - scalable, editable, text-based)
- **Screenshots**: PNG (lossless compression)
- **Photos**: JPEG (efficient for photos)
- **Documents**: PDF
- **Icons**: SVG (preferred for UI rendering)

**Checksum Generation:**

```bash
# Compute SHA-256 for an asset
sha256sum assets/diagrams/pattern-lifecycle.svg
# Output: abc123... assets/diagrams/pattern-lifecycle.svg

# Update JSON with sha256:abc123...
```

**Single-File Distribution (Alternative):**

For practices requiring single-file portability, small assets (icons, simple diagrams) can be embedded using data URIs:

```json
{
  "name": "practice-icon",
  "path": "data:image/svg+xml;base64,PHN2ZyB4bWxucz0i...",
  "mimeType": "image/svg+xml",
  "checksum": "sha256:abc123..."
}
```

Recommended for assets <10KB; use external files for larger assets.

### Using Delivered Artifacts

Users can:

- Review and edit phase outputs
- Regenerate specific phases if source changes
- Use analysis and mapping as methodology documentation
- Use JSON in tooling that consumes Practice Language
- Share JSON with teams and tools
- Distribute as bundles (with assets) or standalone JSON (without assets)
- Edit assets separately and update checksums
- Host assets on CDN and use URLs in path field (future enhancement)

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
