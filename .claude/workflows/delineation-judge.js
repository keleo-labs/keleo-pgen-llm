export const meta = {
  name: 'delineation-judge',
  description: 'Judge panel to determine practice vs method boundaries from Phase 1 analysis',
  whenToUse: 'When Phase 1 analysis covers 8+ alphas and practice/method boundary is unclear',
  phases: [
    { title: 'Propose', detail: '3 independent agents propose delineation strategies' },
    { title: 'Judge', detail: 'Score and synthesize the best delineation' },
  ],
}

const PROPOSAL_SCHEMA = {
  type: 'object',
  properties: {
    strategy: { type: 'string' },
    decision: { enum: ['single-practice', 'method'] },
    practices: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          name: { type: 'string' },
          primaryAlpha: { type: 'string' },
          alphaCount: { type: 'integer' },
          alphas: { type: 'array', items: { type: 'string' } },
          rationale: { type: 'string' },
        },
        required: ['name', 'primaryAlpha', 'alphaCount', 'alphas', 'rationale'],
      },
    },
    reasoning: { type: 'string' },
  },
  required: ['strategy', 'decision', 'practices', 'reasoning'],
}

const VERDICT_SCHEMA = {
  type: 'object',
  properties: {
    winner: { type: 'integer' },
    decision: { enum: ['single-practice', 'method'] },
    practices: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          name: { type: 'string' },
          primaryAlpha: { type: 'string' },
          alphas: { type: 'array', items: { type: 'string' } },
        },
        required: ['name', 'primaryAlpha', 'alphas'],
      },
    },
    scoring: { type: 'string' },
    reasoning: { type: 'string' },
  },
  required: ['winner', 'decision', 'practices', 'reasoning'],
}

const parsedArgs = typeof args === 'string' ? JSON.parse(args) : (args || {})
const analysisReport = parsedArgs.analysisReport
const baseline = parsedArgs.baseline || ''

if (!analysisReport) {
  log('ERROR: analysisReport path required')
  return { error: 'analysisReport required' }
}

phase('Propose')

const STRATEGIES = [
  {
    name: 'Primary Alpha Focus',
    instruction: 'Group concerns around PRIMARY ALPHAS. Each practice gets ONE primary baseline alpha and its directly related alphas (via relatesTo, 1-level deep). Aim for 3-7 alphas per practice. Minimize overlap between practices.',
  },
  {
    name: 'Value Stream Oriented',
    instruction: 'Group concerns by DISTINCT VALUE STREAMS or user journeys. Each practice represents a different audience, lifecycle phase, or business outcome. A practice should answer "who gets value and how?" clearly.',
  },
  {
    name: 'Consolidation Oriented',
    instruction: 'Start with the FEWEST practices possible. Prefer a single practice unless there are genuinely irreconcilable value streams. Split only when concerns have different primary stakeholders AND different lifecycle rhythms.',
  },
]

const proposals = await parallel(STRATEGIES.map((s, i) => () =>
  agent(`You are proposing a practice delineation strategy using the "${s.name}" approach.

**Phase 1 analysis to read:** \`${analysisReport}\`
${baseline ? `**Baseline practice to read:** \`${baseline}\`\n` : ''}
**Your strategy:** ${s.instruction}

**Instructions:**
1. Read the Phase 1 analysis report
${baseline ? '2. Read the baseline practice to understand available alphas and their relatesTo relationships\n' : ''}3. Count the total concerns/potential alphas identified in Phase 1
4. Apply your strategy to propose practice boundaries:
   - If 3-7 alphas: propose a single practice
   - If 8+: propose splitting into multiple practices (a method)
5. For each proposed practice, identify:
   - A name
   - The primary alpha
   - Total alpha count (3-7 per practice)
   - The specific alphas it covers
   - Rationale for this grouping

Be specific. Name actual concerns from the analysis, not generic placeholders.`, {
    label: s.name.toLowerCase().replace(/\s+/g, '-'),
    phase: 'Propose',
    schema: PROPOSAL_SCHEMA,
  })
))

const validProposals = proposals.filter(Boolean)
log(`${validProposals.length}/3 proposals received`)

if (validProposals.length < 2) {
  return { error: 'Too few proposals', proposals: validProposals }
}

phase('Judge')

const proposalData = validProposals.map((p, i) => ({
  index: i,
  strategy: p.strategy,
  decision: p.decision,
  practiceCount: p.practices.length,
  practices: p.practices,
  reasoning: p.reasoning,
}))

const verdict = await agent(`You are the DELINEATION JUDGE. Score ${validProposals.length} independent proposals for practice/method boundaries.

**Proposals:**
${JSON.stringify(proposalData, null, 2)}

**Scoring criteria (weight each equally):**

1. **Cohesion** (1-5): Does each practice have a clear primary alpha and value proposition? Can you explain what each practice IS in one sentence?

2. **Completeness** (1-5): Are all Phase 1 concerns covered? No concerns dropped or orphaned?

3. **Minimal Overlap** (1-5): Do practices avoid duplicating the same concerns? Cross-references via dependencies are fine; redundant content is not.

4. **Right Granularity** (1-5): 3-7 alphas per practice? No "everything else" catch-all practices?

5. **Actionability** (1-5): Could Phase 2 mapping proceed with this delineation without ambiguity?

**Your task:**
1. Score each proposal on all 5 criteria
2. Select the WINNER (highest total score)
3. If the winner can be improved by incorporating ideas from other proposals, do so
4. Return the final delineation decision

In case of ties, prefer the simpler proposal (fewer practices).`, {
  label: 'judge',
  phase: 'Judge',
  schema: VERDICT_SCHEMA,
})

return {
  analysisReport,
  proposalCount: validProposals.length,
  verdict: verdict || { error: 'Judge failed' },
}
