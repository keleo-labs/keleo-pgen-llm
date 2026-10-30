---
name: document-review
metadata:
  version: "1.1.1"
description: Review a provided document against practice domain knowledge — what's strong, what could be improved, what isn't needed
triggerPatterns:
  - "review.*document"
  - "review.*deck"
  - "review.*presentation"
  - "assess.*document"
  - "improve.*document"
  - "critique.*document"
  - "gap.*analysis"
  - "deck.*review"
---

# document-review agent entrypoint

Read and follow `skills/document-review/SKILL.md`. Resolve its relative references from that canonical skill directory.

For Claude Code, use AskUserQuestion for structured user choices, the available web and browser tools for sources, and the Task tool when the canonical workflow calls for subagents.
