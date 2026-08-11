export const meta = {
  name: 'consistency-contract',
  description: 'Validate consistency of spec rules across all 3 skills',
  whenToUse: 'After modifying specs or skills, to verify rules are consistent',
  phases: [
    { title: 'Extract', detail: 'Extract specs from each skill' },
    { title: 'Compare', detail: 'Check consistency across skills' },
  ],
}

const SPEC_SCHEMA = {
  type: 'object',
  properties: {
    skill: { type: 'string' },
    scenarioCount: { type: 'integer' },
    categories: { type: 'array', items: { type: 'string' } },
    ruleIds: { type: 'array', items: { type: 'string' } },
    automatable: { type: 'integer' },
  },
  required: ['skill', 'scenarioCount', 'ruleIds'],
}

const CONSISTENCY_SCHEMA = {
  type: 'object',
  properties: {
    findings: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          severity: { enum: ['error', 'warning', 'info'] },
          category: { type: 'string' },
          message: { type: 'string' },
          skills: { type: 'array', items: { type: 'string' } },
        },
        required: ['severity', 'category', 'message'],
      },
    },
    summary: { type: 'string' },
    sharedRules: { type: 'integer' },
    skillSpecificRules: { type: 'integer' },
  },
  required: ['findings', 'summary'],
}

const SKILLS = [
  { name: 'generate-method', path: '.claude/skills/generate-method', specs: '.claude/skills/generate-method/specs/specs-index.json' },
  { name: 'create-baseline-method', path: '.claude/skills/create-baseline-method', specs: '.claude/skills/create-baseline-method/specs/specs-index.json' },
  { name: 'update-method', path: '.claude/skills/update-method', specs: '.claude/skills/update-method/specs/specs-index.json' },
]

phase('Extract')

const extractions = await parallel(SKILLS.map(skill => () =>
  agent(`Extract spec information from a skill.

**Skill:** ${skill.name}
**SKILL.md:** \`${skill.path}/SKILL.md\`
**Specs file (if exists):** \`${skill.specs}\`

**Instructions:**
1. Try to read the specs file first. If it exists, extract scenario data from it.
2. If no specs file, read the SKILL.md and look for Gherkin scenario blocks:
   - \`### Scenario:\` blocks with \`@rule:\` tags
3. Extract:
   - Total scenario count
   - Unique categories (the part before the hyphen in rule IDs, e.g., "semantic" from "semantic-001")
   - All rule IDs
   - Count of automatable scenarios (those with programmatic checks)

Return structured result.`, {
    label: skill.name,
    phase: 'Extract',
    schema: SPEC_SCHEMA,
    effort: 'low',
  })
))

const validExtractions = extractions.filter(Boolean)
log(`Extracted specs from ${validExtractions.length}/3 skills`)

if (validExtractions.length < 2) {
  return { error: 'Too few skills extracted', extractions: validExtractions }
}

phase('Compare')

const comparison = await agent(`Compare spec rules across ${validExtractions.length} skills for consistency.

**Skill specs:**
${JSON.stringify(validExtractions, null, 2)}

**Check these concerns:**

1. **Shared rule consistency**: Rules with the same ID (e.g., semantic-001) across skills should have compatible semantics. Flag if the same rule ID means different things in different skills.

2. **Missing shared rules**: Core rules (semantic-001 through semantic-012, naming-001, aliasing-001 through aliasing-003) should appear in all applicable skills. Flag skills missing rules they should implement.

3. **Baseline-specific rules**: create-baseline-method should have rules that generate-method doesn't (e.g., no contributesTo on root alphas, 5 competency levels). Flag if these are missing.

4. **Update-method inheritance**: update-method should reference generate-method rules (it's a wrapper). Flag if it defines contradictory rules.

5. **Coverage gaps**: Are there spec categories in one skill that are completely absent from another? E.g., if generate-method has aliasing rules but create-baseline doesn't.

Return findings with cross-skill context.`, {
  label: 'compare',
  phase: 'Compare',
  schema: CONSISTENCY_SCHEMA,
})

return {
  skills: validExtractions.length,
  totalRules: validExtractions.reduce((s, e) => s + e.scenarioCount, 0),
  findings: comparison ? comparison.findings : [],
  summary: comparison ? comparison.summary : 'Comparison failed',
}
