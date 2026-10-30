---
name: update-method
version: 1.2.1
description: Update existing Practice/Method JSON files to align with latest generate-method guidance and baseline practice
triggerPatterns:
  - "update.*method"
  - "update.*practice"
  - "refresh.*method"
  - "refresh.*practice"
  - "rework.*method"
  - "rework.*practice"
  - "add.*reference"
  - "find.*reference"
  - "update.*reference"
---

# update-method agent entrypoint

Read and follow `skills/update-method/SKILL.md`. Resolve its relative references from that canonical skill directory.

For Claude Code, use AskUserQuestion for structured user choices, the available web and browser tools for sources, and the Task tool when the canonical workflow calls for subagents.
