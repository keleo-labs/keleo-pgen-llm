# Reference Documentation

Historical documentation of schema issues, validation patterns, and improvement requirements that inform prompt development.

## Files

### improvements-history.md

Historical requirements and improvements checklist from the evolution of the translation workflow.

**Contents:**
- Compaction and reloading strategies
- Modular file generation requirements
- Concurrent practice processing
- Schema property additions (e.g., Citation.url)
- Python utilities organization
- Session resumption capabilities
- Model-agnostic prompt refactoring

**Use:**
- Understanding the evolution of the workflow
- Context for why certain architectural decisions were made
- Historical requirements that shaped current prompts

**Status:** Historical reference (requirements have been implemented)

---

### schema-violations-complete.md

Complete catalog of schema violations found during Practice 1 validation of red-hat-ai-3.

**Validation Details:**
- **Date:** 2026-05-21
- **File:** `practices/red-hat-ai-3/practice-1-ai-platform-management.json`
- **Total Errors:** 23 schema violations
- **Tool:** `validate-json-schema.js`

**Error Categories:**

1. **Narrative Structure (12 errors)**
   - Issue: Narratives must have `name` and `description` (extends PracticeElement)
   - Wrong: `{narrativeName, narrativeTypeName, narrativeContexts}`
   - Correct: `{name, description, narrativeTypeName, narrativeContexts}`

2. **Activity Narratives Property (10 errors)**
   - Issue: Activities use `narratives` not `techniqueNarratives`
   - Wrong: `activity.techniqueNarratives`
   - Correct: `activity.narratives`

3. **Practice Tags Structure (1 error)**
   - Issue: Tags must be nested in `tags` object
   - Wrong: `{domainTags: [...], lifecycleTags: [...], organizationalTags: [...]}`
   - Correct: `{tags: {domainTags: [...], lifecycleTags: [...], organizationalTags: [...]}}`

**Use:**
- Reference when developing Phase 2 prompts
- Understanding common schema compliance issues
- Troubleshooting validation failures
- Creating segment generation rules

**Status:** Active reference for schema compliance

---

### schema-violations-found.md

Specific validation results from early practice translation attempts.

**Contents:**
- Initial validation error reports
- Context for specific schema violations
- Examples of wrong vs correct structures

**Use:**
- Additional examples of schema violations
- Historical context for schema evolution
- Supplementary reference to schema-violations-complete.md

**Status:** Active reference

---

## How to Use These References

### When Developing Phase 1 Prompts

Check `improvements-history.md` for:
- Requirements that shaped the modular approach
- Conciseness and quality standards
- Natural progression discovery principles

### When Developing Phase 2 Prompts

Check `schema-violations-*.md` for:
- Common schema compliance issues
- Property naming mistakes
- Structure requirements
- Object vs string formats

### When Troubleshooting Validation Failures

1. **Check schema violations catalogs** for similar errors
2. **Review correct structure examples** in these documents
3. **Update prompts** to prevent similar errors
4. **Document new patterns** if novel violations discovered

### When Updating the Schema

If `deps/language.schema.json` changes:
1. **Review these documents** to see if violations are now valid or need updates
2. **Update prompts** to reflect new schema requirements
3. **Update violation catalogs** if necessary
4. **Test existing practices** against new schema

## Related Documentation

- **Schema Reference:** `../../deps/language.schema.json`
- **Semantic Guidance:** `../../references/semantics.md`
- **Phase 2 Modular Prompt:** [../phase-2-modular.md](../phase-2-modular.md)
- **Segment Generation Rules:** [../phase-2-segments/segment-generation-rules.md](../phase-2-segments/segment-generation-rules.md)
- **Validation Utilities:** `../../utils/README.md`

## Contributing

When discovering new schema violations:

1. **Document the error** with:
   - File that produced it
   - Validation date and tool
   - Wrong structure
   - Correct structure
   - Explanation of why it's wrong

2. **Update relevant catalog** (schema-violations-complete.md or create new entry)

3. **Update prompts** to prevent recurrence

4. **Add to segment generation rules** if applicable

5. **Test the fix** on an existing practice
