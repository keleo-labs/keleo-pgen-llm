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

# export-notebook-sources agent entrypoint

Read and follow `skills/export-notebook-sources/SKILL.md`. Resolve its relative references from that canonical skill directory.

For Claude Code, use AskUserQuestion for structured user choices, the available web and browser tools for sources, and the Task tool when the canonical workflow calls for subagents.
