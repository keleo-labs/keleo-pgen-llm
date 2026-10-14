#!/usr/bin/env python3
"""Read and write issues on GitHub and internal GitLab, routed by project.

The feedback register raises issues against five projects across two forges, so
a single client that knows the routing is better than each skill learning `gh`
and `glab` separately.

Two rules are enforced here rather than left to the caller:

Creating an issue on a **public** repository requires the body to pass
`issue-sanitiser.py`. The register is internal and the keleo-labs repositories
are public, and a published issue stays reachable by SHA after deletion, so the
check belongs at the point of no return rather than earlier in a workflow where
it can be skipped. Internal GitLab targets are exempt — they are already behind
the firewall, and stripping detail there would lose information for no gain.

Before creating, the target is searched for a near-duplicate. The register's own
comparator is reused so matching behaves the same in both systems.

Usage:
    python3 utils/forge-issues.py --list --project keleo-language
    python3 utils/forge-issues.py --search "forecast weight" --project keleo-pgen-llm
    python3 utils/forge-issues.py --create --project keleo-pgen-llm \
        --title "..." --body-file draft.md --label component:pgen-llm --dry-run
    python3 utils/forge-issues.py --comment 12 --project keleo-studio --body-file note.md
    python3 utils/forge-issues.py --close 12 --project keleo-studio --body-file note.md
"""
import argparse
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils._shared import get_project_root

SANITISER = Path(__file__).resolve().parent / "issue-sanitiser.py"

# Where each project's issues live, and whether its tracker is world-readable.
# `public` drives the sanitisation requirement, not the forge — an internal
# GitLab project takes full detail.
#
# `practice-content` is the exception that has no tracker at all. The generated
# practices, methods and baselines are not public, so a defect in one is not
# published anywhere — not even in sanitised form, because the existence and
# subject of a practice is itself the thing being withheld. Those rows stay in
# the register and are worked from it.
PROJECTS = {
    "practice-content": {"forge": None, "repo": None, "public": False,
                         "publishable": False,
                         "note": "Practice, method and baseline content is not public. "
                                 "Work these from the register; do not file an issue."},
    "keleo-pgen-llm":   {"forge": "github", "repo": "keleo-labs/keleo-pgen-llm",  "public": True},
    "keleo-language":   {"forge": "github", "repo": "keleo-labs/keleo-language",  "public": True},
    "keleo-studio":     {"forge": "github", "repo": "keleo-labs/keleo-studio",    "public": True},
    "keleo-studio-gas": {"forge": "gitlab", "repo": "planify/keleo-studio-gas",
                         "public": False, "host": "gitlab.cee.redhat.com"},
    "keleo-userskillz": {"forge": "gitlab", "repo": "planify/planify-cursor",
                         "public": False, "host": "gitlab.cee.redhat.com"},
}

DUPLICATE_THRESHOLD = 0.72


