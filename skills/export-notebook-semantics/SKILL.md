---
name: export-notebook-semantics
description: Create Markdown guides that help Gemini Notebook, NotebookLM and other LLM question-answering systems interpret Keleo practice, baseline and method exports. Use for companion notebook sources, a Practice Language glossary or guidance on answering from Keleo Markdown.
metadata:
  version: "1.0.0"
triggerPatterns:
  - "notebook.*semantics"
  - "semantics.*notebook"
  - "keleo.*notebook.*companion"
---

# Export notebook semantics

Use [the guide sources](references/guide-sources.md) to create three standalone Markdown files for manual import alongside the files from `export-notebook-sources`. The user can request the guides independently of any practice export. Read the project's `skills/writing-style/SKILL.md` before adapting prose.

For a general request, copy the three versioned Markdown guides listed in the source map. Use the destination the user gives. If the user refers to an existing export and its directory is clear, place the guides beside it. Otherwise use a new directory under `bundles/notebook-sources/`. Check all three destination names before copying. Keep identical copies and report where they are. If existing content differs, place the new guide set in a fresh subdirectory.

For an explicitly requested Practice Language revision or custom export layout, use the guides as a starting point and reconcile the affected sections against the requested sources. Verify the language revision and schema version from that revision, and the Markdown section names against the export. Update the source notes and use separate filenames for the adaptation. If a requested revision is unavailable, identify the gap before delivering any version-specific claims.

Keep each guide understandable by itself. Preserve language terms, field names and relationship direction. Explain how to qualify a target by document and parent element, distinguish a requirement from a recorded result, and handle missing evidence or context. Label examples as fictional. Check that the finished files cover the source map's tests and that their content works without opening links. Return local file links for manual import.
