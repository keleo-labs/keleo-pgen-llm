#!/usr/bin/env python3
"""Inspect .keleo package contents: manifest, documents, versions, dependencies.

Usage:
    python3 utils/inspect-keleo.py bundle.keleo
    python3 utils/inspect-keleo.py bundle.keleo --json
    python3 utils/inspect-keleo.py bundle.keleo --list
"""

import argparse
import json
import sys
import zipfile
from pathlib import Path


def inspect_package(keleo_path):
    """Read and parse a .keleo package, returning structured info."""
    path = Path(keleo_path)
    if not path.exists():
        return None, f"File not found: {path}"
    if not zipfile.is_zipfile(path):
        return None, f"Not a valid ZIP archive: {path}"

    with zipfile.ZipFile(path, "r") as z:
        names = z.namelist()
        if "manifest.json" not in names:
            return None, "No manifest.json found in package"

        manifest = json.loads(z.read("manifest.json"))

        documents = []
        for name in sorted(names):
            if name.startswith("documents/") and name.endswith(".json"):
                try:
                    doc = json.loads(z.read(name))
                    documents.append({
                        "path": name,
                        "name": doc.get("name", "<unnamed>"),
                        "kind": doc.get("kind", "<unknown>"),
                        "version": doc.get("version", ""),
                    })
                except (json.JSONDecodeError, KeyError):
                    documents.append({"path": name, "error": "invalid JSON"})

        assets = [n for n in sorted(names) if n.startswith("assets/")]

    return {
        "file": str(path),
        "manifest": {
            "name": manifest.get("name", ""),
            "version": manifest.get("version", ""),
            "schemaVersion": manifest.get("schemaVersion", ""),
            "description": manifest.get("description", ""),
            "dependencies": manifest.get("dependencies", []),
        },
        "documents": documents,
        "assets": assets,
        "totalFiles": len(names),
    }, None


def main():
    parser = argparse.ArgumentParser(
        description="Inspect .keleo package contents"
    )
    parser.add_argument("file", help=".keleo package file")
    parser.add_argument("--json", action="store_true",
                        help="Output as JSON")
    parser.add_argument("--list", action="store_true",
                        help="List document names only (piping-friendly)")
    args = parser.parse_args()

    info, err = inspect_package(args.file)
    if err:
        print(f"Error: {err}", file=sys.stderr)
        sys.exit(1)

    if args.list:
        for doc in info["documents"]:
            print(doc.get("name", doc.get("path", "")))
        return

    if args.json:
        print(json.dumps(info, indent=2))
        return

    m = info["manifest"]
    print(f"Package: {m['name']}")
    print(f"Version: {m['version']}")
    if m["schemaVersion"]:
        print(f"Schema:  {m['schemaVersion']}")
    if m["description"]:
        print(f"Desc:    {m['description']}")
    print()

    print(f"Documents ({len(info['documents'])}):")
    for doc in info["documents"]:
        if "error" in doc:
            print(f"  {doc['path']} — {doc['error']}")
        else:
            ver = f" v{doc['version']}" if doc["version"] else ""
            print(f"  {doc['kind']:20s} {doc['name']}{ver}")

    if m["dependencies"]:
        print(f"\nDependencies ({len(m['dependencies'])}):")
        for dep in m["dependencies"]:
            pkg = dep.get("packageName", "")
            ver = dep.get("versionRange", "")
            docs = dep.get("documentNames", [])
            print(f"  {pkg} {ver}")
            for d in docs:
                print(f"    - {d}")

    if info["assets"]:
        print(f"\nAssets ({len(info['assets'])}):")
        for a in info["assets"]:
            print(f"  {a}")

    print(f"\nTotal files in archive: {info['totalFiles']}")


if __name__ == "__main__":
    main()
