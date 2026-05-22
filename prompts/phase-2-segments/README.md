# Phase 2 Segment Generation

Rules and guidance for generating JSON segments from Phase 1 modules.

## Overview

**Phase 2 uses a segmented approach** to avoid token limits and enable parallel execution. Instead of generating a monolithic 100KB JSON file in one pass, Phase 2 generates 9 smaller JSON segments (2-40KB each) that are then mechanically assembled.

**Benefits:**
- ✅ Each segment fits within agent token limits
- ✅ Can regenerate individual segments without touching others
- ✅ Clear 1:1 mapping: Phase 1 module → JSON segment
- ✅ All 9 segments can be generated in parallel
- ✅ Assembly is mechanical (Python script, no LLM ambiguity)

## Segment Generation Rules

**File:** [segment-generation-rules.md](segment-generation-rules.md)

Comprehensive rules for generating schema-compliant JSON segments, including:

- Segment structure and size expectations
- Schema compliance requirements
- Common violations to avoid
- Checklist format rules
- Competency reference formats
- Pattern view structures

**This file should be read by agents before generating ANY segment.**

## Segment Mapping

Each Phase 1 module maps to one or more JSON segments:

| Phase 1 Module | JSON Segment(s) | Content | Size |
| -------------- | --------------- | ------- | ---- |
| 01-practice-details.md | 01-practice-skeleton.json | Practice metadata, tags, authors | ~2KB |
| 02-citations.md | 02-citations.json | Citation objects array | ~3KB |
| 03-alphas.md | 03-alphas.json | Alpha objects array with states | ~20-40KB |
| 04-workproducts.md | 04-workproducts.json | WorkProduct objects array with LODs | ~15-25KB |
| 05-activities-roles.md | 05-activities.json | Activity objects array | ~15-20KB |
| 05-activities-roles.md | 05-personas.json | Persona objects array | ~3-5KB |
| 05-activities-roles.md | 05-teams.json | PersonaGroup objects array | ~2KB |
| 06-patterns.md | 06-patterns.json | Pattern objects array with views | ~10-20KB |
| 07-aliases.md | 07-aliases.json | PracticeElementAlias objects array | ~2KB |

**Total:** 9 segments per practice

## Critical Schema Requirements

Before generating any segment, agents must understand these critical requirements:

### 1. Checklist Format

**WRONG:**
```json
"checklist": ["Criterion 1", "Criterion 2", "Criterion 3"]
```

**CORRECT:**
```json
"checklist": [
  {
    "name": "Criterion Name",
    "description": "Specific verifiable criterion",
    "seq": 1
  },
  {
    "name": "Another Criterion",
    "description": "Another verifiable criterion",
    "seq": 2
  }
]
```

**Applies to:**
- Alpha state checklists
- Work product LOD checklists

### 2. Competency Level References

**WRONG:**
```json
{
  "competencyName": "Engineering",
  "level": "Applies"
}
```

**CORRECT:**
```json
{
  "competencyName": "Engineering",
  "competencyLevelName": "Applies"
}
```

**Applies to:**
- Activity recommendedCompetencyLevels
- Persona competencies

### 3. Activity Competencies (Both Required)

Activities must have BOTH:

```json
{
  "requiredCompetencies": ["Engineering", "Analysis"],
  "recommendedCompetencyLevels": [
    {
      "competencyName": "Engineering",
      "competencyLevelName": "Applies"
    },
    {
      "competencyName": "Analysis",
      "competencyLevelName": "Knows"
    }
  ]
}
```

### 4. New Alphas Must Have contributesTo

**WRONG:**
```json
{
  "name": "AI Model Catalog",
  "description": "Repository of AI models",
  "focusName": "Solution",
  "states": [...]
}
```

**CORRECT:**
```json
{
  "name": "AI Model Catalog",
  "description": "Repository of AI models",
  "focusName": "Solution",
  "contributesTo": [
    {
      "alphaName": "Platform Asset",
      "stateName": "Conceived"
    }
  ],
  "states": [...]
}
```

### 5. Pattern View Properties

**Schema-compliant PatternView:**
```json
{
  "seq": 1,
  "name": "View Name",
  "description": "View description",
  "alphaStates": [
    {
      "alphaName": "Alpha Name",
      "stateName": "State Name"
    }
  ],
  "activities": ["Activity Name 1", "Activity Name 2"]
}
```

