#!/usr/bin/env python3
"""Export authored Keleo documents and their Studio GAS practice context as Markdown."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path, PurePosixPath
from zipfile import BadZipFile, ZipFile

import _shared
from notebook_markdown import render


__version__ = "1.0.0"
DEFAULT_STUDIO = Path(__file__).resolve().parents[2] / "keleo-studio-gas"
KINDS = {"practice", "method", "practiceBaseline", "baseline"}


def slug(value):
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "document"


@dataclass(eq=False)
class Document:
    data: dict
    source: str
    bundle: Path
    package: dict
    implied_kind: str = ""
    implied_version: str = ""

    def __post_init__(self):
        if (not isinstance(self.data, dict) or
                self.data.get("kind", self.implied_kind) not in KINDS or
                any(not isinstance(value, str) or not value.strip()
                    for value in (self.data.get("name"), self.version))):
            raise ValueError(f"{self.source}: expected a practice, baseline or method with a name and version")

    @property
    def name(self):
        return self.data["name"]

    @property
    def kind(self):
        kind = self.data.get("kind", self.implied_kind)
        return "baseline" if kind == "practiceBaseline" else kind

    @property
    def version(self):
        return self.data.get("version", self.implied_version)

    @property
    def filename(self):
        version = self.version if re.fullmatch(r"[A-Za-z0-9.+-]+", self.version) else slug(self.version)
        return f"{self.kind}-{slug(self.name)}-v{version}.md"


def read_input(spec):
    """Return requested entry points and available documents, preserving bundle identity."""
    filename, member = _shared.split_package_path(spec)
    path = Path(filename).resolve()
    if path.suffix != ".keleo":
        if member is not None or path.suffix != ".json":
            raise ValueError(f"Expected a JSON file or .keleo bundle: {spec}")
        data = _shared.load_json(path, exit_on_error=False)
        inferred = _shared.detect_kind(data) if isinstance(data, dict) else ""
        doc = Document(data, path.name, path, {}, inferred)
        return [doc], [doc]

    with ZipFile(path) as archive:
        manifest = json.loads(archive.read("manifest.json"))
        documents, selected, seen = [], [], set()
        members = Counter(archive.namelist())
        for entry in manifest["documents"]:
            relative = entry["path"]
            parts = PurePosixPath(relative).parts
            if (relative in seen or len(parts) < 2 or parts[0] != "documents" or
                    ".." in parts or "\\" in relative or not relative.endswith(".json") or
                    members[relative] != 1):
                raise ValueError(f"{path.name}: invalid or missing manifest member {relative}")
            seen.add(relative)
            if entry["documentType"] not in KINDS:
                continue
            doc = Document(json.loads(archive.read(relative)), f"{path.name}::{relative}", path, manifest,
                           entry["documentType"])
            declared_kind = "baseline" if entry["documentType"] == "practiceBaseline" else entry["documentType"]
            if (doc.name, doc.kind) != (entry["documentName"], declared_kind):
                raise ValueError(f"{doc.source}: name or kind differs from the manifest")
            documents.append(doc)
            if relative == member or member is None and entry.get("entryPoint", False):
                selected.append(doc)
    if member is not None and not selected:
        raise ValueError(f"{spec}: selected member is absent or has an unsupported kind")
    return selected, documents


def embedded(doc):
    records = [(record, "practice") for record in doc.data.get("practices", [])]
    if doc.data.get("baselinePractice"):
        records.append((doc.data["baselinePractice"], "baseline"))
    return [Document(record, f"{doc.source} (embedded {record['name']})", doc.bundle, doc.package,
                     kind, doc.version)
            for record, kind in records]


def dependencies(doc):
    data = doc.data
    if doc.kind == "method" and data.get("baselinePractice"):
        yield data["baselinePractice"]["name"], "baseline"
    if data.get("baselinePracticeName"):
        yield data["baselinePracticeName"], "baseline"
    for name in data.get("baselinePracticeNames", data.get("baselineDependencyNames", [])):
        yield name, "baseline"
    for name in data.get("practiceDependencyNames", []):
        yield name, "practice"


@lru_cache(maxsize=1)
def semver_cli():
    """Use npm's installed node-semver implementation for manifest ranges."""
    try:
        result = subprocess.run(["npm", "root", "--global"], capture_output=True,
                                check=True, text=True, timeout=10)
    except (FileNotFoundError, subprocess.SubprocessError) as error:
        raise RuntimeError("npm is required to resolve declared semantic version ranges.") from error
    modules = Path(result.stdout.strip())
    for path in (modules / "npm/node_modules/semver/bin/semver.js", modules / "semver/bin/semver.js",
                 Path("/usr/share/nodejs/semver/bin/semver.js")):
        if path.is_file():
            return path
    raise RuntimeError("Cannot locate node-semver in this npm installation.")


