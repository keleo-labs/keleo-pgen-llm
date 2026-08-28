# Phase 1: Baseline Analysis Prompt

## Context

You are conducting **Phase 1: Analysis** of a **baseline practice creation** workflow. This phase organizes source methodology content into a structured methodological framework. Unlike extension practices, baseline analysis emphasizes **universal, foundational elements** suitable for broad reuse.

**This prompt is nearly identical to `prompts/phase-1-analysis.md` with key adaptations for baseline creation.**

## Key Differences from Extension Practice Analysis

**Emphasis on Universality:**
- Extract concepts at the **framework level** (not implementation-specific)
- Use **vendor-neutral terminology** (avoid tool/platform names)
- Identify **generally applicable** patterns (not niche edge cases)
- Focus on **foundational concerns** (not tactical execution details)

**Simplified Scope:**
- NO practice hierarchy determination (baselines are always single cohesive frameworks)
- Concerns should be **essential** to the domain (not every detail from source)
- Activities should cover **types of work** (not specific execution steps)

## Objective

Extract and organize the key elements from the source methodology into a structured report that identifies:
- **Outcomes** - Primary objectives and intended outcomes
- **Concerns** - **Essential** areas requiring attention (framework-level)
- **Progressive States** - **Universal** maturity waypoints for each concern
- **Work Products** - Artifacts demonstrating progress
- **Activities** - **Types of work** performed (generalizable)
- **Competencies** - Required expertise and **skill categories** (not specific roles)
- **Personas** - Roles combining competencies (will be generalized in Phase 1.5)
- **Workflows** - Common patterns and lifecycles

**Phase 1.5 Distillation** will then:
- Identify Focus areas (default or custom)
- Distill concerns to 8-15 essential alphas
- Generalize activities to 6-12 activity types
- Extract universal competencies (5-10 skill categories)

## Tool Call Guidelines

When running Bash commands, use **simple single-command calls** that match auto-approved patterns (e.g., `grep`, `wc`, `head`, `python3 utils/...`). Do NOT combine commands using variable assignments (`TARGET="..." && grep ...`) or shell loops (`for f in ...; do ... done`) — these trigger permission prompts. Make separate tool calls instead.

## Instructions

**Follow the complete Phase 1 analysis instructions from `prompts/phase-1-analysis.md` with these additional guidelines:**

### Universal Terminology Guidelines

When extracting elements, prefer general terms over specific implementations:

**DO:**
- "Container Orchestration" (not "Kubernetes")
- "Source Control" (not "Git" or "GitHub")
- "Work Tracking" (not "Jira")
- "Cloud Infrastructure" (not "AWS" or "Azure")
- "Access Control" (not "IAM" or "RBAC")

**EXCEPTION:** When the source methodology IS vendor-specific (e.g., AWS Well-Architected Framework), use vendor terms in Phase 1. Phase 1.5 will distill to neutral terminology.

### Concern Extraction Guidelines

**Include concerns that are:**
- ✓ Fundamental to the domain (core to all uses)
- ✓ Broadly applicable (relevant across organizations)
- ✓ Strategic or architectural (not purely tactical)
- ✓ Universal progressions (mature similarly everywhere)

**Consider removing/merging concerns that are:**
- ❌ Implementation-specific (tied to one tool/vendor)
- ❌ Niche edge cases (rare scenarios)
- ❌ Purely tactical (execution minutiae)
- ❌ Context-dependent (only relevant in specific situations)

### Activity Extraction Guidelines

**Extract activities as types of work:**
- Focus on **what** work is done (not **how** it's executed)
- Example: "Establish Security Posture" (not "Configure AWS IAM Policies")
- Example: "Monitor Operations" (not "Set up Datadog Dashboards")

### Competency Extraction Guidelines

**Extract skill categories (not job titles):**
- "Cloud Architecture" (not "Cloud Architect")
- "DevOps Practices" (not "DevOps Engineer")
- "Security Engineering" (not "Security Engineer")
- "Product Management" (not "Product Manager")

## Output Structure

**Write to: `baselines/<name>/01-analysis-report.md`**

**Use the exact same structure as `prompts/phase-1-analysis.md` Section "Final Output Structure":**

1. **Executive Summary**
2. **Methodology Overview**
3. **Outcomes** (organized by perspective)
4. **Concerns** (with states, work products, relationships)
5. **Work Products** (with levels of detail)
6. **Activities** (with technique narratives, outcomes)
7. **Competencies** (with levels)
8. **Personas** (roles combining competencies)
9. **Persona Groups** (teams)
10. **Workflows and Patterns**
11. **Practice Hierarchy** (SKIP for baselines - not applicable)
12. **Citations**

**Expected Output Size:** ~30-50K words (comprehensive extraction, will be distilled in Phase 1.5)

## Quality Standards

**Follow all quality standards from `prompts/phase-1-analysis.md` plus:**

**Universality Check:**
- Before finalizing, review all concern/activity/competency names
- Flag any vendor/tool-specific terminology
- Document why specific terms are used (if intentional)
- Phase 1.5 will distill to neutral terminology

**Comprehensiveness:**
- Extract ALL relevant content (don't pre-filter for essentials)
- Phase 1.5 distillation will reduce to foundational elements
- Better to be comprehensive here than miss essential concepts

## Common Pitfalls to Avoid

❌ **Over-filtering in Phase 1**: Extract comprehensively, let Phase 1.5 distill
❌ **Using implementation details**: Focus on types of work, not specific tools
❌ **Creating practice hierarchy**: Baselines are single cohesive frameworks
❌ **Role-focused competencies**: Extract skill categories, not job titles
❌ **Skipping workflows**: Patterns are important for understanding progressions

## Success Criteria

✅ Comprehensive extraction of source methodology (~30-50K words)
✅ All 4 perspectives represented (Business, Technology, People, Process)
✅ Universal terminology preferred (vendor-neutral where possible)
✅ 12 required sections present (skip Practice Hierarchy)
✅ Rich citations and source references
✅ Output file: `baselines/<name>/01-analysis-report.md`

---

**Next Phase:** Phase 1.5 Distillation will read this comprehensive analysis and identify essential elements suitable for a foundational baseline practice.
