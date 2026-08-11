export const meta = {
  name: 'baseline-evolution',
  description: 'Re-validate dependent practices after baseline changes',
  whenToUse: 'After modifying a baseline practice, to check impact on dependents',
  phases: [
    { title: 'Discover', detail: 'Find all practices depending on the changed baseline' },
    { title: 'Validate', detail: 'Re-validate each dependent practice' },
    { title: 'Report', detail: 'Aggregate impact assessment' },
  ],
}

const IMPACT_SCHEMA = {
  type: 'object',
  properties: {
    practice: { type: 'string' },
    path: { type: 'string' },
    errors: { type: 'integer' },
    warnings: { type: 'integer' },
    brokenReferences: { type: 'array', items: { type: 'string' } },
    suggestedMode: { type: 'string' },
    summary: { type: 'string' },
  },
  required: ['practice', 'path', 'errors', 'warnings', 'summary'],
}

const parsedArgs = typeof args === 'string' ? JSON.parse(args) : (args || {})
const baselineName = parsedArgs.baselineName
const baselinePath = parsedArgs.baselinePath || ''
const schema = parsedArgs.schema || 'deps/language.schema.json'

if (!baselineName) {
  log('ERROR: baselineName required')
  return { error: 'baselineName required' }
}

phase('Discover')

const discovery = await agent(`Find all practices depending on a baseline.

\`\`\`bash
python3 utils/discover-dependencies.py --dependents "${baselineName}"
\`\`\`

Parse the JSON output. Return:
- dependents: array of {name, path, kind, role}
- count: total number`, {
  label: 'discover',
  phase: 'Discover',
  schema: {
    type: 'object',
    properties: {
      dependents: {
        type: 'array',
        items: {
          type: 'object',
          properties: {
            name: { type: 'string' },
            path: { type: 'string' },
            kind: { type: 'string' },
          },
          required: ['name', 'path'],
        },
      },
      count: { type: 'integer' },
    },
    required: ['dependents', 'count'],
  },
  effort: 'low',
})

if (!discovery || !discovery.dependents || discovery.dependents.length === 0) {
  log('No dependents found')
  return { baselineName, dependents: 0, impacts: [] }
}

const deps = discovery.dependents.filter(d => d.kind === 'practice' || d.kind === 'method')
log(`Found ${deps.length} dependent practices/methods (${discovery.count} total including baselines)`)

if (deps.length === 0) {
  return { baselineName, dependents: 0, impacts: [] }
}

phase('Validate')

const baselineFlag = baselinePath ? `--baseline ${baselinePath}` : ''

const impacts = await pipeline(deps.slice(0, 12), async (dep) => {
  return await agent(`Re-validate a practice against its (potentially changed) baseline.

**Practice:** \`${dep.path}\`
**Baseline:** ${baselinePath || '(discover from practice JSON)'}
**Schema:** ${schema}

## Step 1: Assess
\`\`\`bash
python3 utils/assess-practice.py ${dep.path} ${baselineFlag} --schema ${schema}
\`\`\`

## Step 2: Identify broken references
From the assessment, look for:
- \`baseline-ref-alpha\`: Alpha names that no longer exist in baseline
- \`baseline-ref-alias\`: Alias targets that no longer exist
- \`competency-levels\`: Competency level names that don't match baseline
- \`relationship-type\`: Relationship types that don't match baseline
- Schema validation errors

## Step 3: Return impact assessment
- practice: name from JSON
- path: file path
- errors: error count
- warnings: warning count
- brokenReferences: specific broken reference messages
- suggestedMode: from assessment recommendations
- summary: one-line impact description`, {
    label: dep.name.substring(0, 30),
    phase: 'Validate',
    schema: IMPACT_SCHEMA,
    effort: 'low',
  })
})

phase('Report')

const validImpacts = impacts.filter(Boolean)
const broken = validImpacts.filter(i => i.errors > 0)
const warned = validImpacts.filter(i => i.errors === 0 && i.warnings > 0)
const clean = validImpacts.filter(i => i.errors === 0 && i.warnings === 0)

log(`Impact: ${broken.length} broken, ${warned.length} warned, ${clean.length} clean (of ${validImpacts.length} validated)`)

return {
  baselineName,
  totalDependents: discovery.count,
  validated: validImpacts.length,
  broken: broken.length,
  warned: warned.length,
  clean: clean.length,
  impacts: validImpacts,
  needsUpdate: broken.map(i => ({ practice: i.practice, path: i.path, suggestedMode: i.suggestedMode })),
}
