export const meta = {
  name: 'validated-pipeline',
  description: 'Validate phase outputs with gates, then fix-validate JSON',
  whenToUse: 'After skill generates phase outputs, to validate and fix the full pipeline',
  phases: [
    { title: 'Phase 1 Gate', detail: 'Validate analysis report completeness' },
    { title: 'Phase 2 Gate', detail: 'Validate mapping guide structure + spec compliance' },
    { title: 'Phase 3 Fix', detail: 'Fix-validate loop on generated JSON' },
    { title: 'Summary', detail: 'Aggregate pipeline results' },
  ],
}

const GATE_SCHEMA = {
  type: 'object',
  properties: {
    phase: { type: 'number' },
    gate: { enum: ['pass', 'warn', 'fail'] },
    summary: { type: 'string' },
    criticalCount: { type: 'integer' },
    advisoryCount: { type: 'integer' },
    criticalFailures: {
      type: 'array',
      items: { type: 'string' },
    },
    advisoryFailures: {
      type: 'array',
      items: { type: 'string' },
    },
  },
  required: ['phase', 'gate', 'summary', 'criticalCount', 'advisoryCount'],
}

const parsedArgs = typeof args === 'string' ? JSON.parse(args) : (args || {})
const practiceDir = parsedArgs.practiceDir
const baseline = parsedArgs.baseline || ''
const schema = parsedArgs.schema || 'deps/language.schema.json'
const parents = parsedArgs.parents || []
const kind = parsedArgs.kind || 'practice'
const skipPhase1 = parsedArgs.skipPhase1 || false
const skipPhase2 = parsedArgs.skipPhase2 || false

if (!practiceDir) {
  log('ERROR: args.practiceDir is required')
  return { error: 'practiceDir required' }
}

const results = { phase1: null, phase1_5: null, phase2: null, phase3: null }
let halted = false

// --- Phase 1 Gate ---
if (!skipPhase1 && !halted) {
  phase('Phase 1 Gate')

  const phase1File = kind === 'baseline'
    ? `${practiceDir}/01-analysis-report.md`
    : `${practiceDir}/01-analysis-report.md`

  results.phase1 = await agent(`Validate a Phase 1 analysis report using the gate validator.

**Run this command:**
\`\`\`bash
python3 utils/validate-phase-output.py ${phase1File} --phase 1 --gate
\`\`\`

Parse the JSON output and return structured results.
If the file does not exist, return gate: "fail" with summary explaining the file is missing.

Map criticalFailures and advisoryFailures to arrays of check name strings.`, {
    label: 'phase-1-gate',
    phase: 'Phase 1 Gate',
    schema: GATE_SCHEMA,
    effort: 'low',
  })

  if (results.phase1 && results.phase1.gate === 'fail') {
    log(`Phase 1 GATE FAILED: ${results.phase1.criticalCount} critical failures — halting pipeline`)
    halted = true
  } else if (results.phase1) {
    log(`Phase 1 gate: ${results.phase1.gate} (${results.phase1.advisoryCount} advisory)`)
  }

  if (kind === 'baseline' && !halted) {
    const phase15File = `${practiceDir}/01.5-distilled-essentials.md`
    results.phase1_5 = await agent(`Validate a Phase 1.5 distillation document using the gate validator.

**Run this command:**
\`\`\`bash
python3 utils/validate-phase-output.py ${phase15File} --phase 1.5 --gate
\`\`\`

Parse the JSON output and return structured results.
If the file does not exist, return gate: "pass" with summary noting Phase 1.5 is optional.

Map criticalFailures and advisoryFailures to arrays of check name strings.`, {
      label: 'phase-1.5-gate',
      phase: 'Phase 1 Gate',
      schema: GATE_SCHEMA,
      effort: 'low',
    })

    if (results.phase1_5 && results.phase1_5.gate === 'fail') {
      log(`Phase 1.5 GATE FAILED: ${results.phase1_5.criticalCount} critical failures — halting pipeline`)
      halted = true
    } else if (results.phase1_5) {
      log(`Phase 1.5 gate: ${results.phase1_5.gate}`)
    }
  }
}

