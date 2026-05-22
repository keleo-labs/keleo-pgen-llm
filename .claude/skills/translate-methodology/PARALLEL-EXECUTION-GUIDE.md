# Parallel Execution Guide - Translate Methodology Skill

**Purpose:** Practical instructions for executing the translate-methodology workflow with concurrent agents to maximize speed.

---

## Quick Reference

**Phase 1 Optimization:** 40% faster via 3-agent Wave 2  
**Phase 2 Optimization:** 75% faster via 9-agent parallel segments  
**Method Optimization:** 75% faster via N-agent parallel practices

---

## Phase 1: Wave-Based Module Generation

### Wave 1: Foundation (Sequential)

Generate analysis foundation and practice structure:

```
Agent 1: Module 00 (analysis-plan)
  ↓ wait for completion
Agent 2: Module 01 (practice-details)
```

**Prompt for Module 00:**
```markdown
Generate Module 00: Analysis Plan for {practice-name}

Source materials: {user-provided-sources}
Prompt: Read and apply prompts/phase-1-modules/00-analysis-plan.md
Output: practices/{practice-name}/report-elements/00-analysis-plan.md

Key deliverables:
- Four-perspective analysis framework application
- Alpha extension strategy
- Activity derivation plan
- Pattern identification approach
```

**Prompt for Module 01:**
```markdown
Generate Module 01: Practice Details for {practice-name}

Source materials: {user-provided-sources}
Dependencies: Read report-elements/00-analysis-plan.md
Prompt: Read and apply prompts/phase-1-modules/01-practice-details.md
Output: practices/{practice-name}/report-elements/01-practice-details.md

Key deliverables:
- Practice metadata (name, description, authors, version)
- Domain/lifecycle/organizational tags
- Context narratives
```

### Wave 2: Core Content (Parallel - 3 Agents)

**CRITICAL:** All 3 agents run SIMULTANEOUSLY using parallel Agent tool calls.

**Agent A - Citations:**
```markdown
Generate Module 02: Citations for {practice-name}

Source materials: {user-provided-sources}
Dependencies: Minimal (can read 01 for context but mostly independent)
Prompt: Read and apply prompts/phase-1-modules/02-citations.md
Output: practices/{practice-name}/report-elements/02-citations.md

Key deliverables:
- 5-15 authoritative citations in APA7 format
- Primary sources (methodology creators, official docs)
- Include all provided sources
- Citation Standard narrative type
```

**Agent B - Alphas (CRITICAL PATH):**
```markdown
Generate Module 03: Alphas for {practice-name}

Source materials: {user-provided-sources}
Dependencies: 
  - Read report-elements/00-analysis-plan.md for alpha extension decisions
  - Read report-elements/01-practice-details.md for practice context
Prompt: Read and apply prompts/phase-1-modules/03-alphas.md
Baseline: Read deps/platform-adoption-kernel.json for baseline alphas
Output: practices/{practice-name}/report-elements/03-alphas.md

Key deliverables:
- All alpha definitions (redeclarations + new alphas)
- States with 5-7 checklist criteria each
- contributesTo for all new alphas
- Context and Rationale narratives
- Alpha instances if applicable

CRITICAL:
- No floating alphas (all new alphas must have contributesTo)
- Single-sentence descriptions
- One-sentence checklist criteria
```

**Agent C - Work Products:**
```markdown
Generate Module 04: Work Products for {practice-name}

Source materials: {user-provided-sources}
Dependencies:
  - Read report-elements/00-analysis-plan.md for work product strategy
  - Read report-elements/01-practice-details.md for practice context
  - Lightly reference report-elements/03-alphas.md for alpha states (if Agent B finishes first)
Prompt: Read and apply prompts/phase-1-modules/04-workproducts.md
Reference: Read references/workproduct-assessment-rubric.csv for LOD guidance
Output: practices/{practice-name}/report-elements/04-workproducts.md

Key deliverables:
- All work product definitions
- 3-5 Levels of Detail per work product
- contributesTo alpha states for each LOD
- 3-5 characteristic criteria per LOD
- Usage narratives

CRITICAL:
- Single-sentence descriptions
- One-sentence LOD characteristics
- LOD.contributesTo is REQUIRED
```

**Execute Wave 2:** Use Agent tool with 3 parallel calls in a single message.

### Wave 3: Activities (Sequential)

Wait for Wave 2 to complete, then generate activities:

```
Agent: Module 05 (activities-roles)
```

