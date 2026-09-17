# Mode 1B: Light Reanalysis (Phase 1B → 2 → 3)

Targeted re-research of specific analysis sections using existing citations and content as the foundation. Sits between Remap (skips Phase 1 entirely) and Full Reanalysis (redoes Phase 1 from scratch).

**When to use:**
- Source material has been updated (new edition, revised chapter, additional content)
- Skill or language improvements affect specific element types (e.g., new checklist guidance, pattern requirements)
- User-identified gaps in specific analysis sections
- Schema changes that alter how certain elements should be analyzed
- Existing analysis is substantially correct but needs targeted improvements

**Prerequisites:**
- Existing `01-analysis-report.md` in the practice/baseline directory
- User can describe the change scope (what needs updating and why)

## Step 2A: Capture Change Scope

Present the user with structured scope categories. Each category maps to specific sections of the analysis report:

```
What areas of the analysis need re-research?

  a. Concerns/Alphas — states, criteria, narratives (→ sections 1-2)
  b. Work Products — LODs, characteristics (→ section 3)
  c. Activities — techniques, competency mappings (→ sections 4-5)
  d. Competencies — levels, descriptions (→ section 5)
  e. Personas/Groups — roles, team structures (→ sections 6-7)
  f. Patterns/Workflows — lifecycle phases, view coordination (→ sections 8-9)
  g. Citations/References — source materials, reference content (→ sections 10-11)
  h. Custom — describe the specific change below

Select areas (e.g., "a, c") or describe the change:
```

**Also ask:**
- Any new source materials to incorporate? (URLs, files, documents)
- Any specific citations to re-fetch and re-research? (by default, light analysis works from existing analysis text without re-fetching)

**Wait for user response before proceeding.**

### Implied Dependencies

When the user selects a scope, automatically include dependent sections:

| User selects | Also update | Reason |
|---|---|---|
| Concerns/Alphas | Outcomes (section 1) | Outcomes derive from concerns |
| Activities | Competencies (section 5) | Activities define competency requirements |
| Patterns/Workflows | Practices (section 9) | Practice boundaries reference patterns |
| Custom | LLM determines | Based on change description |

## Step 2B: Run Phase 1B - Light Analysis

**IMPORTANT:** This step uses the light analysis prompt, NOT the full Phase 1 prompt.

**Key reference files:**
- Light analysis prompt: `prompts/phase-1-light-analysis.md`
- Existing analysis: `<dir>/01-analysis-report.md`
- Domain framework: `references/domain-framework.md` (read only if Concerns/Alphas are in scope)

**Process:**
1. Read existing `01-analysis-report.md` completely
2. Classify each of the 11 sections as PRESERVE or UPDATE based on user scope + implied dependencies
3. For UPDATE sections:
   - Work from existing analysis text as the baseline
   - If user flagged specific citations for re-research or provided new sources, fetch and read those
   - Otherwise, revise based on the change context (new guidance, schema changes, user-described gaps)
   - Preserve valid existing entries — modify/add/remove only what the change scope warrants
4. For PRESERVE sections:
   - Carry forward verbatim — no rephrasing, reformatting, or adjustment

**Subagent Directives (include in Phase 1B subagent prompt):**
- "Write the complete analysis report using the Write tool (first batch) then Edit tool (to append). Do NOT attempt to return the entire report as text output — write it directly to the file."
- "Write sections incrementally: sections 1-4 in one Write call, then append sections 5-8, then sections 9-11. This prevents output truncation."
- "Proceed immediately with the full update. Do NOT ask for confirmation or present options."

**Post-Phase-1B Section Check:**
After the subagent completes, verify all 11 sections are present:
```bash
grep -c '^## [0-9]' <dir>/01-analysis-report.md
```
Expected: 11 section headers. If fewer, resume the agent: "The analysis report is missing sections. Continue writing from the last section present. Append the remaining sections using the Edit tool."

**Output:** `<dir>/01-analysis-report.md` (OVERWRITE existing — backup already taken in Step 0)

**Baselines only:** If Concerns/Alphas are in scope, also update Phase 1.5 distillation (`<dir>/01.5-distilled-essentials.md`)

**Validation:** Apply Phase 1 Validation from generate-method skill

## Step 2C: Run Phase 2 - Mapping

Identical to Mode 1's Step 2C. Read `.claude/skills/update-method/modes/mode-1-full-reanalysis.md` Step 2C for detailed instructions, including **Subagent Directives** and **Post-Phase-2 Placeholder Check**.

## Step 2D: Run Phase 3 - JSON Generation

Identical to Mode 1's Step 2D. Read `.claude/skills/update-method/modes/mode-1-full-reanalysis.md` Step 2D for detailed instructions, including **Subagent Directives** and **Post-Phase-3 Completeness Gate**.
