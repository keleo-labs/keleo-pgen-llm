# Floating Alphas Rule Enforcement - 2026-05-20

## Issue Identified

The `/translate-methodology` skill was generating **floating alphas** (new alphas without `contributesTo` relationships), which violates the Practice Language semantics defined in `references/semantics.md`.

### What Was Happening

From `references/semantics.md` section 4.1:

> **Baseline Isolation Rules**: When extending a baseline, authors are strictly prohibited from creating floating Alphas. All new Alphas introduced in a Practice must logically refine a parent concept by explicitly declaring a contributesTo relationship. This must match a canonical Alpha.name found either in the baselinePractice or within an explicitly declared practice dependency. Floating Alphas are strictly prohibited.

**Validation Results:**

- ✅ `red-hat-ai-3` Method: 0 floating alphas (compliant)
- ❌ `red-hat-ansible-automation-platform` Method: **11 floating alphas** (violation)
  - Practice 1: Automation Platform, Automation Mesh, Execution Environment Repository, Platform Performance
  - Practice 2: Automation Content, Playbook, Collection, Job Template, Workflow, Development Workspace, Execution Environment

## Root Cause

The prompts had a rule requiring `contributesTo` for new alphas, but it wasn't emphasized strongly enough, and there was no validation enforcement to catch violations.

## Fixes Applied

### 1. Strengthened Phase 1 Module 03 Prompt

**File:** `prompts/phase-1-modules/03-alphas.md`

**Changes:**
- Added **"CRITICAL RULE - NO FLOATING ALPHAS"** section
- Emphasized that floating alphas are **STRICTLY PROHIBITED**
- Made `contributesTo` **MANDATORY** (not just "MUST have")
- Added common mapping examples:
  - Technology/infrastructure → "Platform"
  - Content/artifacts → "Platform Asset"
  - Process/workflow → "Work"
  - Governance → "Platform Governance"
  - Risk/compliance → "Platform Risk And Compliance"
  - Value/economics → "Platform Value And Economics"

### 2. Strengthened Phase 1 Module 00 (Planning) Prompt

**File:** `prompts/phase-1-modules/00-analysis-plan.md`

**Changes:**
- Added **"CRITICAL RULE - NO FLOATING ALPHAS"** to the Alpha Extension Plan section
- Made it explicit that `contributesTo` is **MANDATORY**
- Listed common mapping patterns for planning decisions

### 3. Enhanced Phase 2 Validation

**File:** `prompts/phase-2-modular.md`

**Changes:**
- Added **CRITICAL** validation check explicitly prohibiting floating alphas
- Added logic: "if `name` not in baseline alphas, then `contributesTo` must be non-empty"
- Made it a schema violation, not just a warning

### 4. Updated Project Documentation

**File:** `CLAUDE.md`

**Changes:**
- Added the floating alphas prohibition to the "Alpha Handling" section
- Made it visible in the main project instructions

### 5. Created Validation Utility

**File:** `utils/check-floating-alphas.py`

**Purpose:**
- Validates that all new alphas have `contributesTo` relationships
- Lists the 13 baseline alphas
- Reports violations with practice-specific details
- Can be run standalone or integrated into validation workflow

**Usage:**
```bash
python3 utils/check-floating-alphas.py practices/my-method/my-method.json
```

### 6. Documented the Utility

**File:** `utils/README.md`

**Changes:**
- Added comprehensive documentation for `check-floating-alphas.py`
- Explained the baseline isolation rule
- Listed all 13 baseline alphas
- Provided fix examples with appropriate `contributesTo` mappings

## Baseline Alphas (13 Total)

All new alphas must contribute to one of these:

