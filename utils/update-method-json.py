#!/usr/bin/env python3
"""
Manage method JSON: add/remove/import practices, sync dependency versions and tags.

Replaces the manual Edit calls needed when integrating new practices into a method.

Usage:
    # Add a practice by name:
    python3 utils/update-method-json.py practices/red-hat-ai/red-hat-ai.json \
        --add-practice "Train and Prepare AI Models" --fix

    # Import a practice file (copies into method dir + adds to practiceNames):
    python3 utils/update-method-json.py practices/red-hat-ai/red-hat-ai.json \
        --import-practice practices/other/practice.json --fix

    # Remove a practice:
    python3 utils/update-method-json.py practices/red-hat-ai/red-hat-ai.json \
        --remove-practice "Old Practice Name" --fix

    # Sync dependency versions from resolved practice files:
    python3 utils/update-method-json.py practices/red-hat-ai/red-hat-ai.json \
        --sync-deps --fix

    # Sync tags/keywords from all constituent practices:
    python3 utils/update-method-json.py practices/red-hat-ai/red-hat-ai.json \
        --sync-tags --fix

    # Convert an embedded method to externalized practiceNames:
    python3 utils/update-method-json.py practices/red-hat-ai/red-hat-ai.json \
        --externalize --fix

    # Combined: import + sync all:
    python3 utils/update-method-json.py practices/red-hat-ai/red-hat-ai.json \
        --import-practice external/practice.json --sync-deps --sync-tags --fix

A method may carry its practices either as full embedded objects or as symbolic
`practiceNames`. Every other operation here reads `practiceNames`, so an embedded
method reports "Practices: 0" and silently does nothing. `--externalize` converts
one to the referenced form, writing each embedded practice out as its own document
beside the method where no file of that name already exists. The embedded copies
are the problem it solves: they duplicate documents the package already ships and
drift from them the moment a practice is regenerated.
"""
import argparse
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils._shared import load_json_pair, detect_kind, get_project_root


def externalize_embedded_practices(method_data, method_dir, apply_changes):
    """Convert an embedded `practices` array to symbolic `practiceNames`.

    Each embedded practice is written beside the method as its own document,
    but only where no file of that name exists: a standalone file on disk is
    the authored artifact and the embedded copy is a snapshot of it, so the
    file wins. Returns (changes, warnings).
    """
    embedded = method_data.get("practices") or []
    changes, warnings = [], []

    if not embedded:
        return changes, warnings

    if not all(isinstance(p, dict) for p in embedded):
        warnings.append("`practices` holds non-object entries; nothing externalized")
        return changes, warnings

    names = list(method_data.get("practiceNames", []))

    for practice in embedded:
        name = practice.get("name", "")
        if not name:
            warnings.append("an embedded practice has no name; skipped")
            continue

        slug = name.lower().replace("&", "and")
        slug = "".join(c if c.isalnum() or c.isspace() else "" for c in slug)
        slug = "-".join(slug.split())
        dest = method_dir / f"{slug}.json"

        if dest.exists():
            warnings.append(
                f"'{name}': kept {dest.name} on disk; embedded copy discarded"
            )
        else:
            if apply_changes:
                # An embedded practice omits `kind`, which context supplied.
                written = dict(practice)
                written.setdefault("kind", "practice")
                dest.write_text(json.dumps(written, indent=2) + "\n")
            changes.append(f"wrote embedded '{name}' → {dest.name}")

        if name not in names:
            names.append(name)
            changes.append(f"added '{name}' to practiceNames")

    method_data["practiceNames"] = names
    del method_data["practices"]
    changes.append(f"removed embedded `practices` ({len(embedded)} objects)")

    return changes, warnings