def _load_register_module():
    """Import issue-register.py for its comparator (the filename has a hyphen)."""
    path = Path(__file__).resolve().parent / "issue-register.py"
    spec = importlib.util.spec_from_file_location("issue_register", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def resolve_project(name):
    if name not in PROJECTS:
        print(f"Error: unknown project '{name}'. Known: {', '.join(sorted(PROJECTS))}",
              file=sys.stderr)
        sys.exit(2)
    project = PROJECTS[name]
    if project.get("publishable") is False:
        # Refused here rather than at --create, so --list and --search cannot
        # imply a tracker exists for content that is not published at all.
        print(f"Error: '{name}' has no tracker.\n  {project['note']}", file=sys.stderr)
        sys.exit(2)
    return project


_AUTH_CHECKED = {}


def _cli(project):
    """The forge binary for a project, checked for presence and authentication.

    Authentication is checked once per forge and reported plainly, because an
    unauthenticated client otherwise surfaces as a bare 404 from the API, which
    reads like a missing repository rather than a missing login.
    """
    tool = "gh" if project["forge"] == "github" else "glab"
    path = shutil.which(tool)
    if not path:
        print(f"Error: {tool} is not installed; it is required for "
              f"{project['repo']}.\n"
              f"  install with: brew install {tool}", file=sys.stderr)
        sys.exit(2)

    host = project.get("host", "github.com" if tool == "gh" else "gitlab.com")
    if _AUTH_CHECKED.get(host) is None:
        probe = _run([path, "auth", "status"] + (["--hostname", host] if tool == "gh" else []))
        combined = (probe.stdout or "") + (probe.stderr or "")
        _AUTH_CHECKED[host] = probe.returncode == 0 and "not logged" not in combined.lower()
    if not _AUTH_CHECKED[host]:
        hint = (f"gh auth login --hostname {host}" if tool == "gh"
                else f"glab auth login --hostname {host}")
        print(f"Error: {tool} is not authenticated for {host}.\n"
              f"  run: {hint}", file=sys.stderr)
        sys.exit(2)
    return path


def _run(cmd, env=None):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=120, env=env)
    except (OSError, subprocess.SubprocessError) as exc:
        print(f"Error: {' '.join(cmd[:3])} failed: {exc}", file=sys.stderr)
        sys.exit(2)


def list_issues(project, state="open"):
    """Return [{number, title, state, url}] for a project's tracker."""
    cli = _cli(project)
    if project["forge"] == "github":
        out = _run([cli, "issue", "list", "--repo", project["repo"], "--state", state,
                    "--limit", "200", "--json", "number,title,state,url"])
        if out.returncode != 0:
            print(f"Error: {out.stderr.strip()}", file=sys.stderr)
            sys.exit(2)
        return json.loads(out.stdout or "[]")

    out = _run([cli, "issue", "list", "--repo", project["repo"], "--output", "json",
                *(["--all"] if state == "all" else ["--closed"] if state == "closed" else [])])
    if out.returncode != 0:
        print(f"Error: {out.stderr.strip()}", file=sys.stderr)
        sys.exit(2)
    raw = json.loads(out.stdout or "[]")
    return [{"number": i.get("iid"), "title": i.get("title"),
             "state": i.get("state"), "url": i.get("web_url")} for i in raw]


def find_near_duplicate(project, title, threshold=DUPLICATE_THRESHOLD):
    """Closest existing issue by title, or None.

    Searches open *and* closed: a defect filed again after being closed should
    reopen the conversation on the original rather than start a second thread.
    """
    register = _load_register_module()
    existing = list_issues(project, state="all")
    best, best_score = None, 0.0
    for issue in existing:
        score = register.similarity(title, issue.get("title") or "")
        if score > best_score:
            best, best_score = issue, score
    if best and best_score >= threshold:
        return {**best, "similarity": round(best_score, 3)}
    return None


def check_body(body_file):
    """Run the sanitiser over a draft. Returns (ok, report)."""
    out = _run([sys.executable, str(SANITISER), "--check", str(body_file), "--json"])
    try:
        return out.returncode == 0, json.loads(out.stdout)
    except json.JSONDecodeError:
        return False, {"error": out.stderr.strip() or "sanitiser produced no output"}


def create_issue(project, title, body_file, labels, dry_run):
    # The gate sits here, at the point of no return, rather than in a workflow
    # step a caller can skip.
    if project["public"]:
        ok, report = check_body(body_file)
        if not ok:
            print("REFUSED — body is not safe to publish to a public tracker:",
                  file=sys.stderr)
            for f in report.get("blocking", []):
                print(f"  [{f['kind']}] {f['match']}", file=sys.stderr)
            if "error" in report:
                print(f"  {report['error']}", file=sys.stderr)
            sys.exit(1)

    duplicate = find_near_duplicate(project, title)
    if duplicate:
        print(json.dumps({
            "action": "duplicate",
            "message": "a near-duplicate exists; comment on it instead of filing again",
            "match": duplicate,
        }, indent=2))
        return 3

    if dry_run:
        print(json.dumps({
            "action": "would-create", "repo": project["repo"], "title": title,
            "labels": labels, "sanitised": project["public"],
        }, indent=2))
        return 0

    cli = _cli(project)
    cmd = [cli, "issue", "create", "--repo", project["repo"],
           "--title", title, "--body-file", str(body_file)]
    for label in labels or []:
        cmd += ["--label", label]
    out = _run(cmd)
    if out.returncode != 0:
        print(f"Error: {out.stderr.strip()}", file=sys.stderr)
        sys.exit(2)
    print(json.dumps({"action": "created", "url": out.stdout.strip()}, indent=2))
    return 0