1. **Opportunity** - Business opportunities and value propositions
2. **Organizational Change** - Change management and transformation
3. **Platform** - Core platform infrastructure and technology
4. **Platform Asset** - Reusable content, artifacts, components
5. **Platform Consumption Interface** - APIs, UIs, interfaces for users
6. **Platform Governance** - Governance frameworks and policies
7. **Platform Risk And Compliance** - Security, risk, compliance
8. **Platform Value And Economics** - Financial, value, economics
9. **Requirements** - Business and technical requirements
10. **Stakeholders** - Stakeholder groups and engagement
11. **Team** - Team structures and capabilities
12. **Way Of Working** - Processes, practices, methodologies
13. **Work** - Work items, workflows, execution

## Common Mapping Patterns

| New Alpha Type | Contributes To |
|---------------|----------------|
| Technology/infrastructure (e.g., "Automation Platform", "CI/CD Pipeline") | Platform |
| Content/artifacts (e.g., "Automation Content", "Playbook", "Model") | Platform Asset |
| APIs/interfaces (e.g., "API Gateway", "Web Console") | Platform Consumption Interface |
| Process/workflow (e.g., "Job Template", "Workflow") | Work |
| Governance mechanisms (e.g., "Policy Enforcement") | Platform Governance |
| Risk/compliance frameworks | Platform Risk And Compliance |
| Value/economic models | Platform Value And Economics |
| Team structures (e.g., "Platform Team", "Security Team") | Use instances, not new alphas |

## Impact on Future Translations

Going forward, the `/translate-methodology` skill will:

1. **During Planning (Phase 1 Module 00):**
   - Explicitly plan `contributesTo` relationships for all new alphas
   - Use common mapping patterns to guide decisions

2. **During Alpha Generation (Phase 1 Module 03):**
   - Enforce the rule with **CRITICAL** emphasis
   - Include `contributesTo` for every new alpha
   - Never generate floating alphas

3. **During JSON Translation (Phase 2):**
   - Validate that all new alphas have `contributesTo`
   - Treat floating alphas as schema violations
   - Fail translation if violations found

4. **During Validation (Optional):**
   - Run `check-floating-alphas.py` to verify compliance
   - Report violations before publishing

## Fixing Existing Violations

For `red-hat-ansible-automation-platform`, the 11 floating alphas need to be fixed:

**Practice 1: Platform Administration & Operations**
- Automation Platform → contributesTo: "Platform"
- Automation Mesh → contributesTo: "Platform"
- Execution Environment Repository → contributesTo: "Platform Asset"
- Platform Performance → contributesTo: "Platform" (monitoring/observability aspect)

**Practice 2: Automation Content Development & Delivery**
- Automation Content → contributesTo: "Platform Asset"
- Playbook → contributesTo: "Platform Asset"
- Collection → contributesTo: "Platform Asset"
- Job Template → contributesTo: "Work"
- Workflow → contributesTo: "Work"
- Development Workspace → contributesTo: "Platform" (development environment)
- Execution Environment → contributesTo: "Platform Asset"

## Testing

To verify compliance:

```bash
# Check a specific method
python3 utils/check-floating-alphas.py practices/red-hat-ai-3/red-hat-ai-3.json

# Expected output for compliant method:
# Found 13 baseline alphas
# Checking Method: Red Hat AI 3
# Practice: AI Platform Management
#   ✅ No floating alphas
# ...

# Check for violations
python3 utils/check-floating-alphas.py practices/red-hat-ansible-automation-platform/red-hat-ansible-automation-platform.json

# Expected output with violations:
# Practice: Platform Administration & Operations
#   ❌ FLOATING ALPHAS (new alphas without contributesTo):
#      - Automation Platform
#      - ...
```

## Summary

The skill now has **four layers of enforcement**:

1. **Planning enforcement** - Module 00 requires planning `contributesTo` relationships
2. **Generation enforcement** - Module 03 has **CRITICAL** rule emphasis with examples
3. **Translation validation** - Phase 2 treats floating alphas as schema violations
4. **Post-generation validation** - `check-floating-alphas.py` utility for verification

This ensures that the rule from `references/semantics.md` is properly followed throughout the entire translation workflow.
