#!/usr/bin/env python3
"""Check downstream impact of element renames/removals in a practice or baseline.

Orchestrates the change management pipeline:
1. Generates a ChangeRequest from old vs new JSON (detects nameChanges)
2. Finds all downstream dependents via discover-dependencies (local + remote)
3. Checks each dependent for broken references (dry-run)
4. Optionally applies fixes and rebuilds affected .keleo bundles

Usage:
    # Check impact of changes (dry-run, local only)
    python3 utils/check-downstream-impact.py <old.json> <new.json>

    # Include remote repository in dependency search
    python3 utils/check-downstream-impact.py <old.json> <new.json> --remote

    # Auto-pull remote-only dependents so they can be inspected
    python3 utils/check-downstream-impact.py <old.json> <new.json> --remote --auto-pull

    # Check + fix all affected downstream files + rebuild bundles
    python3 utils/check-downstream-impact.py <old.json> <new.json> --fix --rebuild-bundles

    # Only check specific element types
    python3 utils/check-downstream-impact.py <old.json> <new.json> --element-types WorkProduct State

    # Machine-readable output
    python3 utils/check-downstream-impact.py <old.json> <new.json> --json
"""
import argparse
import importlib.util
import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

_UTILS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_UTILS_DIR))
from _shared import (load_json, load_json_from_keleo, load_all_from_keleo,
                     detect_kind, get_project_root)


