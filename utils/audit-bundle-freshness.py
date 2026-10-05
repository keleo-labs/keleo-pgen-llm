#!/usr/bin/env python3
"""Audit .keleo bundles for stale embedded document copies.

A .keleo bundle embeds a snapshot of every document it depends on. When a
source document is later fixed on disk, bundles built before the fix keep
carrying the old copy. Loaded together in a library view those stale copies
reintroduce content that was already corrected — wrong aliases, old element
names, superseded states.

This compares each document embedded in each bundle against the current
on-disk version of the document with the same name, and reports drift.

Rebuild mode repackages stale bundles from current on-disk sources, bumping
the manifest version. Documents that exist only inside the bundle (typically
externalized method documents generated at packaging time) are carried over
verbatim, since they reference their practices by name rather than by value.

Usage:
    python3 utils/audit-bundle-freshness.py
    python3 utils/audit-bundle-freshness.py --bundle bundles/red-hat-ai.keleo
    python3 utils/audit-bundle-freshness.py --document "Observability"
    python3 utils/audit-bundle-freshness.py --stale-only --json
    python3 utils/audit-bundle-freshness.py --rebuild            # dry run
    python3 utils/audit-bundle-freshness.py --rebuild --fix --bump patch
"""

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _shared import (  # noqa: E402
    detect_kind,
    get_project_root,
    increment_version,
    load_all_from_keleo,
    load_json_pair,
)

SOURCE_DIRS = ["deps", "baselines", "practices"]
# practiceBaseline before practice before method, so bundles stay topological
# and package-keleo's entry-point rule (method, else last) resolves correctly.
KIND_ORDER = {"practiceBaseline": 0, "practice": 1, "method": 2}


def parse_version(version_str):
    """Parse a semver-ish string into a comparable tuple. Unparsable sorts lowest."""
    if not version_str:
        return (-1,)
    parts = []
    for chunk in str(version_str).split("-")[0].split("."):
        try:
            parts.append(int(chunk))
        except ValueError:
            return (-1,)
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts)


def build_source_index(root):
    """Index current on-disk documents by name, keeping the highest version of each."""
    index = {}
    for dirname in SOURCE_DIRS:
        search_path = root / dirname
        if not search_path.is_dir():
            continue

        if dirname == "deps":
            json_files = list(search_path.glob("*.json"))
        else:
            json_files = list(search_path.glob("*/*.json"))
            json_files.extend(search_path.glob("*.json"))

        for json_file in json_files:
            if json_file.name.startswith("_"):
                continue
            if "backup" in str(json_file).lower():
                continue
            if json_file.name.endswith(".changerequest.json"):
                continue

            data, err = load_json_pair(json_file)
            if err or not isinstance(data, dict):
                continue
            name = data.get("name")
            if not name:
                continue

            candidate = {
                "name": name,
                "version": data.get("version", ""),
                "kind": detect_kind(data),
                "path": str(json_file.relative_to(root)),
            }
            existing = index.get(name)
            if existing is None or parse_version(candidate["version"]) > parse_version(
                existing["version"]
            ):
                index[name] = candidate
    return index


def audit_bundle(keleo_path, source_index, root):
    """Compare a bundle's embedded documents against current on-disk sources."""
    documents, err = load_all_from_keleo(keleo_path)
    if err:
        return {"bundle": str(keleo_path.relative_to(root)), "error": err, "documents": []}

    entries = []
    for doc in documents:
        name = doc.get("name")
        if not name:
            continue
        bundled_version = doc.get("version", "")
        source = source_index.get(name)

        if source is None:
            status = "no-source"
            source_version = None
            source_path = None
        else:
            source_version = source["version"]
            source_path = source["path"]
            bundled_tuple = parse_version(bundled_version)
            source_tuple = parse_version(source_version)
            if bundled_tuple < source_tuple:
                status = "stale"
            elif bundled_tuple > source_tuple:
                status = "ahead"
            else:
                status = "current"

        entries.append({
            "document": name,
            "kind": detect_kind(doc),
            "bundledVersion": bundled_version,
            "sourceVersion": source_version,
            "sourcePath": source_path,
            "status": status,
        })

    return {
        "bundle": str(keleo_path.relative_to(root)),
        "documents": sorted(entries, key=lambda e: e["document"]),
    }


