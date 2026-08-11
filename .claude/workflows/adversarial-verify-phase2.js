export const meta = {
  name: 'adversarial-verify-phase2',
  description: 'Adversarial verification of Phase 2 mapping output before JSON generation',
  whenToUse: 'After Phase 2 mapping, before Phase 3 JSON generation',
  phases: [
    { title: 'Mechanical', detail: 'Run verify-mapping-against-specs.py' },
    { title: 'Semantic', detail: 'Independent perspective-diverse verification agents' },
    { title: 'Reconcile', detail: 'Merge findings and produce final verdict' },
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

const semanticAgents = await parallel([
  () => agent(`You are an ALPHA RELATIONSHIP VERIFIER. Read the Phase 2 mapping guide and verify that alpha relationships are semantically correct.

**File to read:** ${mappingGuide}
${baseline ? `**Baseline to read:** ${baseline}` : ''}
${parentInfo}

**Check these specific concerns:**

1. **contributesTo semantic correctness**: Does each new alpha's contributesTo target make sense? A "Cognitive Load" alpha contributing to "Team" makes sense. A "Security Policy" contributing to "Requirements" would be suspicious.

2. **relatesTo meaningfulness**: Are relatesTo relationships genuine inter-alpha dependencies, or are they vague/redundant? Look for relationships that could be stated more precisely.

3. **State progression coherence**: Do each alpha's states form a logical progression from initial to mature? States should represent increasing capability or maturity, not random milestones.

4. **Redeclaration appropriateness**: For redeclared alphas, are the added checklists actually enriching the baseline states with practice-specific detail, or are they generic/unrelated?

5. **Alpha granularity**: Are new alphas at the right granularity? Too fine-grained (should be an activity), too broad (should be split), or overlapping with siblings?

**Important**: Only report genuine concerns. Do not flag things that are clearly correct. Be specific — cite alpha names, state names, and exact issues. Return findings with severity "error" for definite problems and "warning" for questionable choices.`, {
    label: 'alpha-semantics',
    phase: 'Semantic',
    schema: FINDINGS_SCHEMA,
  }),

  () => agent(`You are a COVERAGE AND COMPLETENESS VERIFIER. Read the Phase 2 mapping guide and verify mapping completeness.

**File to read:** ${mappingGuide}
${analysisReport ? `**Phase 1 analysis to read:** ${analysisReport}` : ''}
${baseline ? `**Baseline to read:** ${baseline}` : ''}

**Check these specific concerns:**

1. **Concern coverage**: If a Phase 1 analysis report is available, verify that all major concerns from Phase 1 are addressed in the mapping — either as alphas, activities, work product contributions, or explicit checklist items. Flag concerns that appear to be dropped.

2. **Activity-state gap**: For each alpha, verify that every state beyond the first has at least one activity whose contributesTo references that state. States without activities are "paper states" that can never be achieved.

3. **Pattern completeness**: If patterns are defined, verify they reference all practice alphas (not just a subset). Missing alphas from patterns create incomplete lifecycle views.

4. **Work product coverage**: Verify that major evidence artifacts are captured as work products. Flag alphas that have states but no work product proving those states.

5. **Competency coverage**: Verify activities reference appropriate competencies at appropriate levels (not everything at "Masters" or everything at "Basic").

**Important**: Only report genuine gaps. Some concerns are intentionally addressed through checklists rather than dedicated elements — that's valid. Be specific in your findings.`, {
    label: 'coverage-check',
    phase: 'Semantic',
    schema: FINDINGS_SCHEMA,
  }),

  () => agent(`You are a NAMING AND CONSISTENCY VERIFIER. Read the Phase 2 mapping guide and verify naming quality and internal consistency.

**File to read:** ${mappingGuide}
${baseline ? `**Baseline to read:** ${baseline}` : ''}

**Check these specific concerns:**

1. **Description quality**: Descriptions should be single sentences that capture WHAT the element is, not HOW it works. Flag multi-sentence descriptions or descriptions that read like instructions.

2. **Name uniqueness**: All element names (alphas, activities, work products, patterns) should be unique across the entire practice. Flag any duplicates.

3. **Alias correctness**: If aliases are defined, verify they use domain-appropriate terminology. Verify alias names are NOT used in structural references (contributesTo, mapsTo, activitySpaceName should use canonical baseline names, not aliases).

4. **Keyword appropriateness**: Keywords should be domain-specific technical terms that enable search/discovery. Flag generic words (e.g., "management", "process") or terms that don't appear in the practice content.

5. **Checklist quality**: Checklist items should be verifiable assertions (can be checked as done/not done), not vague aspirations. Flag items that are too abstract to verify.

6. **Narrative structure**: Narratives should use the structured format (narrativeTypeName + narrativeContexts), not free-form prose paragraphs.

**Important**: Focus on naming and consistency issues, not semantic correctness (that's another agent's job). Be specific in your findings.`, {
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