def _import_from(filename):
    """Import a module from a hyphenated filename."""
    path = _UTILS_DIR / filename
    spec = importlib.util.spec_from_file_location(
        filename.replace("-", "_").replace(".py", ""), path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_gen_cr = _import_from("generate-change-request.py")
_apply_cr = _import_from("apply-change-request.py")
_discover = _import_from("discover-dependencies.py")


def _find_dependents(practice_name, search_dirs=None, include_remote=False):
    """Find all practices/methods that depend on the named practice."""
    dirs = search_dirs or ["baselines", "practices", "deps", "bundles"]
    if include_remote:
        _discover._refresh_remote_index_if_stale()
    index, _ = _discover.build_index(dirs, include_remote=include_remote)
    result = _discover.cmd_dependents(practice_name, index)
    return result.get("dependents", [])


def _auto_pull_dependent(name):
    """Pull a remote-only dependent bundle. Returns path if successful."""
    studio_client = _UTILS_DIR / "studio-client.py"
    if not studio_client.exists():
        return None
    try:
        proc = subprocess.run(
            [sys.executable, str(studio_client), "--pull", name, "--json"],
            capture_output=True, text=True, timeout=60,
        )
        if proc.returncode == 0:
            result = json.loads(proc.stdout)
            return result.get("path")
    except (subprocess.TimeoutExpired, OSError, json.JSONDecodeError):
        pass
    return None


def _load_dependent_data(dep):
    """Load JSON data for a dependent, handling both filesystem and .keleo sources."""
    source = dep.get("source", "filesystem")
    if source == "keleo":
        data, err = load_json_from_keleo(dep["path"], document_name=dep["name"])
        if err:
            return None, err
        return data, None
    else:
        return load_json(dep["path"]), None


def _find_affected_bundles(affected_names):
    """Find .keleo bundles that contain any of the affected practice names."""
    bundles_dir = Path(get_project_root()) / "bundles"
    if not bundles_dir.exists():
        return []

    import zipfile
    affected = []
    for keleo in sorted(bundles_dir.glob("*.keleo")):
        try:
            with zipfile.ZipFile(keleo) as zf:
                manifest_data = json.loads(zf.read("manifest.json"))
                doc_names = {d.get("documentName") for d in manifest_data.get("documents", [])}
                if doc_names & affected_names:
                    affected.append(str(keleo))
        except Exception:
            continue

    return affected


def check_impact(old_path, new_path, element_types=None, fix=False,
                 rebuild_bundles=False, search_dirs=None, json_output=False,
                 include_remote=False, auto_pull=False):
    old_data = load_json(old_path)
    new_data = load_json(new_path)

    practice_name = new_data.get("name") or old_data.get("name")
    if not practice_name:
        print("ERROR: Could not determine practice name from JSON files",
              file=sys.stderr)
        sys.exit(1)

    cr = _gen_cr.generate_change_request(
        old_data, new_data, "check-downstream-impact", "draft", None, None)

    name_changes = cr.get("nameChanges", [])
    operations = cr.get("operations", [])
    remove_ops = [op for op in operations if op.get("operation") == "remove"]

    if not name_changes and not remove_ops:
        result = {
            "practice": practice_name,
            "nameChanges": 0,
            "removals": 0,
            "message": "No element renames or removals detected — "
                       "no downstream impact possible",
        }
        if json_output:
            print(json.dumps(result, indent=2))
        else:
            print(f"Practice: {practice_name}")
            print("No element renames or removals detected — "
                  "no downstream impact possible.")
        return result

    type_filter = set(element_types) if element_types else None

    dependents = _find_dependents(practice_name, search_dirs,
                                  include_remote=include_remote)

    # Auto-pull remote-only dependents that are only in .keleo bundles
    pulled = []
    if auto_pull:
        for dep in dependents:
            if dep.get("source") == "keleo" and not Path(dep["path"]).exists():
                pulled_path = _auto_pull_dependent(dep["name"])
                if pulled_path:
                    dep["path"] = pulled_path
                    pulled.append(dep["name"])
                    print(f"Auto-pulled: {dep['name']}", file=sys.stderr)

        if pulled:
            dependents = _find_dependents(practice_name, search_dirs,
                                          include_remote=include_remote)

    if not dependents:
        result = {
            "practice": practice_name,
            "nameChanges": len(name_changes),
            "removals": len(remove_ops),
            "dependents": 0,
            "message": "No downstream dependents found",
        }
        if json_output:
            print(json.dumps(result, indent=2))
        else:
            print(f"Practice: {practice_name}")
            print(f"  Name changes: {len(name_changes)}")
            print(f"  Removals: {len(remove_ops)}")
            print("  No downstream dependents found.")
        return result

    target_reports = []
    affected_paths = []
    affected_names = set()
    keleo_only_affected = []

    for dep in dependents:
        dep_source = dep.get("source", "filesystem")
        dep_data, err = _load_dependent_data(dep)
        if err or dep_data is None:
            target_reports.append({
                "file": dep["path"],
                "name": dep["name"],
                "kind": dep.get("kind", "unknown"),
                "role": dep["role"],
                "source": dep_source,
                "totalChanges": 0,
                "error": err or "Could not load",
                "nameChanges": [],
            })
            continue

        work_data = deepcopy(dep_data) if not fix else dep_data
        kind = detect_kind(work_data)

        results, identity_count = _apply_cr.process_target(
            work_data, kind, name_changes, type_filter,
            operations=remove_ops if remove_ops else None,
        )

        total = sum(len(r["references"]) for r in results)
        report = {
            "file": dep["path"],
            "name": dep["name"],
            "kind": kind,
            "role": dep["role"],
            "source": dep_source,
            "totalChanges": total,
            "nameChanges": results,
        }
        target_reports.append(report)

        if total > 0:
            affected_names.add(dep["name"])
            if dep_source == "filesystem":
                affected_paths.append(dep["path"])
                if fix:
                    with open(dep["path"], "w") as f:
                        json.dump(work_data, f, indent=2, ensure_ascii=False)
                        f.write("\n")
            else:
                keleo_only_affected.append(dep)

    rebuilt_bundles = []
    if fix and rebuild_bundles and affected_paths:
        bundles = _find_affected_bundles(affected_names)
        for bundle_path in bundles:
            try:
                subprocess.run(
                    [sys.executable, "utils/rebuild-keleo.py",
                     bundle_path, "--if-changed"],
                    check=True, capture_output=True, text=True,
                )
                rebuilt_bundles.append(bundle_path)
            except subprocess.CalledProcessError as e:
                print(f"WARNING: Failed to rebuild {bundle_path}: {e.stderr}",
                      file=sys.stderr)

    total_changes = sum(t["totalChanges"] for t in target_reports)
    affected_count = sum(1 for t in target_reports if t["totalChanges"] > 0)
    unaffected_count = sum(1 for t in target_reports if t["totalChanges"] == 0)

    result = {
        "practice": practice_name,
        "dryRun": not fix,
        "nameChanges": len(name_changes),
        "removals": len(remove_ops),
        "summary": {
            "totalDependents": len(dependents),
            "affectedDependents": affected_count,
            "unaffectedDependents": unaffected_count,
            "totalReferenceChanges": total_changes,
        },
        "targets": target_reports,
    }
    if rebuilt_bundles:
        result["rebuiltBundles"] = rebuilt_bundles
    if keleo_only_affected:
        result["keleoOnlyAffected"] = [
            {"name": d["name"], "path": d["path"]} for d in keleo_only_affected
        ]

    if json_output:
        print(json.dumps(result, indent=2))
    else:
        _print_human_report(result, name_changes, remove_ops, target_reports,
                            fix, total_changes, affected_count, unaffected_count,
                            rebuilt_bundles, keleo_only_affected)

    return result


def _print_human_report(result, name_changes, remove_ops, target_reports,
                        fix, total_changes, affected_count, unaffected_count,
                        rebuilt_bundles, keleo_only_affected):
    print(f"Practice: {result['practice']}")
    print(f"  Name changes: {len(name_changes)}")
    for nc in name_changes:
        print(f"    {nc['elementType']}: {nc['fromName']} → {nc['toName']}")
    if remove_ops:
        print(f"  Removals: {len(remove_ops)}")
        for op in remove_ops:
            print(f"    {op['elementType']}: {op['elementName']}")
    print()
    print(f"Downstream dependents: {result['summary']['totalDependents']}")
    print(f"  Affected: {affected_count}")
    print(f"  Unaffected: {unaffected_count}")
    print(f"  Total reference changes: {total_changes}")
    print()

    for t in target_reports:
        if t["totalChanges"] == 0:
            continue
        source_tag = f" [{t['source']}]" if t.get("source") != "filesystem" else ""
        print(f"  {t['name']}{source_tag} ({t['file']})")
        print(f"    {t['totalChanges']} reference(s) to update:")
        for nc in t["nameChanges"]:
            for ref in nc["references"]:
                print(f"      {ref['path']}.{ref['field']}: "
                      f"{ref['old']} → {ref['new']}")
        print()

    if t_errors := [t for t in target_reports if t.get("error")]:
        print("  Could not load:")
        for t in t_errors:
            print(f"    {t['name']}: {t['error']}")
        print()

    if keleo_only_affected:
        print("  NOTE: The following affected dependents are inside .keleo "
              "bundles (not fixable in-place):")
        for d in keleo_only_affected:
            print(f"    {d['name']} ({d['path']})")
        print("  Pull and extract these bundles to apply fixes.")
        print()

    if fix:
        print(f"{'Applied' if total_changes > 0 else 'No changes to apply'}.")
    else:
        if total_changes > 0:
            print("Dry run — use --fix to apply changes.")

    if rebuilt_bundles:
        print(f"\nRebuilt {len(rebuilt_bundles)} bundle(s):")
        for b in rebuilt_bundles:
            print(f"  {b}")


def main():
    parser = argparse.ArgumentParser(
        description="Check downstream impact of element renames/removals "
                    "in a practice or baseline"
    )
    parser.add_argument("old", help="Original (pre-change) JSON file")
    parser.add_argument("new", help="Updated (post-change) JSON file")
    parser.add_argument("--fix", action="store_true",
                        help="Apply fixes to affected downstream files "
                             "(default: dry-run)")
    parser.add_argument("--rebuild-bundles", action="store_true",
                        help="Rebuild .keleo bundles containing affected "
                             "files (requires --fix)")
    parser.add_argument("--remote", action="store_true",
                        help="Include remote repository in dependency search")
    parser.add_argument("--auto-pull", action="store_true",
                        help="Auto-pull remote-only dependents for inspection "
                             "(requires --remote)")
    parser.add_argument("--element-types", nargs="*", metavar="TYPE",
                        help="Only check specific element types "
                             "(e.g., WorkProduct State Alpha)")
    parser.add_argument("--search-dirs", nargs="*",
                        help="Override dependency search directories")
    parser.add_argument("--json", action="store_true", dest="json_output",
                        help="Machine-readable JSON output")
    args = parser.parse_args()

    if args.rebuild_bundles and not args.fix:
        parser.error("--rebuild-bundles requires --fix")
    if args.auto_pull and not args.remote:
        parser.error("--auto-pull requires --remote")

    check_impact(
        args.old, args.new,
        element_types=args.element_types,
        fix=args.fix,
        rebuild_bundles=args.rebuild_bundles,
        search_dirs=args.search_dirs,
        json_output=args.json_output,
        include_remote=args.remote,
        auto_pull=args.auto_pull,
    )


if __name__ == "__main__":
    main()
