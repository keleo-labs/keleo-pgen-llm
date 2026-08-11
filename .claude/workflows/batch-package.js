export const meta = {
  name: 'batch-package',
  description: 'Validate and package multiple practices into .keleo archives in parallel',
  whenToUse: 'After generating or updating multiple practices that need packaging',
  phases: [
    { title: 'Validate', detail: 'Assess and fix each practice JSON' },
    { title: 'Package', detail: 'Create .keleo archives' },
  ],
}

const RESULT_SCHEMA = {
  type: 'object',
  properties: {
    file: { type: 'string' },
    name: { type: 'string' },
    valid: { type: 'boolean' },
    errors: { type: 'integer' },
    warnings: { type: 'integer' },
    packaged: { type: 'boolean' },
    keleoPath: { type: 'string' },
    message: { type: 'string' },
  },
  required: ['file', 'valid', 'packaged'],
}

const parsedArgs = typeof args === 'string' ? JSON.parse(args) : (args || {})
const files = parsedArgs.files || []
const baseline = parsedArgs.baseline || ''
const schema = parsedArgs.schema || 'deps/language.schema.json'
const parents = parsedArgs.parents || []
const version = parsedArgs.version || '1.0.0'
const autoFix = parsedArgs.autoFix !== false

if (!files.length) {
  log('No files provided in args.files')
  return { error: 'files required', totalFiles: 0 }
}

phase('Validate')

const results = await pipeline(files, async (file) => {
  const baselineFlag = baseline ? `--baseline ${baseline}` : ''
  const parentFlags = parents.map(p => `--parent ${p}`).join(' ')

  return await agent(`Validate a practice JSON file, optionally fix it, then package into .keleo.

**File:** \`${file}\`
**Baseline:** ${baseline || '(none)'}
**Schema:** ${schema}
**Auto-fix:** ${autoFix}
**Version:** ${version}

## Step 1: Assess
\`\`\`bash
python3 utils/assess-practice.py ${file} ${baselineFlag} --schema ${schema} ${parentFlags}
\`\`\`

## Step 2: Fix (if auto-fix enabled and issues found)
${autoFix ? `\`\`\`bash
python3 utils/fix-common-issues.py ${file} ${baseline} --fix --all
\`\`\`
Re-assess after fixing.` : 'Skip — auto-fix disabled.'}

## Step 3: Package (only if 0 errors)
Extract the practice name from the JSON file. Then:
\`\`\`bash
python3 utils/package-keleo.py --name <practice-name> --version ${version} \\
  --description "<practice description>" \\
  --documents ${baseline ? baseline + ' ' : ''}${file} \\
  -o bundles/<practice-name>.keleo
\`\`\`

Return structured result with file, valid (0 errors), packaged (package created), keleoPath, errors, warnings, and message.`, {
    label: file.split('/').pop(),
    phase: 'Validate',
    schema: RESULT_SCHEMA,
    effort: 'low',
  })
})

phase('Package')

const valid = results.filter(Boolean)
const packaged = valid.filter(r => r.packaged)
const failed = valid.filter(r => !r.valid)

log(`Batch complete: ${packaged.length}/${files.length} packaged, ${failed.length} failed validation`)

return {
  totalFiles: files.length,
  processed: valid.length,
  packaged: packaged.length,
  failed: failed.length,
  results: valid,
}
