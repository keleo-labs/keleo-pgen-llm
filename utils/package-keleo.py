#!/usr/bin/env python3
"""
Create .keleo packages from Practice Language JSON documents.

Bundles baselines, practices, methods, and assets into a ZIP archive
with a PackageManifest (manifest.json) at the root.

Usage:
    # Baseline-only package
    python3 utils/package-keleo.py \\
        --name "platform-adoption-kernel" --version "1.0.0" \\
        --description "Platform Adoption Kernel" \\
        --documents baselines/platform-adoption-kernel.json \\
        -o baselines/platform-adoption-kernel.keleo

    # Practice + baseline package
    python3 utils/package-keleo.py \\
        --name "devsecops" --version "1.0.0" \\
        --description "DevSecOps Practice" \\
        --documents deps/baseline.json practices/devsecops/devsecops.json \\
        -o practices/devsecops/devsecops.keleo

    # Method package (auto-generates externalized method JSON)
    python3 utils/package-keleo.py \\
        --name "platform-engineering" --version "1.0.0" \\
        --description "Platform Engineering Method" \\
        --documents deps/baseline.json practice-1.json practice-2.json \\
        --method-name "Platform Engineering Method" \\
        --method-description "Comprehensive platform engineering methodology" \\
        --method-narrative-file _method-narrative.json \\
        -o platform-engineering.keleo

    # Convert existing embedded method JSON to .keleo
    python3 utils/package-keleo.py \\
        --from-embedded method.json \\
        --baseline deps/baseline.json \\
        -o method.keleo
"""
import argparse
import copy
import json
import os
import sys
import zipfile
from collections import OrderedDict
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils._shared import detect_kind, get_schema_version, load_json


def dedup_by_name(items):
    seen = set()
    result = []
    for item in items:
        name = item.get("name")
        if name and name not in seen:
            seen.add(name)
            result.append(item)
    return result


def collect_file_assets(documents, base_dirs):
    """Find file-based assets across all documents and resolve their paths."""
    asset_files = {}
    for doc in documents:
        for asset in doc.get("assets", []):
            asset_path = asset.get("path")
            if not asset_path:
                continue
            for base_dir in base_dirs:
                full_path = Path(base_dir) / asset_path
                if full_path.exists():
                    asset_files[asset_path] = str(full_path)
                    break
    return asset_files


def build_externalized_method(args, documents):
    """Generate a lightweight externalized method JSON from constituent documents."""
    baseline_name = None
    practice_names = []

    for doc in documents:
        kind = detect_kind(doc)
        if kind == "practiceBaseline":
            baseline_name = doc.get("name")
        elif kind == "practice":
            practice_names.append(doc.get("name"))

    if not baseline_name:
        print("ERROR: No baseline document found among --documents. "
              "Cannot generate method without a baseline.", file=sys.stderr)
        sys.exit(1)

    if not practice_names:
        print("ERROR: No practice documents found among --documents. "
              "Cannot generate method without practices.", file=sys.stderr)
        sys.exit(1)

    all_citations = []
    all_assets = []
    all_domain_tags = set()
    all_lifecycle_tags = set()
    all_org_tags = set()

    for doc in documents:
        if detect_kind(doc) == "practice":
            all_citations.extend(doc.get("citations", []))
            all_assets.extend(doc.get("assets", []))
            tags = doc.get("tags", {})
            all_domain_tags.update(tags.get("domainTags", []))
            all_lifecycle_tags.update(tags.get("lifecycleTags", []))
            all_org_tags.update(tags.get("organizationalTags", []))

    method = OrderedDict()
    method["kind"] = "method"
    method["name"] = args.method_name
    method["description"] = args.method_description or (
        f"Comprehensive methodology combining {len(practice_names)} practices."
    )
    method["baselinePracticeName"] = baseline_name
    method["practiceNames"] = practice_names

    method["tags"] = {
        "domainTags": sorted(all_domain_tags),
        "lifecycleTags": sorted(all_lifecycle_tags),
        "organizationalTags": sorted(all_org_tags),
    }

    if args.method_narrative_file:
        narratives = load_json(args.method_narrative_file)
        if not isinstance(narratives, list):
            narratives = [narratives]
        method["narratives"] = narratives

    method["citations"] = dedup_by_name(all_citations)
    method["assets"] = dedup_by_name(all_assets)

    return method


