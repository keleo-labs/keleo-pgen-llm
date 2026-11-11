## Keep authored content in separate git repositories

The code repository supplies the skills and utilities. A content repository owns the practice, baseline, and report directories you choose to put under git. You can use several private repositories and expose only selected directories from each one. The project paths remain `practices/<slug>/`, `baselines/<slug>/`, and `reports/<slug>/`.

Invoke `/content-repos` for guided setup, import, status, and unmounting. The commands below also work directly.

Create each content repository beside this checkout with ordinary `git init` or clone an existing one. Use the same three top-level directories as this project. Keep authored JSON, analysis and mapping documents, prompt history, report Markdown, and source diagram assets. Copy the supplied `docs/content-repo.gitignore` into each content repo; its contents are:

```gitignore
.DS_Store
**/backup-*/
**/_*
**/lint*.json
**/*practice-catalog.json
**/.published-docs.json
*.pdf
*.keleo
```

Add a root `README.md` that explains how Keleo models practices, methods, baselines and projects in machine-readable form and says what authored content this repository holds. Link to [keleo-language](https://github.com/keleo-labs/keleo-language) for the schema and semantics and [keleo-pgen-llm](https://github.com/keleo-labs/keleo-pgen-llm) for the generation and reporting tools. In an existing repository, keep its description and add only the missing context.

Keep publication state and generated exports locally. Review `git status` before adding files: report workspaces can contain private evidence, and the repository's membership determines who can read what you commit.

### Configure a checkout

Copy `config/content-repos.example.json` to the ignored `config/content-repos.json` and adjust the repo paths and selected items. The example assigns Platform Adoption Essentials to the core repo and the Red Hat Sales Essentials tree, including Partner Ecosystem Essentials, to the sales repo. Paths are relative to this project root, and every selected slug has one owner. An unselected directory in a content repo remains invisible to the project.

Run `python3 utils/content-repos.py mount` to preview the links, then add `--fix` to create them. `check` exits with an error if a selected directory is missing or its link is absent or occupied. The tool rejects a content repository inside this code repository.

### Add or import an item

Choose the owning repo before a generation or reporting skill creates its workspace. `add` prepares the directory and link. If the item already exists locally, it copies and verifies the complete directory in the content repo, keeps the original under `content-import-backups/`, and then creates the link.

```bash
python3 utils/content-repos.py add core practices example-practice
python3 utils/content-repos.py add core practices example-practice --fix
python3 utils/content-repos.py check
git -C ../keleo-content-core status --short
```

The command never stages, commits, pushes, or creates a remote. Review and commit in the owning content repo when you are ready. To stop exposing an item without deleting it, run `python3 utils/content-repos.py unmount practices example-practice --fix`.

The `deps/platform-adoption-kernel.json` compatibility link resolves only when you mount or create its local baseline. Project skills use Studio MCP for published baselines without a mount. The older Partner Ecosystem baseline formerly under `deps/` has been retired; Studio MCP supplies its published version, while a mounted local copy remains optional.