@lru_cache(maxsize=4096)
def matches_range(version, constraint):
    parts = re.fullmatch(r"v?(\d+(?:\.\d+){0,2})([-+].*)?", version)
    if not parts:
        return False
    core, suffix = parts.groups()
    normalized = ".".join(str(int(part)) for part in core.split("."))
    normalized += ".0" * (2 - normalized.count(".")) + (suffix or "")
    try:
        result = subprocess.run(["node", str(semver_cli()), "--range", constraint, "--", normalized],
                                capture_output=True, text=True, timeout=10)
    except (FileNotFoundError, subprocess.TimeoutExpired) as error:
        raise RuntimeError("Node.js is required to resolve declared semantic version ranges.") from error
    return result.returncode == 0 and bool(result.stdout.strip())


def select(owner, name, kind, pool, local):
    candidates = [d for d in pool if d.name == name and d.kind == kind]
    preferred = [d for d in local if d.name == name and d.kind == kind]
    ranges = [item["versionRange"] for item in owner.data.get("dependencyVersions", [])
              if item["documentName"] == name]
    package_constraints = owner.package.get("dependencies", [])
    candidates = list(dict.fromkeys([*preferred, *candidates]))
    applicable = [item for item in package_constraints
                  if name in item.get("documentNames", [])]
    valid = []
    for candidate in candidates:
        package = candidate.package.get("package", {})
        constraints = [item for item in package_constraints
                       if item["packageName"] == package.get("name")
                       and ("documentNames" not in item or name in item["documentNames"])]
        if candidate.bundle != owner.bundle and applicable and not constraints:
            continue
        if (all(matches_range(candidate.version, term) for term in ranges)
                and all(matches_range(package.get("version", ""), item["versionRange"])
                        for item in constraints)):
            valid.append(candidate)
    if not valid:
        option = f" (required version: {', '.join(ranges)})" if ranges else ""
        details = "missing" if not candidates else "no candidate matches the declared constraints"
        raise ValueError(f"{kind} {name!r} {details}{option}")
    for tier in (preferred, [d for d in valid if d.bundle == owner.bundle], valid):
        matches = [d for d in tier if d in valid]
        if matches:
            break
    first = matches[0]
    if any(doc.data != first.data for doc in matches[1:]):
        options = ", ".join(f"{doc.source} v{doc.version}" for doc in matches)
        raise ValueError(f"{kind} {name!r} is ambiguous: {options}")
    return first


def method_members(doc, pool, local):
    names = doc.data.get("practiceNames", [item["name"] for item in doc.data.get("practices", [])])
    try:
        return [select(doc, name, "practice", pool, local) for name in names]
    except ValueError as error:
        raise ValueError(f"Method {doc.name!r} requires {error}") from error


def graph(root, pool, local, members=()):
    """Build the exact name library the GAS resolver receives for this root."""
    resolved = {root.name: root}
    edges = defaultdict(list)
    issues = []
    active = []
    complete = set()
    root_members = {member.name: member for member in members}

    def visit(doc):
        if doc in complete:
            return
        active.append(doc)
        requests = list(dependencies(doc))
        if doc is root:
            requests.extend((member.name, "practice") for member in members)
        for name, kind in dict.fromkeys(requests):
            try:
                if doc is root and kind == "practice" and name in root_members:
                    candidate = root_members[name]
                else:
                    candidate = select(doc, name, kind, pool, local)
                if candidate in active or any(item.name == name for item in active):
                    cycle = " → ".join([*(item.name for item in active), name])
                    raise ValueError(f"dependency cycle {cycle}")
                if name in resolved and resolved[name].data != candidate.data:
                    raise ValueError(f"multiple versions or definitions of {name!r} in one Studio view")
                candidate = resolved.setdefault(name, candidate)
            except ValueError as error:
                issues.append(f"{doc.name}: {error}")
                continue
            edges[doc].append(candidate)
            visit(candidate)
        active.pop()
        complete.add(doc)

    visit(root)
    return resolved, edges, list(dict.fromkeys(issues))


