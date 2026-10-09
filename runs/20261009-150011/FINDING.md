# Run 20261009-150011 — superseded

**Do not quote these numbers.** The run measured the harness, not the skill.

`/generate-method` opens with a mandatory plan-mode gate and will stop to ask a
clarifying question. Headless there is nobody to answer. The with-skill cell
created its workspace and effective context, wrote `00-prompt-history.md` with

```
**Answered:**

> <pending>
```

and halted after 40 turns, 14,676 tokens, 252s, $2.47 — producing no analysis
report, no mapping guide and no JSON. It therefore scored `pass_rate: 0.0` on
three file-existence assertions.

The without-skill cell had no such gate. It ran 106 turns, 331,215 tokens,
3,411s and $28.59, followed the phase prompts in `prompts/` unaided, and
produced a complete practice scoring `pass_rate: 1.0` on 284 assertions.

So the headline `mean_pass_rate` delta of **-1.0** says the skill is worse than
no skill. It says nothing of the kind. It says a skill with an interactive gate
cannot complete in a non-interactive harness.

## What changed afterwards

1. Both arms now get a `--append-system-prompt` preamble stating the session is
   non-interactive: no plan mode, no questions, record the assumption and carry
   on. Applied to both arms, so it cannot bias the comparison.
2. `prompts/` in the cell is now an explicit choice. Including it — the default
   — makes the comparison "what the skill's orchestration adds over the phase
   prompts it already ships". `--no-prompts` measures the harder question. The
   first run included them without saying so, which is why the without-skill arm
   could follow the pipeline at all.

## What the run does establish

- The isolation held: both cells passed the contamination check before running.
- Cells build, run, are kept, and grade. `--rescore` re-reads them for free.
- Metric capture off the CLI JSON works: turns, tokens, duration, cost.
- A real cost baseline for this case: roughly $31 and 61 minutes for two cells,
  the without-skill arm accounting for 92% of both.

A re-run under the fixed harness is needed before any delta is reported.
