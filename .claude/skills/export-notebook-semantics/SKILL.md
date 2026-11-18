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

# export-notebook-semantics agent entrypoint

Read and follow `skills/export-notebook-semantics/SKILL.md`. Resolve its relative references from that canonical skill directory.

For Claude Code, use AskUserQuestion for structured user choices, the available web and browser tools for sources, and the Task tool when the canonical workflow calls for subagents.