def find_practice_files(method_dir, practice_names, baseline_name=None):
    """Find practice JSON files in method dir and project directories."""
    found = {}
    search_dirs = [method_dir]

    root = get_project_root()
    if root:
        search_dirs.extend([
            root / "practices",
            root / "baselines",
            root / "deps",
        ])

    for name in practice_names:
        for search_dir in search_dirs:
            if not search_dir.exists():
                continue
            for json_file in search_dir.rglob("*.json"):
                if json_file.name.startswith("_"):
                    continue
                data, err = load_json_pair(json_file)
                if err or not isinstance(data, dict):
                    continue
                if data.get("name") == name:
                    found[name] = (json_file, data.get("version", "1.0.0"))
                    break
            if name in found:
                break

    if baseline_name and baseline_name not in found:
        for search_dir in search_dirs:
            if not search_dir.exists():
                continue
            for json_file in search_dir.rglob("*.json"):
                if json_file.name.startswith("_"):
                    continue
                data, err = load_json_pair(json_file)
                if err or not isinstance(data, dict):
                    continue
                if data.get("name") == baseline_name:
                    found[baseline_name] = (json_file, data.get("version", "1.0.0"))
                    break
            if baseline_name in found:
                break

    return found


def sync_dependency_versions(method_data, method_dir):
    """Rebuild dependencyVersions from resolved practice files."""
    baseline_name = method_data.get("baselinePracticeName", "")
    practice_names = method_data.get("practiceNames", [])
    all_dep_names = []
    if baseline_name:
        all_dep_names.append(baseline_name)
    all_dep_names.extend(practice_names)

    resolved = find_practice_files(method_dir, practice_names, baseline_name)

    new_dvs = []
    warnings = []
    for name in all_dep_names:
        if name in resolved:
            _, version = resolved[name]
            parts = version.split(".")
            while len(parts) < 3:
                parts.append("0")
            version = ".".join(parts[:3])
            new_dvs.append({
                "documentName": name,
                "versionRange": f"^{version}",
            })
        else:
            warnings.append(f"WARNING: could not resolve dependency '{name}'")

    return new_dvs, warnings


def sync_tags_from_practices(method_data, method_dir):
    """Merge tags and keywords from all constituent practice JSONs."""
    practice_names = method_data.get("practiceNames", [])
    resolved = find_practice_files(method_dir, practice_names)

    domain_tags = set()
    lifecycle_tags = set()
    org_tags = set()
    keywords = set()

    existing_tags = method_data.get("tags", {})
    for t in existing_tags.get("domainTags", []):
        domain_tags.add(t)
    for t in existing_tags.get("lifecycleTags", []):
        lifecycle_tags.add(t)
    for t in existing_tags.get("organizationalTags", []):
        org_tags.add(t)
    for k in method_data.get("keywords", []):
        keywords.add(k)

    for name in practice_names:
        if name not in resolved:
            continue
        fpath, _ = resolved[name]
        data, err = load_json_pair(fpath)
        if err or not isinstance(data, dict):
            continue
        ptags = data.get("tags", {})
        for t in ptags.get("domainTags", []):
            domain_tags.add(t)
        for t in ptags.get("lifecycleTags", []):
            lifecycle_tags.add(t)
        for t in ptags.get("organizationalTags", []):
            org_tags.add(t)
        for k in data.get("keywords", []):
            keywords.add(k)

    new_tags = {
        "domainTags": sorted(domain_tags),
        "lifecycleTags": sorted(lifecycle_tags),
        "organizationalTags": sorted(org_tags),
    }
    new_keywords = sorted(keywords)

    return new_tags, new_keywords


