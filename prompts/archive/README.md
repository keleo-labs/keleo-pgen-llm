# Archived Prompts

Deprecated prompts kept for historical reference and to document the evolution of the translation approach.

## Overview

These prompts are **no longer used** by the `/translate-methodology` skill but are preserved to understand:
- Why the modular approach was adopted
- What didn't work in earlier approaches
- Evolution of the translation methodology
- Historical context for current design decisions

**Do not use these prompts for new translations.** Refer to active prompts in parent directory.

## Archived Prompts

### phase-1-monolithic.md

**Original Approach:** Generate complete research report in a single pass

**What it did:**
- Read all source materials at once
- Generate entire practice analysis (~50-80K words) in single LLM session
- Produce one large markdown file with all sections

**Why it was deprecated:**

1. **Token limit issues** - Large practices exceeded context windows
2. **All-or-nothing** - Couldn't regenerate specific sections without redoing everything
3. **Quality variability** - Large outputs had inconsistent quality across sections
4. **Validation difficulty** - Hard to validate and debug 80K word outputs
5. **No parallelization** - Couldn't leverage concurrent execution

**When it was used:** Initial prototype, early translations

**Replacement:** Modular Phase 1 prompts in `../phase-1-modules/`

**Key lessons learned:**
- Modular generation produces more consistent quality
- Smaller outputs are easier to validate and iterate
- Incremental progress is better than all-or-nothing
- Parallel execution potential requires modularity

---

### phase-2-monolithic.md

**Original Approach:** Generate complete practice JSON in a single pass

**What it did:**
- Read all Phase 1 modules (200-400KB total)
- Generate complete practice JSON (80-120KB) in single LLM session
- Produce final schema-compliant JSON directly

**Why it was deprecated:**

1. **Token limit failures** - Input (Phase 1 modules) + Output (JSON) exceeded limits for large practices
2. **Quality inconsistency** - Latter parts of large JSON had more errors
3. **Extraction incompleteness** - Missed narratives, checklists, and details in large outputs
4. **No error recovery** - If generation failed partway, had to start over
5. **No selective regeneration** - Couldn't regenerate just alphas or just activities

**Token usage example (Practice 2):**
- Input: ~338KB of Phase 1 modules
- Output: ~102KB complete JSON
- Total: **440KB in single session** → FAILED

**When it was used:** Early Phase 2 implementations, before segmentation

**Replacement:** Segmented Phase 2 approach documented in `../phase-2-modular.md` and `../phase-2-segments/`

**Key lessons learned:**
- Segmented generation solves token limit problems
- 1:1 mapping (module → segment) is easier to understand and debug
- Parallel segment generation dramatically faster
- Mechanical assembly (Python) more reliable than LLM assembly
- Incremental validation catches issues earlier

---

## Comparison: Monolithic vs Modular

### Phase 1

| Aspect | Monolithic | Modular |
| ------ | ---------- | ------- |
| **Output** | 1 file (50-80K words) | 8 files (3-20K words each) |
| **Time** | 60-90 min (all at once) | 35-50 min (parallelized) |
| **Quality** | Variable across sections | Consistent per module |
| **Iteration** | Regenerate everything | Regenerate specific modules |
| **Validation** | End-to-end only | Per-module validation |
| **Parallelization** | Not possible | Wave 2 runs 3 agents concurrently |

### Phase 2

| Aspect | Monolithic | Segmented |
| ------ | ---------- | --------- |
| **Input** | All modules (~300KB) | One module at a time |
| **Output** | 1 JSON (80-120KB) | 9 JSON segments (2-40KB each) |
| **Time** | 60-90 min (or FAIL) | 15-20 min (parallelized) |
| **Token limits** | Often exceeded | Never exceeded |
| **Quality** | Incomplete extraction | Complete extraction |
| **Iteration** | Regenerate everything | Regenerate specific segments |
| **Parallelization** | Not possible | All 9 segments run concurrently |
| **Assembly** | LLM-based (ambiguous) | Python script (mechanical) |

## Historical Context

### Timeline

**Early 2026:**
- Initial monolithic prompts developed
- Tested on small methodologies (worked)
- Scaled to larger methodologies (failed on token limits)

**Mid 2026:**
- Modular Phase 1 approach developed
- Wave-based execution designed
- Parallel execution opportunities identified

**Late 2026:**
- Segmented Phase 2 approach developed
- Assembly scripts created
- Validation pipeline automated

**Current:**
- Fully modular two-phase pipeline
- Parallel execution at multiple levels
- 50-75% faster than original approach

### Design Principles Learned

From monolithic to modular:

1. **Small is better** - Smaller LLM outputs have higher quality
2. **Modularity enables parallelism** - Can't parallelize a monolith
3. **Clear boundaries** - Each module/segment has clear scope
4. **Incremental validation** - Catch issues early, not at the end
5. **Selective regeneration** - Fix problems without redoing everything
6. **Mechanical assembly** - Python scripts more reliable than LLM assembly

### Architectural Insights

**What worked from monolithic:**
- ✅ Phase 1 → Phase 2 separation
- ✅ Research analysis before JSON translation
- ✅ Four-perspective framework
- ✅ Baseline mapping approach

**What needed modularity:**
- ❌ Single-pass generation (token limits)
- ❌ All-or-nothing execution (no iteration)
- ❌ No parallelization (too slow)
- ❌ End-to-end validation only (issues found late)

**Result:** Keep high-level architecture, modularize execution

## When to Reference These Files

### For Understanding History
- Why was the workflow designed this way?
- What problems did modularity solve?
- How did the approach evolve?

### For Comparison
- What's different between old and new approaches?
- What were the pain points of monolithic generation?
- What benefits did modularity bring?

### For New Prompt Development
- What NOT to do (anti-patterns)
- Lessons learned from failed approaches
- Principles for sustainable prompt design

### NOT for Production Use
- ❌ Do not use these prompts for new translations
- ❌ Do not copy patterns from these prompts
- ❌ Do not reference as current documentation

## Related Documentation

- **Current Phase 1 Prompts:** [../phase-1-modules/](../phase-1-modules/)
- **Current Phase 2 Approach:** [../phase-2-modular.md](../phase-2-modular.md)
- **Segmented Approach:** [../phase-2-segments/](../phase-2-segments/)
- **Workflow Optimization:** `../../.claude/skills/translate-methodology/WORKFLOW-OPTIMIZATION.md`
- **Improvements History:** [../reference/improvements-history.md](../reference/improvements-history.md)