def bump_version(version_str, bump):
    """Bump a version, preserving any prerelease/build suffix (e.g. '1.0.4-fork')."""
    if bump == "none":
        return version_str
    core, sep, suffix = (version_str or "1.0.0").partition("-")
    try:
        bumped = increment_version(core, bump)
    except (ValueError, IndexError):
        return version_str
    return f"{bumped}{sep}{suffix}" if sep else bumped


def read_manifest(keleo_path):
    """Return the bundle's manifest dict, or None."""
    try:
        with zipfile.ZipFile(keleo_path, "r") as zf:
            if "manifest.json" not in zf.namelist():
                return None
            return json.loads(zf.read("manifest.json"))
    except (zipfile.BadZipFile, json.JSONDecodeError, OSError):
        return None


def stage_bundled_document(keleo_path, document_name, staging_dir):
    """Extract a bundle-only document to staging. Returns its path, or None."""
    manifest = read_manifest(keleo_path)
    if not manifest:
        return None
    try:
        with zipfile.ZipFile(keleo_path, "r") as zf:
            for entry in manifest.get("documents", []):
                if entry.get("documentName") != document_name:
                    continue
                zip_path = entry.get("path", "")
                if zip_path not in zf.namelist():
                    return None
                target = staging_dir / Path(zip_path).name
                target.write_bytes(zf.read(zip_path))
                return target
    except (zipfile.BadZipFile, OSError):
        return None
    return None


def rebuild_bundle(keleo_path, source_index, root, bump, apply_changes):
    """Repackage one bundle from current on-disk sources. Returns a result dict."""
    rel = str(keleo_path.relative_to(root))
    manifest = read_manifest(keleo_path)
    if not manifest:
        return {"bundle": rel, "status": "error", "message": "unreadable manifest"}

    package = manifest.get("package", {}) or {}
    old_version = package.get("version", "") or "1.0.0"
    new_version = bump_version(old_version, bump)

    staging = Path(tempfile.mkdtemp(prefix="keleo-stage-"))
    try:
        resolved, carried = [], []
        for entry in manifest.get("documents", []):
            name = entry.get("documentName", "")
            kind = entry.get("documentType", "practice")
            source = source_index.get(name)
            if source:
                resolved.append((KIND_ORDER.get(source["kind"], 1), root / source["path"]))
                continue
            staged = stage_bundled_document(keleo_path, name, staging)
            if staged is None:
                return {
                    "bundle": rel, "status": "error",
                    "message": f"cannot resolve document {name!r}",
                }
            carried.append(name)
            resolved.append((KIND_ORDER.get(kind, 1), staged))

        ordered = [str(p) for _, p in sorted(resolved, key=lambda x: x[0])]

        if not apply_changes:
            return {
                "bundle": rel, "status": "dry-run",
                "oldVersion": old_version, "newVersion": new_version,
                "documents": len(ordered), "carriedOver": carried,
            }

        out_tmp = staging / keleo_path.name
        cmd = [
            sys.executable, str(Path(__file__).parent / "package-keleo.py"),
            "--documents", *ordered,
            "--name", package.get("name", "") or keleo_path.stem,
            "--version", new_version,
            "--description", package.get("description", "") or "",
            "-o", str(out_tmp),
        ]
        authors = package.get("authors") or []
        if authors:
            cmd += ["--authors", *authors]
        if package.get("license"):
            cmd += ["--license", package["license"]]

        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0 or not out_tmp.exists():
            return {
                "bundle": rel, "status": "error",
                "message": (proc.stderr or proc.stdout).strip()[:400],
            }

        shutil.move(str(out_tmp), str(keleo_path))
        return {
            "bundle": rel, "status": "rebuilt",
            "oldVersion": old_version, "newVersion": new_version,
            "documents": len(ordered), "carriedOver": carried,
        }
    finally:
        shutil.rmtree(staging, ignore_errors=True)


STATUS_MARK = {
    "stale": "STALE  ",
    "ahead": "AHEAD  ",
    "current": "ok     ",
    "no-source": "no-src ",
}


