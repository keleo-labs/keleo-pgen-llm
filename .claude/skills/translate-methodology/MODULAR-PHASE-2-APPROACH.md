# Modular Phase 2 JSON Generation

**Date:** 2026-05-21  
**Issue:** Monolithic Phase 2 translation (100KB JSON in one go) exceeds agent token limits  
**Solution:** Generate JSON in segments matching Phase 1 modules, then assemble

---

## The Problem with Monolithic Phase 2

**Original Phase 2 approach:**
- Read ALL Phase 1 modules (modules 01-07, often 200-400KB total)
- Generate complete practice JSON (80-120KB) in single agent session
- Result: **Token limit exceeded** for large practices

**Token Usage Example (Practice 2):**
- Input: ~338KB of Phase 1 modules
- Output: ~102KB complete JSON
- Total: **440KB in single session** → FAILS

---

## The Modular Solution

**New Phase 2 approach:**
- Generate **one JSON segment per Phase 1 module**
- Each segment is 3-20KB (well within limits)
- Python script assembles segments into complete practice JSON
- Method JSON assembled from practice JSONs

**Benefits:**
- ✅ Each segment generation fits in token limits
- ✅ Can regenerate individual segments without touching others
- ✅ Clear 1:1 mapping: Phase 1 module → JSON segment
- ✅ Assembly is mechanical (no LLM ambiguity)
- ✅ Same modular philosophy as Phase 1

---

## Directory Structure

```
practices/<practice-name>/
├── report-elements/
│   └── practice-N-<name>/
│       ├── 00-analysis-plan.md        # Phase 1 modules
│       ├── 01-practice-details.md
│       ├── 02-citations.md
│       ├── 03-alphas.md
│       ├── 04-workproducts.md
│       ├── 05-activities-roles.md
│       ├── 06-patterns.md
│       └── 07-aliases.md
├── json-segments/
│   └── practice-N/
│       ├── 01-practice-skeleton.json   # Generated segments
│       ├── 02-citations.json
│       ├── 03-alphas.json
│       ├── 04-workproducts.json
│       ├── 05-activities.json
│       ├── 05-personas.json
│       ├── 05-teams.json
│       ├── 06-patterns.json
│       └── 07-aliases.json
├── practice-N-<name>.json              # Assembled practice
└── <method-name>.json                  # Assembled method (if multi-practice)
```

---

## Workflow

### Phase 2.1: Generate JSON Segments

For each practice, generate 9 JSON segments:

#### Segment 01: Practice Skeleton
**Input:** `01-practice-details.md`  
**Output:** `01-practice-skeleton.json`  
**Content:**
```json
{
  "name": "Practice Name",
  "description": "Practice description (single sentence)",
  "baselinePracticeName": "Platform Adoption Essentials",
  "domainTags": [...],
  "lifecycleTags": [...],
  "organizationalTags": [...],
  "authors": [...],
  "createdAt": "2026-05-21",
  "updatedAt": "2026-05-21",
  "version": "1.0",
  "keywords": [...]
}
```

#### Segment 02: Citations
**Input:** `02-citations.md`  
**Output:** `02-citations.json`  
**Content:** Array of Citation objects

#### Segment 03: Alphas
**Input:** `03-alphas.md`  
**Output:** `03-alphas.json`  
**Content:** Array of Alpha objects with states, checklists, narratives

#### Segment 04: Work Products
**Input:** `04-workproducts.md`  
**Output:** `04-workproducts.json`  
**Content:** Array of WorkProduct objects with LODs, checklists

#### Segment 05a: Activities
**Input:** `05-activities-roles.md` (Activities section)  
**Output:** `05-activities.json`  
**Content:** Array of Activity objects with narratives

#### Segment 05b: Personas
**Input:** `05-activities-roles.md` (Personas section)  
**Output:** `05-personas.json`  
**Content:** Array of Persona objects with competencies

#### Segment 05c: Teams
**Input:** `05-activities-roles.md` (Persona Groups section)  
**Output:** `05-teams.json`  
**Content:** Array of PersonaGroup objects with persona names

#### Segment 06: Patterns
**Input:** `06-patterns.md`  
**Output:** `06-patterns.json`  
**Content:** Array of Pattern objects with pattern views

#### Segment 07: Aliases
**Input:** `07-aliases.md`  
**Output:** `07-aliases.json`  
**Content:** Array of PracticeElementAlias objects

### Phase 2.2: Assemble Practice JSON

Run assembly script:
```bash
python3 assemble-practice-json.py <practice-number>
```

**What it does:**
1. Loads all 9 JSON segments
2. Extracts instances from patterns (alphaInstances, workProductInstances)
3. Merges into complete practice JSON structure
4. Validates completeness
5. Saves `practice-N-<name>.json`

