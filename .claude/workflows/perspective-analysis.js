export const meta = {
  name: 'perspective-analysis',
  description: 'Parallel four-perspective Phase 1 analysis with synthesis',
  whenToUse: 'For thorough Phase 1 analysis using diverse perspectives',
  phases: [
    { title: 'Analyze', detail: '4 parallel perspective agents analyze source materials' },
    { title: 'Synthesize', detail: 'Merge perspectives into unified analysis report' },
  ],
}

const PERSPECTIVE_SCHEMA = {
  type: 'object',
  properties: {
    perspective: { type: 'string' },
    outcomes: { type: 'array', items: { type: 'string' } },
    concerns: { type: 'array', items: { type: 'string' } },
    activities: { type: 'array', items: { type: 'string' } },
    workProducts: { type: 'array', items: { type: 'string' } },
    competencies: { type: 'array', items: { type: 'string' } },
    personas: { type: 'array', items: { type: 'string' } },
    relationships: { type: 'array', items: { type: 'string' } },
    wordCount: { type: 'integer' },
  },
  required: ['perspective', 'outcomes', 'concerns', 'activities'],
}

const parsedArgs = typeof args === 'string' ? JSON.parse(args) : (args || {})
const sourceFiles = parsedArgs.sourceFiles || []
const outputDir = parsedArgs.outputDir
const practiceName = parsedArgs.practiceName || 'practice'

if (!sourceFiles.length || !outputDir) {
  log('ERROR: sourceFiles and outputDir required')
  return { error: 'sourceFiles and outputDir required' }
}

const sourceList = sourceFiles.map(f => `- \`${f}\``).join('\n')

const PERSPECTIVES = [
  {
    name: 'Business',
    focus: 'Value proposition, ROI, stakeholder alignment, risk/compliance, business outcomes',
    mapTo: 'Value focus',
  },
  {
    name: 'Technology',
    focus: 'Architecture, implementation patterns, integration, deployment, technical capabilities',
    mapTo: 'Solution focus',
  },
  {
    name: 'People',
    focus: 'Roles, skills, team design, organizational change, competency requirements',
    mapTo: 'Endeavor focus',
  },
  {
    name: 'Process',
    focus: 'Workflows, value streams, lifecycle stages, governance, decision points',
    mapTo: 'May span multiple focuses',
  },
]

phase('Analyze')

const perspectiveResults = await parallel(PERSPECTIVES.map(p => () =>
  agent(`You are analyzing source methodology documentation from the **${p.name} Perspective**.

**Your focus:** ${p.focus}
**Maps to:** ${p.mapTo}

**Source files to read:**
${sourceList}

**Also read the domain framework for analytical structure:**
- \`references/domain-framework.md\`

**Instructions:**
1. Read all source files
2. Extract ONLY content relevant to your perspective (${p.name})
3. Identify:
   - **Outcomes**: What business/technical/people/process outcomes does this methodology promise?
   - **Concerns**: What areas of attention does this methodology address from your perspective?
   - **Activities**: What specific work activities are described?
   - **Work Products**: What artifacts or deliverables are produced?
   - **Competencies**: What skills or expertise are needed?
   - **Personas**: What roles are involved?
   - **Relationships**: What dependencies or connections exist between concerns?

Be thorough but focused on YOUR perspective. Other agents cover the other perspectives.
Include specific details, not generic observations.
Aim for 10-20 items per category where the source material supports it.`, {
    label: p.name.toLowerCase(),
    phase: 'Analyze',
    schema: PERSPECTIVE_SCHEMA,
  })
))

const validResults = perspectiveResults.filter(Boolean)
log(`${validResults.length}/4 perspective analyses completed`)

if (validResults.length < 2) {
  return { error: 'Too few perspectives completed', results: validResults }
}

phase('Synthesize')

const perspectiveData = JSON.stringify(validResults, null, 2)

const synthesis = await agent(`You are synthesizing 4 perspective analyses into a unified Phase 1 analysis report.

**Perspective results:**
${perspectiveData}

**Read the Phase 1 prompt for the required output format:**
- \`prompts/phase-1-analysis.md\` (specifically the Output Format section)
- \`references/domain-framework.md\`

**Also read the source files to fill any gaps:**
${sourceList}

**Instructions:**
1. Read the Phase 1 output format requirements
2. Merge all perspective findings into the standard sections:
   - ## 1. Outcomes — unified from all perspectives
   - ## 2. Concerns (Areas of Attention) — deduplicated, noting which perspective(s) identified each
   - ## 3. Work Products — merged, removing duplicates
   - ## 4. Activities — merged, noting perspective origin
   - ## 5. Competencies — unified skill requirements
   - ## 6. Personas — merged roles
   - ## 7. Persona Groups (Teams) — team structures
   - ## 8. Workflows and Patterns — lifecycle sequences
   - ## 9. Practices — preliminary practice boundaries
   - ## 10. Citations — from source materials

3. Write the complete merged analysis to:
   \`${outputDir}/01-analysis-report.md\`

4. Validate the output:
\`\`\`bash
python3 utils/validate-phase-output.py ${outputDir}/01-analysis-report.md --phase 1 --gate
\`\`\`

Each concern should note which perspective(s) identified it for traceability.
Target 30-50K words total. Ensure all 4 perspectives are represented.`, {
  label: 'synthesize',
  phase: 'Synthesize',
})

return {
  perspectives: validResults.length,
  outputDir,
  synthesis: synthesis ? 'completed' : 'failed',
}
