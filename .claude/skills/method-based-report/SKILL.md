---
name: method-based-report
metadata:
  version: "1.1.1"
description: Generate plain English reports structured by practice/method narrative frameworks — audience sees domain insight, not Keleo internals
triggerPatterns:
  - "method.*report"
  - "practice.*report"
  - "report.*using"
  - "write.*report"
  - "generate.*report"
---

# method-based-report agent entrypoint

Read and follow `skills/method-based-report/SKILL.md`. Resolve its relative references from that canonical skill directory.

For Claude Code, use AskUserQuestion for structured user choices, the available web and browser tools for sources, and the Task tool when the canonical workflow calls for subagents.
