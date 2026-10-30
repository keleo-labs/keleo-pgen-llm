---
name: plan-from-feedback
description: Publish register issues to project trackers, then resolve keleo-pgen-llm issues — skills, prompts and utilities from the public tracker, practice content from the register
metadata:
  version: "1.0.0"
triggerPatterns:
  - "plan.*feedback"
  - "feedback.*plan"
  - "issue.*register"
  - "triage.*issues"
  - "process.*feedback"
  - "publish.*issues"
---

# plan-from-feedback agent entrypoint

Read and follow `skills/plan-from-feedback/SKILL.md`. Resolve its relative references from that canonical skill directory.

For Claude Code, use AskUserQuestion for structured user choices, the available web and browser tools for sources, and the Task tool when the canonical workflow calls for subagents.
