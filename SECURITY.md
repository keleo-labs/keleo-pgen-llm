# Security

## This repository is public

`keleo-labs/keleo-pgen-llm` is a public repository on GitHub. Everything
committed here is world-readable the moment it is pushed, and remains readable
by commit SHA after any later deletion. That single fact sets the standard for
everything below, and it is stricter than the one most internal repositories
work to.

The repository holds tooling, prompts, reference documentation and skills. It
deliberately holds no generated content: `practices/`, `baselines/`,
`bundles/`, `reports/` and `scratch/` are excluded, and only their `.gitkeep`
files are tracked. Methodology output routinely contains customer and partner
material, so keeping it out of the tree is the control that matters most.

## What must never be committed

Credentials of any kind — API tokens, OAuth access or refresh tokens, session
cookies, JWTs, private keys. Customer or partner data, including a single
email address in an example. Red Hat internal material that has not been
published: unreleased product detail, account plans, pricing, internal
presentations. Personal home paths such as `/Users/<name>/`, machine
hostnames, and personal email addresses.

Public Red Hat documentation is fine. The distinction is publication, not
subject matter.

## Where credentials live

`.claude/user-config.json` holds the bundle repository deployment URL and its
bearer token, along with the issue register URL and reporter email. It is
gitignored and must stay that way. `utils/studio-client.py --configure` writes
it; nothing else should.

A credential written anywhere inside the tracked tree is one `git add` away
from a public commit. If you add tooling that authenticates, write its state
to `.claude/user-config.json` or to `~/.config/`, and commit an example with
empty values rather than the real file.

## Four layers, each catching what the one before cannot

**Keep it out of the working tree.** `scratch/` is ignored wholesale — page
snapshots, extracted documents, API dumps, anything downloaded while
investigating. A file that cannot be staged needs no scanner, and `git add -A`
cannot sweep up what is ignored. This is prevention rather than detection, so
it is the layer that matters most.

**gitleaks at commit.** The default rule set — GitHub, Slack, AWS, Google,
JWT, private keys — extended with rules the defaults structurally cannot
cover: email addresses, absolute home paths, the bundle repository bearer
token, Apps Script deployment URLs, and Google file IDs that name an internal
document even when its contents are elsewhere.

**trufflehog at pre-push.** Its `--only-verified` mode calls the provider's
API to find out whether a credential is still live, which gitleaks cannot do.
Too slow for every commit, exactly right before anything leaves the machine.

**GitHub Actions over full history.** `fetch-depth: 0` is what makes it full
history rather than the same scope as the hook. This is the layer that catches
anything committed before the hooks existed, or pushed from a clone where
nobody installed them.

## Installing the hooks

CI configuration does nothing until it runs, and hooks are per-clone. Anyone
working on this repository installs them:

```bash
pre-commit install --hook-type pre-commit --hook-type pre-push
```

Check a branch before pushing:

```bash
python3 ~/.claude/skills/git-guardrails/scripts/guardrails.py --check
```

## Accepted findings in history

`.gitleaksignore` lists seven findings from commits predating these controls —
six absolute home paths and one Apps Script deployment URL. None is a
credential and none survives at HEAD. History was left intact deliberately:
the exposure is a username and a directory layout, and a force-push on a
public repository breaks every clone and fork for little return.

Each entry carries a comment saying what it is. Add one only the same way.

## If something leaks anyway

Rotate first, then clean history. The order matters: a secret pushed to a
public repository should be assumed read, so removing the commit is
housekeeping rather than remediation.

1. Rotate or revoke the credential at the provider. For a session cookie,
   signing out of the application is the rotation.
2. Tell anyone who has cloned or forked.
3. Only then consider rewriting history, knowing GitHub keeps unreferenced
   objects reachable by SHA for some time regardless.
4. Add a rule to `.gitleaks.toml` so the same shape is caught next time, and
   say in the commit message what it is for.

## False positives

Retire a false positive with an allowlist entry in `.gitleaks.toml`, never an
inline ignore comment and never `--no-verify`. An allowlist entry is
reviewable in the diff and carries a comment explaining itself; a bypass
leaves no trace. Prefer the narrowest form: a `regexes` entry scoped to one
rule before a `paths` entry that exempts a whole file.
