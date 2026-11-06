#!/usr/bin/env python3
"""Mount selected directories from independent git repositories into this project."""

import argparse
import filecmp
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


__version__ = "1.0.0"
ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/content-repos.json"
KINDS = ("practices", "baselines", "reports")
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")


def inside(path, parent):
    return path == parent or parent in path.parents


def load_config():
    if not CONFIG.is_file():
        raise ValueError(f"Missing {CONFIG}; see docs/content-repos.md")
    data = json.loads(CONFIG.read_text(encoding="utf-8"))
    if set(data) != {"version", "repositories"} or data["version"] != "1.0.0":
        raise ValueError("content-repos config must use version 1.0.0")
    if not isinstance(data["repositories"], list):
        raise ValueError("repositories must be a list")
    owners, names = {}, set()
    for repo in data["repositories"]:
        if set(repo) != {"name", "path", "items"} or not isinstance(repo["name"], str):
            raise ValueError("Each repository needs name, path, and items")
        if repo["name"] in names or not SLUG.fullmatch(repo["name"]):
            raise ValueError(f"Invalid or duplicate repository name: {repo['name']}")
        names.add(repo["name"])
        if not isinstance(repo["path"], str) or not repo["path"]:
            raise ValueError(f"Invalid path for {repo['name']}")
        path = (ROOT / repo["path"]).expanduser().resolve()
        if inside(path, ROOT):
            raise ValueError(f"Repository must be outside this project: {path}")
        if not path.is_dir():
            raise ValueError(f"Missing repository: {path}")
        result = subprocess.run(["git", "-C", str(path), "rev-parse", "--show-toplevel"],
                                capture_output=True, text=True)
        if result.returncode or Path(result.stdout.strip()).resolve() != path:
            raise ValueError(f"Not a git repository root: {path}")
        repo["resolved_path"] = path
        items = repo["items"]
        if not isinstance(items, dict) or set(items) != set(KINDS):
            raise ValueError(f"{repo['name']} needs practices, baselines, and reports lists")
        for kind, slugs in items.items():
            if not isinstance(slugs, list):
                raise ValueError(f"{repo['name']}.{kind} must be a list")
            for slug in slugs:
                if not isinstance(slug, str) or not SLUG.fullmatch(slug):
                    raise ValueError(f"Invalid {kind} item name: {slug}")
                key = (kind, slug)
                if key in owners:
                    raise ValueError(f"Duplicate owner for {kind}/{slug}: {owners[key]} and {repo['name']}")
                owners[key] = repo["name"]
    return data


def save_config(data):
    clean = {"version": data["version"], "repositories": [
        {key: repo[key] for key in ("name", "path", "items")}
        for repo in data["repositories"]]}
    temporary = CONFIG.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(clean, indent=2) + "\n", encoding="utf-8")
    temporary.replace(CONFIG)


def same_tree(left, right):
    """Compare copied content, including link targets; never follow imported links."""
    if left.is_symlink() or right.is_symlink():
        return left.is_symlink() and right.is_symlink() and left.readlink() == right.readlink()
    if left.is_file() or right.is_file():
        return left.is_file() and right.is_file() and filecmp.cmp(left, right, shallow=False)
    if not left.is_dir() or not right.is_dir():
        return False
    left_names = {p.name for p in left.iterdir()}
    return left_names == {p.name for p in right.iterdir()} and all(
        same_tree(left / name, right / name) for name in left_names)


def entries(data):
    for repo in data["repositories"]:
        for kind in KINDS:
            for slug in repo["items"][kind]:
                yield repo, kind, slug, ROOT / kind / slug, repo["resolved_path"] / kind / slug


