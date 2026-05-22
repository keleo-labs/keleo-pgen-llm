# Phase 2 Parsers - Reusable JSON Translation Utilities

This directory contains reusable Python parsers for translating Phase 1 modular markdown into schema-compliant JSON.

## Overview

These parsers implement the Phase 2 translation process from the `/translate-methodology` skill. They can be used for any methodology translation following the Phase 1 modular format.

## Parsers

### Core Parsers

1. **`alpha_parser.py`** - Extracts alpha definitions, states, checklists, narratives, instances
2. **`workproduct_parser.py`** - Extracts work products, levels of detail, contributions, instances
3. **`activity_parser.py`** - Extracts activities, personas, teams, technique narratives
4. **`pattern_parser.py`** - Extracts patterns, views, alpha states tracked, instance tracking
5. **`alias_parser.py`** - Extracts practice element aliases from terminology mappings

### Orchestrator

**`translate_practice.py`** - Main script that uses all parsers to build complete practice JSON

**`assemble_method.py`** - Combines multiple practice JSONs into method JSON

## Usage

### Translate a Single Practice

```bash
python translate_practice.py \
  <practice-dir> \
  <baseline-path> \
  <output-file>
```

**Example:**
```bash
python translate_practice.py \
  ../../practices/red-hat-ansible-automation-platform/report-elements/practice-1 \
  ../../deps/platform-adoption-kernel.json \
  ../../practices/red-hat-ansible-automation-platform/practice-1.json
```

### Use Individual Parsers

Each parser can be run standalone for testing:

```bash
# Test alpha parser
python alpha_parser.py practice-1/03a-alphas-solution.md practice-1/03b-alphas-endeavor.md

# Test work product parser
python workproduct_parser.py practice-1/04-workproducts.md

# Test activity parser
python activity_parser.py practice-1/05-activities-roles.md

# Test pattern parser
python pattern_parser.py practice-1/06-patterns.md
```

## Input Format

Parsers expect Phase 1 modular markdown files:

- `01-practice-details.md` - Practice metadata, tags, keywords
- `02-citations.md` - APA7 format citations
- `03-alphas.md` (or `03a`, `03b`, `03c` if split) - Alpha definitions
- `04-workproducts.md` - Work product definitions
- `05-activities-roles.md` - Activities, personas, teams
- `06-patterns.md` - Pattern definitions
- `07-aliases.md` - Terminology aliases (optional)

## Output Format

Generates schema-compliant JSON following `deps/language.schema.json`.

## Features

### Robust Markdown Parsing

- Handles multiple header levels (`##`, `###`, `####`)
- Extracts structured content (checklists, narratives, references)
- Cleans and normalizes text
- Handles split files (e.g., alphas by focus)

### Schema Compliance

- Generates JSON matching exact schema structure
- Uses correct property names (`contributesTo`, `worksOn`, etc.)
- Maintains required fields
- Validates references where possible

### Validation Support

- Cross-references alpha states in work products and activities
- Maps competencies to baseline competency names
- Extracts activity space references
- Parses alpha progressions (`contributesTo`)

## Reusability

These parsers are designed to be **methodology-agnostic**:

- No hardcoded practice names
- Flexible markdown pattern matching
- Configurable via command-line arguments
- Can be imported as Python modules

## Integration with Skill

To use these parsers in the `/translate-methodology` skill:

1. Phase 1 completes with modular markdown in `report-elements/`
2. Phase 1.5 generates `cross-reference-index.json`
3. Phase 2 uses `translate_practice.py` for each practice
4. Method assembler combines practices into final method JSON
5. Validation scripts (Phase 2.5, 2.6, 2.7) run on generated JSON

## Limitations

### Current Simplifications

1. **Citations** - Basic APA7 parsing (may need refinement)
2. **Narratives** - Simplified narrative type detection
3. **Alpha Instances** - Basic instance extraction (needs context)
4. **Competency Mapping** - May need baseline competency validation
5. **Activity Spaces** - Not extracted from baseline (would need enhancement)

### Known Gaps

- **Alias parsing:** Stub exists but needs full implementation to extract from `07-aliases.md`
- **Alpha instances:** Parser detects instances but doesn't connect to practice root or pattern views
- **Work product instances:** Parser detects instances but doesn't add to practice JSON
- **Pattern view instances:** Instance tracking in pattern views not being extracted
- Some narrative structures may not parse correctly
- Complex cross-practice references in methods need validation

## Next Steps

### For Current Translation

1. Run on Practice 1 and Practice 2
2. Review generated JSON for quality
3. Run schema validation
4. Apply Phase 2.5 fixes (property names)
5. Run Phase 2.6 validation (baseline references)
6. Run Phase 2.7 validation (internal integrity)

### For Future Enhancements

**Priority (Part of Standard Workflow):**

1. **Implement alias parser** - Parse `07-aliases.md` and populate `practiceElementAliases[]`
2. **Connect alpha instances** - Extract from pattern views and add to practice root + pattern views
3. **Connect work product instances** - Extract and add to practice root + pattern views
4. **Pattern view instance tracking** - Parse "Specific Instances Tracked" sections

**Secondary:**

1. Enhance narrative type detection
2. Add baseline activity space extraction
3. Improve competency mapping validation
4. Add comprehensive unit tests

## Example Output

Running on AAP Practice 1 generates:

```json
{
  "name": "Platform Administration & Operations",
  "description": "...",
  "baselinePracticeName": "Platform Adoption Essentials",
  "alphas": [7 alphas with states and checklists],
  "workProducts": [10 work products with LODs],
  "activities": [13 activities with technique narratives],
  "patterns": [4 patterns with views],
  "citations": [11+ citations]
}
```

## Support

These utilities are maintained as part of the keleo-pgen-llm project. For issues or enhancements, see the project repository.
