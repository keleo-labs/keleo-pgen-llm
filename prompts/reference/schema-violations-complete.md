# Complete Schema Violations Found - Practice 1 Validation Results

**Validation performed:** 2026-05-21 using `validate-json-schema.js`
**Total errors:** 23 schema violations
**File validated:** `practices/red-hat-ai-3/practice-1-ai-platform-management.json`

---

## Error Category 1: Narrative Structure (12 errors - all alphas)

**Issue:** Narratives extend `PracticeElement` which requires `name` and `description` properties.

**WRONG:**
```json
{
  "narrativeName": "Value and Context",
  "narrativeTypeName": "Context and Rationale",
  "narrativeContexts": [...]
}
```

**CORRECT:**
```json
{
  "name": "Value and Context",
  "description": "Explains the value proposition and context for this alpha",
  "narrativeTypeName": "Context and Rationale",
  "narrativeContexts": [...]
}
```

**Root cause:** Phase 2 segment generation used `narrativeName` instead of `name` + `description`.

**Schema reference:** `PracticeElement` requires `name` and `description` (line 10). `Narrative` extends `PracticeElement` (line 496-497).

**Fix applies to:**
- Alpha narratives (segment 03)
- Activity narratives (segment 05a)
- Pattern narratives (segment 06)

---

## Error Category 2: Activity Narratives Property Name (5 errors - all activities)

**Issue:** Activities have `techniqueNarratives` property but schema only defines `narratives` (from PracticeElement).

**WRONG:**
```json
{
  "name": "Deploy AI Platform Infrastructure",
  "description": "...",
  "techniqueNarratives": [
    {
      "narrativeTypeName": "How-To Guide",
      "narrativeContexts": [...]
    }
  ]
}
```

**CORRECT:**
```json
{
  "name": "Deploy AI Platform Infrastructure",
  "description": "...",
  "narratives": [
    {
      "name": "Deployment Technique",
      "description": "Step-by-step deployment guidance",
      "narrativeTypeName": "How-To Guide",
      "narrativeContexts": [...]
    }
  ]
}
```

**Root cause:** Phase 2 segment generation invented property name `techniqueNarratives` not in schema.

**Schema reference:** `ActivitySpaceCore` extends `PracticeElement` (line 292), which has `narratives` array (line 45-46). No `techniqueNarratives` property exists in schema.

**Fix applies to:**
- All activities (segment 05a)

---

## Error Category 3: Practice Tags Structure (3 errors)

**Issue:** Tags must be nested in a `tags` object, not at Practice root level.

**WRONG:**
```json
{
  "name": "AI Platform Management",
  "description": "...",
  "domainTags": ["AI/ML", "Platform Engineering"],
  "lifecycleTags": ["Operations", "Strategy"],
  "organizationalTags": ["Technology"]
}
```

**CORRECT:**
```json
{
  "name": "AI Platform Management",
  "description": "...",
  "tags": {
    "domainTags": ["AI/ML", "Platform Engineering"],
    "lifecycleTags": ["Operations", "Strategy"],
    "organizationalTags": ["Technology"]
  }
}
```

**Root cause:** Phase 2 segment 01 (practice skeleton) placed tags at root instead of nested in `tags` object.

**Schema reference:** `PracticeElement.tags` is oneOf object-with-buckets or flat-array (lines 14-43). Practice extends PracticeElement (line 688).

**Fix applies to:**
- Practice skeleton (segment 01)

---

## Error Category 4: Teams vs PersonaGroups (1 error)

**Issue:** Practice uses `teams` property but schema defines `personaGroups`.

**WRONG:**
```json
{
  "teams": [
    {
      "name": "Platform Engineering",
      "description": "...",
      "personaNames": ["Platform Engineer", "Cluster Administrator"]
    }
  ]
}
```

**CORRECT:**
```json
{
  "personaGroups": [
    {
      "name": "Platform Engineering",
      "description": "...",
      "personaNames": ["Platform Engineer", "Cluster Administrator"]
    }
  ]
}
```

**Root cause:** Phase 2 assembly used `teams` property name instead of schema's `personaGroups`.

**Schema reference:** Practice has `personaGroups` array (line 756-760), not `teams`.

**Fix applies to:**
- Practice assembly script (segment 05c → final assembly)

---

## Error Category 5: Schema Match Failures (2 errors)

**Issue:** Overall schema validation failures due to the property name mismatches above.

**Errors 22-23:** Root-level schema matching fails because of unevaluated properties (domainTags, lifecycleTags, organizationalTags, teams).

**Fix:** These will resolve automatically when errors 1-4 are fixed.

---

## Summary of Required Fixes

| Segment | Property | Change Required |
|---------|----------|----------------|
| 01 - Practice Skeleton | Root-level tags | Nest in `tags` object |
| 03 - Alphas | `narratives[]` | Add `name` and `description` to each narrative |
| 05a - Activities | `techniqueNarratives` | Rename to `narratives`, add `name`/`description` to each |
| 05c - Teams | Property name | Rename to `personaGroups` in assembly |

---

## Affected Prompts to Update

1. **`prompts/phase-1-modules/03-alphas.md`** - Ensure narratives have name/description
2. **`prompts/phase-1-modules/05-activities-roles.md`** - Ensure narratives have name/description
3. **`prompts/phase-1-modules/06-patterns.md`** - Ensure narratives have name/description
4. **Phase 2 segment prompts or scripts** - Fix property name mappings:
   - Tags structure (segment 01)
   - Narrative structure (segments 03, 05a, 06)
   - Activity narratives property name (segment 05a)
   - Teams → personaGroups (assembly)

---

## Validation Checklist (After Fixes)

Before regenerating segments, ensure prompts specify:

- [ ] All Narrative objects have `name`, `description`, `narrativeTypeName`, `narrativeContexts`
- [ ] Activity narratives use `narratives` property, not `techniqueNarratives`
- [ ] Practice tags nested in `tags: { domainTags, lifecycleTags, organizationalTags }`
- [ ] Practice uses `personaGroups` property, not `teams`
- [ ] All tag arrays follow PracticeElement.tags schema structure

**Final validation:** Run `node utils/validate-json-schema.js <practice-file>.json` to confirm 0 errors.
