export const meta = {
  name: 'alpha-cluster-mapping',
  description: 'Parallel Phase 2 mapping by alpha clusters for faster generation',
  whenToUse: 'For practices with many alphas where sequential mapping is slow',
  phases: [
    { title: 'Cluster', detail: 'Group alphas into independent clusters' },
    { title: 'Map', detail: 'Map each cluster in parallel' },
    { title: 'Merge', detail: 'Assemble cluster mappings into unified guide' },
  ],
}

const CLUSTER_SCHEMA = {
  type: 'object',
  properties: {
    clusters: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          name: { type: 'string' },
          primaryAlpha: { type: 'string' },
          alphas: { type: 'array', items: { type: 'string' } },
          concerns: { type: 'array', items: { type: 'string' } },
        },
        required: ['name', 'primaryAlpha', 'alphas'],
      },
    },
    metadata: { type: 'string' },
    keywords: { type: 'string' },
    aliases: { type: 'string' },
  },
  required: ['clusters'],
}

const parsedArgs = typeof args === 'string' ? JSON.parse(args) : (args || {})
const analysisReport = parsedArgs.analysisReport
const baseline = parsedArgs.baseline || ''
const outputDir = parsedArgs.outputDir
const practiceName = parsedArgs.practiceName || 'practice'

if (!analysisReport || !outputDir || !baseline) {
  log('ERROR: analysisReport, baseline, and outputDir required')
  return { error: 'analysisReport, baseline, and outputDir required' }
}

phase('Cluster')

const clusters = await agent(`Analyze a Phase 1 analysis report and group alphas into independent mapping clusters.

**Analysis report:** \`${analysisReport}\`
**Baseline:** \`${baseline}\`

**Instructions:**
1. Read the analysis report and baseline
2. Identify all alphas that will be mapped (both new and redeclared)
3. Group them into 2-4 clusters based on semantic proximity:
   - Each cluster should have a primary alpha and 2-4 related alphas
   - Clusters should be as independent as possible (minimal cross-cluster relatesTo)
   - Every alpha must appear in exactly one cluster
4. Also extract the practice-level metadata (name, description, baselinePracticeName, keywords, aliases) as text strings — these are shared across clusters and will be prepended to the merged output.

Return clusters array plus the shared metadata, keywords, and aliases as markdown strings.`, {
  label: 'cluster',
  phase: 'Cluster',
  schema: CLUSTER_SCHEMA,
})

if (!clusters || !clusters.clusters || clusters.clusters.length < 2) {
  log('Clustering produced fewer than 2 clusters — single-pass mapping recommended')
  return { error: 'Too few clusters for parallel mapping', clusters }
}

log(`${clusters.clusters.length} clusters identified`)

phase('Map')

const clusterResults = await parallel(clusters.clusters.map((c, i) => () =>
  agent(`Map a cluster of alphas from Phase 1 analysis to Practice Language structures.

**Analysis report:** \`${analysisReport}\`
**Baseline:** \`${baseline}\`
**Also read:** \`references/semantics.md\`

**YOUR CLUSTER: "${c.name}"**
- Primary Alpha: ${c.primaryAlpha}
- Alphas to map: ${c.alphas.join(', ')}
${c.concerns ? `- Related concerns: ${c.concerns.join(', ')}` : ''}

**Read the Phase 2 mapping prompt for format requirements:**
- \`prompts/phase-2-mapping.md\` (Output Format section)

**Map ONLY the alphas in your cluster.** For each alpha:
1. Determine type: Redeclaration, Specialization (contributesTo), or Variant (mapsTo)
2. Define states (3+ for new alphas)
3. Map relatesTo relationships (including direction)
4. Map work products that prove these alpha states
5. Map activities that advance these alpha states
6. Ensure every state beyond the first has a supporting activity

Output the mapping as markdown following the Phase 2 format. Write to:
\`${outputDir}/_cluster-${i}.md\``, {
    label: `cluster-${i}-${c.name.toLowerCase().replace(/\s+/g, '-').substring(0, 20)}`,
    phase: 'Map',
  })
))

const validMappings = clusterResults.filter(Boolean)
log(`${validMappings.length}/${clusters.clusters.length} cluster mappings completed`)

phase('Merge')

const clusterFiles = clusters.clusters.map((_, i) => `${outputDir}/_cluster-${i}.md`)

await agent(`Merge cluster mapping files into a unified Phase 2 mapping guide.

**Cluster files to read:**
${clusterFiles.map(f => `- \`${f}\``).join('\n')}

**Shared metadata from clustering:**
${clusters.metadata || '(extract from analysis report)'}

**Shared keywords:**
${clusters.keywords || '(extract from analysis report)'}

**Shared aliases:**
${clusters.aliases || '(none)'}

**Read the Phase 2 format:**
- \`prompts/phase-2-mapping.md\` (Output Format section)

**Instructions:**
1. Read all cluster files
2. Assemble into the standard Phase 2 structure:
   - Metadata, Delineation Analysis, Baseline Practice Index
   - Merge all Alpha Mappings sections
   - Merge all Work Product Mappings sections
   - Merge all Activity Mappings sections
   - Build unified Alpha-State-Activity Gap Analysis
   - Build unified Pattern Mappings (all alphas in views)
   - Add Alias Mappings and Validation Checklist
3. Write the merged guide to: \`${outputDir}/02-mapping-guide.md\`
4. Validate:
\`\`\`bash
python3 utils/validate-phase-output.py ${outputDir}/02-mapping-guide.md --phase 2 --gate
\`\`\`
5. Clean up cluster files:
\`\`\`bash
rm ${clusterFiles.join(' ')}
\`\`\``, {
  label: 'merge',
  phase: 'Merge',
})

return {
  clusterCount: clusters.clusters.length,
  mappingsCompleted: validMappings.length,
  outputDir,
}