def convert_embedded_method(method_data, baseline_data):
    """Convert an embedded method JSON to externalized form + separate documents."""
    documents = []

    if baseline_data:
        documents.append(copy.deepcopy(baseline_data))

    embedded_practices = method_data.get("practices", [])
    practice_names = []
    for practice in embedded_practices:
        p = copy.deepcopy(practice)
        if "kind" not in p:
            p["kind"] = "practice"
        documents.append(p)
        practice_names.append(p.get("name", ""))

    externalized = OrderedDict()
    externalized["kind"] = "method"
    externalized["name"] = method_data.get("name", "")
    externalized["description"] = method_data.get("description", "")

    baseline_name = method_data.get("baselinePracticeName")
    if not baseline_name and baseline_data:
        baseline_name = baseline_data.get("name", "")
    if not baseline_name:
        bp = method_data.get("baselinePractice")
        if bp:
            baseline_name = bp.get("name", "")
            documents.insert(0, copy.deepcopy(bp))
    if baseline_name:
        externalized["baselinePracticeName"] = baseline_name

    externalized["practiceNames"] = practice_names

    for key in ("tags", "narratives", "citations", "assets",
                "acknowledgements", "alphaBindings", "assetNames",
                "authors", "version", "createdAt", "updatedAt", "keywords"):
        if key in method_data and key != "practices":
            externalized[key] = method_data[key]

    documents.append(externalized)
    return documents, externalized


def collect_package_dependencies(documents):
    """Build PackageDependency entries from document dependencyVersions.

    Groups document-level version constraints by documentName and produces
    package-level dependency entries with the tightest versionRange found.
    """
    dep_map = OrderedDict()
    doc_names = {doc.get("name") for doc in documents if doc.get("name")}

    for doc in documents:
        for dv in doc.get("dependencyVersions", []):
            dep_name = dv.get("documentName", "")
            version_range = dv.get("versionRange", "")
            if dep_name and dep_name not in doc_names and dep_name not in dep_map:
                dep_map[dep_name] = version_range

    return [
        OrderedDict([("packageName", name), ("versionRange", vr)])
        for name, vr in dep_map.items()
        if vr
    ]


def build_manifest(package_identity, documents_meta, documents=None, dependencies=None):
    """Build a PackageManifest dict.

    Auto-reads schemaVersion from the schema $comment. When documents are
    provided and no explicit dependencies are given, auto-builds package
    dependencies from document-level dependencyVersions.
    """
    manifest = OrderedDict()
    manifest["schemaVersion"] = get_schema_version() or "1.0.0"
    manifest["package"] = package_identity
    manifest["documents"] = documents_meta
    if dependencies:
        manifest["dependencies"] = dependencies
    elif documents:
        auto_deps = collect_package_dependencies(documents)
        if auto_deps:
            manifest["dependencies"] = auto_deps
    return manifest


def doc_filename(doc):
    """Derive a stable filename from a document's name."""
    name = doc.get("name", "unnamed")
    slug = name.lower().replace(" ", "-")
    safe = "".join(c for c in slug if c.isalnum() or c == "-")
    safe = "-".join(part for part in safe.split("-") if part)
    return f"{safe}.json"


def verify_package(output_path):
    """List contents of a .keleo package and verify its manifest."""
    with zipfile.ZipFile(output_path, "r") as zf:
        infos = zf.infolist()
        total_size = sum(i.file_size for i in infos)
        compressed_size = sum(i.compress_size for i in infos)

        print(f"\n--- Package Verification: {output_path} ---")
        print(f"  Files: {len(infos)}")
        print(f"  Size: {compressed_size:,} bytes (compressed), {total_size:,} bytes (uncompressed)")
        print()

        for info in sorted(infos, key=lambda i: i.filename):
            print(f"  {info.file_size:>8,}  {info.filename}")

        if "manifest.json" in zf.namelist():
            manifest = json.loads(zf.read("manifest.json"))
            docs = manifest.get("documents", [])
            print(f"\n  Manifest: {len(docs)} document(s)")
            for doc in docs:
                entry = " [entry]" if doc.get("entryPoint") else ""
                print(f"    {doc.get('documentType', '?'):20s} {doc.get('documentName', '?')}{entry}")
        else:
            print("\n  WARNING: manifest.json not found in package!")

        print("--- End Verification ---\n")