### Phase 2.3: Assemble Method JSON

For multi-practice methods:
```bash
python3 rebuild-method-json.py
```

Combines all practice JSONs into method JSON.

---

## Segment Generation Instructions

Each segment should be generated using a **focused prompt** that:
1. Reads ONLY the relevant Phase 1 module
2. Extracts ONLY the content for that segment
3. Follows Phase 2 extraction rules (clean text, extract ALL content)
4. Outputs valid JSON matching schema

### Example: Generating Segment 03 (Alphas)

**Prompt:**
```
Generate 03-alphas.json from Phase 1 module 03-alphas.md

CRITICAL REQUIREMENTS:
- Read: report-elements/practice-N-<name>/03-alphas.md
- Extract ALL alphas with complete:
  - State definitions (name, description, seq, checklist)
  - Narratives from "Context and Rationale" sections
  - contributesTo relationships for new alphas
- Clean all text (remove markdown, remove metadata phrases)
- Output: json-segments/practice-N/03-alphas.json

Output format: Array of Alpha objects
```

### Segment Size Estimates

| Segment | Input Size | Output Size | Agent Feasible? |
|---------|-----------|-------------|-----------------|
| 01-skeleton | 20KB | 2KB | ✅ Yes |
| 02-citations | 15KB | 3KB | ✅ Yes |
| 03-alphas | 50-150KB | 20-40KB | ✅ Yes |
| 04-workproducts | 30-80KB | 15-25KB | ✅ Yes |
| 05-activities | 30-50KB | 15-20KB | ✅ Yes |
| 05-personas | 10-20KB | 3-5KB | ✅ Yes |
| 05-teams | 5-10KB | 2KB | ✅ Yes |
| 06-patterns | 20-50KB | 10-20KB | ✅ Yes |
| 07-aliases | 5-10KB | 2KB | ✅ Yes |

**All segments fit within agent token limits!**

---

## Advantages Over Monolithic Approach

### Development
- **Incremental progress:** Generate and validate one segment at a time
- **Error isolation:** If segment fails, only regenerate that segment
- **Parallel generation:** Can spawn 9 agents to generate all segments simultaneously

### Quality
- **Focused extraction:** Each agent focuses on ONE module type
- **Easier validation:** Validate segment against its module
- **Clear accountability:** Issues traced to specific module/segment

### Maintenance
- **Selective regeneration:** Fix issue in alphas? Regenerate only 03-alphas.json
- **Version control friendly:** Segment changes are small, clear diffs
- **Reusable components:** Segment prompts work across all practices

---

## Skill Integration

Update `/translate-methodology` skill workflow:

### Old Phase 2 (Monolithic):
```
Step 4: Phase 2 - Modular JSON Translation
  → Read all modules
  → Generate complete practice.json
  → (FAILS for large practices)
```

### New Phase 2 (Segmented):
```
Step 4: Phase 2 - Segmented JSON Generation
  Step 4.1: Generate 9 JSON segments (one per module)
  Step 4.2: Assemble practice JSON from segments
  Step 4.3: Assemble method JSON from practices
```

---

## Example: Practice 1 Regeneration

**Traditional approach (FAILED):**
```
Agent: "Generate complete practice-1-platform-management.json from all modules"
Result: Token limit exceeded (338KB input + 100KB output)
```

**Modular approach (SUCCESS):**
```
# Generate segments (9 agents in parallel, each ~5-10 min)
Agent 1: Generate 01-practice-skeleton.json from 01-practice-details.md
Agent 2: Generate 02-citations.json from 02-citations.md
Agent 3: Generate 03-alphas.json from 03-alphas.md
Agent 4: Generate 04-workproducts.json from 04-workproducts.md
Agent 5: Generate 05-activities.json from 05-activities-roles.md
Agent 6: Generate 05-personas.json from 05-activities-roles.md
Agent 7: Generate 05-teams.json from 05-activities-roles.md
Agent 8: Generate 06-patterns.json from 06-patterns.md
Agent 9: Generate 07-aliases.json from 07-aliases.md

# Assemble (1 min)
python3 assemble-practice-json.py 1

Result: ✅ Complete practice-1-platform-management.json (100KB)
```

---

## Summary

**The modular Phase 2 approach solves the token limit problem by:**

1. **Breaking generation into segments** matching Phase 1 modules
2. **Each segment is small** (2-40KB) and fits in agent limits
3. **Assembly is mechanical** (Python script, no LLM needed)
4. **Parallelizable** (9 agents generate all segments simultaneously)
5. **Maintainable** (regenerate individual segments selectively)

This mirrors the successful modular approach used in Phase 1 and should become the **standard Phase 2 workflow** for the `/translate-methodology` skill.
