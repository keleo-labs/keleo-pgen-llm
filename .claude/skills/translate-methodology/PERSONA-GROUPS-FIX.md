# Persona Groups Fix - May 2026

## Issue

PersonaGroups in generated JSON had `null` personaNames arrays, violating the schema requirement.

**Schema Requirement:**
```json
{
  "personaGroups": [
    {
      "name": "Platform Team",
      "description": "...",
      "personaNames": ["Platform Architect", "DevOps Engineer", "SRE Engineer"]
    }
  ]
}
```

**Actual Output (BROKEN):**
```json
{
  "personaGroups": [
    {
      "name": "Platform Operations Team",
      "description": "...",
      "personaNames": null  // ❌ WRONG
    }
  ]
}
```

## Root Cause

**Phase 1 Module 05 Prompt** didn't clearly specify the required format for persona group member lists:

- Original prompt had vague guidance: "Team composition. List the personas..."
- No explicit requirement for a parseable "Team Members:" section
- Generated markdown had narrative descriptions of team composition but no explicit bullet lists

**Phase 2 Translation Prompt** couldn't extract persona names:

- Expected to "extract persona names from composition description"
- Had no clear parsing instructions for the markdown structure
- Resulted in null personaNames

## Fix Applied

### 1. Updated Phase 1 Module 05 Prompt

File: `prompts/phase-1-modules/05-activities-roles.md`

**Added explicit structure requirement:**

```markdown
### Persona Group: [Team Name]

**Description:** [Single sentence describing the team's primary purpose]

**Responsibilities:**

[2-3 paragraphs describing team responsibilities, purpose, and ways of working]

**Team Composition:**

[1 paragraph describing typical team size, structure, and organizational context]

**Team Members:**

**CRITICAL - REQUIRED FORMAT FOR PHASE 2 PARSING:**

This team consists of:
- **[Persona Name]** (must match exactly a Persona name defined in ## Personas section above)
- **[Persona Name]**
- **[Persona Name]**

[List ALL personas that are part of this team. Each name must EXACTLY match a persona name from the Personas section above. This explicit list is required for Phase 2 JSON translation.]
```

**Key Changes:**
- Added **CRITICAL** warning about required format
- Explicit "This team consists of:" marker for parsing
- Clear bullet list structure with bold persona names
- Requirement that names EXACTLY match Personas section

### 2. Updated Phase 2 Translation Prompt

File: `prompts/phase-2-modular.md`

**Added detailed parsing instructions:**

```markdown
**For Persona Groups:**

1. Extract group name from heading: `### Persona Group: [Name]` or `### Team: [Name]`
2. Extract description from **Description:** section (single sentence)
3. **CRITICAL:** Parse **Team Members:** section to extract persona names:
   - Look for the explicit list: "This team consists of:"
   - Extract each persona name from the bullet list (format: `- **[Persona Name]**`)
   - Remove markdown formatting (bold) to get clean names
   - Each name must EXACTLY match a persona name from the Personas section
4. Create personaNames array with the extracted names

**Example parsing:**

From markdown:
```markdown
### Team: Platform Operations Team

**Description:** The primary team responsible for platform operations.

**Team Members:**

This team consists of:
- **Platform Administrator**
- **Site Reliability Engineer (SRE)**
- **Infrastructure Engineer**
```

Translates to:
```json
{
  "name": "Platform Operations Team",
  "description": "The primary team responsible for platform operations.",
  "personaNames": ["Platform Administrator", "Site Reliability Engineer (SRE)", "Infrastructure Engineer"]
}
```

**VALIDATION:** Every personaName MUST match a persona name defined in the personas array.
```

**Key Changes:**
- Step-by-step parsing instructions
- Concrete example showing markdown → JSON
- Validation requirement

## Impact

**Existing Generated Content:**
- Content generated with the old prompts will have null personaNames
- Requires regeneration of Module 05 or manual fixing of JSON

**Future Generations:**
- Phase 1 will produce parseable Team Members sections
- Phase 2 will correctly extract persona names
- PersonaGroups will have valid personaNames arrays

## Remediation for Existing Content

For content already generated (like Red Hat Ansible Automation Platform):

**Option 1: Regenerate Module 05**
```bash
# Re-run Phase 1 Module 05 with updated prompt
# Then re-run Phase 2 translation
```

**Option 2: Manual JSON Fix**
```python
# Read module 05 markdown
# Parse "Team Members:" sections manually
# Update JSON personaGroups[].personaNames
```

**Option 3: Update Markdown + Re-translate**
```bash
# Edit existing 05-activities-roles.md
# Add "Team Members:" sections with bullet lists
# Re-run Phase 2 translation
```

## Validation

After fix, validate that:

1. ✅ All personaGroups have non-null personaNames arrays
2. ✅ All personaNames entries match personas[].name exactly
3. ✅ All personas in personas[] are referenced by at least one personaGroup
4. ✅ Schema validation passes

```bash
# Check for null personaNames
jq '[.practices[].personaGroups[] | select(.personaNames == null)] | length' <practice>.json
# Should return: 0

# Validate all personaNames exist as personas
jq '.practices[0] | {personas: [.personas[].name], personaGroups: [.personaGroups[].personaNames[] // []]} | .personaGroups - .personas' <practice>.json
# Should return: []
```

## Date

**Fix Applied:** 2026-05-20  
**Files Modified:**
- `prompts/phase-1-modules/05-activities-roles.md`
- `prompts/phase-2-modular.md`

## Related Schema

**PersonaGroup Schema** (from `language.schema.json`):
```json
{
  "allOf": [
    {
      "$ref": "#/$defs/PracticeElement"
    },
    {
      "type": "object",
      "required": [
        "personaNames"
      ],
      "properties": {
        "personaNames": {
          "type": "array",
          "items": {
            "type": "string",
            "description": "Persona.name entries (symbolic links in the same practice)."
          }
        }
      }
    }
  ]
}
```

**Key Point:** `personaNames` is REQUIRED and must be an array of strings matching persona names.