def create_package(output_path, manifest, documents_with_paths, asset_files):
    """Write the .keleo ZIP archive."""
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        manifest_json = json.dumps(manifest, indent=2, ensure_ascii=False)
        zf.writestr("manifest.json", manifest_json)

        for zip_path, doc_data in documents_with_paths:
            doc_json = json.dumps(doc_data, indent=2, ensure_ascii=False)
            zf.writestr(zip_path, doc_json)

        for asset_zip_path, asset_fs_path in asset_files.items():
            if Path(asset_fs_path).exists():
                zf.write(asset_fs_path, asset_zip_path)


def run_bundle(args):
    """Bundle mode: package listed documents into a .keleo file."""
    documents = []
    source_dirs = set()
    for path in args.documents:
        doc = load_json(path)
        documents.append(doc)
        source_dirs.add(str(Path(path).resolve().parent))

    if args.method_name:
        method_doc = build_externalized_method(args, documents)
        documents.append(method_doc)

    if getattr(args, "extra_documents", None):
        existing_names = {d.get("name") for d in documents}
        for path in args.extra_documents:
            doc = load_json(path)
            if doc.get("name") not in existing_names:
                documents.append(doc)
                existing_names.add(doc.get("name"))
                source_dirs.add(str(Path(path).resolve().parent))

    documents_meta = []
    documents_with_paths = []
    seen_filenames = set()
    entry_point_set = False

    for doc in documents:
        kind = detect_kind(doc)
        fname = doc_filename(doc)
        if fname in seen_filenames:
            base, ext = fname.rsplit(".", 1)
            counter = 2
            while f"{base}-{counter}.{ext}" in seen_filenames:
                counter += 1
            fname = f"{base}-{counter}.{ext}"
        seen_filenames.add(fname)

        zip_path = f"documents/{fname}"

        is_entry = False
        if kind == "method":
            is_entry = True
            entry_point_set = True

        documents_meta.append(OrderedDict([
            ("path", zip_path),
            ("documentType", kind),
            ("documentName", doc.get("name", "")),
            ("entryPoint", is_entry),
        ]))
        documents_with_paths.append((zip_path, doc))

    if not entry_point_set and documents_meta:
        documents_meta[-1]["entryPoint"] = True

    package_identity = OrderedDict()
    package_identity["name"] = args.name
    package_identity["version"] = args.version
    package_identity["description"] = args.description or ""
    if args.authors:
        package_identity["authors"] = args.authors
    if args.license:
        package_identity["license"] = args.license

    asset_files = collect_file_assets(documents, source_dirs)
    manifest = build_manifest(package_identity, documents_meta, documents=documents)

    create_package(args.output, manifest, documents_with_paths, asset_files)

    type_counts = {}
    for dm in documents_meta:
        t = dm["documentType"]
        type_counts[t] = type_counts.get(t, 0) + 1

    print(f"Package '{args.name}' v{args.version} created successfully.")
    print(f"  schemaVersion: {manifest.get('schemaVersion', '?')}")
    print(f"  Documents: {len(documents_meta)} ({', '.join(f'{v} {k}' for k, v in type_counts.items())})")
    if manifest.get("dependencies"):
        print(f"  Dependencies: {len(manifest['dependencies'])} package(s)")
    if asset_files:
        print(f"  Assets: {len(asset_files)} files bundled")
    print(f"  Output: {args.output}")


