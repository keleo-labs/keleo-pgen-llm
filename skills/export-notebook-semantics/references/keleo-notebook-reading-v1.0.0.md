# Read Keleo notebook exports

Companion guide 1.0.0 · Keleo notebook exporter 1.0.0 · Practice Language schema 5.1.0

Use this guide to interpret exported practice, baseline and method files. The practice and method files supply the facts about the methodology. This guide explains how to find and qualify those facts.

## Start with the question and the document

Identify the method or practice, its version and the element in question. Where an element is nested, name its parent. For example, look for the state `Reviewed` under the alpha `Access Risk`, or the level `Reviewed` under the work product `Access Review Record`. These two uses of the same label describe different things.

- **What did a document author declare?** Use **Authored content** in the named document. It preserves the authored fields, including fields later changed or omitted in composition.
- **What does this practice show after inheritance?** Start with **Authored content** and apply **Studio practice view**. Each field shown there replaces the corresponding authored field for this view. Fields listed as omitted are outside the composed view. Other authored fields retain their values. Read **Dependencies and gaps** before treating the view as complete.
- **What spans several practices?** Start with **Method members** and the method's authored guidance or bindings. Follow the named member files for their own elements. Each member's Studio practice view is local to that practice. The method file contains method-level material. Member order alone establishes neither delivery order nor a prerequisite.
- **What has a team achieved?** Look for an actual project assessment and its evidence. Practice criteria, expected states, examples and outcome definitions describe what to assess. A recorded result needs its own source.

## Follow a reference and check its source

The export preserves exact field names such as `alphaName`, `stateName` and `levelOfDetailName`. A nearby **Reference context** excerpt repeats material from the named target. Follow the target's document and section for the full record. Use the plain-text names if your notebook cannot follow the Markdown link. Cite the document and section that support the claim, and name the contributing practice or baseline when the export identifies it.

Use the canonical name for structural references. A declared alias is a presentation label within its stated scope. Preserve the exact spelling, case and parent element when following a name.

A **Studio-synthesised placeholder** records a name that needed a target during composition. Use the name to explain what is missing, and cite a definition or criterion only when a source supplies it. If the export shows an ambiguous reference, keep its candidate meanings separate until a source identifies the intended target.

## Handle missing context

**Dependencies and gaps** can identify a missing document, a version mismatch or a cycle. A dependency marked **absent from this export** can still have contributed excerpts to the Studio view. Add its standalone source when a question needs its complete definition or other content beyond the excerpts. Report that a claim is unresolved in the available sources when you cannot verify the target.

**External sources and assets** lists cited materials and where the export mentions them. Treat a link, title or asset path as a reference. For a question about the contents of the linked file, use that file as a source if it is available.

## Example answer

In this fictional example, the reader asks “Has Access Risk reached Reviewed?”

“Access Review v1.2, Alphas / Access Risk / Reviewed, requires a review record that names the decision and reviewer. The available source is methodology guidance. Actual completion would need the project's current assessment and the cited review record.”

This guide draws on the Keleo notebook exporter 1.0.0 renderer (`utils/notebook_markdown.py`) and Keleo Language revision `35f3eefc3756783d0b66c4324e0972ee089e3439` (Merge §10 and Semantics §§4.3, 12.4–12.5 and 16.2).
