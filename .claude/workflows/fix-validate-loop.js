export const meta = {
  name: 'fix-validate-loop',
  description: 'Iteratively fix and validate practice/baseline JSON files',
  whenToUse: 'After Phase 3 generation or when assess-practice.py reports auto-fixable issues',
  phases: [
    { title: 'Fix-Validate', detail: 'Assess, auto-fix, re-assess loop per file' },
    { title: 'Report', detail: 'Aggregate results across all files' },
  ],
}

const RESULT_SCHEMA = {
  type: 'object',
  properties: {
    file: { type: 'string' },
    kind: { type: 'string' },
    iterations: { type: 'integer' },
    initialErrors: { type: 'integer' },
    initialWarnings: { type: 'integer' },
    finalErrors: { type: 'integer' },
    finalWarnings: { type: 'integer' },
    remainingCategories: {
      type: 'array',
      items: { type: 'string' },
    },
    fixesApplied: {
      type: 'array',
      items: { type: 'string' },
    },
    suggestedUpdateMode: { type: 'string' },
  },
  required: [
    'file', 'kind', 'iterations',
    'initialErrors', 'initialWarnings',
    'finalErrors', 'finalWarnings',
    'remainingCategories', 'fixesApplied', 'suggestedUpdateMode',
  ],
}

const parsedArgs = typeof args === 'string' ? JSON.parse(args) : (args || {})
const files = parsedArgs.files || []
const baseline = parsedArgs.baseline || ''
const schema = parsedArgs.schema || 'deps/language.schema.json'
const parents = parsedArgs.parents || []
const maxIter = parsedArgs.maxIterations || 5

if (!files.length) {
  log('No files provided in args.files — nothing to do')
  return { totalFiles: 0, results: [] }
}

phase('Fix-Validate')

const results = await pipeline(files, async (file) => {
  const baselineFlag = baseline ? `--baseline ${baseline}` : ''
  const schemaFlag = schema ? `--schema ${schema}` : ''
  const parentFlags = parents.map(p => `--parent ${p}`).join(' ')
  const baselinePos = baseline || ''

  return await agent(`You are running an iterative fix-validate loop on a Practice Language JSON file.

**File:** \`${file}\`
**Baseline:** ${baseline || '(none)'}
**Schema:** ${schema}
**Parents:** ${JSON.stringify(parents)}
**Max iterations:** ${maxIter}

## Process

### Step 1 — Initial Assessment
Run:
\`\`\`bash
python3 utils/assess-practice.py ${file} ${baselineFlag} ${schemaFlag} ${parentFlags}
\`\`\`
Parse the JSON output. Record the initial error count and warning count from the \`issues\` array.

### Step 2 — Fix Loop (up to ${maxIter} iterations)
Repeat until no auto-fixable issues remain OR issue counts stop decreasing:

a) Run fix-common-issues with all auto-fixes:
\`\`\`bash
python3 utils/fix-common-issues.py ${file} ${baselinePos} --fix --all
\`\`\`

b) If the assessment showed \`competency-levels\` issues and a baseline is available:
\`\`\`bash
python3 utils/fix-competency-levels.py ${file} ${baseline} --fix
\`\`\`

c) Re-run the assessment command from Step 1.

d) Compare error+warning counts with the previous iteration. If counts did not decrease, stop looping.

### Step 3 — Return structured result
Return a JSON object with the fields defined in the schema. For \`remainingCategories\`, list the unique category names from any remaining issues. For \`fixesApplied\`, list the unique category names from fixes that were applied across all iterations.`, {
    label: file.split('/').pop(),
    phase: 'Fix-Validate',
    schema: RESULT_SCHEMA,
    effort: 'low',
  })
})

phase('Report')

const valid = results.filter(Boolean)
const totalInitialErrors = valid.reduce((s, r) => s + r.initialErrors, 0)
const totalFinalErrors = valid.reduce((s, r) => s + r.finalErrors, 0)
const totalInitialWarnings = valid.reduce((s, r) => s + r.initialWarnings, 0)
const totalFinalWarnings = valid.reduce((s, r) => s + r.finalWarnings, 0)

log(`Fix-validate complete: ${valid.length}/${files.length} files processed`)
log(`Errors: ${totalInitialErrors} → ${totalFinalErrors} | Warnings: ${totalInitialWarnings} → ${totalFinalWarnings}`)

return {
  totalFiles: files.length,
  processed: valid.length,
  allClean: valid.every(r => r.finalErrors === 0),
  totalInitialErrors,
  totalFinalErrors,
  totalInitialWarnings,
  totalFinalWarnings,
  results: valid,
}
