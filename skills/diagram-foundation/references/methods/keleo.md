# Keleo practice diagrams

Version: 1.2.0

Use the practice JSON as the source of truth. These forms follow the Keleo
Studio navigator's diagram semantics. The three static renderers below are copied
from `keleo-studio-gas/utils/` with their shared text helper; the four native
views use this repository's existing spec and SVG pipeline. Keep the source
JSON available so the figure can be regenerated.

| Diagram | Practice relation | Command route |
|---|---|---|
| Practice dependency | `baselinePracticeNames`, `practiceDependencyNames`, or `practiceNames` | `derive-diagram.py --view practice-dependency` |
| Orchestration | `patternOrchestrations[].stages` and their relative placement | `node skills/diagram-foundation/scripts/keleo/render-orchestration-diagram.mjs` |
| Practice pattern | `patterns[].patternViews`, their alpha state targets, narrative contexts and return loops | `node skills/diagram-foundation/scripts/keleo/render-pattern-matrix.mjs` |
| Alpha (concern) overview | Alphas grouped by `focusName`, with `contributesTo` and `mapsTo` edges | `derive-diagram.py --view concern-overview` |
| Activity overview | `activitySpaces` grouped by focus, with nested `activities` | `derive-diagram.py --view activity-overview` |
| Alpha state | Ordered `states` and guarded `loopsBackTo` returns | `node skills/diagram-foundation/scripts/keleo/render-state-flow-diagram.mjs` |
| Alpha relationship | One alpha's directed `relatesTo` neighbourhood | `derive-diagram.py --view alpha-relationship --seed "<Alpha>"` |

The four derived views emit native JSON specs. Use `--out-dir <assets> --name
<stem>`, then `python3 utils/render-diagram.py --dir <assets>`. Scope large
overviews with `--focus` or raise `--max-nodes` only when the rendered figure
remains readable. A dependency view follows direct declarations and any
transitive documents supplied with repeated `--dependency-doc <practice.json>`;
unavailable documents stay as named leaf nodes. An activity space
without nested activities is still shown as a space, as Studio does.

The copied renderers read one practice document and write SVG directly. For a
self-contained report, copy that document into `assets/source/` first and use
the copied path in the command:

```bash
node skills/diagram-foundation/scripts/keleo/render-orchestration-diagram.mjs assets/source/practice.json "Orchestration name" --out assets/orchestration.svg
node skills/diagram-foundation/scripts/keleo/render-pattern-matrix.mjs assets/source/practice.json "Pattern name" --out assets/pattern.svg
node skills/diagram-foundation/scripts/keleo/render-state-flow-diagram.mjs assets/source/practice.json "Alpha name" --out assets/alpha-state.svg
```

If a pattern's `narrativeTypeName` comes from a baseline, render from an
effective context containing that narrative type. Rendering only the leaf
practice omits the narrative band and reports the missing type.

Omit the name to render the first matching element. `--all --outdir <assets>`
renders every matching element. Preserve warnings about unresolved stages,
pattern narrative types or state loop targets; they identify omitted context or edges. These SVGs retain Studio's
visual palette and cannot become native editable Slides shapes. For report or
slide use, inspect the image at final display width and add alt text and a
caption. A state loop must remain visible; a generic maturity stack is only
suitable when the alpha has no `loopsBackTo`. A wide orchestration needs a
landscape page, appendix or separate focused figures; shrinking it into a
standard report column makes its stage labels unreadable.
A wide practice pattern has the same limit. Keep its full SVG and, for a
portrait report, render consecutive phase excerpts as separate panels. Label
each with `--title "Pattern name — Part N"`; `--note-offset N` continues note
numbering. Preserve the `loopsBackTo` declaration in the later excerpt and use
`--external-loop-part "Part 1"` so its guarded arrow visibly points back to
the named phase in the earlier panel. The caption can explain the link, but
must not stand in for the return path.