// --- Phase 2 Gate ---
if (!skipPhase2 && !halted) {
  phase('Phase 2 Gate')

  const phase2File = `${practiceDir}/02-mapping-guide.md`
  const baselineFlag = baseline ? `--baseline ${baseline}` : ''
  const parentFlags = parents.map(p => `--parent ${p}`).join(' ')

  results.phase2 = await agent(`Validate a Phase 2 mapping guide using TWO validators and return combined results.

**Step 1 — Structure validation:**
\`\`\`bash
python3 utils/validate-phase-output.py ${phase2File} --phase 2 --kind ${kind} --gate
\`\`\`

**Step 2 — Spec compliance (mechanical checks):**
\`\`\`bash
python3 utils/verify-mapping-against-specs.py ${phase2File} ${baselineFlag} ${parentFlags} --kind ${kind} --summary
\`\`\`

Combine results:
- Start with the gate result from Step 1 (pass/warn/fail)
- If Step 2 reports any errors, escalate gate to "fail"
- If Step 2 reports only warnings, escalate gate to at least "warn"
- Merge advisory/critical counts from both steps
- List all critical failures from both steps in criticalFailures array
- List all advisory failures from both steps in advisoryFailures array
- Set phase to 2`, {
    label: 'phase-2-gate',
    phase: 'Phase 2 Gate',
    schema: GATE_SCHEMA,
    effort: 'low',
  })

  if (results.phase2 && results.phase2.gate === 'fail') {
    log(`Phase 2 GATE FAILED: ${results.phase2.criticalCount} critical failures — halting pipeline`)
    halted = true
  } else if (results.phase2) {
    log(`Phase 2 gate: ${results.phase2.gate} (${results.phase2.criticalCount}c/${results.phase2.advisoryCount}a)`)
  }
}

// --- Phase 3 Fix-Validate ---
if (!halted) {
  phase('Phase 3 Fix')

  const dirName = practiceDir.split('/').pop()
  const jsonFile = `${practiceDir}/${dirName}.json`
  const parentFlags = parents.map(p => `--parent ${p}`).join(' ')
  const baselineFlag = baseline ? `--baseline ${baseline}` : ''

  results.phase3 = await agent(`Run a fix-validate loop on a Phase 3 JSON file.

**File:** \`${jsonFile}\`
**Baseline:** ${baseline || '(none)'}
**Schema:** ${schema}
**Parents:** ${JSON.stringify(parents)}

## Process

### Step 1 — Initial Assessment
\`\`\`bash
python3 utils/assess-practice.py ${jsonFile} ${baselineFlag} --schema ${schema} ${parentFlags}
\`\`\`
Parse the JSON output. Record initial error and warning counts.

If the file does not exist, return gate: "fail" with summary explaining the file is missing.

### Step 2 — Fix Loop (up to 5 iterations)
Repeat until no auto-fixable issues remain OR counts stop decreasing:

a) Run fixes:
\`\`\`bash
python3 utils/fix-common-issues.py ${jsonFile} ${baseline} --fix --all
\`\`\`

b) If competency-levels issues exist and baseline is available:
\`\`\`bash
python3 utils/fix-competency-levels.py ${jsonFile} ${baseline} --fix
\`\`\`

c) Re-assess and compare counts.

### Step 3 — Return gate result
- gate: "pass" if 0 errors remaining
- gate: "warn" if 0 errors but warnings remain
- gate: "fail" if errors remain after max iterations
- criticalCount = final error count
- advisoryCount = final warning count
- summary: describe what was fixed`, {
    label: 'phase-3-fix',
    phase: 'Phase 3 Fix',
    schema: GATE_SCHEMA,
    effort: 'low',
  })

  if (results.phase3) {
    log(`Phase 3: ${results.phase3.gate} (${results.phase3.criticalCount}e/${results.phase3.advisoryCount}w)`)
  }
}

// --- Summary ---
phase('Summary')

const gates = [results.phase1, results.phase1_5, results.phase2, results.phase3].filter(Boolean)
const overallGate = halted ? 'fail'
  : gates.some(g => g.gate === 'fail') ? 'fail'
  : gates.some(g => g.gate === 'warn') ? 'warn'
  : 'pass'

log(`Pipeline ${overallGate}: ${gates.map(g => `P${g.phase}=${g.gate}`).join(', ')}`)

return {
  practiceDir,
  kind,
  overallGate,
  halted,
  haltedAt: halted ? (results.phase1?.gate === 'fail' ? 'phase1' : results.phase1_5?.gate === 'fail' ? 'phase1.5' : 'phase2') : null,
  gates: {
    phase1: results.phase1,
    phase1_5: results.phase1_5,
    phase2: results.phase2,
    phase3: results.phase3,
  },
}
