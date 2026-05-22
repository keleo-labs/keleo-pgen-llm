# Phase 1 Module 07: Practice Element Aliases

**Execution Context:** This module generates terminology mappings when the source methodology uses different terms than the baseline. This is optional - only generate if source uses different terminology.

**Size Estimate:** ~500-1,000 words (very small module).

---

## Role and Objective

You are a **Practice Research Analyst** creating terminology mappings between source methodology terms and baseline practice language terms.

**Input:**
- Module 01 practice-details.md (terminology mapping table if present)
- All previous modules (to identify any terminology inconsistencies)
- Source methodology materials
- Baseline framework

**Output:** Aliases document (~500-1,000 words) mapping source terms to baseline terms, or a note that no aliases are needed.

---

## Required Resources

1. **Read Module 01** - `report-elements/01-practice-details.md`
   - Check if terminology mapping table was created
   
2. **Read All Modules** - `report-elements/00-*.md through 06-*.md`
   - Identify any terms used inconsistently
   
3. **Baseline Framework** - `deps/platform-adoption-kernel.json`
   - Extract canonical baseline element names
   
4. **Source Materials** - User-provided methodology documentation
   - Identify source-specific terminology

---

## When Aliases Are Needed

Create aliases when:

1. **Source uses different names for baseline concepts:**
   - Source calls "Platform" → "Landing Zone"
   - Source calls "Team" → "Squad"
   - Source calls "Requirements" → "User Needs"

2. **Industry-specific terminology:**
   - Financial services: "Control Framework" for "Platform Governance"
   - Healthcare: "Care Delivery Platform" for "Platform"

3. **Vendor-specific branding:**
   - AWS: "Well-Architected Review" for specific work product
   - Google: "SRE Engagement" for specific activity space

4. **Consistency with existing organizational vocabulary:**
   - Company already uses "Product Team" to mean "Platform Team"
   - Company calls work management "Epic" instead of "Work"

---

## When Aliases Are NOT Needed

Do NOT create aliases for:

1. **Generic synonyms that aren't used in source:**
   - Don't alias "Platform" → "System" unless source explicitly uses "System" to mean Platform
   
2. **Theoretical alternatives:**
   - Don't create aliases "just in case"
   
3. **Overly broad mappings:**
   - Don't alias "Infrastructure" → "Platform" (too vague)

**Rule:** Only create aliases for terms that ACTUALLY appear in the source methodology and clearly map to specific baseline elements.

---

## Output Structure

If aliases are needed:

---

## Practice Element Aliases

This practice uses terminology that maps to baseline concepts as follows:

### Terminology Mapping Table

| Source Term | Baseline Element Name | Element Type | Usage Context |
|:------------|:---------------------|:-------------|:--------------|
| [Source Term] | [Exact Baseline Name] | Alpha | [Brief context note] |
| [Source Term] | [Exact Baseline Name] | ActivitySpace | [Brief context note] |
| [Source Term] | [Exact Baseline Name] | WorkProduct | [Brief context note] |
| [Source Term] | [Exact Baseline Name] | Competency | [Brief context note] |
| [Source Term] | [Exact Baseline Name] | Focus | [Brief context note] |

**Examples:**

| Source Term | Baseline Element Name | Element Type | Usage Context |
|:------------|:---------------------|:-------------|:--------------|
| Landing Zone | Platform | Alpha | AWS-specific term for platform in cloud context |
| Well-Architected Review | Platform Assessment | WorkProduct | AWS framework assessment artifact |
| Squad | Team | Alpha | Spotify/Agile terminology for team structure |
| User Needs | Requirements | Alpha | User-centric terminology for requirements |
| Cloud Center of Excellence | Platform Team | PersonaGroup | Enterprise cloud governance team |

### Alias Usage Guidelines

**For Practitioners:**
When reading this practice document, recognize that:
- References to "[Baseline Term]" in the practice align with "[Source Term]" in the original source methodology
- Internal practice definitions use baseline terminology for consistency
- When consulting source materials, translate between the terminologies using this table

**For Tooling:**
These aliases should be applied at the presentation layer only:
- Internal JSON uses canonical baseline names for all structural references
- User interfaces may display source terms as aliases
- Aliases do not affect validation or schema compliance

**Strict Isolation:**
- Alias names are NEVER used in structural references (contributesTo, alphaName, stateName, etc.)
- All internal linkage uses canonical baseline names
- Aliases serve only as presentation-layer substitutions

---

If NO aliases are needed:

---

## Practice Element Aliases

**No Aliases Required**

This practice uses baseline terminology consistently throughout. No source-specific terminology mappings are necessary.

---

## Writing Guidelines

1. **Only actual source terms:** Don't invent aliases; only map terms that actually appear in source
2. **Exact baseline names:** The "Baseline Element Name" column must use exact names from baseline (case-sensitive)
3. **Correct element types:** Accurately identify whether it's an Alpha, ActivitySpace, WorkProduct, etc.
4. **Brief context:** Usage context should explain WHY the source uses this term (vendor, industry, existing vocabulary)
5. **Complete mapping:** If an alias is used, map ALL occurrences consistently
6. **No structural usage:** Emphasize that aliases are presentation-only, not structural

## Element Type Reference

Valid element types for aliases:

- **Alpha** - Area of concern
- **ActivitySpace** - Category of work
- **Activity** - Specific work type (only if source methodology explicitly names activities differently)
- **WorkProduct** - Artifact or deliverable
- **Competency** - Skill or capability
- **Focus** - Value, Solution, or Endeavor (rare to alias)
- **PersonaGroup** - Team structure
- **Persona** - Individual role (only if source uses different role names)

## Common Alias Patterns

**AWS/Cloud Provider Terminology:**
- Landing Zone → Platform
- Account → Platform Instance
- Well-Architected Review → Platform Assessment
- Service Catalog → Capability Catalog

**Agile/Scaling Framework Terminology:**
- Squad → Team
- Tribe → Team (at different scale)
- Epic → Work (if used to mean work management)
- Product Owner → Product Manager

**Enterprise/Industry Terminology:**
- Control Framework → Platform Governance
- Service Delivery → Platform Consumption Interface
- Change Management → Organizational Change

## Execution Instructions

1. Read Module 01 to check if terminology mapping table was created
2. Review all previous modules (00-06) for terminology consistency
3. Compare terms used in modules against source materials
4. Identify terms where source explicitly uses different names for baseline concepts
5. If aliases needed:
   - Create comprehensive mapping table
   - Verify baseline element names are exact matches
   - Verify element types are correct
   - Add usage context explanations
   - Include usage guidelines
6. If NO aliases needed:
   - Create simple "No Aliases Required" note
7. Do NOT create hypothetical aliases

**Quality Check:**
- [ ] Only includes terms ACTUALLY used in source materials
- [ ] Baseline element names are exact matches (verified against baseline)
- [ ] Element types are accurate
- [ ] Usage context explains WHY source uses this term
- [ ] Usage guidelines emphasize presentation-only, not structural use

**Output:** Save aliases document (or "no aliases" note) to be consumed by Phase 2.
