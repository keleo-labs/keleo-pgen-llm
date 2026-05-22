# Critical Rule: Always Regenerate JSON from Scratch

**Date:** 2026-05-21  
**Issue:** Incremental patching of corrupt JSON creates compounding errors  
**Solution:** Always regenerate JSON from Phase 1 modules when picking up existing work

---

## The Problem with Incremental Fixes

When JSON generation fails or produces corrupt output, attempting to "fix" the corrupt JSON through incremental patching leads to:

1. **Compounding corruption:** Patches built on corrupt structure create more corruption
2. **Missing baselines:** Can't tell what was intentionally omitted vs. what's corrupt
3. **Inconsistent structure:** Different patterns/sections have different issues
4. **Wasted effort:** Fixing one issue reveals another, endless cycle

**Example corruption patterns seen:**
- Duplicate pattern views ("Pattern Views" + actual views)
- Empty arrays where content should exist (alphas, activities, workProducts)
- Missing content (narratives, checklists, competencies)
- Malformed references (wrong names, broken links)

---

## The Rule

**When picking up existing methodology work with generated JSON:**

### ❌ DO NOT:
- Try to "fix" existing corrupt JSON
- Run incremental patch scripts on corrupt files
- Assume existing JSON is partially correct

### ✅ DO:
- **Delete all existing practice JSON files**
- **Regenerate from Phase 1 modules** using Phase 2 translation
- Start with clean slate every time

---

## Implementation

### Step 1: Assess Existing Work

When picking up existing work, check Phase 1 completion:

```bash
cd practices/<method-name>

# Check Phase 1 modules
ls report-elements/practice-*/

# Expected: 00-07 modules for each practice (or 01-07-combined for simple practices)
```

If Phase 1 modules exist and are complete → proceed to regeneration  
If Phase 1 modules incomplete → complete Phase 1 first

### Step 2: Back Up and Delete Existing JSON

```bash
# Back up corrupt JSON for reference (optional)
mkdir -p corrupt-json-backup
cp practice-*.json red-hat-ai-3.json corrupt-json-backup/

# Delete all JSON files
rm practice-*.json red-hat-ai-3.json *.json 2>/dev/null

# Confirm deletion
ls *.json  # Should show "No such file"
```

### Step 3: Regenerate Using Phase 2

**Option A: Use /translate-methodology skill (recommended)**

Re-invoke the skill and skip to Phase 2:
```
/translate-methodology --phase 2 --practice <practice-name>
```

**Option B: Manual Phase 2 Application**

For each practice:
1. Read `prompts/phase-2-modular.md`
2. Apply it to the practice's modules in `report-elements/practice-N-*/`
3. Generate complete JSON with ALL content extracted
4. Save to `practice-N-<name>.json`

**Option C: Agent-Based Regeneration (for small practices)**

For practices with <50KB modules, spawn agent:
```
Apply prompts/phase-2-modular.md to practice-N modules and generate complete practice-N-<name>.json with ALL content extracted.
```

### Step 4: Rebuild Method JSON

After all practices regenerated:
```bash
python3 rebuild-method-json.py
```

### Step 5: Validate

```bash
python3 validate-internal-integrity.py
```

---

## Why This Rule Exists

### Case Study: red-hat-ai-3 Method (2026-05-21)

**Scenario:** Method had corrupt JSON from incomplete Phase 2 translation

**Attempted Fix:** Ran `comprehensive-content-fix.py` to patch missing content
- ✓ Added some missing narratives, checklists, competencies
- ✗ Created duplicate pattern views
- ✗ Left alphas missing from pattern views
- ✗ Created empty pattern view objects
- ✗ Inconsistent structure across practices

**Result:** More corruption, not less

**Correct Approach:** Delete all JSON, regenerate from Phase 1 modules
- ✓ Clean structure throughout
- ✓ Consistent extraction approach
- ✓ All content present or intentionally omitted
- ✓ Validation passes

---

## When Incremental Fixes ARE Appropriate

The rule applies to **regenerating existing work**. Incremental fixes ARE appropriate for:

1. **Post-generation refinement:** After clean generation, running targeted fixes for specific issues (e.g., property name corrections, baseline reference validation)
2. **Schema compliance:** Fixing known property name mismatches (Phase 2.5)
3. **Baseline reference corrections:** Mapping to canonical names (Phase 2.6)
4. **Minor corrections:** Fixing a typo, correcting a single reference

The key distinction:
- **Regeneration:** Start from Phase 1 modules → JSON (clean slate)
- **Refinement:** Start from clean JSON → corrected JSON (targeted fixes)

---

## Updating the Skill Workflow

The `/translate-methodology` skill should implement this rule:

### New Step 0: Check for Existing JSON

**Before Phase 2:**

```python
if practice_json_exists():
    ask_user("Existing JSON found. Delete and regenerate from scratch? (Recommended)")
    if user_confirms:
        backup_json()  # Optional
        delete_json()
        proceed_to_phase_2()
    else:
        warn("Working with existing JSON may compound corruption")
```

### Updated Phase 2 Description

**Old:** "Translate Phase 1 modules to JSON"  
**New:** "Generate clean JSON from Phase 1 modules (deleting any existing JSON first)"

---

## Summary

**The Rule in One Sentence:**

> When picking up existing methodology work, always delete existing JSON and regenerate from Phase 1 modules rather than attempting incremental fixes on corrupt structure.

**Why:**
- Corrupt JSON compounds errors when patched
- Clean regeneration ensures consistent structure
- Phase 1 modules are source of truth, not existing JSON

**Exception:**
- Post-generation refinement of clean JSON for specific known issues (schema compliance, baseline references, etc.)