**Prompt for Module 05:**
```markdown
Generate Module 05: Activities and Roles for {practice-name}

Source materials: {user-provided-sources}
Dependencies:
  - Read report-elements/00-analysis-plan.md for activity derivation plan
  - Read report-elements/01-practice-details.md for practice context
  - Read report-elements/03-alphas.md for alpha states
  - Read report-elements/04-workproducts.md for work products
Prompt: Read and apply prompts/phase-1-modules/05-activities-roles.md
Output: practices/{practice-name}/report-elements/05-activities-roles.md

Key deliverables:
- All activities with contributesTo alpha states
- Rich "How to Perform" technique narratives (STAR, How-To, etc.)
- worksOn work product references
- recommendedCompetencyLevels with exact baseline names
- All personas with competency requirements
- Persona Groups (teams) with member lists

CRITICAL:
- Activities MUST NOT duplicate ActivitySpace names
- Single-sentence descriptions for activities and personas
- Focused technique narratives (2-5 paragraphs, 2-4 sentences each)
- Exact baseline competency names (Analysis, Engineering, Leadership, Management, etc.)
```

### Wave 4: Patterns (Sequential)

Wait for Wave 3 to complete, then generate patterns:

```
Agent: Module 06 (patterns)
Agent: Module 07 (aliases) - optional, can run parallel with 06 if needed
```

**Prompt for Module 06:**
```markdown
Generate Module 06: Patterns for {practice-name}

Source materials: {user-provided-sources}
Dependencies:
  - Read report-elements/00-analysis-plan.md for pattern identification
  - Read report-elements/01-practice-details.md for practice context
  - Read report-elements/03-alphas.md for alpha states
  - Read report-elements/04-workproducts.md for work products
  - Read report-elements/05-activities-roles.md for activities
Prompt: Read and apply prompts/phase-1-modules/06-patterns.md
Output: practices/{practice-name}/report-elements/06-patterns.md

Key deliverables:
- Pattern definitions with narratives
- Pattern views (lifecycle orchestrations)
- Activities, alphas, work products per view
- Alpha instances and work product instances
- View sequencing (seq property)

CRITICAL:
- Single-sentence descriptions
- Each view must have seq number
- Track instances in views for assembly extraction
```

**Prompt for Module 07:**
```markdown
Generate Module 07: Aliases for {practice-name}

Source materials: {user-provided-sources}
Dependencies: Read all previous modules for element names
Prompt: Read and apply prompts/phase-1-modules/07-aliases.md
Output: practices/{practice-name}/report-elements/07-aliases.md

Key deliverables:
- Terminology mappings if source uses different terms
- OR "No aliases needed" if using same terminology as baseline

Note: This is often very short or empty.
```

---

## Phase 2: Parallel Segment Generation

### Segment Generation (Parallel - 9 Agents)

**CRITICAL:** All 9 agents run SIMULTANEOUSLY using parallel Agent tool calls.

**Pre-requisites:**
- All Phase 1 modules must be complete
- cross-reference-index.json must exist

**Create output directory:**
```bash
mkdir -p practices/{practice-name}/json-segments/practice-1/
```

**Segment Agent Prompts:**

**Agent 1 - Practice Skeleton:**
```markdown
Generate Segment 01: Practice Skeleton

Module: Read report-elements/practice-1/01-practice-details.md
Schema: Read deps/language.schema.json
Specs: Read .claude/skills/translate-methodology/SEGMENT-SCHEMA-SPECS.md (Segment 01)
Output: json-segments/practice-1/01-practice-skeleton.json

Extract: name, description, tags, authors, version, keywords
Format: JSON object (NOT array)
Size: ~2KB

CRITICAL:
- Clean all markdown syntax from text
- Single-sentence description
- Remove practice metadata phrases
```

**Agent 2 - Citations:**
```markdown
Generate Segment 02: Citations

Module: Read report-elements/practice-1/02-citations.md
Schema: Read deps/language.schema.json
Specs: Read .claude/skills/translate-methodology/SEGMENT-SCHEMA-SPECS.md (Segment 02)
Output: json-segments/practice-1/02-citations.json

Extract: All citations with authors, date, source, url
Format: JSON array of Citation objects
Size: ~3KB

Schema: {name, description, authors[], date, source, url}
```

