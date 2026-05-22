# Segment Generation Rules - Schema Compliance

**CRITICAL:** All generated JSON MUST comply with `/Users/eseymour/code/keleo-pgen-llm/deps/language.schema.json`

## Checklist Format (MOST COMMON ERROR)

**WRONG (string):**
```json
"checklist": [
  "Platform team established with 2+ engineers: Core infrastructure team formed..."
]
```

**CORRECT (object):**
```json
"checklist": [
  {
    "name": "Platform Team Established",
    "description": "Core infrastructure team formed with minimum 2 platform engineers assigned full-time, roles defined (lead engineer, operations engineer), reporting structure established, and team has access to necessary tools and systems.",
    "seq": 1
  }
]
```

## Schema Requirements by Element

### AlphaState.checklist
- **Type:** Array of Checklist objects
- **Required fields:** name (string), description (string), seq (integer)
- **Optional:** verificationMethod, evidencedBy
- **Source:** Parse checklist criteria from alpha state sections

### LevelOfDetail.checklist  
- **Type:** Array of Checklist objects
- **Required fields:** name (string), description (string), seq (integer)
- **Source:** Parse LOD characteristics/checklist items

### Activity.requiredCompetencies
- **Type:** Array of CompetencyLevelReference objects
- **Format:** `{"competencyName": "string", "level": integer}`
- **Source:** Parse from "Required Competencies" sections

### Activity.techniqueNarratives
- **Type:** Array of Narrative objects
- **Structure:**
  ```json
  {
    "narrativeTypeName": "How-To Guide" | "STAR Format" | "Lifecycle",
    "narrativeContexts": [
      {
        "narrativeElementName": "Step 1" | "Situation" | etc,
        "context": "Detailed narrative text...",
        "seq": 1
      }
    ]
  }
  ```

## Text Cleaning Rules

1. Remove ALL markdown syntax: `**bold**`, `*italic*`, `# headers`, `- bullets`
2. Remove metadata phrases: "From module:", "Based on:", "As described in:"
3. Keep domain content and technical details
4. Preserve natural sentence structure

## Semantic Guidance (from semantics.md)

### Section 3.3 - Checklists
> "A checklist item must represent a demonstrable operational truth required for phase-gating."

Checklist descriptions should be:
- **Specific:** State exactly what must be true
- **Verifiable:** Can be checked via evidence
- **Actionable:** Practitioner knows what to do

### Section 4.1 - Alphas
> "Baseline Isolation Rules: All new Alphas introduced in a Practice must logically refine a parent concept by explicitly declaring a contributesTo relationship."

**NO FLOATING ALPHAS:** Every new alpha MUST have `contributesTo` array with parent alpha name.

### Section 9.3 - PracticeElement Adaptation
> "The new practice MUST NOT change the name property of the original element"
> "The new practice MUST NOT change the description property of the original element"

When redeclaring baseline alphas: Keep exact name and description, add new states/checklists only.

## Output Validation Checklist

Before saving ANY segment JSON:

- [ ] All `checklist` arrays contain objects with {name, description, seq}
- [ ] All `contributesTo` arrays reference valid alpha names
- [ ] All `requiredCompetencies` use proper object format
- [ ] All text is cleaned (no markdown)
- [ ] JSON syntax is valid (run `jq empty <file>`)
- [ ] File size is within expected range for segment type
