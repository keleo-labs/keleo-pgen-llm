---
name: add-agent-vendor
description: Add another LLM agent or CLI to this repository's shared-skill architecture. Use when asked to support a new vendor, agent, or model runtime.
metadata:
  version: "1.0.0"
---

# Add an agent vendor

The canonical workflows and foundations live in `skills/`; shared project guidance lives in `AGENTS-ALL.md`. Agent entrypoints and hooks are adapters only. Read `config/agent-vendors.json`, `utils/vendor-skills.py`, and the current hook integration before changing anything.

1. Check the new agent's current primary documentation for its project instruction file, skill discovery paths, hook events, payload fields, and whether it also discovers existing vendor directories. Record the documented capabilities and gaps in the README.
2. Add one vendor record to `config/agent-vendors.json`. If the agent discovers `.agents/skills`, use that shared entrypoint and leave `skillsDir` null; otherwise choose its native skill directory. Avoid duplicate discoverable skills where the agent scans multiple vendor directories.
3. Create a thin project instruction entrypoint that directs the agent to `AGENTS-ALL.md`. Run `python3 utils/vendor-skills.py --fix` to scaffold skill wrappers for any new `skillsDir`. Store per-skill tool mappings in `adapter.md` beside its wrapper, then regenerate; generated entrypoints load these additions without overwriting them.
4. Add project hook configuration for equivalent prompt-history events. If the event payload differs, extend `utils/prompt-history.py` at its input boundary; preserve session isolation and duplicate-event handling. If the agent has no compatible event, document the manual `--add-interaction` path.
5. Add fixture-based hook tests, check wrapper parity with `python3 utils/vendor-skills.py --check`, and smoke-test skill discovery and hooks in the agent when its CLI is available. Update the README and version any changed contracts.

A new vendor must not become the source of truth for a shared skill or utility. Ask for missing product intent only after the agent's documented capabilities have been checked.
