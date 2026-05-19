---
name: translate-methodology
description: Transform enterprise methodology documentation into schema-compliant Practice Language JSON using a two-phase LLM workflow
triggerPatterns:
  - "translate.*methodology"
  - "generate.*practice.*json"
  - "convert.*framework.*practice"
  - "methodology.*translation"
---

# Methodology Translation Skill

This skill transforms enterprise methodology documentation (e.g., AWS Well-Architected, SAFe, TOGAF, Team Topologies) into schema-compliant Practice Language JSON using a rigorous two-phase workflow.

## Workflow Overview

**Phase 1: Research Analysis** → Human-readable structured report  
**Phase 2: JSON Translation** → Schema-compliant JSON

This is a complex, multi-step process. **You MUST use EnterPlanMode** before beginning work to:
1. Understand the source materials provided
2. Plan the research approach across the four perspectives
3. Identify potential practices and their boundaries
4. Create a step-by-step execution plan

## Required Resources

The following files guide the translation process:

### Phase Instructions
- `gemini-prompts/phase 1 gem.md` - Research analyst instructions (82KB comprehensive guide)
- `gemini-prompts/phase 2 gem.md` - JSON translation instructions (44KB schema mapping)

### Reference Framework
- `references/domain-framework.md` - Four-perspective analysis framework (Business, Technology, People, Process)
- `references/workproduct-assessment-rubric.csv` - 5-level maturity rubric for states and levels of detail
- `references/semantics.md` - Comprehensive semantic guidance for schema interpretation

### Schema & Baseline
- `deps/language.schema.json` - JSON Schema that output MUST validate against
- `deps/platform-adoption-kernel.json` - Platform Adoption Essentials baseline (all alphas, activity spaces, competencies, narrative types)

## User Input

The user will provide source methodology materials via:
- **Files**: PDFs, markdown, documentation exports
- **URLs**: Web documentation, whitepapers, framework sites
- **Iterative refinement**: Additional context or clarification

## Phase 1: Research Analysis

Your objective is to act as a **Practice Research Analyst** and create a comprehensive human-readable research report.

### Output File Management

**CRITICAL:** Early in your analysis, determine the name for the Method or Practice being created. Use this name to:

1. **Create a subdirectory** in the `practices/` directory:
   ```bash
   mkdir -p practices/<practice-or-method-name>
   ```
   
2. **Choose appropriate naming**:
   - Use kebab-case (lowercase with hyphens)
   - Be descriptive but concise
   - Example: `aws-well-architected`, `team-topologies`, `safe-platform-adoption`

3. **Save the Phase 1 report** as a markdown file in this directory:
   ```
   practices/<practice-or-method-name>/research-report.md
   ```
   
   OR use a more descriptive name:
   ```
   practices/<practice-or-method-name>/<practice-name>-research-report.md
   ```

**Before proceeding to Phase 2**, ensure the report is written to the appropriate file location.

### Analysis Framework

Apply the four-perspective analysis from `references/domain-framework.md`:

1. **Business Perspective**: Value proposition, ROI, stakeholder alignment, risk/compliance
   - Maps to: Value focus areas
   - Assess maturity using the rubric

2. **Technology Perspective**: Architecture, implementation, integration, deployment, lifecycle
   - Maps to: Solution focus areas
   - Assess maturity using the rubric

3. **People Perspective**: Roles, skills, team design, organizational change
   - Maps to: Endeavor focus areas
   - Assess maturity using the rubric

4. **Process Perspective**: Workflows, value realization, strategy, industry alignment
   - Maps to: May span multiple focuses
   - Assess maturity using the rubric

### Key Decisions During Research

**Alpha Handling** (critical - read `gemini-prompts/phase 1 gem.md` section on this):
- **Redeclaration**: Enriching baseline alphas with practice-specific checklists
- **Specialization**: Creating new alphas that contribute to baseline alphas
- **Instances**: Tracking specific occurrences (e.g., "Platform Team" instance of "Team")
- **Multi-perspective merging**: When the same alpha appears in multiple perspectives, create ONE merged redeclaration

**Activity Derivation**:
- Bottom-up from Alpha state progression needs
- Must map to baseline ActivitySpace names (load from `deps/platform-adoption-kernel.json`)
- Activity names must be SPECIFIC and different from ActivitySpace names
- Example: ActivitySpace "Architect and Build the Foundation" → Activity "Design Infrastructure Architecture"

**Practice Partitioning**:
- Analyze for distinct practices based on:
  - Different use-cases (greenfield vs brownfield)
  - Different value-streams (building vs consuming)
  - Different stakeholder journeys
  - Different capability domains
- Bias toward multiple focused practices over monolithic ones

### Report Structure

