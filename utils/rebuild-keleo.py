#!/usr/bin/env python3
"""Rebuild .keleo packages from their existing manifests using current source files.

Extracts the manifest from each .keleo, locates the current source JSON files
on disk, and rebuilds the package with updated content.

Usage:
    # Rebuild all bundles
    python3 utils/rebuild-keleo.py --all

    # Rebuild specific bundles
    python3 utils/rebuild-keleo.py bundles/scrum-foundations.keleo bundles/team-topologies-v5.keleo

    # Dry run — show what would be rebuilt
    python3 utils/rebuild-keleo.py --all --dry-run

    # Rebuild only bundles whose source files changed since last package
    python3 utils/rebuild-keleo.py --all --if-changed
"""

import argparse
import json
import os
import sys
import zipfile
from pathlib import Path


_SOURCE_CACHE = None


def _build_source_index():
    """Build an index of all practice/baseline JSON files by document name."""
    global _SOURCE_CACHE
    if _SOURCE_CACHE is not None:
        return _SOURCE_CACHE
    _SOURCE_CACHE = {}

    for search_dir in [Path("practices"), Path("baselines")]:
        if not search_dir.exists():
            continue
        for d in search_dir.iterdir():
            if not d.is_dir():
                continue
            for f in d.glob("*.json"):
                if f.name.startswith("_"):
                    continue
                try:
                    data = json.loads(f.read_text())
                    name = data.get("name")
                    if name:
                        _SOURCE_CACHE[name] = str(f)
                except (json.JSONDecodeError, KeyError):
                    pass

    for f in Path("deps").glob("*.json"):
        try:
            data = json.loads(f.read_text())
            name = data.get("name")
            if name:
                _SOURCE_CACHE[name] = str(f)
        except (json.JSONDecodeError, KeyError):
            pass

    return _SOURCE_CACHE


def find_source_file(doc_name, doc_kind):
    """Locate the source JSON file for a document by name and kind."""
    index = _build_source_index()
    if doc_name in index:
        return index[doc_name]
    return None


def extract_manifest(keleo_path):
    """Extract manifest from a .keleo file."""
    with zipfile.ZipFile(keleo_path, "r") as zf:
        with zf.open("manifest.json") as mf:
            return json.load(mf)


def rebuild_keleo(keleo_path, dry_run=False, if_changed=False):
    """Rebuild a single .keleo package."""
    keleo_path = Path(keleo_path)
    try:
        manifest = extract_manifest(keleo_path)
    except (zipfile.BadZipFile, KeyError) as e:
        return {"file": str(keleo_path), "status": "error", "message": str(e)}

    documents = manifest.get("documents", [])
    keleo_mtime = keleo_path.stat().st_mtime

    source_files = []
    missing = []
    any_changed = False

    for doc in documents:
        name = doc.get("documentName", "") or doc.get("name", "")
        kind = doc.get("documentType", "") or doc.get("kind", "")
        src = find_source_file(name, kind)
        if src:
            source_files.append(src)
            if os.path.getmtime(src) > keleo_mtime:
                any_changed = True
        else:
            missing.append(f"{name} ({kind})")

    if missing:
        return {
            "file": str(keleo_path),
            "status": "missing_sources",
            "missing": missing,
            "found": len(source_files),
        }

    if if_changed and not any_changed:
        return {"file": str(keleo_path), "status": "unchanged"}

    if dry_run:
        return {
            "file": str(keleo_path),
            "status": "would_rebuild",
            "documents": len(source_files),
            "sources": source_files,
        }

    entry_doc = None
    for doc in documents:
        if doc.get("entryPoint") or doc.get("entry"):
            entry_doc = doc
            break
    if not entry_doc:
        entry_doc = documents[-1]

    entry_name = entry_doc.get("name", "")
    entry_kind = entry_doc.get("kind", "")

    pkg_name = manifest.get("name", keleo_path.stem)
    pkg_version = manifest.get("version", "1.0.0")
    pkg_description = manifest.get("description", "")
    pkg_authors = manifest.get("authors", ["Keleo"])

    cmd_parts = [
        sys.executable, "utils/package-keleo.py",
        "--documents", *source_files,
        "--name", pkg_name,
        "--version", pkg_version,
        "--description", pkg_description,
        "--authors", *pkg_authors,
        "-o", str(keleo_path),
    ]

    import subprocess
    result = subprocess.run(
        cmd_parts,
        capture_output=True, text=True, cwd=os.getcwd()
    )

    if result.returncode == 0:
        return {
            "file": str(keleo_path),
            "status": "rebuilt",
            "documents": len(source_files),
        }
    else:
        return {
            "file": str(keleo_path),
            "status": "build_error",
            "stderr": result.stderr.strip()[-500:],
        }


def main():
    parser = argparse.ArgumentParser(description="Rebuild .keleo packages from manifests")
    parser.add_argument("files", nargs="*", help=".keleo files to rebuild")
    parser.add_argument("--all", action="store_true", help="Rebuild all bundles in bundles/")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be rebuilt")
    parser.add_argument("--if-changed", action="store_true", help="Only rebuild if sources changed")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    args = parser.parse_args()

    if args.all:
        files = sorted(Path("bundles").glob("*.keleo"))
    elif args.files:
        files = [Path(f) for f in args.files]
    else:
        parser.error("Specify .keleo files or use --all")

    results = []
    for f in files:
        r = rebuild_keleo(f, dry_run=args.dry_run, if_changed=args.if_changed)
        results.append(r)
        if not args.json:
            status = r["status"]
            if status == "rebuilt":
                print(f"  ✓ {r['file']} ({r['documents']} docs)")
            elif status == "would_rebuild":
                print(f"  → {r['file']} ({r['documents']} docs)")
            elif status == "unchanged":
                print(f"  - {r['file']} (unchanged)")
            elif status == "missing_sources":
                print(f"  ✗ {r['file']} — missing: {', '.join(r['missing'])}")
            elif status == "error":
                print(f"  ✗ {r['file']} — {r['message']}")
            elif status == "build_error":
                print(f"  ✗ {r['file']} — build failed: {r.get('stderr', '')[:200]}")

    if args.json:
        json.dump(results, sys.stdout, indent=2)
        print()

    counts = {}
    for r in results:
        counts[r["status"]] = counts.get(r["status"], 0) + 1

    if not args.json:
        print(f"\nSummary: {len(results)} packages")
        for status, count in sorted(counts.items()):
            print(f"  {status}: {count}")


if __name__ == "__main__":
    main()