**Common mistakes:**
- ❌ Using `alphas` instead of `alphaStates`
- ❌ Adding `workProducts` property (not in schema)
- ❌ Missing `seq` property (required)
- ❌ Activity objects instead of strings

### 6. LevelOfDetail.contributesTo (Required)

Every LOD must have contributesTo:

```json
{
  "seq": 1,
  "name": "Level Name",
  "description": "Level description",
  "contributesTo": [
    {
      "alphaName": "Platform",
      "stateName": "Architecture Selected"
    }
  ],
  "checklist": [...]
}
```

## Assembly Process

After all 9 segments are generated, run assembly script:

```bash
python3 assemble-practice-json.py <practice-number>
```

**What assembly does:**
1. Loads all 9 JSON segments
2. Extracts instances from patterns:
   - `alphaInstances` from pattern views
   - `workProductInstances` from pattern views
3. Merges into complete practice JSON structure:
   ```json
   {
     "name": "...",
     "description": "...",
     "citations": [],        // from segment 02
     "alphas": [],           // from segment 03
     "workProducts": [],     // from segment 04
     "activities": [],       // from segment 05-activities
     "personas": [],         // from segment 05-personas
     "personaGroups": [],    // from segment 05-teams
     "patterns": [],         // from segment 06
     "practiceElementAliases": [],  // from segment 07
     "alphaInstances": [],   // extracted by assembly
     "workProductInstances": []  // extracted by assembly
   }
   ```
4. Validates completeness
5. Saves `practice-N-<name>.json`

## Parallel Execution

All 9 segments can be generated **simultaneously** using parallel Agent tool calls:

```python
# Agent 1: Skeleton
Agent(description="Generate practice skeleton",
      prompt="Generate 01-practice-skeleton.json from 01-practice-details.md...")

# Agent 2: Citations
Agent(description="Generate citations",
      prompt="Generate 02-citations.json from 02-citations.md...")

# ... Agent 3-9 ...
# All 9 agents run concurrently
```

**Critical path:** Segment 03 (alphas) typically takes longest (~15-20 min)

See `.claude/skills/translate-methodology/PARALLEL-EXECUTION-GUIDE.md` for detailed parallel execution instructions with ready-to-use agent prompts.

## Validation Before Assembly

After segment generation, validate JSON syntax:

```bash
for seg in json-segments/practice-1/*.json; do
    jq empty "$seg" || echo "Invalid JSON: $seg"
done
```

## Output Location

```
practices/<name>/
└── json-segments/
    └── practice-1/
        ├── 01-practice-skeleton.json
        ├── 02-citations.json
        ├── 03-alphas.json
        ├── 04-workproducts.json
        ├── 05-activities.json
        ├── 05-personas.json
        ├── 05-teams.json
        ├── 06-patterns.json
        └── 07-aliases.json
```

## Common Issues and Solutions

### Issue: Checklist items as strings

**Symptom:** Schema validation fails with "must be object"

**Solution:** Use checklist object format with name, description, seq

### Issue: Missing contributesTo on new alphas

**Symptom:** Floating alpha validation error

**Solution:** Add contributesTo array pointing to baseline alpha

### Issue: Wrong competency property names

**Symptom:** Schema validation fails on Activity or Persona

**Solution:**
- Activities: Use `recommendedCompetencyLevels` with `competencyLevelName`
- Personas: Use `competencies` (not `requiredCompetencies`)

### Issue: Pattern view using wrong properties

**Symptom:** Schema validation fails on PatternView

**Solution:**
- Use `alphaStates` not `alphas`
- Include `seq` property
- Don't add `workProducts` property
- Activities are strings, not objects

## Related Documentation

- **Main Phase 2 Prompt:** [../phase-2-modular.md](../phase-2-modular.md)
- **Segment Schema Specs:** `../../.claude/skills/translate-methodology/SEGMENT-SCHEMA-SPECS.md`
- **Schema Reference:** `../../deps/language.schema.json`
- **Semantic Guidance:** `../../references/semantics.md`
- **Schema Violations Catalog:** [../reference/schema-violations-complete.md](../reference/schema-violations-complete.md)
