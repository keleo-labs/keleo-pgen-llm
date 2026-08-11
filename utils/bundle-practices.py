#!/usr/bin/env python3
"""
Batch-package Practice Language JSON files into .keleo archives.

Scans practice and baseline directories, resolves baseline dependencies,
and creates .keleo packages by calling package-keleo.py for each target.

Usage:
    # Package all practices
    python3 utils/bundle-practices.py

    # Package specific directories
    python3 utils/bundle-practices.py practices/team-topologies practices/red-hat-ai

    # Dry run
    python3 utils/bundle-practices.py --dry-run

    # Include baselines
    python3 utils/bundle-practices.py --include-baselines

    # Output to different directory
    python3 utils/bundle-practices.py -o output/
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _shared import load_json_pair, detect_kind
import importlib
_discover = importlib.import_module("discover-dependencies")
build_index = _discover.build_index
extract_dependency_names = _discover.extract_dependency_names
resolve_name = _discover.resolve_name

PACKAGE_SCRIPT = str(Path(__file__).resolve().parent / "package-keleo.py")


def collect_dependency_paths(file_path, index, embedded_names=None):
    """Resolve all dependency file paths for a practice/method/baseline.

    Follows baseline chains transitively. Includes practice dependencies
    directly (no recursion). Returns (baseline_paths, practice_dep_paths).
    """
    data, err = load_json_pair(file_path)
    if err or not data:
        return [], []

    kind = detect_kind(data)
    skip_names = set(embedded_names or [])
    baselines = []
    practice_deps = []
    visited = set()

    def _collect_baselines(fpath):
        d, e = load_json_pair(fpath)
        if e or not d:
            return
        k = detect_kind(d)
        for name, role in extract_dependency_names(d, k):
            if role != "baselinePractice" or name in visited:
                continue
            visited.add(name)
            match = resolve_name(name, index)
            if match["status"] == "found":
                baselines.append(match["path"])
                _collect_baselines(match["path"])

    _collect_baselines(file_path)

    for name, role in extract_dependency_names(data, kind):
        if role == "practiceDependency" and name not in skip_names and name not in visited:
            visited.add(name)
            match = resolve_name(name, index)
            if match["status"] == "found":
                practice_deps.append(match["path"])

    return baselines, practice_deps


def scan_directory(directory):
    """Scan a directory for practice/method/baseline JSON files."""
    results = []
    for f in sorted(Path(directory).iterdir()):
        if f.suffix != ".json" or f.name.startswith("_") or f.name.startswith("."):
            continue
        if "backup" in f.name.lower() or "temp" in f.name.lower():
            continue
        data, err = load_json_pair(f)
        if err or not data or "name" not in data:
            continue
        kind = detect_kind(data)
        results.append({
            "path": str(f),
            "kind": kind,
            "name": data.get("name", ""),
            "description": data.get("description", ""),
            "version": data.get("version", "1.0.0"),
            "baseline": data.get("baselinePracticeName", ""),
            "hasEmbedded": bool(data.get("practices")),
        })
    return results


def slugify(name):
    slug = name.lower().replace(" ", "-").replace("&", "and")
    safe = "".join(c for c in slug if c.isalnum() or c in "-")
    return "-".join(part for part in safe.split("-") if part)


def plan_directory(directory, files, dep_index):
    """Determine packages to create from a directory's files."""
    packages = []
    methods = [f for f in files if f["kind"] == "method"]
    practices = [f for f in files if f["kind"] == "practice"]
    baselines_list = [f for f in files if f["kind"] == "practiceBaseline"]

    covered_names = set()

    for method in methods:
        slug = slugify(method["name"])

        embedded_names = []
        if method["hasEmbedded"]:
            data, _ = load_json_pair(method["path"])
            if data:
                embedded_names = [p.get("name", "") for p in data.get("practices", [])]
                covered_names.update(embedded_names)

            bl_paths, pd_paths = collect_dependency_paths(
                method["path"], dep_index, embedded_names=embedded_names
            )
            packages.append({
                "type": "from-embedded",
                "slug": slug,
                "method_path": method["path"],
                "baseline_paths": bl_paths,
                "practice_dep_paths": pd_paths,
                "name": method["name"],
                "source": str(directory),
            })
        else:
            bl_paths, pd_paths = collect_dependency_paths(method["path"], dep_index)
            packages.append({
                "type": "standalone",
                "slug": slug,
                "doc_path": method["path"],
                "baseline_paths": bl_paths,
                "practice_dep_paths": pd_paths,
                "name": method["name"],
                "source": str(directory),
            })

    for practice in practices:
        if practice["name"] in covered_names:
            continue
        bl_paths, pd_paths = collect_dependency_paths(practice["path"], dep_index)
        packages.append({
            "type": "standalone",
            "slug": slugify(practice["name"]),
            "doc_path": practice["path"],
            "baseline_paths": bl_paths,
            "practice_dep_paths": pd_paths,
            "name": practice["name"],
            "source": str(directory),
        })

    for baseline in baselines_list:
        bl_paths, _ = collect_dependency_paths(baseline["path"], dep_index)
        packages.append({
            "type": "baseline-only",
            "slug": slugify(baseline["name"]),
            "doc_path": baseline["path"],
            "baseline_paths": bl_paths,
            "name": baseline["name"],
            "source": str(directory),
        })

    return packages