**Agent 3 - Alphas (CRITICAL PATH):**
```markdown
Generate Segment 03: Alphas

Module: Read report-elements/practice-1/03-alphas.md (or 03a, 03b, 03c if split)
Schema: Read deps/language.schema.json
Specs: Read .claude/skills/translate-methodology/SEGMENT-SCHEMA-SPECS.md (Segment 03)
Baseline: Read deps/platform-adoption-kernel.json
Index: Read cross-reference-index.json for validation
Output: json-segments/practice-1/03-alphas.json

Extract: ALL alphas with:
- States (name, description, seq, checklist)
- Checklist items as OBJECTS {name, description, seq} NOT strings
- Narratives from "Context and Rationale" sections
- contributesTo for new alphas
- supportingAlphas if applicable

Format: JSON array of Alpha objects
Size: ~20-40KB (largest segment)

CRITICAL:
- Checklist MUST be objects, not strings
- contributesTo REQUIRED for new alphas
- Extract ALL narratives
- Clean all markdown and metadata phrases
```

**Agent 4 - Work Products:**
```markdown
Generate Segment 04: Work Products

Module: Read report-elements/practice-1/04-workproducts.md
Schema: Read deps/language.schema.json
Specs: Read .claude/skills/translate-methodology/SEGMENT-SCHEMA-SPECS.md (Segment 04)
Index: Read cross-reference-index.json for validation
Output: json-segments/practice-1/04-workproducts.json

Extract: ALL work products with:
- levelsOfDetail array (3-5 levels)
- LOD checklist items as OBJECTS {name, description, seq} NOT strings
- LOD.contributesTo REQUIRED (array of AlphaContribution)
- Usage narratives
- Work product instances if applicable

Format: JSON array of WorkProduct objects
Size: ~15-25KB

CRITICAL:
- Checklist MUST be objects, not strings
- LevelOfDetail.contributesTo is REQUIRED
- Extract ALL LOD checklists
```

**Agent 5 - Activities:**
```markdown
Generate Segment 05: Activities

Module: Read report-elements/practice-1/05-activities-roles.md (Activities section)
Schema: Read deps/language.schema.json
Specs: Read .claude/skills/translate-methodology/SEGMENT-SCHEMA-SPECS.md (Segment 05)
Index: Read cross-reference-index.json for validation
Output: json-segments/practice-1/05-activities.json

Extract: ALL activities with:
- contributesTo (array of AlphaContribution)
- worksOn (array of work product names)
- requiredCompetencies (array of competency names)
- recommendedCompetencyLevels (array of {competencyName, competencyLevelName})
- involves (array of persona names)
- narratives from "How to Perform" sections

Format: JSON array of Activity objects
Size: ~15-20KB

CRITICAL:
- Use {competencyName, competencyLevelName} NOT {competencyName, level}
- Include BOTH requiredCompetencies AND recommendedCompetencyLevels
- Extract ALL "How to Perform" narratives
- Clean all markdown
```

**Agent 6 - Personas:**
```markdown
Generate Segment 06: Personas

Module: Read report-elements/practice-1/05-activities-roles.md (Personas section)
Schema: Read deps/language.schema.json
Specs: Read .claude/skills/translate-methodology/SEGMENT-SCHEMA-SPECS.md (Segment 06)
Output: json-segments/practice-1/05-personas.json

Extract: ALL personas with:
- competencies array (NOT requiredCompetencies)
- Use {competencyName, competencyLevelName} format
- Extract from "**Competencies:**" sections

Format: JSON array of Persona objects
Size: ~3-5KB

CRITICAL:
- Property name is `competencies` NOT `requiredCompetencies`
- Extract ALL competency requirements
```

**Agent 7 - Teams:**
```markdown
Generate Segment 07: Teams

Module: Read report-elements/practice-1/05-activities-roles.md (Persona Groups section)
Schema: Read deps/language.schema.json
Specs: Read .claude/skills/translate-methodology/SEGMENT-SCHEMA-SPECS.md (Segment 07)
Output: json-segments/practice-1/05-teams.json

Extract: ALL persona groups with:
- personas array (list of persona names)
- Extract from "**Team Members:**" sections

Format: JSON array of PersonaGroup objects
Size: ~2KB

CRITICAL:
- Extract ALL team member lists
```

**Agent 8 - Patterns:**
```markdown
Generate Segment 08: Patterns

Module: Read report-elements/practice-1/06-patterns.md
Schema: Read deps/language.schema.json
Specs: Read .claude/skills/translate-methodology/SEGMENT-SCHEMA-SPECS.md (Segment 08)
Index: Read cross-reference-index.json for validation
Output: json-segments/practice-1/06-patterns.json

Extract: ALL patterns with:
- patternViews array
- PatternView.alphaStates (NOT alphas)
- PatternView.seq REQUIRED
- PatternView.activities (string names, not objects)
- NO workProducts property in PatternView (not in schema)
- alphaInstances and workProductInstances in views

Format: JSON array of Pattern objects
Size: ~10-20KB

CRITICAL:
- PatternView uses `alphaStates` NOT `alphas`
- PatternView.seq is REQUIRED
- NO `workProducts` property in PatternView
- activities are strings, not objects
```

