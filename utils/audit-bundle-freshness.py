#!/usr/bin/env python3
"""Audit .keleo bundles for stale embedded document copies.

A .keleo bundle embeds a snapshot of every document it depends on. When a
source document is later fixed on disk, bundles built before the fix keep
carrying the old copy. Loaded together in a library view those stale copies
reintroduce content that was already corrected — wrong aliases, old element
names, superseded states.

This compares each document embedded in each bundle against the current
on-disk version of the document with the same name and kind, and reports drift.

Rebuild mode repackages stale bundles from current on-disk sources, bumping
the manifest version. Documents that exist only inside the bundle (typically
externalized method documents generated at packaging time) are carried over
verbatim, since they reference their practices by name rather than by value.

A rebuild that writes requires an explicit scope: `--bundle`, `--document`, or
`--all`. Without one it refuses and names the count it would have touched. The
default audit is corpus-wide, so an unscoped `--rebuild --fix` inherits that
breadth and repackages every bundle carrying a drifted copy -- which is the
right operation when a shared baseline moves, and the wrong one when a single
practice was updated and the caller is thinking about its bundle alone. The two
read as the same command, so the scope is made explicit rather than assumed.
Dry runs stay unscoped: surveying the whole corpus costs nothing and the survey
is the point.

Usage:
    python3 utils/audit-bundle-freshness.py
    python3 utils/audit-bundle-freshness.py --bundle bundles/red-hat-ai.keleo
    python3 utils/audit-bundle-freshness.py --document "Observability"
    python3 utils/audit-bundle-freshness.py --stale-only --json
    python3 utils/audit-bundle-freshness.py --rebuild            # dry run, corpus-wide
    python3 utils/audit-bundle-freshness.py --rebuild --fix --bundle bundles/x.keleo
    python3 utils/audit-bundle-freshness.py --rebuild --fix --all --bump patch
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
    version_sort_key as parse_version,
    check_dependency_versions,
    version_satisfies_range,
)

SOURCE_DIRS = ["deps", "baselines", "practices"]
__version__ = "1.3.0"
# practiceBaseline before practice before method, so bundles stay topological
# and package-keleo's entry-point rule (method, else last) resolves correctly.
KIND_ORDER = {"practiceBaseline": 0, "practice": 1, "method": 2}


def build_source_index(root):
    """Index documents by (name, kind), keeping the highest version of each."""
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
            key = (name, candidate["kind"])
            existing = index.get(key)
            if existing is None or parse_version(candidate["version"]) > parse_version(
                existing["version"]
            ):
                index[key] = candidate
    return index


def source_for(source_index, name, kind=None):
    """Resolve an exact document identity; never guess across document kinds."""
    if kind:
        return source_index.get((name, kind))
    candidates = [source for (candidate_name, _), source in source_index.items()
                  if candidate_name == name]
    if len(candidates) > 1:
        raise ValueError(f"ambiguous document {name!r}: document kind is required")
    return candidates[0] if candidates else None


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
        source = source_for(source_index, name, detect_kind(doc))

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
                source_data, error = load_json_pair(root / source_path)
                status = "content-differs" if error or source_data != doc else "current"

        entries.append({
            "document": name,
            "kind": detect_kind(doc),
            "bundledVersion": bundled_version,
            "sourceVersion": source_version,
            "sourcePath": source_path,
            "status": status,
        })

    version_findings = []
    for doc in documents:
        for finding in check_dependency_versions(doc, documents):
            version_findings.append({"document": doc.get("name"), **finding})
    manifest = read_manifest(keleo_path) or {}
    for dependency in manifest.get("dependencies", []):
        name = dependency.get("packageName")
        candidates = []
        for candidate in sorted((root / "bundles").glob("*.keleo")):
            identity = (read_manifest(candidate) or {}).get("package", {})
            if identity.get("name") == name:
                candidates.append(identity.get("version", ""))
        if candidates:
            constraint = dependency.get("versionRange", "")
            if any(version_satisfies_range(version, constraint) is True for version in candidates):
                continue
            version = max(candidates, key=parse_version)
            satisfied = version_satisfies_range(version, constraint)
            if satisfied is not True:
                version_findings.append({"severity": "warning", "category": "dependency-version",
                                         "message": f"Package '{name}' at {version}: constraint {constraint} "
                                                    + ("not satisfied" if satisfied is False else "could not be evaluated")})
    return {
        "bundle": str(keleo_path.relative_to(root)),
        "documents": sorted(entries, key=lambda e: e["document"]),
        "versionFindings": version_findings,
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


def stage_bundled_document(keleo_path, document_entry, staging_dir):
    """Extract a bundle-only document to staging. Returns its path, or None."""
    manifest = read_manifest(keleo_path)
    if not manifest:
        return None
    try:
        with zipfile.ZipFile(keleo_path, "r") as zf:
            for entry in manifest.get("documents", []):
                if entry.get("path") != document_entry.get("path"):
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


def manifest_document_names(manifest):
    """The set of document names a manifest lists."""
    present = {
        (entry.get("documentName") or "")
        for entry in manifest.get("documents", [])
    }
    present.discard("")
    return present


def declared_dependencies(path):
    """Every document name one document declares as a dependency."""
    data, err = load_json_pair(path)
    if err or not isinstance(data, dict):
        return []
    declared = [data.get("baselinePracticeName")]
    declared += data.get("practiceDependencyNames") or []
    declared += data.get("baselinePracticeNames") or []
    declared += data.get("practiceNames") or []
    return [name for name in declared if name]


def missing_dependencies(document_paths, present_names):
    """Names the given documents declare that are not in present_names.

    A rebuild repackages the document set the manifest already lists. When an
    entry point gains a dependency after the bundle was built, that set is no
    longer the closure, and repackaging it produces an archive whose entry
    point cannot resolve -- which a later freshness audit then passes, because
    every document the archive does contain is current. Catching it here is
    the difference between the tool reporting what is true and certifying the
    opposite.
    """
    missing = []
    for path in document_paths:
        for name in declared_dependencies(path):
            if name not in present_names and name not in missing:
                missing.append(name)
    return sorted(missing)


def close_over_dependencies(resolved, present, source_index, root):
    """Pull in declared dependencies the bundle lacks, until the set is closed.

    Transitive by construction: a document added to close one gap may declare
    dependencies of its own, so the frontier is recomputed after each pass
    rather than taken once. Names the source index cannot place are left for
    the caller to report -- adding nothing is the honest outcome, since a
    bundle that still cannot resolve its entry point must not be written.

    Added documents sort ahead of the ones already in the manifest, and later
    waves ahead of earlier ones, because each wave is the dependencies of the
    one before it. Order is not cosmetic here: package-keleo takes the last
    document as the entry point where no method is present, so appending a
    dependency to a practice bundle would silently make that dependency the
    entry point.
    """
    added, depth = [], 0
    while True:
        frontier = missing_dependencies([p for _, _, p in resolved], present)
        depth += 1
        wave = []
        for name in frontier:
            source = source_for(source_index, name)
            if source is None:
                continue
            # Negative rank sorts ahead of the manifest's own documents (0), and a
            # deeper wave ahead of the one that pulled it in.
            wave.append((KIND_ORDER.get(source["kind"], 1), -depth, root / source["path"]))
            present.add(name)
            added.append(name)
        if not wave:
            return added
        resolved.extend(wave)


def rebuild_bundle(keleo_path, source_index, root, bump, apply_changes, reclose=False):
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
            kind = entry.get("documentType")
            source = source_for(source_index, name, kind)
            if source:
                resolved.append((KIND_ORDER.get(source["kind"], 1), 0, root / source["path"]))
                continue
            staged = stage_bundled_document(keleo_path, entry, staging)
            if staged is None:
                return {
                    "bundle": rel, "status": "error",
                    "message": f"cannot resolve document {name!r}",
                }
            carried.append(name)
            resolved.append((KIND_ORDER.get(kind, 1), 0, staged))

        present = manifest_document_names(manifest)
        added = close_over_dependencies(resolved, present, source_index, root) if reclose else []

        ordered = [str(p) for _, _, p in sorted(resolved, key=lambda x: (x[0], x[1]))]

        missing = missing_dependencies(ordered, present)
        if missing:
            remedy = (
                ". Those names are not in deps/, baselines/ or practices/, so the "
                "closure cannot be completed from disk. Generate or pull them first"
                if reclose else
                ". A rebuild repackages the documents the bundle already "
                "holds and does not add newly declared ones, so it would "
                "report success on an archive that cannot resolve its own "
                "entry point. Re-run with --reclose to add them from disk"
            )
            return {
                "bundle": rel, "status": "error",
                "message": (
                    "bundle is missing declared dependencies: "
                    + ", ".join(repr(m) for m in missing) + remedy
                ),
                "missingDependencies": missing,
            }

        if not apply_changes:
            return {
                "bundle": rel, "status": "dry-run",
                "oldVersion": old_version, "newVersion": new_version,
                "documents": len(ordered), "carriedOver": carried,
                "addedDependencies": added,
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

        old_entries = {(e.get("documentName"), e.get("documentType"))
                       for e in manifest.get("documents", []) if e.get("entryPoint")}
        rebuilt_manifest = read_manifest(out_tmp) or {}
        new_entries = {(e.get("documentName"), e.get("documentType"))
                       for e in rebuilt_manifest.get("documents", []) if e.get("entryPoint")}
        if old_entries and new_entries != old_entries:
            return {
                "bundle": rel, "status": "error",
                "message": "rebuild would change entry-point document identity; original bundle preserved",
            }
        shutil.move(str(out_tmp), str(keleo_path))
        return {
            "bundle": rel, "status": "rebuilt",
            "oldVersion": old_version, "newVersion": new_version,
            "documents": len(ordered), "carriedOver": carried,
            "addedDependencies": added,
        }
    except ValueError as exc:
        return {"bundle": rel, "status": "error", "message": str(exc)}
    finally:
        shutil.rmtree(staging, ignore_errors=True)


STATUS_MARK = {
    "content-differs": "DIFFERS",
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

        stale = [d for d in result["documents"] if d["status"] in ("stale", "content-differs")]
        if stale_only and not stale and not result.get("versionFindings"):
            continue
        if stale:
            stale_bundles += 1
            total_stale += len(stale)

        print(f"=== {result['bundle']} ===")
        for finding in result.get("versionFindings", []):
            print(f"  WARNING: {finding['message']}")
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

    return 1 if total_stale or any(r.get("error") or r.get("versionFindings") for r in results) else 0


def main():
    parser = argparse.ArgumentParser(
        description="Audit .keleo bundles for stale embedded document copies"
    )
    parser.add_argument("--version", action="version", version=__version__)
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
        "--reclose", action="store_true",
        help="On rebuild, add declared dependencies the bundle lacks from "
             "deps/, baselines/ and practices/, transitively, rather than "
             "refusing. Use when an entry point gained a dependency after "
             "the bundle was built",
    )
    parser.add_argument(
        "--bump", choices=["patch", "minor", "major", "none"], default="patch",
        help="Manifest version bump applied on rebuild (default: patch)",
    )
    parser.add_argument(
        "--all", action="store_true",
        help="Permit an unscoped rebuild to write. Required with --rebuild --fix "
             "when neither --bundle nor --document narrows the target set",
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
                if any(d["status"] in ("stale", "content-differs") for d in r["documents"])
            ]
        if not targets:
            print("No stale bundles — nothing to rebuild.")
            return 0

        # An unscoped rebuild that writes must say so. The audit defaults to the
        # whole corpus, so `--rebuild --fix` after updating one practice looks
        # identical to the deliberate corpus-wide repackage and does the latter.
        # Refuse once, naming the count, rather than reporting the breadth after
        # the archives have already been replaced.
        if args.fix and not args.bundle and not args.document and not args.all:
            print(
                f"REFUSED — an unscoped rebuild would write {len(targets)} bundle(s):",
                file=sys.stderr,
            )
            for result in targets:
                print(f"  {result['bundle']}", file=sys.stderr)
            print(
                "\nNarrow it with --bundle or --document, or pass --all to confirm "
                "you mean every drifted bundle. Drop --fix to dry-run instead.",
                file=sys.stderr,
            )
            return 2

        outcomes = []
        for result in targets:
            keleo_path = root / result["bundle"]
            outcome = rebuild_bundle(
                keleo_path, source_index, root, args.bump, args.fix, args.reclose
            )
            outcomes.append(outcome)
            if args.json:
                continue
            if outcome["status"] == "error":
                print(f"  ERROR   {outcome['bundle']}: {outcome['message']}")
            else:
                verb = "REBUILT" if outcome["status"] == "rebuilt" else "would rebuild"
                notes = []
                if outcome.get("carriedOver"):
                    notes.append("carried over: " + ", ".join(outcome["carriedOver"]))
                if outcome.get("addedDependencies"):
                    notes.append("added: " + ", ".join(outcome["addedDependencies"]))
                note = f"  ({'; '.join(notes)})" if notes else ""
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
            1 for r in results for d in r["documents"] if d["status"] in ("stale", "content-differs")
        )
        print(json.dumps({
            "bundlesAudited": len(results),
            "staleDocumentCopies": stale,
            "results": results,
        }, indent=2))
        return 1 if stale or any(r.get("error") or r.get("versionFindings") for r in results) else 0

    return print_report(results, args.stale_only)


if __name__ == "__main__":
    sys.exit(main())
