# Claude Code instructions

Read [AGENTS-ALL.md](AGENTS-ALL.md) before working in this repository. It is the source of truth for project architecture, coding standards, validation and skill workflows.

Claude Code discovers project skill entrypoints in `.claude/skills/`. Each entrypoint loads the canonical skill in `skills/`. Project hook settings are in `.claude/settings.json`; keep local permissions and credentials in ignored files.