def main():
    parser = argparse.ArgumentParser(
        description="Manage method JSON: add/remove/import practices, sync deps and tags"
    )
    parser.add_argument("method_file", help="Path to method JSON file")
    parser.add_argument(
        "--add-practice", action="append", default=[],
        help="Add practice name to practiceNames (repeatable)"
    )
    parser.add_argument(
        "--remove-practice", action="append", default=[],
        help="Remove practice name from practiceNames (repeatable)"
    )
    parser.add_argument(
        "--import-practice", action="append", default=[],
        help="Copy practice file into method dir and add to practiceNames (repeatable)"
    )
    parser.add_argument(
        "--sync-deps", action="store_true",
        help="Rebuild dependencyVersions from resolved practice files"
    )
    parser.add_argument(
        "--sync-tags", action="store_true",
        help="Merge tags/keywords from all constituent practices"
    )
    parser.add_argument(
        "--externalize",
        action="store_true",
        help=(
            "Convert an embedded `practices` array to symbolic `practiceNames`, "
            "writing each embedded practice beside the method where no file of "
            "that name exists. Runs before the other operations, so --sync-deps "
            "and --sync-tags see the practices an embedded method would hide"
        ),
    )
    parser.add_argument(
        "--fix", action="store_true",
        help="Write changes (default: dry-run)"
    )
    args = parser.parse_args()

    method_path = Path(args.method_file)
    data, err = load_json_pair(method_path)
    if err:
        print(f"Error loading {method_path}: {err}", file=sys.stderr)
        sys.exit(2)

    kind = detect_kind(data)
    if kind != "method":
        print(f"Error: {method_path} is kind '{kind}', expected 'method'", file=sys.stderr)
        sys.exit(2)

    method_dir = method_path.parent
    changes = []
    warnings = []

    # Externalize first: every operation below reads practiceNames, which an
    # embedded method does not have.
    if args.externalize:
        ext_changes, ext_warnings = externalize_embedded_practices(
            data, method_dir, args.fix
        )
        changes.extend(ext_changes)
        warnings.extend(ext_warnings)
        if not ext_changes:
            warnings.append("no embedded `practices` array; already externalized")

    practice_names = list(data.get("practiceNames", []))

    for imp_path in args.import_practice:
        imp_file = Path(imp_path)
        if not imp_file.exists():
            print(f"Error: {imp_file} not found", file=sys.stderr)
            sys.exit(2)
        imp_data, imp_err = load_json_pair(imp_file)
        if imp_err:
            print(f"Error loading {imp_file}: {imp_err}", file=sys.stderr)
            sys.exit(2)
        imp_name = imp_data.get("name", "")
        if not imp_name:
            print(f"Error: {imp_file} has no name field", file=sys.stderr)
            sys.exit(2)

        dest = method_dir / imp_file.name
        if imp_file.resolve() != dest.resolve():
            if args.fix:
                shutil.copy2(imp_file, dest)
            changes.append(f"imported {imp_file.name} → {dest}")

        if imp_name not in practice_names:
            practice_names.append(imp_name)
            changes.append(f"added '{imp_name}' to practiceNames")

    for name in args.add_practice:
        if name not in practice_names:
            practice_names.append(name)
            changes.append(f"added '{name}' to practiceNames")
        else:
            warnings.append(f"'{name}' already in practiceNames")

    for name in args.remove_practice:
        if name in practice_names:
            practice_names.remove(name)
            changes.append(f"removed '{name}' from practiceNames")
        else:
            warnings.append(f"'{name}' not in practiceNames")

    if practice_names != data.get("practiceNames", []):
        data["practiceNames"] = practice_names

    if args.sync_deps:
        new_dvs, dep_warnings = sync_dependency_versions(data, method_dir)
        warnings.extend(dep_warnings)
        old_dvs = data.get("dependencyVersions", [])
        if new_dvs != old_dvs:
            data["dependencyVersions"] = new_dvs
            changes.append(f"synced dependencyVersions ({len(new_dvs)} entries)")

    if args.sync_tags:
        new_tags, new_keywords = sync_tags_from_practices(data, method_dir)
        old_tags = data.get("tags", {})
        old_keywords = data.get("keywords", [])

        added_domain = set(new_tags["domainTags"]) - set(old_tags.get("domainTags", []))
        added_lifecycle = set(new_tags["lifecycleTags"]) - set(old_tags.get("lifecycleTags", []))
        added_org = set(new_tags["organizationalTags"]) - set(old_tags.get("organizationalTags", []))
        added_keywords = set(new_keywords) - set(old_keywords)

        if added_domain or added_lifecycle or added_org:
            data["tags"] = new_tags
            tag_count = len(added_domain) + len(added_lifecycle) + len(added_org)
            changes.append(f"synced tags (+{tag_count} new)")

        if added_keywords:
            data["keywords"] = new_keywords
            changes.append(f"synced keywords (+{len(added_keywords)} new)")

    mode = "WRITE" if args.fix else "DRY-RUN"
    print(f"Method: {data.get('name')} v{data.get('version', '?')}")
    print(f"Practices: {len(practice_names)}")
    print(f"Mode: {mode}")
    print()

    if warnings:
        for w in warnings:
            print(f"  {w}")

    if changes:
        for c in changes:
            print(f"  {c}")
    else:
        print("  No changes needed.")

    if args.fix and changes:
        with open(method_path, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print(f"\nWritten to {method_path}")

    if not args.fix and changes:
        print("\nRun with --fix to apply changes.")


if __name__ == "__main__":
    main()