**Agent 9 - Aliases:**
```markdown
Generate Segment 09: Aliases

Module: Read report-elements/practice-1/07-aliases.md
Schema: Read deps/language.schema.json
Specs: Read .claude/skills/translate-methodology/SEGMENT-SCHEMA-SPECS.md (Segment 09)
Output: json-segments/practice-1/07-aliases.json

Extract: Terminology mappings or empty array if no aliases

Format: JSON array of PracticeElementAlias objects (or [])
Size: ~2KB
```

**Execute All 9 Segments:** Use Agent tool with 9 parallel calls in a single message.

### Assembly (Automatic)

After all segments complete, run assembly script:

```bash
cd practices/{practice-name}
python3 assemble-practice-json.py 1  # or practice number
```

**What assembly does:**
1. Loads all 9 JSON segments
2. Extracts instances from patterns (alphaInstances, workProductInstances)
3. Merges into complete practice JSON structure
4. Validates completeness
5. Saves `practice-1-{name}.json`

---

## Multi-Practice Method Parallelization

### Method Planning Wave

**Sequential:**
```
Agent: Module 00 (method-plan)
```

**Prompt for Method Plan:**
```markdown
Generate Module 00: Method Plan for {method-name}

Source materials: {user-provided-sources}
Prompt: Read and apply prompts/phase-1-modules/00-method-plan.md
Output: practices/{method-name}/report-elements/00-method-plan.md

Key deliverables:
- Method overview and objectives
- Practice composition (how many practices, their scopes)
- Integration strategy
- Adoption guidance framework
```

### Practice Generation Wave (Parallel - N Agents)

**CRITICAL:** All N practice agents run SIMULTANEOUSLY.

For each practice 1..N, spawn an agent that executes the complete Phase 1 workflow:

**Agent for Practice 1:**
```markdown
Generate all Phase 1 modules for Practice 1: {practice-1-name}

Source materials: {user-provided-sources}
Dependencies: Read report-elements/00-method-plan.md for practice scope
Output directory: practices/{method-name}/report-elements/practice-1/

Execute Phase 1 workflow:
1. Module 00: analysis-plan
2. Module 01: practice-details
3. Wave 2 (parallel): modules 02, 03, 04
4. Module 05: activities-roles
5. Module 06: patterns
6. Module 07: aliases

Use the optimized wave approach internally.
```

**Agent for Practice 2:**
```markdown
Generate all Phase 1 modules for Practice 2: {practice-2-name}

Source materials: {user-provided-sources}
Dependencies: Read report-elements/00-method-plan.md for practice scope
Output directory: practices/{method-name}/report-elements/practice-2/

Execute Phase 1 workflow:
[Same as Practice 1]
```

**Execute All Practice Agents:** Use Agent tool with N parallel calls.

### Method Assembly Wave

After all practice modules complete:

```
Agent: Module 08 (method-assembly)
```

**Prompt for Method Assembly:**
```markdown
Generate Module 08: Method Assembly for {method-name}

Dependencies: Read all practice modules from practice-1/ through practice-N/
Prompt: Read and apply prompts/phase-1-modules/08-method-assembly.md
Output: practices/{method-name}/report-elements/08-method-assembly.md

Key deliverables:
- Integration patterns across practices
- Method-level orchestration
- Adoption pathways
- Cross-practice dependencies
```

---

## Validation Pipeline (Automated Sequence)

After JSON assembly, run validation pipeline without pauses:

```bash
cd practices/{practice-name}

# Phase 2.5: Schema compliance fixing
python3 ../../utils/fix-property-names.py
if [ $? -ne 0 ]; then echo "Schema fix failed"; exit 1; fi

# Phase 2.6: Baseline validation
python3 ../../utils/validate-baseline-references.py
if [ $? -ne 0 ]; then echo "Baseline validation failed"; exit 1; fi

# For methods: rebuild after fixes
if [ -f "rebuild-method-json.py" ]; then
    python3 rebuild-method-json.py
fi

# Phase 2.7: Internal integrity
python3 ../../utils/validate-internal-integrity.py
if [ $? -ne 0 ]; then 
    echo "⚠ Internal integrity issues found. Review INTERNAL-INTEGRITY-REPORT.md"
    exit 1
fi

# Phase 2.8: Schema validation
node ../../utils/validate-json-schema.js {practice-name}.json
if [ $? -ne 0 ]; then echo "Schema validation failed"; exit 1; fi

echo "✓ All validation passed!"
```

