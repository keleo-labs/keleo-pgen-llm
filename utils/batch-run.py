#!/usr/bin/env python3
"""Plan and track a tiered, multi-session batch regeneration run.

A full regeneration of a baseline and everything beneath it is too large to
finish in one session: dozens of documents, each needing Phase 1 analysis,
Phase 2 mapping and Phase 3 JSON, in an order the dependency graph fixes. This
utility holds the plan and the progress on disk so a later session can pick the
run up where the last one stopped, and so "what can run in parallel right now"
is answered from the graph rather than from memory.

Work is grouped into units by authoring directory, because Phase 1 analysis is
written per directory (one report covering a method and its member practices)
while Phase 2 and Phase 3 are per document.

Usage:
    # Plan a run from a dependency closure
    python3 utils/batch-run.py runs/sales-regen --init \
        --closure "Red Hat Sales Essentials" --bump major

    # What is ready to start right now
    python3 utils/batch-run.py runs/sales-regen --ready --phase 1
    python3 utils/batch-run.py runs/sales-regen --ready --phase 2

    # Progress overview
    python3 utils/batch-run.py runs/sales-regen --status

    # Record progress
    python3 utils/batch-run.py runs/sales-regen --set-unit crm-foundations --phase 1 --state done
    python3 utils/batch-run.py runs/sales-regen --set-doc "CRM Foundations" --phase 3 --state done
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _shared import increment_version

MANIFEST_NAME = "run-manifest.json"
PHASES = ["1", "2", "3"]
STATES = ["pending", "running", "done", "blocked", "failed", "skipped"]


def _load_closure(root_name, search_dirs):
    """Run the closure command from discover-dependencies as a library call."""
    import importlib.util

    mod_path = Path(__file__).resolve().parent / "discover-dependencies.py"
    spec = importlib.util.spec_from_file_location("discover_dependencies", mod_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    index, _ = mod.build_index(search_dirs)
    return mod.cmd_closure(root_name, index)


def _unit_slug(canonical_path):
    """Authoring directory that owns a document, used as the work-unit key."""
    path = Path(canonical_path)
    return path.parent.name if path.parent.name not in ("", ".") else path.stem


def cmd_init(run_dir, root_name, search_dirs, bump, force):
    """Build a run manifest from the dependency closure under a root."""
    run_path = Path(run_dir)
    manifest_path = run_path / MANIFEST_NAME
    if manifest_path.exists() and not force:
        return {"error": f"Manifest already exists: {manifest_path} (use --force to replace)"}

    closure = _load_closure(root_name, search_dirs)
    if "error" in closure:
        return closure

    units = defaultdict(lambda: {"documents": []})
    for doc in closure["documents"]:
        slug = _unit_slug(doc["canonicalPath"])
        unit = units[slug]
        unit["slug"] = slug
        unit["directory"] = str(Path(doc["canonicalPath"]).parent)
        unit["documents"].append({
            "name": doc["name"],
            "kind": doc["kind"],
            "path": doc["canonicalPath"],
            "tier": doc["tier"],
            "currentVersion": doc["version"],
            "targetVersion": increment_version(doc["version"] or "1.0.0", bump) if bump else None,
            "dependsOn": doc["dependsOn"],
            "duplicatePaths": doc["duplicatePaths"],
            "phase2": "pending",
            "phase3": "pending",
            "validated": "pending",
            "notes": "",
        })

    unit_list = []
    for slug in sorted(units):
        unit = units[slug]
        unit["tier"] = min(d["tier"] for d in unit["documents"])
        unit["phase1"] = "pending"
        unit["documents"].sort(key=lambda d: (d["tier"], d["name"]))
        unit_list.append(unit)
    unit_list.sort(key=lambda u: (u["tier"], u["slug"]))

    manifest = {
        "root": root_name,
        "bump": bump,
        "searchDirs": search_dirs,
        "documentCount": closure["count"],
        "tierCount": closure["tierCount"],
        "unitCount": len(unit_list),
        "units": unit_list,
    }

    run_path.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    manifest["manifestPath"] = str(manifest_path)
    return manifest


def _load_manifest(run_dir):
    manifest_path = Path(run_dir) / MANIFEST_NAME
    if not manifest_path.exists():
        return None, {"error": f"No manifest at {manifest_path} — run --init first"}
    return json.loads(manifest_path.read_text(encoding="utf-8")), None


def _save_manifest(run_dir, manifest):
    (Path(run_dir) / MANIFEST_NAME).write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )


def _doc_index(manifest):
    return {
        doc["name"]: (unit, doc)
        for unit in manifest["units"]
        for doc in unit["documents"]
    }


def cmd_ready(manifest, phase):
    """List the work that can start now, given what is already done.

    Phase 1 needs nothing but an unstarted unit — analysis reads source
    material, not the baseline, so every unit's analysis is independent.
    Phase 2 needs its unit's analysis finished and every in-closure dependency
    through Phase 3, because a mapping resolves against element names that are
    only fixed once the dependency's JSON exists. Phase 3 needs its own mapping.
    """
    docs = _doc_index(manifest)
    ready = []

    if phase == "1":
        for unit in manifest["units"]:
            if unit["phase1"] == "pending":
                ready.append({
                    "unit": unit["slug"],
                    "directory": unit["directory"],
                    "tier": unit["tier"],
                    "documents": [d["name"] for d in unit["documents"]],
                })
        return {"phase": phase, "ready": ready, "count": len(ready)}

    for unit in manifest["units"]:
        for doc in unit["documents"]:
            key = f"phase{phase}"
            if doc[key] != "pending":
                continue
            if phase == "2":
                # "skipped" satisfies the gate as fully as "done". A unit whose
                # analysis was deliberately skipped — a pure-assembly method has
                # no source material of its own to analyse — would otherwise
                # never surface as ready, and six of them sat invisible in this
                # run's manifest. Only an unfinished analysis blocks.
                if unit["phase1"] not in ("done", "skipped"):
                    continue
                blockers = [
                    d for d in doc["dependsOn"]
                    if d in docs and docs[d][1]["phase3"] != "done"
                ]
                if blockers:
                    continue
            elif phase == "3" and doc["phase2"] != "done":
                continue
            ready.append({
                "unit": unit["slug"],
                "document": doc["name"],
                "kind": doc["kind"],
                "path": doc["path"],
                "tier": doc["tier"],
                "targetVersion": doc["targetVersion"],
            })

    return {"phase": phase, "ready": ready, "count": len(ready)}


def cmd_status(manifest):
    """Summarise progress by phase and by tier."""
    counts = defaultdict(lambda: defaultdict(int))
    for unit in manifest["units"]:
        counts["phase1"][unit["phase1"]] += 1
        for doc in unit["documents"]:
            for key in ("phase2", "phase3", "validated"):
                counts[key][doc[key]] += 1

    by_tier = defaultdict(lambda: {"units": 0, "documents": 0, "phase3Done": 0})
    for unit in manifest["units"]:
        by_tier[unit["tier"]]["units"] += 1
        for doc in unit["documents"]:
            by_tier[doc["tier"]]["documents"] += 1
            if doc["phase3"] == "done":
                by_tier[doc["tier"]]["phase3Done"] += 1

    return {
        "root": manifest["root"],
        "bump": manifest.get("bump"),
        "unitCount": manifest["unitCount"],
        "documentCount": manifest["documentCount"],
        "progress": {k: dict(v) for k, v in counts.items()},
        "byTier": {str(t): by_tier[t] for t in sorted(by_tier)},
    }


def cmd_set(manifest, unit_slug, doc_name, phase, state, note):
    """Record a phase state against a unit or a document."""
    key = "validated" if phase == "validated" else f"phase{phase}"

    if unit_slug:
        for unit in manifest["units"]:
            if unit["slug"] == unit_slug:
                if key != "phase1":
                    for doc in unit["documents"]:
                        doc[key] = state
                        if note:
                            doc["notes"] = note
                else:
                    unit[key] = state
                return {"updated": unit_slug, "key": key, "state": state}
        return {"error": f"No such unit: {unit_slug}"}

    docs = _doc_index(manifest)
    if doc_name not in docs:
        return {"error": f"No such document: {doc_name}"}
    unit, doc = docs[doc_name]
    if key == "phase1":
        unit[key] = state
    else:
        doc[key] = state
    if note:
        doc["notes"] = note
    return {"updated": doc_name, "unit": unit["slug"], "key": key, "state": state}


def fmt_init(result):
    lines = [
        f"Run planned for \"{result['root']}\": {result['documentCount']} documents "
        f"in {result['unitCount']} work units across {result['tierCount']} tiers.",
        f"Manifest: {result['manifestPath']}",
    ]
    if result.get("bump"):
        lines.append(f"Version bump: {result['bump']}")
    current_tier = None
    for unit in result["units"]:
        if unit["tier"] != current_tier:
            current_tier = unit["tier"]
            lines.append(f"\nTier {current_tier}:")
        names = ", ".join(d["name"] for d in unit["documents"])
        lines.append(f"  {unit['slug']} ({unit['directory']})")
        lines.append(f"    {names}")
    return "\n".join(lines)


def fmt_ready(result):
    if not result["ready"]:
        return f"Phase {result['phase']}: nothing ready."
    lines = [f"Phase {result['phase']}: {result['count']} ready"]
    for item in result["ready"]:
        if "document" in item:
            lines.append(
                f"  [tier {item['tier']}] {item['document']} ({item['kind']}) "
                f"→ v{item['targetVersion']} — {item['path']}"
            )
        else:
            lines.append(f"  [tier {item['tier']}] {item['unit']} — {item['directory']}")
            lines.append(f"      {', '.join(item['documents'])}")
    return "\n".join(lines)


def fmt_status(result):
    lines = [
        f"Run: {result['root']} (bump={result['bump']})",
        f"{result['unitCount']} units, {result['documentCount']} documents",
        "",
        "Progress:",
    ]
    for key in ("phase1", "phase2", "phase3", "validated"):
        states = result["progress"].get(key, {})
        summary = ", ".join(f"{s}={n}" for s, n in sorted(states.items()))
        lines.append(f"  {key:10} {summary or '(none)'}")
    lines.append("")
    lines.append("By tier (documents through Phase 3):")
    for tier, data in result["byTier"].items():
        lines.append(f"  tier {tier}: {data['phase3Done']}/{data['documents']}")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Plan and track a tiered, multi-session batch regeneration run"
    )
    parser.add_argument("run_dir", help="Directory holding the run manifest")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--init", action="store_true", help="Create a run manifest from a closure")
    group.add_argument("--status", action="store_true", help="Show progress by phase and tier")
    group.add_argument("--ready", action="store_true", help="List work that can start now")
    group.add_argument("--set-unit", metavar="SLUG", nargs="+",
                       help="Record a phase state for one or more work units")
    group.add_argument("--set-doc", metavar="NAME", nargs="+",
                       help="Record a phase state for one or more documents")

    parser.add_argument("--closure", metavar="NAME", help="Root document name (with --init)")
    parser.add_argument("--bump", choices=["patch", "minor", "major"],
                        help="Version bump to plan for each document (with --init)")
    parser.add_argument("--search-dirs", nargs="+", default=["baselines", "practices", "deps"],
                        help="Directories to scan when building the closure")
    parser.add_argument("--force", action="store_true", help="Replace an existing manifest")
    parser.add_argument("--phase", choices=PHASES + ["validated"], help="Phase to query or set")
    parser.add_argument("--state", choices=STATES, help="State to record (with --set-*)")
    parser.add_argument("--note", default="", help="Note to attach (with --set-*)")
    parser.add_argument("--json", action="store_true", help="Output JSON instead of text")
    args = parser.parse_args()

    if args.init:
        if not args.closure:
            parser.error("--init requires --closure NAME")
        result = cmd_init(args.run_dir, args.closure, args.search_dirs, args.bump, args.force)
        print(json.dumps(result, indent=2) if args.json else
              (f"Error: {result['error']}" if "error" in result else fmt_init(result)))
        sys.exit(1 if "error" in result else 0)

    manifest, err = _load_manifest(args.run_dir)
    if err:
        print(json.dumps(err) if args.json else f"Error: {err['error']}")
        sys.exit(1)

    if args.status:
        result = cmd_status(manifest)
        print(json.dumps(result, indent=2) if args.json else fmt_status(result))
        sys.exit(0)

    if args.ready:
        if not args.phase or args.phase == "validated":
            parser.error("--ready requires --phase 1|2|3")
        result = cmd_ready(manifest, args.phase)
        print(json.dumps(result, indent=2) if args.json else fmt_ready(result))
        sys.exit(0)

    if not args.phase or not args.state:
        parser.error("--set-unit/--set-doc require --phase and --state")

    targets = args.set_unit or args.set_doc
    results = [
        cmd_set(manifest, t if args.set_unit else None,
                None if args.set_unit else t, args.phase, args.state, args.note)
        for t in targets
    ]
    failed = [r for r in results if "error" in r]
    if len(failed) < len(results):
        _save_manifest(args.run_dir, manifest)

    if args.json:
        print(json.dumps(results if len(results) > 1 else results[0], indent=2))
    else:
        for r in results:
            print(f"Error: {r['error']}" if "error" in r
                  else f"{r['updated']}: {r['key']} = {r['state']}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
