---
name: decision-analysis
metadata:
  version: "1.1.1"
description: Structured trade-off analysis for architectural, strategic, or technical decisions — balanced options evaluation with contextual verdicts
triggerPatterns:
  - "analyze.*question"
  - "decision.*analysis"
  - "trade.*off"
  - "weigh.*options"
  - "compare.*approaches"
  - "should.*we"
  - "which.*approach"
  - "pros.*cons"
---

# decision-analysis agent entrypoint

Read and follow `skills/decision-analysis/SKILL.md`. Resolve its relative references from that canonical skill directory.

For Claude Code, use AskUserQuestion for structured user choices, the available web and browser tools for sources, and the Task tool when the canonical workflow calls for subagents.