def mount(data, fix, check=False):
    problems = []
    for repo, kind, slug, link, target in entries(data):
        label = f"{kind}/{slug} ({repo['name']})"
        if not target.is_dir():
            problems.append(f"Missing content directory: {target}")
        elif not inside(target.resolve(), repo["resolved_path"]):
            problems.append(f"Content directory escapes repository: {target}")
        elif link.is_symlink() and link.resolve() == target.resolve():
            print(f"mounted {label}")
        elif link.exists() or link.is_symlink():
            problems.append(f"Path occupied; import or resolve manually: {link}")
        elif check:
            problems.append(f"Not mounted: {link}")
        elif fix:
            link.symlink_to(target, target_is_directory=True)
            print(f"mounted {label}")
        else:
            print(f"would mount {label}")
    if problems:
        raise ValueError("\n".join(problems))


def add(data, repo_name, kind, slug, fix):
    if kind not in KINDS or not SLUG.fullmatch(slug):
        raise ValueError("Use practices, baselines, or reports and a kebab-case item name")
    repo = next((r for r in data["repositories"] if r["name"] == repo_name), None)
    if repo is None:
        raise ValueError(f"Unknown repository: {repo_name}")
    if any(slug in r["items"][kind] for r in data["repositories"]):
        raise ValueError(f"Already selected: {kind}/{slug}")
    target = repo["resolved_path"] / kind / slug
    link = ROOT / kind / slug
    if target.exists() or target.is_symlink():
        raise ValueError(f"Target already exists: {target}")
    if link.is_symlink():
        raise ValueError(f"Path is already a symlink: {link}")
    if link.exists() and not link.is_dir():
        raise ValueError(f"Path is not a directory: {link}")
    print(f"{'would import' if link.exists() else 'would prepare'} {kind}/{slug} in {repo_name}")
    if not fix:
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    if link.exists():
        backup = ROOT / "content-import-backups" / kind / f"{slug}-{datetime.now():%Y%m%d-%H%M%S}"
        if backup.exists():
            raise ValueError(f"Backup path already exists: {backup}")
        temporary = target.with_name(f".{slug}.importing")
        if temporary.exists():
            raise ValueError(f"Incomplete earlier import: {temporary}")
        shutil.copytree(link, temporary, symlinks=True)
        if not same_tree(link, temporary):
            shutil.rmtree(temporary)
            raise ValueError(f"Copy verification failed: {link}")
        temporary.rename(target)
        backup.parent.mkdir(parents=True, exist_ok=True)
        link.rename(backup)
        try:
            link.symlink_to(target, target_is_directory=True)
        except OSError:
            backup.rename(link)
            raise
        print(f"original retained at {backup}")
    else:
        target.mkdir()
        link.symlink_to(target, target_is_directory=True)
    repo["items"][kind].append(slug)
    save_config(data)


def unmount(data, kind, slug, fix):
    match = next((e for e in entries(data) if e[1:3] == (kind, slug)), None)
    if match is None:
        raise ValueError(f"Not selected: {kind}/{slug}")
    repo, _, _, link, target = match
    if not link.is_symlink() or link.resolve() != target.resolve():
        raise ValueError(f"Not the expected mount: {link}")
    print(f"would unmount {kind}/{slug} from {repo['name']}")
    if fix:
        link.unlink()
        repo["items"][kind].remove(slug)
        save_config(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("action", choices=("check", "mount", "add", "unmount"))
    parser.add_argument("arguments", nargs="*")
    parser.add_argument("--fix", action="store_true", help="Apply changes; otherwise dry-run")
    args = parser.parse_args()
    try:
        data = load_config()
        if args.action in ("check", "mount") and not args.arguments:
            mount(data, args.action == "mount" and args.fix, args.action == "check")
        elif args.action == "add" and len(args.arguments) == 3:
            add(data, *args.arguments, args.fix)
        elif args.action == "unmount" and len(args.arguments) == 2:
            unmount(data, *args.arguments, args.fix)
        else:
            parser.error("check/mount take no arguments; add takes REPO KIND SLUG; unmount takes KIND SLUG")
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"content-repos: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
