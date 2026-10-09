export const meta = {
  name: 'adversarial-verify-phase2',
  description: 'Adversarial verification of Phase 2 mapping output before JSON generation',
  whenToUse: 'After Phase 2 mapping, before Phase 3 JSON generation',
  phases: [
    { title: 'Mechanical', detail: 'Run verify-mapping-against-specs.py' },
    { title: 'Semantic', detail: 'Verifier agents from verification-foundation/verifiers/phase-2.md' },
    { title: 'Reconcile', detail: 'Merge findings and produce final verdict' },
  ],
}

// Opt-in deep run of the Phase 2 verification gate. The generation skills run
// the same briefs inline via the Agent tool as a blocking gate — see
// .claude/skills/verification-foundation/VERIFY-FOUNDATION.md. Use this
// workflow to re-verify an existing mapping guide outside a generation run.

const FINDINGS_SCHEMA = {
  type: 'object',
  properties: {
    findings: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          rule: { type: 'string' },
          severity: { enum: ['error', 'warning', 'info'] },
          message: { type: 'string' },
          evidence: { type: 'string' },
        },
        required: ['severity', 'message'],
      },
    },
    summary: { type: 'string' },
  },
  required: ['findings', 'summary'],
}

const VERDICT_SCHEMA = {
  type: 'object',
  properties: {
    confirmed: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          originalMessage: { type: 'string' },
          verdict: { enum: ['confirmed', 'false-positive', 'needs-context'] },
          reasoning: { type: 'string' },
        },
        required: ['originalMessage', 'verdict', 'reasoning'],
      },
    },
    newFindings: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          severity: { enum: ['error', 'warning'] },
          message: { type: 'string' },
          evidence: { type: 'string' },
        },
        required: ['severity', 'message'],
      },
    },
    overallVerdict: { enum: ['pass', 'pass-with-warnings', 'fail'] },
    summary: { type: 'string' },
  },
  required: ['confirmed', 'newFindings', 'overallVerdict', 'summary'],
}

const parsedArgs = typeof args === 'string' ? JSON.parse(args) : (args || {})
const mappingGuide = parsedArgs.mappingGuide
const baseline = parsedArgs.baseline || ''
const analysisReport = parsedArgs.analysisReport || ''
const specs = parsedArgs.specs || '.claude/skills/generate-method/specs/specs-index.json'
const parents = parsedArgs.parents || []

if (!mappingGuide) {
  log('ERROR: args.mappingGuide is required')
  return { error: 'mappingGuide path required' }
}

// --- Stage 1: Mechanical verification ---
phase('Mechanical')

const baselineFlag = baseline ? `--baseline ${baseline}` : ''
const specsFlag = specs ? `--specs ${specs}` : ''

const mechanical = await agent(`Run mechanical verification of the Phase 2 mapping guide and return the findings.

**Command:**
\`\`\`bash
python3 utils/verify-mapping-against-specs.py ${mappingGuide} ${baselineFlag} ${specsFlag}
\`\`\`

Parse the JSON output. Return:
- findings: array of all findings from the output's "findings" array
- summary: a one-line summary of the extraction counts and finding counts`, {
  label: 'mechanical',
  phase: 'Mechanical',
  schema: FINDINGS_SCHEMA,
  effort: 'low',
})

const mechanicalFindings = (mechanical && mechanical.findings) || []

log(`Mechanical: ${mechanicalFindings.length} findings`)

// --- Stage 2: Perspective-diverse semantic verification ---
phase('Semantic')

const parentInfo = parents.length > 0
  ? `Parent practices: ${parents.join(', ')}. Some contributesTo targets may resolve to parent practice alphas — do NOT flag these as errors.`
  : 'No parent practices specified.'

// The briefs live in the verification foundation, shared with the generation
// skills, so the opt-in deep run and the skills' default inline run check the
// same things. Inlining them here let the two drift.
const BRIEFS = '.claude/skills/verification-foundation/verifiers/phase-2.md'

