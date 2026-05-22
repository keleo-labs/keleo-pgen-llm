# Development Scripts

This directory contains development and one-off scripts used during the evolution of the Practice Language Code Generation System. These scripts were instrumental in developing, testing, and refining the pipeline but are **not part of the core workflow**.

## Directory Structure

```
scripts/
├── extraction/     # Component extraction from modules
├── building/       # Practice JSON construction
├── completion/     # Finalizing and completing partial JSONs
├── migration/      # One-off migration and fix scripts
└── translation/    # Early translation experiments
```

## Core Workflow vs Development Scripts

**For production use**, rely on:
- **`/translate-methodology` skill** - Automated three-phase pipeline
- **`utils/` directory** - Permanent validation and fix utilities

**These scripts** are:
- Development aids used while building the pipeline
- One-off utilities for specific practices (often with hardcoded paths)
- Experimental approaches superseded by the modular workflow
- Kept for reference and potential future adaptation

## When to Use These Scripts

These scripts are generally **not needed** for normal practice translation. They may be useful for:

1. **Debugging** - Understanding how components were extracted during development
2. **Recovery** - Manually extracting specific elements if the pipeline fails
3. **Adaptation** - Starting point for custom extraction logic
4. **Reference** - Understanding the evolution of the translation approach

## Script Categories

### [extraction/](extraction/)
Scripts for extracting specific components (alphas, work products, activities) from Phase 1 markdown modules. Used during pipeline development to test component extraction logic.

### [building/](building/)
Scripts for building Practice JSON structures from extracted components. Early experiments in JSON construction before the modular Phase 2 approach.

### [completion/](completion/)
Scripts for completing partial or incomplete Practice JSONs. Used to fill in missing activities, personas, or other elements during iterative development.

### [migration/](migration/)
One-off scripts for fixing specific issues in generated JSONs or migrating between schema versions. Generally practice-specific with hardcoded paths.

### [translation/](translation/)
Early translation experiments from Phase 1 modules to JSON. Superseded by the current `prompts/phase-2-modular.md` approach.

## Recommended Workflow

Instead of using these scripts directly, use the integrated workflow:

```bash
# Use the skill for end-to-end translation
/translate-methodology [source-files-or-urls]

# Or use the permanent utilities in utils/ for validation
cd practices/my-practice/
python3 ../../utils/fix-property-names.py
python3 ../../utils/validate-baseline-references.py
python3 ../../utils/validate-internal-integrity.py
```

See the [utils README](../utils/README.md) for permanent utilities that support the `/translate-methodology` skill.

## Contributing

If you develop new extraction or validation logic in these scripts and it proves valuable, consider:

1. **Generalizing** - Remove hardcoded paths and practice-specific logic
2. **Moving to utils/** - Make it a permanent, reusable utility
3. **Integrating into the skill** - Add to `/translate-methodology` workflow
4. **Documenting** - Update the relevant README with usage instructions
