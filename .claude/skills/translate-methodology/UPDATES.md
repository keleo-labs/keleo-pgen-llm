# Translate Methodology Skill Updates

## Recent Updates (2026-05-20)

### Phase 2 Enhancement: Instances and Aliases Support

**Status:** Planned - Documentation updated, implementation pending

**What Changed:**

Added requirements to extract and include three previously missing schema elements:

1. **PracticeElementAliases** - Terminology mappings
2. **AlphaInstances** - Concrete instances of alphas tracked in patterns
3. **WorkProductInstances** - Concrete instances of work products

### Updated Documentation

**`.claude/skills/translate-methodology/SKILL.md`:**

- Updated Step 4 (Phase 2) to include instance and alias parsing requirements
- Added "Critical Elements to Include" section with:
  - PracticeElementAliases extraction from module 07
  - AlphaInstances extraction from pattern views
  - WorkProductInstances extraction from patterns
- Specified schema structure for each element type

**`utils/phase2-parsers/README.md`:**

- Updated parser list to include `alias_parser.py`
- Updated known gaps to reflect instances/aliases as priority items
- Reorganized "Future Enhancements" into Priority vs Secondary

### Implementation Needed

**Priority parsers to implement:**

1. **`alias_parser.py`** - NEW
   - Parse `07-aliases.md` 
   - Extract alias mappings (legacy term → current term)
   - Format: `{practiceElementType, practiceElementName, aliasName}`
   - Add to `practice.practiceElementAliases[]`

2. **Enhanced `pattern_parser.py`**
   - Parse "Specific Instances Tracked" sections in pattern views
   - Extract instance names and their parent alpha/work product
   - Add instances to pattern view: `patternView.alphaInstances[]`

3. **Enhanced `translate_practice.py`**
   - Call alias parser for module 07
   - Aggregate alpha instances from all pattern views
   - Aggregate work product instances where found
   - Add to practice root: `practice.alphaInstances[]`, `practice.workProductInstances[]`

### Example from AAP Translation

**Aliases found in markdown:**
- "Ansible Tower" → "automation controller" (Alpha)
- "Ansible Galaxy" → "automation hub" (Alpha)
- "Receptor" → "automation mesh components" (Alpha)

**Instances found in patterns:**
- "Platform Operations Team" (instance of "Team" alpha)
- "Infrastructure Team" (instance of "Team" alpha)
- "Security Team" (instance of "Team" alpha)

**Current status:** These are documented in markdown but NOT in JSON output.

### Schema References

From `deps/language.schema.json`:

```json
{
  "practice": {
    "practiceElementAliases": [],  // PracticeElementAlias[]
    "alphaInstances": [],           // AlphaInstanceName[]
    "workProductInstances": []      // WorkProductInstanceName[]
  },
  "patternView": {
    "alphaInstances": []             // AlphaInstance[]
  }
}
```

### Next Steps

When implementing these features:

1. Create `alias_parser.py` following pattern of other parsers
2. Update `pattern_parser.py` to extract instances from pattern views
3. Update `translate_practice.py` to aggregate instances and call alias parser
4. Test on AAP method to verify extraction
5. Update validation scripts to check instance references

---

## Previous Updates

See Git history for earlier changes.