Follow the exact structure defined in `gemini-prompts/phase 1 gem.md`:
- Executive Summary
- Methodology Overview
- Practice sections with:
  - Practice Overview
  - Context and Background (narratives)
  - Focus sections (Value, Solution, Endeavor)
    - Alphas with progressive states
    - Work Products with levels of detail
  - Activities and Responsibilities
  - Roles and Teams
  - Patterns and Workflows
- **Citations and References** (MANDATORY)
  - APA7 format
  - Citation Standard narratives
  - 5-15 authoritative sources per practice
- Appendix: Terminology Mapping (if applicable)

### Critical Requirements for Phase 1

1. **Write in natural prose** - NOT pseudo-code or JSON-like notation
2. **Be comprehensive** - Capture all verification criteria, all techniques
3. **Use structured headers** - Enable Phase 2 parsing
4. **Include rich narratives** - Especially in "How to Perform This Activity" sections
5. **Cite authoritative sources** - Primary methodology creators preferred
6. **Apply maturity rubric** - Use the CSV to inform LOD and State progressions

## Phase 2: JSON Translation

Your objective is to act as a **Data Translation Engine** and convert the Phase 1 report into schema-compliant JSON.

### Output File Management

**CRITICAL:** Store the generated JSON in the same directory as the Phase 1 report:

1. **Locate the Phase 1 directory**: `practices/<practice-or-method-name>/`

2. **Save the JSON output** using the practice/method name:
   ```
   practices/<practice-or-method-name>/<practice-name>.json
   ```
   
   For a Method with multiple practices:
   ```
   practices/<method-name>/<method-name>.json
   ```

3. **Final directory structure should be**:
   ```
   practices/
   └── <practice-or-method-name>/
       ├── research-report.md          # Phase 1 output
       └── <practice-name>.json        # Phase 2 output
   ```

**After writing the JSON file**, validate it against the schema if possible.

### Translation Process

**Step 1: Load Baseline Data**

Read `deps/platform-adoption-kernel.json` to extract:
- Exact Alpha names, State names for each
- Exact ActivitySpace names
- Exact Competency names and CompetencyLevel names
- Exact NarrativeType names and their NarrativeElement structures
- Exact Focus names ("Value", "Solution", "Endeavor")

**Step 2: Parse Report Structure**

Systematically extract from the Phase 1 report:
- Alphas from focus sections → Alpha objects with states
- WorkProducts from focus sections → WorkProduct objects with LODs
- Activities from activity sections → Activity objects
- Personas and PersonaGroups from roles section
- Patterns and PatternViews from patterns section
- Citations → Narrative objects with narrativeTypeName: "Citation Standard"
- Terminology mappings → PracticeElementAlias objects

**Step 3: Intelligent Content Extraction**

**Narratives**:
- Identify narrative type from content structure (STAR, StoryBrand, Essay, Lifecycle, etc.)
- Segment prose into NarrativeContext objects
- Map paragraphs to appropriate narrativeElementName values

**States & Checklists**:
- Extract state descriptions
- Convert criteria bullets to Checklist objects with seq numbers
- Generate brief checklist names from descriptions

**LODs & Contributions**:
- Extract level descriptions
- Convert criteria to Checklist objects
- Parse "provides evidence for" into AlphaContribution objects

**Activities**:
- Extract activity descriptions
- Parse "Outcomes and Alpha Progression" → contributesTo array
- Parse "Work Products Created/Refined" → worksOn array
- Parse "Required Capabilities" → requiredCompetencies & recommendedCompetencyLevels
- Parse "Team Involvement" → involves array (PersonaGroup names ONLY)
- Parse "How to Perform This Activity" subsections → narratives array

**Step 4: Exact Name Matching**

**CRITICAL VALIDATION** - All symbolic references must be exact, case-sensitive string matches:
- alphaName → must match baseline or declared Alpha.name
- stateName → must match State.name within that Alpha
- activitySpaceName → must match baseline ActivitySpace.name exactly
- competencyName → must match baseline Competency.name exactly
- competencyLevelName → must be: "Basic", "Applies", "Masters", "Adapts", or "Innovating"
- narrativeTypeName → must match baseline NarrativeType.name exactly
- narrativeElementName → must match NarrativeElement.name in that NarrativeType

**If you find a mismatch**: Check terminology mappings, check for typos, DO NOT GUESS.

**Step 5: Generate Metadata and Tags**

**Metadata**:
```json
{
  "authors": ["Generated by Claude Code from source methodology"],
  "createdAt": "2026-05-19",
  "updatedAt": "2026-05-19",
  "version": "1.0",
  "keywords": [/* extract from executive summary */]
}
```

**Tags** (extract from practice overview):
```json
{
  "tags": {
    "domainTags": ["Architecture", "Security", "FinOps", ...],
    "lifecycleTags": ["Strategy", "Implementation", "Operations", ...],
    "organizationalTags": [/* business units, org levels */]
  }
}
```

**Step 6: Assemble JSON Structure**

