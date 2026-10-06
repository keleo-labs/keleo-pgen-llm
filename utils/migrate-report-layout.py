#!/usr/bin/env python3
"""Migrate flat reports into per-report workspace directories.

Reports used to be written as a flat `reports/<slug>.md` with diagram assets in
a parallel tree at `reports/assets/<slug>/`. They are now self-contained
workspaces mirroring the practice convention:

    reports/<slug>/
        00-prompt-history.md        (written by prompt-history.py, not here)
        <slug>.md
        <slug>.pdf                  (and any other companion export)
        .published-docs.json        (per-directory google-doc republish state)
        assets/<name>.svg           (and the .json spec beside it)

Embedded image paths shorten from `assets/<slug>/x.svg` to `assets/x.svg`,
which is why the markdown is rewritten rather than only moved. Doc IDs in
`.published-docs.json` are keyed by filename, and the filename does not change,
so republishing an already-published report keeps updating the same Doc.

Idempotent: a report already in workspace form is reported as such and skipped,
so a partially migrated tree can be finished by re-running.

Usage:
    python3 utils/migrate-report-layout.py                  # dry run (default)
    python3 utils/migrate-report-layout.py --fix
    python3 utils/migrate-report-layout.py --fix --json
    python3 utils/migrate-report-layout.py --reports-dir path/to/reports --fix
"""

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _shared import get_project_root  # noqa: E402

#: Lives at the reports/ root, not inside a report, so it is never a companion.
STATE_FILE = ".published-docs.json"

#: Files at the reports/ root that are infrastructure rather than report output.
RESERVED_NAMES = {STATE_FILE, ".gitignore", ".gitkeep", "assets"}


def _slug_of(markdown_path):
    return markdown_path.stem


def _companions(reports_dir, slug):
    """Sibling exports of a report: <slug>.pdf, <slug>.docx, and the like."""
    return sorted(
        p for p in reports_dir.glob(f"{slug}.*")
        if p.is_file() and p.suffix.lower() != ".md"
    )


def _rewrite_embeds(text, slug):
    """Drop the redundant slug segment from asset links: assets/<slug>/x → assets/x.

    Covers markdown images and links, plus raw src/href attributes, since a
    report may embed an SVG through HTML when it needs sizing control.
    """
    patterns = [
        (rf"\]\(assets/{re.escape(slug)}/", "](assets/"),
        (rf'(src|href)=(["\'])assets/{re.escape(slug)}/', r"\1=\2assets/"),
    ]
    count = 0
    for pattern, replacement in patterns:
        text, n = re.subn(pattern, replacement, text)
        count += n
    return text, count


def _plan_report(reports_dir, markdown_path):
    """Build the migration plan for one flat report. No filesystem writes."""
    slug = _slug_of(markdown_path)
    target_dir = reports_dir / slug
    asset_src = reports_dir / "assets" / slug

    plan = {
        "slug": slug,
        "targetDir": str(target_dir),
        "markdown": markdown_path.name,
        "companions": [p.name for p in _companions(reports_dir, slug)],
        "assets": sorted(p.name for p in asset_src.iterdir()) if asset_src.is_dir() else [],
        "embedsRewritten": 0,
        "publishedState": False,
        "errors": [],
    }

    if target_dir.exists() and not target_dir.is_dir():
        plan["errors"].append(f"{target_dir} exists and is not a directory")
        return plan
    if (target_dir / markdown_path.name).exists():
        plan["errors"].append(f"{target_dir / markdown_path.name} already exists")
        return plan

    _, plan["embedsRewritten"] = _rewrite_embeds(
        markdown_path.read_text(encoding="utf-8"), slug
    )
    return plan


def _apply_report(reports_dir, markdown_path, plan, published):
    """Execute a plan: move files, rewrite embeds, carry published state."""
    slug = plan["slug"]
    target_dir = reports_dir / slug
    target_dir.mkdir(parents=True, exist_ok=True)

    text, _ = _rewrite_embeds(markdown_path.read_text(encoding="utf-8"), slug)
    (target_dir / markdown_path.name).write_text(text, encoding="utf-8")
    markdown_path.unlink()

    for companion in _companions(reports_dir, slug):
        shutil.move(str(companion), str(target_dir / companion.name))

    asset_src = reports_dir / "assets" / slug
    if asset_src.is_dir():
        asset_dst = target_dir / "assets"
        asset_dst.mkdir(exist_ok=True)
        for asset in sorted(asset_src.iterdir()):
            shutil.move(str(asset), str(asset_dst / asset.name))
        asset_src.rmdir()

    entry = published.pop(markdown_path.name, None)
    if entry is not None:
        (target_dir / STATE_FILE).write_text(
            json.dumps({markdown_path.name: entry}, indent=2) + "\n", encoding="utf-8"
        )
        plan["publishedState"] = True