def studio_view(doc, library, studio_dir):
    harness = studio_dir / "utils/merge-practice.mjs"
    if not harness.is_file():
        raise ValueError(f"Studio GAS merger not found at {harness}. Supply --studio-gas-dir.")
    with tempfile.TemporaryDirectory(prefix="notebook-studio-") as directory:
        for index, item in enumerate(library.values()):
            data = {"kind": item.kind, "version": item.version, **item.data}
            if item.kind == "baseline" and data.get("baselineDependencyNames") and not data.get("baselinePracticeNames"):
                data = {**data, "baselinePracticeNames": data["baselineDependencyNames"]}
            (Path(directory) / f"{index}.json").write_text(json.dumps(data), encoding="utf-8")
        try:
            result = subprocess.run(
                ["node", str(harness), directory, doc.name, "--json"],
                check=True, capture_output=True, text=True, encoding="utf-8", timeout=60)
        except subprocess.CalledProcessError as error:
            raise ValueError(f"Studio GAS could not resolve {doc.name}: {error.stderr.strip()}") from error
        except subprocess.TimeoutExpired as error:
            raise ValueError(f"Studio GAS timed out resolving {doc.name}") from error
        except FileNotFoundError as error:
            raise ValueError("Node.js is required to run the Studio GAS merger.") from error
    diagnostics = "\n".join(line for line in result.stderr.splitlines()
                            if line.strip() and not line.lstrip().startswith("at "))
    return json.loads(result.stdout), diagnostics


def export(inputs, dependencies_paths, output_dir, studio_dir):
    roots, pool = [], []
    for spec in inputs:
        entries, docs = read_input(spec)
        if not entries:
            raise ValueError(f"{spec} has no supported entry point. Select an exact archive member with ::documents/….json.")
        roots.extend(entries)
        pool.extend(doc for doc in docs if not any(
            row.source == doc.source and row.bundle == doc.bundle for row in pool))
    for spec in dependencies_paths:
        entries, docs = read_input(spec)
        pool.extend(entries if "::" in spec else docs)

    selections = {}
    methods = {}
    for root in roots:
        local = embedded(root) if root.kind == "method" else []
        members = method_members(root, pool, local) if root.kind == "method" else []
        if root.kind == "method":
            methods[root] = members
        for doc in [root, *members]:
            current = selections.get(doc.filename)
            if current is not None:
                prior, prior_local = current
                if (prior.data != doc.data or prior.bundle != doc.bundle
                        or ([d.data for d in prior_local] != [d.data for d in local]
                            and prior_local and local)):
                    raise ValueError(f"Output name collision or different Studio contexts: {doc.filename}")
                if local and not prior_local:
                    selections[doc.filename] = (doc, local)
            else:
                selections[doc.filename] = (doc, local)

    prepared = {}
    for doc, local in selections.values():
        library, edges, issues = graph(doc, pool, local, methods.get(doc, []))
        view, diagnostics = (None, "")
        if doc.kind != "method":
            view, diagnostics = studio_view(doc, library, studio_dir)
        prepared[doc] = (library, edges, issues, view, diagnostics)

    outputs = {}
    for filename, (doc, _) in selections.items():
        library, edges, issues, view, diagnostics = prepared[doc]
        members = methods.get(doc, [])
        views = [(member, prepared[selections[member.filename][0]][3]) for member in members]
        outputs[filename] = render(doc, view, library, edges, issues, diagnostics, views, selections)

    output_dir.mkdir(parents=True, exist_ok=True)
    if any((output_dir / name).exists() or (output_dir / name).is_symlink() for name in outputs):
        raise ValueError(f"An export file already exists in {output_dir}. Choose an empty export directory.")
    with tempfile.TemporaryDirectory(dir=output_dir, prefix=".notebook-") as directory:
        stage = Path(directory)
        for name, contents in outputs.items():
            (stage / name).write_text(contents, encoding="utf-8")
        linked = []
        try:
            for name in outputs:
                # A hard link publishes a complete file and refuses a concurrent overwrite.
                os.link(stage / name, output_dir / name)
                linked.append(name)
        except OSError:
            for name in linked:
                target = output_dir / name
                if target.exists() and os.path.samestat(target.lstat(), (stage / name).stat()):
                    target.unlink()
            raise
    return [output_dir / name for name in outputs]


def main():
    parser = argparse.ArgumentParser(description=__doc__, epilog="Select an exact bundle member with archive.keleo::documents/member.json.")
    parser.add_argument("sources", nargs="+", help="Root JSON files, .keleo bundles or exact archive members")
    parser.add_argument("--dependency", action="append", default=[], help="Additional JSON file, bundle or exact archive member")
    parser.add_argument("--output-dir", required=True, type=Path, help="Directory for the Markdown sources")
    parser.add_argument("--studio-gas-dir", default=DEFAULT_STUDIO, type=Path, help="Trusted keleo-studio-gas checkout")
    parser.add_argument("--version", action="version", version=__version__)
    args = parser.parse_args()
    try:
        for path in export(args.sources, args.dependency, args.output_dir, args.studio_gas_dir.resolve()):
            print(path)
    except (OSError, ValueError, TypeError, KeyError, RuntimeError, BadZipFile) as error:
        parser.exit(1, f"error: {error}\n")


if __name__ == "__main__":
    main()