def print_report(results, stale_only):
    total_stale = 0
    stale_bundles = 0
    by_document = defaultdict(list)

    for result in results:
        if result.get("error"):
            print(f"=== {result['bundle']} ===")
            print(f"  ERROR: {result['error']}\n")
            continue

        stale = [d for d in result["documents"] if d["status"] == "stale"]
        if stale_only and not stale:
            continue
        if stale:
            stale_bundles += 1
            total_stale += len(stale)

        print(f"=== {result['bundle']} ===")
        shown = stale if stale_only else result["documents"]
        for doc in shown:
            mark = STATUS_MARK.get(doc["status"], doc["status"])
            versions = f"v{doc['bundledVersion'] or '?'}"
            if doc["status"] in ("stale", "ahead"):
                versions += f" -> v{doc['sourceVersion']}"
                by_document[doc["document"]].append(result["bundle"])
            print(f"  {mark} {doc['document']} ({doc['kind']}) {versions}")
        print()

    print("--- Summary ---")
    print(f"Bundles audited: {len(results)}")
    print(f"Bundles with stale documents: {stale_bundles}")
    print(f"Stale document copies: {total_stale}")

    if by_document:
        print("\nDocuments needing rebundling:")
        for name in sorted(by_document):
            bundles = sorted(set(by_document[name]))
            print(f"  {name}: {len(bundles)} bundle(s)")
            for bundle in bundles:
                print(f"    - {bundle}")

    return 1 if total_stale else 0


def main():
    parser = argparse.ArgumentParser(
        description="Audit .keleo bundles for stale embedded document copies"
    )
    parser.add_argument(
        "--bundle", action="append",
        help="Audit a specific bundle (repeatable). Default: all bundles/*.keleo",
    )
    parser.add_argument(
        "--document", action="append",
        help="Only report on documents with these names (repeatable)",
    )
    parser.add_argument(
        "--stale-only", action="store_true",
        help="Show only stale entries and the bundles containing them",
    )
    parser.add_argument(
        "--rebuild", action="store_true",
        help="Repackage bundles that carry stale documents from current on-disk sources",
    )
    parser.add_argument(
        "--bump", choices=["patch", "minor", "major", "none"], default="patch",
        help="Manifest version bump applied on rebuild (default: patch)",
    )
    parser.add_argument(
        "--fix", action="store_true",
        help="Write rebuilt bundles (without it, --rebuild is a dry run)",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    args = parser.parse_args()

    root = get_project_root()

    if args.bundle:
        bundle_paths = [Path(b).resolve() for b in args.bundle]
    else:
        bundle_paths = sorted((root / "bundles").glob("*.keleo"))

    if not bundle_paths:
        print("No .keleo bundles found.", file=sys.stderr)
        return 2

    source_index = build_source_index(root)
    results = [audit_bundle(p, source_index, root) for p in bundle_paths]

    if args.document:
        wanted = set(args.document)
        filtered = []
        for result in results:
            docs = [d for d in result["documents"] if d["document"] in wanted]
            if docs or result.get("error"):
                filtered.append({**result, "documents": docs})
        results = filtered

    if args.rebuild:
        # Naming bundles explicitly is taken as intent to rebuild them,
        # stale or not; a bare --rebuild only touches drifted bundles.
        if args.bundle:
            targets = results
        else:
            targets = [
                r for r in results
                if any(d["status"] == "stale" for d in r["documents"])
            ]
        if not targets:
            print("No stale bundles — nothing to rebuild.")
            return 0

        outcomes = []
        for result in targets:
            keleo_path = root / result["bundle"]
            outcome = rebuild_bundle(
                keleo_path, source_index, root, args.bump, args.fix
            )
            outcomes.append(outcome)
            if args.json:
                continue
            if outcome["status"] == "error":
                print(f"  ERROR   {outcome['bundle']}: {outcome['message']}")
            else:
                verb = "REBUILT" if outcome["status"] == "rebuilt" else "would rebuild"
                carried = outcome.get("carriedOver") or []
                note = f"  (carried over: {', '.join(carried)})" if carried else ""
                print(f"  {verb:<14} {outcome['bundle']}  "
                      f"v{outcome['oldVersion']} -> v{outcome['newVersion']}  "
                      f"({outcome['documents']} docs){note}")

        if args.json:
            print(json.dumps({"rebuilds": outcomes}, indent=2))
        else:
            errors = sum(1 for o in outcomes if o["status"] == "error")
            print(f"\n--- Summary ---\nBundles targeted: {len(outcomes)}  Errors: {errors}")
            if not args.fix:
                print("Dry run. Re-run with --fix to write.")
        return 1 if any(o["status"] == "error" for o in outcomes) else 0

    if args.json:
        stale = sum(
            1 for r in results for d in r["documents"] if d["status"] == "stale"
        )
        print(json.dumps({
            "bundlesAudited": len(results),
            "staleDocumentCopies": stale,
            "results": results,
        }, indent=2))
        return 1 if stale else 0

    return print_report(results, args.stale_only)


if __name__ == "__main__":
    sys.exit(main())
