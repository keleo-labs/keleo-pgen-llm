# Phase 1B: Light Analysis Prompt

## Context

You are conducting **Phase 1B: Light Analysis** — a targeted update to an existing Phase 1 analysis report. Unlike full Phase 1 analysis (which reads all source materials from scratch), light analysis builds on the existing report, updating only the sections within the user's declared change scope.

## Objective

Produce an updated `01-analysis-report.md` that:
- **Preserves** out-of-scope sections verbatim (no rephrasing, reformatting, or adjustment)
- **Updates** in-scope sections using existing content as the baseline, incorporating changes from new guidance, schema updates, user-described gaps, or re-researched sources
- Maintains the same 11-section structure as a full Phase 1 analysis report

## Inputs

1. **Existing analysis report** — `01-analysis-report.md` in the practice/baseline directory. Read completely before making any changes.
2. **Change scope** — User-provided structured categories and/or free text describing what needs updating and why.
3. **New source materials** (optional) — URLs, files, or documents the user provides for incorporation.
4. **Citations to re-research** (optional) — Specific citations the user flags for re-fetching. By default, work from existing analysis text without re-fetching.

## Resources Available

Reference documents for UPDATE sections (read only when the relevant scope is active):

- **`references/domain-framework.md`** — Four-perspective enterprise analysis framework. Read when Concerns/Alphas are in scope.
- **`references/workproduct-assessment-rubric.csv`** — 5-level maturity rubric. Read when Work Products are in scope.
- **Source materials** — User-provided or cited URLs. Read when the user provides new sources or flags specific citations for re-research.

## Tool Call Guidelines

When running Bash commands, use **simple single-command calls** that match auto-approved patterns (e.g., `grep`, `wc`, `head`, `python3 utils/...`). Do NOT combine commands using variable assignments (`TARGET="..." && grep ...`) or shell loops (`for f in ...; do ... done`) — these trigger permission prompts. Make separate tool calls instead.

## Instructions

### Step 1: Load Existing Analysis

Read the existing `01-analysis-report.md` completely. Identify all 11 sections:

1. Outcomes
2. Concerns (with Progressive States)
3. Work Products (with Levels of Detail)
4. Activities
5. Competencies
6. Personas
7. Persona Groups (Teams)
8. Workflows and Patterns
9. Practices
10. Reference Content Candidates
11. Citations

Note the current content, structure, and quality of each section.

### Step 2: Classify Sections

Based on the user's declared change scope, classify each section as **PRESERVE** or **UPDATE**.

**Scope-to-section mapping:**

| Scope Category | Primary Sections | Also Update (implied) |
|---|---|---|
| Concerns/Alphas | 2 (Concerns) | 1 (Outcomes) |
| Work Products | 3 (Work Products) | — |
| Activities | 4 (Activities) | 5 (Competencies) |
| Competencies | 5 (Competencies) | — |
| Personas/Groups | 6 (Personas), 7 (Groups) | — |
| Patterns/Workflows | 8 (Workflows/Patterns) | 9 (Practices) |
| Citations/References | 10 (References), 11 (Citations) | — |
| Custom | Determined from user description | Determined from user description |

Any section not covered by the user's scope is **PRESERVE**.

### Step 3: Update In-Scope Sections

For each **UPDATE** section:

1. **Start from existing content** — the current section text is the baseline, not a blank slate
2. **Apply the change context:**
   - If the change is skill/guidance improvements: revise content to align with the new guidance (e.g., improved checklist criteria, better state progressions, enhanced activity descriptions)
   - If the change is schema/language updates: revise content to use new structural patterns or element types
   - If the change is source material updates: incorporate new information from the provided sources
   - If the change is gap remediation: expand or improve the section based on the user's description of what's missing
3. **Incorporate new sources** (if provided):
   - Read user-provided URLs or files
   - Integrate relevant findings into the section
   - Add new citations to Section 11 for any new sources used
4. **Re-research flagged citations** (if any):
   - Fetch the URLs of citations the user specifically flagged
   - Compare current content with the source
   - Update the section with any new or changed information
5. **Preserve valid existing entries** — do not remove or rewrite entries that remain correct and within quality standards. Only modify, add, or remove what the change scope warrants.

### Step 4: Preserve Out-of-Scope Sections

For each **PRESERVE** section, carry forward the existing text **verbatim**. This means:
- Exact same text, formatting, and structure
- No rephrasing, reordering, or "improvements"
- No fixing of issues that aren't in scope (those belong to a separate update)

### Step 5: Assemble Updated Report

Produce the complete `01-analysis-report.md` with:
- Updated metadata header (current date, "Light Reanalysis" noted, source materials listed)
- All 11 sections in order — PRESERVE sections verbatim, UPDATE sections with changes applied
- Updated Section 11 (Citations) if new sources were added
- Updated Section 10 (Reference Content Candidates) if new references were discovered during re-research

## Output Format

The output follows the same 11-section structure as a full Phase 1 analysis report. See `prompts/phase-1-analysis.md` for the complete section format specification — the report template section defines heading hierarchy, field names, and content structure for each of the 11 sections.

## Quality Standards

### Preservation Fidelity
- PRESERVE sections must be verbatim — identical to the original report
- Do not "fix" formatting, terminology, or structure in preserved sections

### Update Quality
- UPDATE sections must meet the same quality standards as full Phase 1 output
- **Descriptions**: Single grammatically correct sentence, max 20 words
- **State/LOD Descriptions**: Max 12 words
- **Criteria**: Distinct observable criteria, one sentence each; typical 3-7 per state, 3-5 per LOD
- **No placeholders**: No "etc.", "...", or incomplete entries
- **Source fidelity**: Preserve source terminology; let source content drive progression

### Content Integrity
- Do not lose valid existing entries in UPDATE sections
- New content must be traceable to source materials or the stated change context
- Cross-references between sections must remain consistent (e.g., activities referencing concerns, patterns referencing activities)

## Output Location

Overwrite: `<dir>/01-analysis-report.md` (where `<dir>` is the practice or baseline directory)

## Success Criteria

- ✓ PRESERVE sections are verbatim copies of the original
- ✓ UPDATE sections address the user's declared change scope
- ✓ UPDATE sections retain valid existing entries as baseline
- ✓ New sources (if provided) are integrated and cited
- ✓ Cross-references between sections remain consistent
- ✓ Report follows the same 11-section structure as full Phase 1 output

This updated analysis will be used as input for Phase 2 (Mapping to Baseline Practice).
