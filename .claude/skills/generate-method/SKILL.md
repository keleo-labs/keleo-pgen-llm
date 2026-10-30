---
name: generate-method
version: 1.4.1
metadata:
  version: "1.4.1"
description: Generate Practice Language JSON from methodology documentation using clean 3-phase workflow (Analysis → Mapping → JSON)
triggerPatterns:
  - "generate.*method"
  - "generate.*practice"
  - "create.*method"
  - "analyze.*methodology"
  - "map.*methodology"
---

# generate-method agent entrypoint

Read and follow `skills/generate-method/SKILL.md`. Resolve its relative references from that canonical skill directory.

For Claude Code, use AskUserQuestion for structured user choices, the available web and browser tools for sources, and the Task tool when the canonical workflow calls for subagents.
