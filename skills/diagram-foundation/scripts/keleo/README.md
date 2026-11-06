# Keleo Studio static diagrams

Version: 1.2.0

These files are copied from `keleo-studio-gas/utils/` and retain the Studio
layout algorithms and SVG styling. `diagram-text.mjs` is shared by the three
renderers. Local changes: orchestration and state flow support `--help`;
pattern matrix supports `--title`, `--note-offset` and `--external-loop-part`
for consecutive report panels that keep their cross-panel return visible.

| Script | Diagram |
|---|---|
| `render-orchestration-diagram.mjs` | `patternOrchestrations` timeline, including concurrent and nested stages |
| `render-pattern-matrix.mjs` | Pattern views by phase, with target states, notes and guarded returns |
| `render-state-flow-diagram.mjs` | One alpha's ordered states and guarded return loops |

All accept a practice JSON path, an optional element name, `--out <svg>` for a
single figure, or `--all --outdir <directory>` for a set. Their source document
is the editable input; the SVG is generated output. See
`../../references/methods/keleo.md` for the full seven-form selection guide.