**Single Practice**:
```json
{
  "name": "...",
  "description": "...",
  "baselinePracticeName": "Platform Adoption Essentials",
  "tags": {...},
  "practiceElementAliases": [...],
  "narratives": [...],
  "alphas": [...],
  "alphaInstances": [...],
  "workProducts": [...],
  "workProductInstances": [...],
  "activities": [...],
  "personas": [...],
  "personaGroups": [...],
  "patterns": [...],
  "authors": [...],
  "createdAt": "...",
  "updatedAt": "...",
  "version": "...",
  "keywords": [...]
}
```

**Multiple Practices (Method)**:
```json
{
  "name": "Method Name",
  "description": "...",
  "baselinePracticeName": "Platform Adoption Essentials",
  "practices": [
    {/* full Practice object 1 */},
    {/* full Practice object 2 with practiceDependencyNames if needed */}
  ],
  "narratives": [/* method-level narratives */]
}
```

### Critical Requirements for Phase 2

1. **Zero hallucination** - Only use names from baseline or declared in practice
2. **Complete translation** - No truncation, no placeholders, no "// omitted"
3. **Exact matching** - All symbolic references must be precise string matches
4. **Instance handling** - AlphaInstanceName in practice.alphaInstances, AlphaInstance in PatternView.alphaInstances
5. **Redeclaration integrity** - Preserve baseline descriptions/state names exactly
6. **Citations included** - Every practice must have Citation Standard narratives
7. **Activity naming** - No activity name matches its ActivitySpace name

## Validation Checklist

Before finalizing Phase 2 output, verify:

### Schema Compliance
- [ ] All REQUIRED fields present
- [ ] Arrays meet minimum items (states ≥3, levelsOfDetail ≥2)
- [ ] No invented properties
- [ ] Correct property names (e.g., "evidenceBy" not "evidencedBy" on AlphaInstance)

### Exact Name Matching
- [ ] All alphaName, stateName, activitySpaceName, workProductName, levelOfDetailName, competencyName, competencyLevelName, narrativeTypeName, narrativeElementName references are exact matches

### Completeness
- [ ] No empty required arrays
- [ ] All narrativeContexts complete for their narrative type
- [ ] All PersonaGroups and Personas defined and referenced correctly

### Citations
- [ ] Practice has 5-15 Citation Standard narratives
- [ ] Each citation has Author, Date, Title, Source
- [ ] Citations from authoritative sources

### Focus Consistency
- [ ] Every Alpha has focusName: "Value", "Solution", or "Endeavor"
- [ ] Every Activity focusName matches its ActivitySpace's focus

### Activity Naming
- [ ] No Activity.name exactly matches its activitySpaceName
- [ ] All Activity names are specific (verb + specific subject)

## Final Output

**Phase 1**: 
1. Determine practice/method name early in analysis
2. Create subdirectory: `practices/<practice-name>/`
3. Write research report: `practices/<practice-name>/research-report.md`

**Phase 2**: 
1. Read the Phase 1 report from `practices/<practice-name>/research-report.md`
2. Generate schema-compliant JSON
3. Write JSON: `practices/<practice-name>/<practice-name>.json`
4. Validate against schema (optional but recommended)

**Validation command** (if validation tools available):
```bash
# If using a JSON schema validator like ajv-cli
ajv validate -s deps/language.schema.json -d practices/<practice-name>/<practice-name>.json
```

**Final deliverables in `practices/<practice-name>/`**:
- `research-report.md` - Human-readable analysis and methodology mapping
- `<practice-name>.json` - Schema-compliant Practice or Method JSON

## Execution Notes

1. **Always start with EnterPlanMode** to analyze sources and plan approach
2. **Read all reference files** before starting Phase 1
3. **Determine naming early** - Establish practice/method name at start of Phase 1 to create proper directory structure
4. **Create directory structure** - Use `mkdir -p practices/<practice-name>/` before writing files
5. **Take your time in Phase 1** - Rich narratives and complete research enable accurate Phase 2 translation
6. **Be exact in Phase 2** - Fuzzy matching will produce invalid JSON
7. **Write files to correct locations** - All outputs for a practice go in the same subdirectory
8. **Iterate with the user** - Ask for clarification if source materials are ambiguous

## Common Pitfalls to Avoid

- **Phase 1**: Writing pseudo-JSON instead of natural prose
- **Phase 1**: Omitting "How to Perform This Activity" guidance
- **Phase 1**: Missing citations
- **Phase 2**: Guessing baseline element names instead of exact matching
- **Phase 2**: Using Activity name that duplicates ActivitySpace name
- **Phase 2**: Creating multiple alpha declarations when should be one merged redeclaration
- **Phase 2**: Putting AlphaInstance in practice.alphaInstances (should be AlphaInstanceName)
- **Both**: Not applying the four-perspective framework rigorously
