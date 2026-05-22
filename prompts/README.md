# Practice Language Translation Prompts

This directory contains all LLM prompts used by the `/translate-methodology` skill to transform enterprise methodology documentation into schema-compliant Practice Language JSON.

## Directory Structure

```
prompts/
├── README.md                      # This file
├── phase-1-modules/               # Phase 1: Modular research analysis
│   ├── 00-analysis-plan.md
│   ├── 00-method-plan.md
│   ├── 01-practice-details.md
│   ├── 02-citations.md
│   ├── 03-alphas.md
│   ├── 04-workproducts.md
│   ├── 05-activities-roles.md
│   ├── 06-patterns.md
│   ├── 07-aliases.md
│   └── 08-method-assembly.md
├── phase-1-assembly.md            # Phase 1.5: Assemble modules and validate
├── phase-2-modular.md             # Phase 2: Incremental JSON translation
├── phase-2-segments/              # Phase 2: Segment generation rules
│   └── segment-generation-rules.md
├── reference/                     # Reference documentation
│   ├── improvements-history.md
│   ├── schema-violations-complete.md
│   └── schema-violations-found.md
└── archive/                       # Deprecated prompts (historical reference)
    ├── phase-1-monolithic.md
    └── phase-2-monolithic.md
```

## Active Prompts

### Phase 1: Research Analysis (Modular)

**Directory:** [phase-1-modules/](phase-1-modules/)

Generates focused research modules (3K-20K words each) that analyze source methodologies using the four-perspective framework.

**Modules:**
- **00-analysis-plan.md** - Strategic analysis and planning (for single practices)
- **00-method-plan.md** - Method composition planning (for multi-practice methods)
- **01-practice-details.md** - Practice metadata, tags, context
- **02-citations.md** - Bibliographic references (5-15 authoritative sources)
- **03-alphas.md** - Alpha definitions with states and checklists
- **04-workproducts.md** - Work product definitions with LODs
- **05-activities-roles.md** - Activities with technique narratives, personas, teams
- **06-patterns.md** - Pattern orchestrations and views
- **07-aliases.md** - Terminology mappings (if source uses different terms)
- **08-method-assembly.md** - Method integration layer (for multi-practice methods)

**Output:** 7-9 markdown files per practice (~50-80K words total)

### Phase 1.5: Assembly

**File:** [phase-1-assembly.md](phase-1-assembly.md)

Concatenates Phase 1 modules into complete research report and generates cross-reference validation index.

**Output:**
- `research-report.md` - Assembled documentation
- `cross-reference-index.json` - Validation index

### Phase 2: JSON Translation

**File:** [phase-2-modular.md](phase-2-modular.md)

Translates Phase 1 modules into schema-compliant JSON using incremental approach (reads modules directly, not the 80K report).

**Segment Rules:** [phase-2-segments/segment-generation-rules.md](phase-2-segments/segment-generation-rules.md)

**Output:** Schema-compliant Practice or Method JSON

## Reference Documentation

**Directory:** [reference/](reference/)

Documentation of schema issues, validation patterns, and historical improvements:

- **improvements-history.md** - Historical requirements and improvements checklist
- **schema-violations-complete.md** - Complete catalog of schema violations found during development
- **schema-violations-found.md** - Specific validation results from practice translations

These documents inform prompt development and provide troubleshooting guidance.

## Archived Prompts

**Directory:** [archive/](archive/)

Deprecated prompts kept for historical reference:

- **phase-1-monolithic.md** - Original single-pass Phase 1 approach (replaced by modular)
- **phase-2-monolithic.md** - Original single-pass Phase 2 approach (replaced by modular)

These prompts are **not used** by the current skill but are preserved to document the evolution of the translation approach.

## Prompt Development Guidelines

### When to Update Prompts

**Phase 1 prompts** should be updated when:
- Source methodology analysis needs improvement
- Four-perspective framework application changes
- Narrative quality or conciseness rules evolve
- New semantic patterns discovered in `references/semantics.md`

**Phase 2 prompts** should be updated when:
- Schema changes (`deps/language.schema.json`)
- Semantic rules change (`references/semantics.md`)
- Common validation errors discovered
- JSON structure or property names change

### Prompt Optimization Principles

1. **Self-Contained:** Each prompt includes all context needed (no external dependencies)
2. **Resource References:** Explicitly list all files to read (schema, baseline, reference docs)
3. **Execution Instructions:** Clear step-by-step process for the LLM to follow
4. **Quality Standards:** Specific rules for conciseness, completeness, accuracy
5. **Examples:** Show correct vs incorrect patterns where helpful

### Testing Prompt Changes

After modifying a prompt:
1. **Test on existing practice** - Regenerate specific module and compare to previous version
2. **Validate quality** - Ensure descriptions are single sentences, narratives are focused
3. **Check schema compliance** - Verify JSON output passes all validation steps
4. **Document changes** - Note what was changed and why in commit message

## Integration with Skill

The `/translate-methodology` skill references these prompts at specific execution steps:

**Phase 1 Module Generation:**
```bash
# Skill reads and applies each module prompt sequentially
prompts/phase-1-modules/00-analysis-plan.md
prompts/phase-1-modules/01-practice-details.md
prompts/phase-1-modules/02-citations.md
# ... etc
```

**Phase 1.5 Assembly:**
```bash
prompts/phase-1-assembly.md
```

**Phase 2 Translation:**
```bash
prompts/phase-2-modular.md
```

## Related Documentation

- **Skill Documentation:** `.claude/skills/translate-methodology/SKILL.md`
- **Workflow Optimization:** `.claude/skills/translate-methodology/WORKFLOW-OPTIMIZATION.md`
- **Parallel Execution:** `.claude/skills/translate-methodology/PARALLEL-EXECUTION-GUIDE.md`
- **Schema Reference:** `deps/language.schema.json`
- **Semantic Guidance:** `references/semantics.md`
- **Project Instructions:** `CLAUDE.md`

## Version History

**Current Version:** Modular two-phase pipeline (Phase 1 modules + Phase 2 incremental)

**Previous Versions:**
- Monolithic single-pass approach (archived)
- Early Gemini-specific prompts (removed, replaced with model-agnostic versions)

See `reference/improvements-history.md` for detailed evolution of prompt requirements.