def run_convert(args):
    """Convert an embedded method JSON to a .keleo package."""
    method_data = load_json(args.from_embedded)

    baseline_data = None
    if args.baseline:
        baseline_data = load_json(args.baseline)
    elif method_data.get("baselinePractice"):
        baseline_data = method_data["baselinePractice"]

    documents, externalized = convert_embedded_method(method_data, baseline_data)

    source_dirs = {str(Path(args.from_embedded).resolve().parent)}
    if args.baseline:
        source_dirs.add(str(Path(args.baseline).resolve().parent))

    if getattr(args, "extra_documents", None):
        existing_names = {d.get("name") for d in documents}
        for path in args.extra_documents:
            doc = load_json(path)
            if doc.get("name") not in existing_names:
                documents.insert(-1, doc)
                existing_names.add(doc.get("name"))
                source_dirs.add(str(Path(path).resolve().parent))

    documents_meta = []
    documents_with_paths = []
    seen_filenames = set()

    for doc in documents:
        kind = detect_kind(doc)
        fname = doc_filename(doc)
        if fname in seen_filenames:
            base, ext = fname.rsplit(".", 1)
            counter = 2
            while f"{base}-{counter}.{ext}" in seen_filenames:
                counter += 1
            fname = f"{base}-{counter}.{ext}"
        seen_filenames.add(fname)

        zip_path = f"documents/{fname}"
        is_entry = (doc is externalized)

        documents_meta.append(OrderedDict([
            ("path", zip_path),
            ("documentType", kind),
            ("documentName", doc.get("name", "")),
            ("entryPoint", is_entry),
        ]))
        documents_with_paths.append((zip_path, doc))

    name = externalized.get("name", "package").lower().replace(" ", "-")
    safe_name = "".join(c for c in name if c.isalnum() or c == "-")
    safe_name = "-".join(part for part in safe_name.split("-") if part)

    package_identity = OrderedDict()
    package_identity["name"] = args.name or safe_name
    package_identity["version"] = args.version or "1.0.0"
    package_identity["description"] = args.description or externalized.get("description", "")

    asset_files = collect_file_assets(documents, source_dirs)
    manifest = build_manifest(package_identity, documents_meta, documents=documents)

    create_package(args.output, manifest, documents_with_paths, asset_files)

    practice_count = sum(1 for dm in documents_meta if dm["documentType"] == "practice")
    print(f"Converted embedded method to .keleo package.")
    print(f"  schemaVersion: {manifest.get('schemaVersion', '?')}")
    print(f"  Method: {externalized.get('name', '?')}")
    print(f"  Practices extracted: {practice_count}")
    print(f"  Baseline: {externalized.get('baselinePracticeName', '?')}")
    if manifest.get("dependencies"):
        print(f"  Dependencies: {len(manifest['dependencies'])} package(s)")
    if asset_files:
        print(f"  Assets: {len(asset_files)} files bundled")
    print(f"  Output: {args.output}")


def main():
    parser = argparse.ArgumentParser(
        description="Create .keleo packages from Practice Language JSON documents"
    )

    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--documents", nargs="+",
                      help="JSON document files to bundle into the package")
    mode.add_argument("--from-embedded",
                      help="Convert an existing embedded method JSON to .keleo package")
    mode.add_argument("--verify-only", metavar="KELEO_FILE",
                      help="Verify an existing .keleo package (list contents, no build)")

    parser.add_argument("--name", help="Package name (kebab-case)")
    parser.add_argument("--version", default="1.0.0", help="Package version (semver)")
    parser.add_argument("--description", help="Package description")
    parser.add_argument("--authors", nargs="+", help="Package authors")
    parser.add_argument("--license", help="SPDX license identifier")
    parser.add_argument("--output", "-o", help="Output .keleo file path (required for build modes)")

    parser.add_argument("--method-name",
                        help="Generate an externalized method document with this name")
    parser.add_argument("--method-description",
                        help="Description for the generated method document")
    parser.add_argument("--method-narrative-file",
                        help="JSON file with method-level narrative definitions")

    parser.add_argument("--baseline",
                        help="Baseline JSON file (used with --from-embedded when baseline "
                             "is not embedded in the method)")
    parser.add_argument("--extra-documents", nargs="+",
                        help="Additional JSON documents to include (transitive baselines, "
                             "practice dependencies)")
    parser.add_argument("--verify", action="store_true",
                        help="List package contents after creation to confirm all documents "
                             "are included")

    args = parser.parse_args()

    if args.verify_only:
        verify_package(args.verify_only)
    elif args.documents:
        if not args.output:
            parser.error("--output/-o is required when using --documents mode")
        if not args.name:
            parser.error("--name is required when using --documents mode")
        run_bundle(args)
        if args.verify:
            verify_package(args.output)
    else:
        if not args.output:
            parser.error("--output/-o is required when using --from-embedded mode")
        run_convert(args)
        if args.verify:
            verify_package(args.output)


if __name__ == "__main__":
    main()
