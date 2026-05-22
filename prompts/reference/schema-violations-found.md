# Complete Schema Violations Found in Generated JSON

## CRITICAL: All segments must be regenerated with these fixes

---

## 1. Checklist Format (AFFECTS: Alphas, WorkProducts)

**WRONG:**
```json
"checklist": [
  "Platform team established with 2+ engineers"
]
```

**CORRECT:**
```json
"checklist": [
  {
    "name": "Platform Team Established",
    "description": "Platform team established with 2+ engineers",
    "seq": 1
  }
]
```

**Fix in:** 03-alphas.json, 04-workproducts.json

---

## 2. CompetencyLevelReference Format (AFFECTS: Activities, Personas)

**WRONG:**
```json
"recommendedCompetencyLevels": [
  {
    "competencyName": "Engineering",
    "level": 5
  }
]
```

**CORRECT:**
```json
"recommendedCompetencyLevels": [
  {
    "competencyName": "Engineering",
    "competencyLevelName": "Expert"
  }
]
```

**Competency level names:**
- Level 1: "Awareness"
- Level 2: "Novice"  
- Level 3: "Proficient"
- Level 4: "Advanced"
- Level 5: "Expert"

**Fix in:** 05-activities.json, 05-personas.json

---

## 3. Persona.competencies Property Name (AFFECTS: Personas)

**WRONG:**
```json
{
  "name": "Platform Engineer",
  "requiredCompetencies": [...]
}
```

**CORRECT:**
```json
{
  "name": "Platform Engineer",
  "competencies": [...]
}
```

**Schema says:** `Persona.competencies` (not `requiredCompetencies`)

**Fix in:** 05-personas.json

---

## 4. Activity Required vs Recommended Competencies (AFFECTS: Activities)

**Activities must have BOTH:**

```json
{
  "name": "Deploy AI Platform Infrastructure",
  "requiredCompetencies": [
    "Engineering",
    "Site Reliability"
  ],
  "recommendedCompetencyLevels": [
    {
      "competencyName": "Engineering",
      "competencyLevelName": "Expert"
    },
    {
      "competencyName": "Site Reliability",
      "competencyLevelName": "Proficient"
    }
  ]
}
```

- `requiredCompetencies`: Simple string array of competency names
- `recommendedCompetencyLevels`: Array of CompetencyLevelReference objects

**Fix in:** 05-activities.json

---

## 5. PatternView Property Names (AFFECTS: Patterns)

**WRONG:**
```json
{
  "name": "Prerequisites",
  "alphas": [
    {"alphaName": "Platform", "stateName": "Ready"}
  ],
  "workProducts": [
    {"workProductName": "Architecture Doc", "levelOfDetailName": "Detailed"}
  ],
  "activities": ["Deploy Infrastructure"]
}
```

**CORRECT:**
```json
{
  "name": "Prerequisites",
  "seq": 1,
  "alphaStates": [
    {"alphaName": "Platform", "stateName": "Ready"}
  ],
  "activities": ["Deploy Infrastructure"]
}
```

**Critical changes:**
- Property is `alphaStates` (NOT `alphas`)
- Property is `activities` (activity NAMES as strings)
- NO `workProducts` property in PatternView schema
- `seq` is REQUIRED

**Fix in:** 06-patterns.json

---

## 6. LevelOfDetail.contributesTo is REQUIRED (AFFECTS: WorkProducts)

**Each level of detail MUST have contributesTo:**

```json
{
  "name": "Outlined",
  "description": "...",
  "seq": 1,
  "checklist": [...],
  "contributesTo": [
    {
      "alphaName": "Platform",
      "stateName": "Architecture Selected"
    }
  ]
}
```

**Schema says:** `contributesTo` is REQUIRED on LevelOfDetail

**Fix in:** 04-workproducts.json

---

## Summary of Affected Segments

| Segment | Violations |
|---------|-----------|
| 03-alphas.json | Checklist format |
| 04-workproducts.json | Checklist format, LOD.contributesTo required |
| 05-activities.json | CompetencyLevelReference format, both required/recommended fields |
| 05-personas.json | Property name (competencies not requiredCompetencies), CompetencyLevelReference format |
| 06-patterns.json | Property names (alphaStates not alphas), seq required, no workProducts |

---

## Validation Checklist

Before saving ANY segment:

- [ ] All `checklist` arrays use objects with {name, description, seq}
- [ ] All `CompetencyLevelReference` use {competencyName, competencyLevelName}
- [ ] Persona property is `competencies` not `requiredCompetencies`
- [ ] Activities have BOTH `requiredCompetencies` AND `recommendedCompetencyLevels`
- [ ] PatternView uses `alphaStates` not `alphas`
- [ ] PatternView has `seq` field
- [ ] PatternView does NOT have `workProducts` property
- [ ] All LOD have `contributesTo` array
- [ ] Run `jq empty <file>` to verify JSON syntax