---

## Example: Complete Optimized Workflow

**User request:** `/translate-methodology https://aws.amazon.com/architecture/well-architected/`

**Execution:**

```python
# Step 1: Planning (5-10 min)
EnterPlanMode()
# Analysis: Single Practice (AWS Well-Architected Framework)
ExitPlanMode()

# Step 2: Phase 1 - Wave 1 (Sequential: 8 min)
Agent("Generate Module 00", prompt=module_00_prompt)
# Wait for completion
Agent("Generate Module 01", prompt=module_01_prompt)

# Step 3: Phase 1 - Wave 2 (Parallel: 20 min - critical path is alphas)
Agent(description="Generate citations", prompt=module_02_prompt)
Agent(description="Generate alphas", prompt=module_03_prompt)  # Critical path
Agent(description="Generate work products", prompt=module_04_prompt)
# All 3 run concurrently

# Step 4: Phase 1 - Wave 3 (Sequential: 20 min)
Agent("Generate Module 05", prompt=module_05_prompt)

# Step 5: Phase 1 - Wave 4 (Sequential: 15 min)
Agent("Generate Module 06", prompt=module_06_prompt)
Agent("Generate Module 07", prompt=module_07_prompt)

# Step 6: Phase 1.5 - Assembly (3 min)
Agent("Assemble research report", prompt=assembly_prompt)

# Step 7: Phase 2 - All Segments (Parallel: 20 min - critical path is alphas)
Agent(description="Generate segment 01", prompt=segment_01_prompt)
Agent(description="Generate segment 02", prompt=segment_02_prompt)
Agent(description="Generate segment 03", prompt=segment_03_prompt)  # Critical path
Agent(description="Generate segment 04", prompt=segment_04_prompt)
Agent(description="Generate segment 05", prompt=segment_05_prompt)
Agent(description="Generate segment 06", prompt=segment_06_prompt)
Agent(description="Generate segment 07", prompt=segment_07_prompt)
Agent(description="Generate segment 08", prompt=segment_08_prompt)
Agent(description="Generate segment 09", prompt=segment_09_prompt)
# All 9 run concurrently

# Step 8: Assembly (1 min)
Bash("python3 assemble-practice-json.py 1")

# Step 9: Validation Pipeline (10 min)
Bash(validation_pipeline_script)

# Total: ~97 minutes (vs ~180 minutes sequential)
```

---

## Tips for Efficient Parallel Execution

### 1. Batch Agent Calls in Single Message
```python
# ✅ Good: All run in parallel
Agent("task 1", ...)
Agent("task 2", ...)
Agent("task 3", ...)

# ❌ Bad: Run sequentially across multiple messages
# Message 1:
Agent("task 1", ...)
# Message 2:
Agent("task 2", ...)
# Message 3:
Agent("task 3", ...)
```

### 2. Monitor Critical Path
The longest-running agent determines wave completion time:
- **Wave 2:** Module 03 (alphas) is typically 15-20 min
- **Phase 2:** Segment 03 (alphas) is typically 15-20 min
- Other agents finish faster and wait

### 3. Handle Agent Failures Gracefully
If any agent in a wave fails:
- Note which agents succeeded
- Re-run only failed agents (don't repeat successful ones)
- Investigate failure cause before re-running

### 4. Use run_in_background for Very Long Waves
For multi-practice methods with many practices:
```python
Agent("Generate Practice 1 modules", run_in_background=True)
Agent("Generate Practice 2 modules", run_in_background=True)
Agent("Generate Practice 3 modules", run_in_background=True)
# Continue with other work, get notified when complete
```

### 5. Validate Segments Before Assembly
After parallel segment generation, quickly validate JSON syntax:
```bash
for seg in json-segments/practice-1/*.json; do
    jq empty "$seg" || echo "Invalid JSON: $seg"
done
```

---

## Performance Targets

| Metric | Sequential | Optimized | Target |
| ------ | ---------- | --------- | ------ |
| **Single Practice** | 130-195 min | 58-82 min | < 90 min |
| **2-Practice Method** | 270-400 min | 75-105 min | < 120 min |
| **3-Practice Method** | 405-600 min | 100-140 min | < 150 min |
| **5-Practice Method** | 675-1000 min | 150-200 min | < 240 min |

**Key Success Indicator:** Wall-clock time reduction of 50-75% while maintaining quality (≥95% validation pass rate).