def comment_issue(project, number, body_file, dry_run):
    if project["public"]:
        ok, report = check_body(body_file)
        if not ok:
            print("REFUSED — comment is not safe to publish:", file=sys.stderr)
            for f in report.get("blocking", []):
                print(f"  [{f['kind']}] {f['match']}", file=sys.stderr)
            sys.exit(1)
    if dry_run:
        print(json.dumps({"action": "would-comment", "repo": project["repo"],
                          "issue": number}, indent=2))
        return 0
    cli = _cli(project)
    out = _run([cli, "issue", "comment", str(number), "--repo", project["repo"],
                "--body-file", str(body_file)])
    if out.returncode != 0:
        print(f"Error: {out.stderr.strip()}", file=sys.stderr)
        sys.exit(2)
    print(json.dumps({"action": "commented", "issue": number}, indent=2))
    return 0


def close_issue(project, number, body_file, dry_run):
    if body_file:
        rc = comment_issue(project, number, body_file, dry_run)
        if rc:
            return rc
    if dry_run:
        print(json.dumps({"action": "would-close", "repo": project["repo"],
                          "issue": number}, indent=2))
        return 0
    cli = _cli(project)
    out = _run([cli, "issue", "close", str(number), "--repo", project["repo"]])
    if out.returncode != 0:
        print(f"Error: {out.stderr.strip()}", file=sys.stderr)
        sys.exit(2)
    print(json.dumps({"action": "closed", "issue": number}, indent=2))
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Read and write issues on GitHub and internal GitLab",
        formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    parser.add_argument("--project", required=True, choices=sorted(PROJECTS),
                        help="Owning project; determines forge, repo and whether "
                             "the tracker is public")
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--list", action="store_true", help="List issues")
    action.add_argument("--search", metavar="TITLE",
                        help="Report the closest existing issue by title")
    action.add_argument("--create", action="store_true", help="Create an issue")
    action.add_argument("--comment", metavar="NUMBER", help="Comment on an issue")
    action.add_argument("--close", metavar="NUMBER", help="Close an issue")
    action.add_argument("--routing", action="store_true",
                        help="Print the routing table and exit")
    parser.add_argument("--title")
    parser.add_argument("--body-file")
    parser.add_argument("--label", action="append", default=[])
    parser.add_argument("--state", default="open", choices=["open", "closed", "all"])
    parser.add_argument("--dry-run", action="store_true",
                        help="Report what would happen without writing")
    args = parser.parse_args()

    if args.routing:
        print(json.dumps(PROJECTS, indent=2))
        return 0

    project = resolve_project(args.project)

    if args.list:
        print(json.dumps(list_issues(project, args.state), indent=2))
        return 0

    if args.search:
        match = find_near_duplicate(project, args.search)
        print(json.dumps({"query": args.search, "match": match}, indent=2))
        return 0

    if args.create:
        if not args.title or not args.body_file:
            print("Error: --create needs --title and --body-file", file=sys.stderr)
            return 2
        return create_issue(project, args.title, args.body_file, args.label, args.dry_run)

    if args.comment:
        if not args.body_file:
            print("Error: --comment needs --body-file", file=sys.stderr)
            return 2
        return comment_issue(project, args.comment, args.body_file, args.dry_run)

    if args.close:
        return close_issue(project, args.close, args.body_file, args.dry_run)

    return 0


if __name__ == "__main__":
    sys.exit(main())