const verifierBrief = (name) => `Read ${BRIEFS} and follow the brief under the heading
for the \`${name}\` verifier, exactly as written. Also read
.claude/skills/verification-foundation/VERIFY-FOUNDATION.md sections 4 and 5 for the
findings contract and severity calibration.

**Substitutions for this run:**
- \`{GUIDE}\` = ${mappingGuide}
- \`{REPORT}\` = ${analysisReport || '(no Phase 1 analysis report supplied — skip checks that require it)'}
- \`{BASELINE}\` = ${baseline || '(no baseline supplied — skip checks that require it)'}
- \`{PARENTS}\` = ${parentInfo}
- \`{SUFFIX}\` = (empty)
- \`{SOURCES}\` = (not supplied in this workflow — work from the analysis report)

**Return** your findings in this response rather than writing a file: this workflow
collects them in-process. Use the same findings shape the brief specifies.`

const semanticAgents = await parallel([
  () => agent(verifierBrief('source-fidelity'), {
    label: 'source-fidelity',
    phase: 'Semantic',
    schema: FINDINGS_SCHEMA,
  }),

  () => agent(verifierBrief('alpha-semantics'), {
    label: 'alpha-semantics',
    phase: 'Semantic',
    schema: FINDINGS_SCHEMA,
  }),

  () => agent(verifierBrief('coverage'), {
    label: 'coverage-check',
    phase: 'Semantic',
    schema: FINDINGS_SCHEMA,
  }),

  () => agent(verifierBrief('naming-consistency'), {
    label: 'naming-quality',
    phase: 'Semantic',
    schema: FINDINGS_SCHEMA,
  }),
])

const allSemanticFindings = semanticAgents
  .filter(Boolean)
  .flatMap(r => r.findings || [])

log(`Semantic: ${allSemanticFindings.length} findings from ${semanticAgents.filter(Boolean).length} agents`)

// --- Stage 3: Reconcile ---
phase('Reconcile')

const allFindings = [
  ...mechanicalFindings.map(f => ({ ...f, source: 'mechanical' })),
  ...allSemanticFindings.map(f => ({ ...f, source: 'semantic' })),
]

const reconciled = await agent(`You are the RECONCILIATION JUDGE. You have findings from mechanical verification and semantic verification of a Phase 2 mapping guide.

**All findings (${allFindings.length} total):**
${JSON.stringify(allFindings, null, 2)}

**Your task:**

1. For EACH mechanical finding, decide if it is:
   - "confirmed" — clearly a real issue
   - "false-positive" — not actually a problem (explain why)
   - "needs-context" — might be an issue but needs more information (e.g., parent practice context)

2. For EACH semantic finding, decide if it adds NEW value beyond what the mechanical checks caught. Discard duplicates of mechanical findings.

3. Compile a final list of "newFindings" — semantic findings that are genuinely new issues not caught by mechanical verification.

4. Set overallVerdict:
   - "fail" if any confirmed errors exist
   - "pass-with-warnings" if only warnings remain
   - "pass" if all issues are false positives or resolved

5. Write a brief summary paragraph.

Be conservative: when in doubt, confirm a finding rather than dismissing it. But do dismiss obvious false positives (e.g., cross-practice references that would resolve with a --parent flag).`, {
  label: 'reconcile',
  phase: 'Reconcile',
  schema: VERDICT_SCHEMA,
})

if (reconciled) {
  const confirmed = (reconciled.confirmed || []).filter(c => c.verdict === 'confirmed').length
  const falsePos = (reconciled.confirmed || []).filter(c => c.verdict === 'false-positive').length
  const newCount = (reconciled.newFindings || []).length
  log(`Verdict: ${reconciled.overallVerdict} | ${confirmed} confirmed, ${falsePos} false-positives, ${newCount} new semantic findings`)
}

return {
  mappingGuide,
  mechanical: { findingCount: mechanicalFindings.length },
  semantic: { findingCount: allSemanticFindings.length, agentCount: semanticAgents.filter(Boolean).length },
  reconciled: reconciled || { overallVerdict: 'unknown', confirmed: [], newFindings: [], summary: 'Reconciliation failed' },
}
