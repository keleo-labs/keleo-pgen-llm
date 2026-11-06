---
name: content-repos
description: Create and manage separate git repositories for selected Keleo practices, baselines, and reports. Use when asked to set up a content repo, import or mount an item, inspect ownership and status, or detach an item from this project.
metadata:
  version: "1.1.0"
---

## Content repositories

Use `utils/content-repos.py` for item operations and `docs/content-repos.md` for the layout and configuration format. The behavioral contract is [contract.feature](contract.feature). Keep canonical skills and utilities in this code repository; content repos hold authored workspaces. Preserve unrelated local content and git changes.

## Establish ownership

Identify the exact practice, baseline, or report directories the user wants to version and the repository that should own each one. Inspect `config/content-repos.json`, the candidate paths, `git -C <repo> status --short`, and any existing remote before changing them. If a repo or item is unnamed and cannot be inferred, ask only for that choice; do not assign existing private reports to a repo by guesswork.

For a new local repository, create it outside this project's git tree with `git init`. Copy `docs/content-repo.gitignore` to its root and add an entry to the ignored, versioned `config/content-repos.json`, starting from `config/content-repos.example.json` if needed. For an existing repository, register its path and only the requested items. Keep every unselected item out of the configuration.

During setup, write a root `README.md` that briefly explains how Keleo models practices, methods, baselines and projects in machine-readable form; identifies this repository's authored content; and links to [keleo-language](https://github.com/keleo-labs/keleo-language) for the schema and semantics and [keleo-pgen-llm](https://github.com/keleo-labs/keleo-pgen-llm) for generation and reporting tools. Add any missing context to an existing README without replacing its description. A local repository has no remote by default; if the user requests a hosted repository, use the available git remote workflow and verify that its visibility is private before uploading content.

## Mount or import

Use the utility's dry run before `--fix`:

```bash
python3 utils/content-repos.py mount
python3 utils/content-repos.py mount --fix
python3 utils/content-repos.py add <repo> <practices|baselines|reports> <slug>
python3 utils/content-repos.py add <repo> <practices|baselines|reports> <slug> --fix
python3 utils/content-repos.py check
```

Register an item already in a content repo, then mount it. Use `add` for a new item or to import a local directory into a repository where that item does not yet exist. The import keeps a verified original under `content-import-backups/`. If both sides already hold content, inspect and reconcile them explicitly; never replace either directory. `check` must pass before calling the item ready.

## Manage existing content

Read `config/content-repos.json` to identify an item's owner, then inspect changes with `git -C <repo-path> status --short` and `git -C <repo-path> diff`. Review authored files and ignored outputs before staging or committing. Commit locally when the user's request includes versioning the completed content; do not push or create a remote unless requested. Follow the repository's normal git safety workflow for remote actions.

To detach an item, preview and apply `python3 utils/content-repos.py unmount <kind> <slug> --fix`, then check that the repository directory still exists. Unmount removes the project link and its selection, not the content or its git history. Report the owner, selected paths, mount state, local backup location after an import, and any pending git changes.
