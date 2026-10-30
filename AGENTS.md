# Codex and shared agent instructions

Read [AGENTS-ALL.md](AGENTS-ALL.md) before working in this repository. It is the source of truth for project architecture, coding standards, validation and skill workflows.

Codex discovers project skill entrypoints in `.agents/skills/`. Each entrypoint loads the canonical skill in `skills/`. Project hook settings are in `.codex/hooks.json`; user configuration belongs in the ignored `config/user-config.json`.