def _prune_root(reports_dir, published, had_state_file):
    """Remove the now-redundant root assets/ tree and published-state file."""
    pruned = []
    assets_root = reports_dir / "assets"
    if assets_root.is_dir() and not any(assets_root.iterdir()):
        assets_root.rmdir()
        pruned.append("assets/")

    state_path = reports_dir / STATE_FILE
    if had_state_file:
        if published:  # entries whose report was not migrated — keep them
            state_path.write_text(json.dumps(published, indent=2) + "\n", encoding="utf-8")
        elif state_path.exists():
            state_path.unlink()
            pruned.append(STATE_FILE)
    return pruned


def migrate(reports_dir, apply_changes):
    flat = sorted(
        p for p in reports_dir.glob("*.md")
        if p.is_file() and p.name not in RESERVED_NAMES
    )
    already = sorted(
        d.name for d in reports_dir.iterdir()
        if d.is_dir() and d.name not in RESERVED_NAMES and any(d.glob("*.md"))
    )

    state_path = reports_dir / STATE_FILE
    had_state_file = state_path.exists()
    published = json.loads(state_path.read_text(encoding="utf-8")) if had_state_file else {}

    plans, errors = [], []
    for markdown_path in flat:
        plan = _plan_report(reports_dir, markdown_path)
        if plan["errors"]:
            errors.extend(f"{plan['slug']}: {e}" for e in plan["errors"])
        plans.append(plan)

    if errors:
        return {"status": "blocked", "errors": errors, "reports": plans,
                "alreadyMigrated": already, "pruned": []}

    pruned = []
    if apply_changes:
        for markdown_path, plan in zip(flat, plans):
            _apply_report(reports_dir, markdown_path, plan, published)
        pruned = _prune_root(reports_dir, published, had_state_file)

    return {
        "status": "migrated" if apply_changes else "dry-run",
        "reportsDir": str(reports_dir),
        "migrated": len(plans),
        "alreadyMigrated": already,
        "reports": plans,
        "pruned": pruned,
        "errors": [],
    }


def _print_human(result):
    if result["status"] == "blocked":
        print("Migration blocked:\n")
        for error in result["errors"]:
            print(f"  ERROR  {error}")
        print("\nResolve the collisions above and re-run.")
        return

    header = "Would migrate" if result["status"] == "dry-run" else "Migrated"
    print(f"{header} {result['migrated']} report(s) in {result['reportsDir']}\n")

    for plan in result["reports"]:
        print(f"  {plan['slug']}/")
        print(f"    {plan['markdown']}")
        for name in plan["companions"]:
            print(f"    {name}")
        for name in plan["assets"]:
            print(f"    assets/{name}")
        if plan["embedsRewritten"]:
            print(f"    ({plan['embedsRewritten']} embed path(s) rewritten)")
        if plan["publishedState"]:
            print(f"    {STATE_FILE} (published Doc ID carried)")

    if result["alreadyMigrated"]:
        print(f"\nAlready in workspace form ({len(result['alreadyMigrated'])}): "
              + ", ".join(result["alreadyMigrated"]))
    if result["pruned"]:
        print("\nPruned from reports/: " + ", ".join(result["pruned"]))
    if result["status"] == "dry-run" and result["migrated"]:
        print("\nNothing written. Re-run with --fix to apply.")


def main():
    parser = argparse.ArgumentParser(
        description="Migrate flat reports into per-report workspace directories"
    )
    parser.add_argument(
        "--reports-dir",
        help="Reports directory to migrate (default: <project root>/reports)",
    )
    parser.add_argument(
        "--fix", action="store_true",
        help="Apply the migration (default: dry run, nothing is written)",
    )
    parser.add_argument("--json", action="store_true", help="Emit the result as JSON")
    args = parser.parse_args()

    reports_dir = Path(args.reports_dir) if args.reports_dir else Path(get_project_root()) / "reports"
    if not reports_dir.is_dir():
        print(f"Reports directory not found: {reports_dir}", file=sys.stderr)
        sys.exit(2)

    result = migrate(reports_dir, args.fix)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        _print_human(result)

    sys.exit(1 if result["status"] == "blocked" else 0)


if __name__ == "__main__":
    main()
