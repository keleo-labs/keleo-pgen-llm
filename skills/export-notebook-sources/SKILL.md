---
name: export-notebook-sources
description: Export Keleo practices, baselines or methods as Markdown sources for Gemini Notebook, NotebookLM and other LLM question-answering systems. Use for a single document, a method or a list of practices.
metadata:
  version: "1.0.0"
triggerPatterns:
  - "export.*notebook"
  - "practice.*notebook"
  - "method.*notebook"
---

# Export notebook sources

Use the repository exporter to preserve authored fields and attach Studio GAS context. Ask for a document name or local path when the request does not identify any source. For local input, use the supplied JSON or `.keleo` files. For published names, read [published-bundles.md](references/published-bundles.md).

Run from the repository root. Use a new output directory under `bundles/notebook-sources/` when the user gives no destination.

```bash
python3 utils/export-notebook-sources.py selected.keleo \
  --dependency supporting.keleo --output-dir bundles/notebook-sources/example
```

Use positional inputs only for the documents the user selects. For a method, pass the method as the sole positional input and supply separate member JSON, baselines and other related files via `--dependency`. The exporter creates the declared member files automatically. For a practice list, pass each selected practice as a positional input.

Pass `archive.keleo::documents/name.json` to select an exact archive member. Supply `--studio-gas-dir` when the trusted Studio GAS checkout is outside the default sibling directory. The exporter uses Node.js to run that checkout's merge harness and npm to check declared version ranges.

Add supporting inputs with `--dependency` so their Studio-selected context is available without adding full files to the export. To produce an independent Markdown file for a dependency, pass the dependency as a positional input. Review **Dependencies and gaps** in the result. Retry with available exact dependencies when there is a gap. If a supporting dependency remains unavailable, return the authored export and name the gap. A requested document or method member must be present.

Return links to the generated files, identify the method and member files and call out unresolved dependencies. The user can upload the `.md` files directly. Cite external references as separate optional sources.
