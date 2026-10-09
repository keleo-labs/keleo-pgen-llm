export const meta = {
  name: 'cross-practice-verify',
  description: 'Check naming, aliasing, and alpha consistency across practices sharing a baseline',
  whenToUse: 'After generating multiple practices against the same baseline',
  phases: [
    { title: 'Scan', detail: 'Identify shared-baseline practices and extract elements' },
    { title: 'Verify', detail: 'Check cross-practice consistency' },
  ],
}

const FINDINGS_SCHEMA = {
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
          practices: { type: 'array', items: { type: 'string' } },
        },
        required: ['severity', 'category', 'message'],
      },
    },
    summary: { type: 'string' },
  },
  required: ['findings', 'summary'],
}

const parsedArgs = typeof args === 'string' ? JSON.parse(args) : (args || {})
const baselineName = parsedArgs.baselineName
const practiceFiles = parsedArgs.practiceFiles || []

if (!baselineName && !practiceFiles.length) {
  log('ERROR: Provide either baselineName or practiceFiles')
  return { error: 'baselineName or practiceFiles required' }
}

phase('Scan')

const scanResult = await agent(`Discover practices sharing a baseline and extract element names for cross-practice comparison.

${baselineName ? `**Step 1: Find dependents**
\`\`\`bash
python3 utils/discover-dependencies.py --dependents "${baselineName}"
\`\`\`
From the results, collect the file paths of all practices (kind: "practice") that depend on this baseline.` : `**Practice files provided:** ${JSON.stringify(practiceFiles)}`}

**Step 2: For each practice file**, run:
\`\`\`bash
python3 utils/assess-practice.py <file.json> --schema deps/language.schema.json
\`\`\`

Extract from each practice:
- Practice name
- All alpha names (new + redeclared)
- All alias names and their canonical targets
- All activity names
- All work product names
- All keywords

Return a JSON object with:
- practices: array of {name, path, alphas: string[], aliases: {aliasName, canonicalName}[], activities: string[], workProducts: string[], keywords: string[]}
- summary: one-line count`, {
  label: 'scan',
  phase: 'Scan',
  schema: {
    type: 'object',
    properties: {
      practices: {
        type: 'array',
        items: {
          type: 'object',
          properties: {
            name: { type: 'string' },
            path: { type: 'string' },
            alphas: { type: 'array', items: { type: 'string' } },
            aliases: { type: 'array', items: { type: 'object' } },
            activities: { type: 'array', items: { type: 'string' } },
            workProducts: { type: 'array', items: { type: 'string' } },
            keywords: { type: 'array', items: { type: 'string' } },
          },
          required: ['name', 'path'],
        },
      },
      summary: { type: 'string' },
    },
    required: ['practices', 'summary'],
  },
})

if (!scanResult || !scanResult.practices || scanResult.practices.length < 2) {
  log('Need at least 2 practices to compare')
  return { error: 'Need at least 2 practices', scan: scanResult }
}

log(`Scanned ${scanResult.practices.length} practices`)

phase('Verify')

const practiceData = JSON.stringify(scanResult.practices, null, 2)

// The brief is shared with the generation skills' Phase 2 gate so the two
// cannot drift — see .claude/skills/verification-foundation/.
const verified = await agent(`Read .claude/skills/verification-foundation/verifiers/phase-2.md
and follow the brief under the heading for the \`cross-practice-consistency\` verifier,
exactly as written. Also read
.claude/skills/verification-foundation/VERIFY-FOUNDATION.md sections 4 and 5 for the
findings contract and severity calibration.

The practices have already been scanned, so work from the data below rather than
re-reading the mapping guides.

**Practices to compare (${scanResult.practices.length} total):**
${practiceData}

**Return** your findings in this response rather than writing a file: this workflow
collects them in-process.`, {
  label: 'verify',
  phase: 'Verify',
  schema: FINDINGS_SCHEMA,
})

return {
  baselineName,
  practiceCount: scanResult.practices.length,
  findings: verified ? verified.findings : [],
  summary: verified ? verified.summary : 'Verification failed',
}