def build_command(pkg, output_dir):
    """Build the package-keleo.py command for a package."""
    output_path = str(Path(output_dir) / f"{pkg['slug']}.keleo")
    bl_paths = pkg.get("baseline_paths", [])
    pd_paths = pkg.get("practice_dep_paths", [])

    if pkg["type"] == "from-embedded":
        cmd = [
            sys.executable, PACKAGE_SCRIPT,
            "--from-embedded", pkg["method_path"],
            "-o", output_path,
        ]
        if bl_paths:
            cmd.extend(["--baseline", bl_paths[0]])
        extras = bl_paths[1:] + pd_paths
        if extras:
            cmd.extend(["--extra-documents", *extras])
        return cmd, output_path

    docs = list(bl_paths) + list(pd_paths) + [pkg["doc_path"]]

    cmd = [
        sys.executable, PACKAGE_SCRIPT,
        "--documents", *docs,
        "--name", pkg["slug"],
        "-o", output_path,
    ]
    return cmd, output_path


def main():
    parser = argparse.ArgumentParser(
        description="Batch-package Practice Language JSON into .keleo archives"
    )
    parser.add_argument("targets", nargs="*",
                        help="Directories or JSON files to package (default: all practices/)")
    parser.add_argument("--include-baselines", action="store_true",
                        help="Also package baselines/ directories")
    parser.add_argument("--dry-run", "-n", action="store_true",
                        help="Show what would be packaged without creating files")
    parser.add_argument("--output", "-o", default="bundles",
                        help="Output directory for .keleo files (default: bundles/)")
    args = parser.parse_args()

    dep_index, _ = build_index(["baselines", "practices", "deps"])

    if args.targets:
        target_dirs = args.targets
    else:
        target_dirs = []
        practices_path = Path("practices")
        if practices_path.is_dir():
            for entry in sorted(practices_path.iterdir()):
                if entry.is_dir() and not entry.name.startswith("."):
                    target_dirs.append(str(entry))
            for f in sorted(practices_path.glob("*.json")):
                if not f.name.startswith("."):
                    target_dirs.append(str(f))
        if args.include_baselines:
            baselines_path = Path("baselines")
            if baselines_path.is_dir():
                for entry in sorted(baselines_path.iterdir()):
                    if entry.is_dir() and not entry.name.startswith("."):
                        target_dirs.append(str(entry))

    all_packages = []
    for target in target_dirs:
        target_path = Path(target)
        if target_path.is_file() and target_path.suffix == ".json":
            data, err = load_json_pair(target)
            if err or not data or "name" not in data:
                continue
            kind = detect_kind(data)
            slug = slugify(data.get("name", target_path.stem))
            if kind == "method" and data.get("practices"):
                embedded_names = [p.get("name", "") for p in data.get("practices", [])]
                bl_paths, pd_paths = collect_dependency_paths(
                    str(target), dep_index, embedded_names=embedded_names
                )
                all_packages.append({
                    "type": "from-embedded",
                    "slug": slug,
                    "method_path": str(target),
                    "baseline_paths": bl_paths,
                    "practice_dep_paths": pd_paths,
                    "name": data.get("name", ""),
                    "source": str(target),
                })
            else:
                bl_paths, pd_paths = collect_dependency_paths(str(target), dep_index)
                all_packages.append({
                    "type": "standalone",
                    "slug": slug,
                    "doc_path": str(target),
                    "baseline_paths": bl_paths,
                    "practice_dep_paths": pd_paths,
                    "name": data.get("name", ""),
                    "source": str(target),
                })
        elif target_path.is_dir():
            files = scan_directory(target)
            if files:
                all_packages.extend(plan_directory(target, files, dep_index))

    if not args.dry_run:
        Path(args.output).mkdir(parents=True, exist_ok=True)

    results = []
    for pkg in all_packages:
        cmd, output_path = build_command(pkg, args.output)

        if args.dry_run:
            results.append({
                "name": pkg["name"],
                "type": pkg["type"],
                "source": pkg["source"],
                "output": output_path,
                "status": "dry-run",
                "command": " ".join(cmd),
            })
            continue

        if pkg["type"] != "baseline-only" and not pkg.get("baseline_paths"):
            results.append({
                "name": pkg["name"],
                "type": pkg["type"],
                "source": pkg["source"],
                "output": output_path,
                "status": "skipped",
                "reason": "No baseline dependencies could be resolved",
            })
            continue

        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode == 0:
            results.append({
                "name": pkg["name"],
                "type": pkg["type"],
                "source": pkg["source"],
                "output": output_path,
                "status": "success",
            })
        else:
            results.append({
                "name": pkg["name"],
                "type": pkg["type"],
                "source": pkg["source"],
                "output": output_path,
                "status": "error",
                "stderr": proc.stderr.strip()[:200],
            })

    success = sum(1 for r in results if r["status"] == "success")
    errors = sum(1 for r in results if r["status"] == "error")
    skipped = sum(1 for r in results if r["status"] == "skipped")
    dry_run = sum(1 for r in results if r["status"] == "dry-run")

    report = {
        "dryRun": args.dry_run,
        "outputDir": args.output,
        "packages": results,
        "summary": {
            "total": len(results),
            "success": success,
            "errors": errors,
            "skipped": skipped,
        },
    }
    print(json.dumps(report, indent=2))

    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
