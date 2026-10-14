"""Shared utilities for Practice Language JSON tools.

Internal module — not a CLI tool. Import from individual scripts:
    from utils._shared import load_json, merge_by_name, MERGEABLE_ARRAYS
"""

import copy
import json
import os
import shutil
import sys
import zipfile
from collections import OrderedDict
from pathlib import Path

# Google Workspace CLI. Resolved from PATH so non-Homebrew installs (npm, for
# example) work; the Homebrew location is only a last-resort fallback.
GWS = shutil.which("gws") or "/opt/homebrew/bin/gws"


# discover-dependencies.py reports documents that live inside a package as
# "bundles/<name>.keleo::documents/<doc>.json". Resolving that form here means
# every consumer of a resolved path can open it, rather than each one learning
# to read archives separately.
PACKAGE_SEPARATOR = "::"


def split_package_path(file_path):
    """Split "package.keleo::member/path.json" into (archive, member).

    Returns (file_path, None) for an ordinary filesystem path.
    """
    text = str(file_path)
    if PACKAGE_SEPARATOR not in text:
        return text, None
    archive, _, member = text.partition(PACKAGE_SEPARATOR)
    return archive, member or None


def read_package_member(archive_path, member_path):
    """Read one member out of a .keleo archive as text.

    Returns (text, None) on success or (None, error_string) on failure. A bare
    document filename is accepted as well as a full member path, provided it
    matches exactly one member.
    """
    try:
        with zipfile.ZipFile(archive_path, "r") as zf:
            names = zf.namelist()
            if member_path not in names:
                leaf = member_path.rsplit("/", 1)[-1]
                matches = [n for n in names if n.rsplit("/", 1)[-1] == leaf]
                if len(matches) != 1:
                    detail = "not found" if not matches else f"matches {len(matches)} members"
                    return None, f"Member '{member_path}' {detail} in {archive_path}"
                member_path = matches[0]
            return zf.read(member_path).decode("utf-8"), None
    except FileNotFoundError:
        return None, f"File not found: {archive_path}"
    except zipfile.BadZipFile:
        return None, f"Invalid ZIP archive: {archive_path}"


def read_document_text(file_path):
    """Read a document as text from a path or a "package::member" reference.

    Returns (text, None) on success or (None, error_string) on failure.
    """
    archive, member = split_package_path(file_path)
    if member is None:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read(), None
        except FileNotFoundError:
            return None, f"File not found: {file_path}"
    return read_package_member(archive, member)


def load_json(file_path, exit_on_error=True):
    """Load and parse a JSON file, or a document inside a .keleo package.

    Args:
        file_path: Path to JSON file, or "package.keleo::member.json" (str or Path).
        exit_on_error: If True, print error JSON and sys.exit(1) on failure.
                       If False, raise the underlying exception.

    Returns:
        Parsed JSON as dict/list.
    """
    text, err = read_document_text(file_path)
    if err:
        if exit_on_error:
            print(json.dumps({"error": err}))
            sys.exit(1)
        raise FileNotFoundError(err)
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        if exit_on_error:
            print(json.dumps({"error": f"Invalid JSON in {file_path}: {e}"}))
            sys.exit(1)
        raise


def version_sort_key(version_str):
    """Parse a semver-ish string into a comparable tuple. Unparsable sorts lowest.

    Tolerant by design: documents carry shortened forms ("1.0") and the odd
    prerelease suffix, and a version that cannot be read should lose a
    "which is newest" comparison rather than crash it.
    """
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


def load_json_pair(file_path):
    """Load JSON returning (data, error_string) tuple. Never exits.

    Accepts a filesystem path or a "package.keleo::member.json" reference.
    """
    text, err = read_document_text(file_path)
    if err:
        return None, err
    try:
        return json.loads(text), None
    except json.JSONDecodeError as e:
        return None, f"Invalid JSON in {file_path}: {e}"


def resolve_reference_context(practice_path, baseline_data):
    """Return the vocabulary source for name-validation checks.

    Narrative types and competencies are inherited down the whole baseline
    chain, so a leaf baseline sees only its own. Validating against the leaf
    makes every inherited value look invalid, and "fixing" it rewrites valid
    names to bad fuzzy matches.

    `_effective-context.json` already holds the merged vocabulary from every
    baseline and dependency practice, so prefer it whenever it sits beside the
    practice being fixed. Falls back to the supplied baseline when absent.
    """
    if practice_path:
        candidate = os.path.join(os.path.dirname(os.path.abspath(practice_path)),
                                 "_effective-context.json")
        if os.path.exists(candidate):
            data, err = load_json_pair(candidate)
            if data and not err:
                return data, candidate
    return baseline_data, None


MERGEABLE_ARRAYS = [
    "focuses", "alphas", "activitySpaces", "competencies",
    "narrativeTypes", "narratives", "citations", "assets",
    "workProducts", "patterns", "personas", "personaGroups",
    "alphaInstances", "workProductInstances",
    "patternGroups", "outcomes", "acknowledgements", "references",
]


def _stamp_contributor(entry, source):
    """Record `source` as a contributor of `entry`, preserving earlier contributors.

    Sets `_contributingPracticeName` to the most recent contributor (last writer
    wins) and appends to the ordered `_contributingPracticeNames` list. When the
    same element name is declared by several documents, the scalar alone loses
    every contributor but the last — consumers deciding practiceDependencyNames
    must read the list.
    """
    if source is None:
        return
    entry["_contributingPracticeName"] = source
    contributors = entry.get("_contributingPracticeNames") or []
    if source not in contributors:
        contributors = contributors + [source]
    entry["_contributingPracticeNames"] = contributors


def merge_by_name(base_list, overlay_list, base_source=None, overlay_source=None):
    """Merge two lists of objects by 'name' key. Overlay overrides base.

    When source names are provided, stamps _contributingPracticeName (last
    writer) and _contributingPracticeNames (all contributors, in merge order)
    on each element for provenance tracking.
    """
    merged = OrderedDict()
    for item in (base_list or []):
        if "name" in item:
            entry = copy.deepcopy(item)
            if base_source is not None and "_contributingPracticeName" not in entry:
                _stamp_contributor(entry, base_source)
            merged[item["name"]] = entry
    for item in (overlay_list or []):
        if "name" in item:
            if item["name"] in merged:
                existing = merged[item["name"]]
                combined = copy.deepcopy(existing)
                prior = existing.get("_contributingPracticeNames") or []
                combined.update(copy.deepcopy(item))
                if prior:
                    combined["_contributingPracticeNames"] = list(prior)
                _stamp_contributor(combined, overlay_source)
                merged[item["name"]] = combined
            else:
                entry = copy.deepcopy(item)
                _stamp_contributor(entry, overlay_source)
                merged[item["name"]] = entry
    return list(merged.values())


def merge_pattern_groups(base_list, overlay_list, base_source=None, overlay_source=None):
    """Merge PatternGroup lists with entry-level merge by patternName.

    Groups merge by canonical name per merge spec §6.15. Within same-name
    groups, entries merge by patternName with overlay seq taking precedence.
    Unique groups from either side are preserved as-is.
    """
    merged = OrderedDict()
    for item in (base_list or []):
        if "name" in item:
            entry = copy.deepcopy(item)
            if base_source is not None and "_contributingPracticeName" not in entry:
                entry["_contributingPracticeName"] = base_source
            merged[item["name"]] = entry
    for item in (overlay_list or []):
        if "name" in item:
            if item["name"] in merged:
                existing = merged[item["name"]]
                base_entries = OrderedDict()
                for e in existing.get("entries", []):
                    pn = e.get("patternName")
                    if pn:
                        base_entries[pn] = e
                for e in (item.get("entries") or []):
                    pn = e.get("patternName")
                    if pn:
                        base_entries[pn] = copy.deepcopy(e)

                combined = copy.deepcopy(existing)
                overlay_copy = copy.deepcopy(item)
                overlay_copy.pop("entries", None)
                combined.update(overlay_copy)
                combined["entries"] = list(base_entries.values())

                if overlay_source is not None:
                    combined["_contributingPracticeName"] = overlay_source
                merged[item["name"]] = combined
            else:
                entry = copy.deepcopy(item)
                if overlay_source is not None:
                    entry["_contributingPracticeName"] = overlay_source
                merged[item["name"]] = entry
    return list(merged.values())


def finalize_variants(effective):
    """Post-merge variant aggregation per merge.md §7.2a (alphas) and §7.2b (work products).

    Walks alphas and work products with mapsTo, appends the full variant object
    to the target element's variants array. Variants remain in the top-level
    array as authored elements; the variants array on the parent is additive
    for UI rendering and taxonomy discovery.
    """
    for array_key in ("alphas", "workProducts"):
        items = effective.get(array_key, [])
        if not items:
            continue
        by_name = {item["name"]: item for item in items if "name" in item}
        for item in items:
            target_name = item.get("mapsTo")
            if target_name and target_name in by_name:
                target = by_name[target_name]
                variants = target.setdefault("variants", [])
                if not any(v.get("name") == item["name"] for v in variants):
                    variants.append(copy.deepcopy(item))


def load_json_from_keleo(keleo_path, document_name=None, document_type=None):
    """Load a JSON document from a .keleo ZIP archive.

    Returns (data, None) on success or (None, error_string) on failure.
    If document_name is provided, matches against manifest documentName.
    If document_type is provided, filters by documentType.
    If neither is provided, returns the entry-point document.
    """
    try:
        with zipfile.ZipFile(keleo_path, "r") as zf:
            if "manifest.json" not in zf.namelist():
                return None, f"No manifest.json in {keleo_path}"
            manifest = json.loads(zf.read("manifest.json"))
            documents = manifest.get("documents", [])
            if not documents:
                return None, f"No documents in manifest of {keleo_path}"

            target = None
            for doc in documents:
                if document_name and doc.get("documentName") == document_name:
                    if document_type is None or doc.get("documentType") == document_type:
                        target = doc
                        break
                elif document_type and doc.get("documentType") == document_type:
                    target = doc
                    break

            if target is None:
                for doc in documents:
                    if doc.get("entryPoint"):
                        target = doc
                        break

            if target is None:
                target = documents[0]

            zip_path = target.get("path", "")
            if zip_path not in zf.namelist():
                return None, f"Document path {zip_path} not found in {keleo_path}"

            data = json.loads(zf.read(zip_path))
            return data, None
    except zipfile.BadZipFile:
        return None, f"Invalid ZIP archive: {keleo_path}"
    except json.JSONDecodeError as e:
        return None, f"Invalid JSON in {keleo_path}: {e}"


def load_all_from_keleo(keleo_path):
    """Load all JSON documents from a .keleo ZIP archive.

    Returns (list_of_dicts, None) on success or (None, error_string) on failure.
    """
    try:
        with zipfile.ZipFile(keleo_path, "r") as zf:
            if "manifest.json" not in zf.namelist():
                return None, f"No manifest.json in {keleo_path}"
            manifest = json.loads(zf.read("manifest.json"))
            documents = manifest.get("documents", [])
            if not documents:
                return None, f"No documents in manifest of {keleo_path}"

            result = []
            for doc_entry in documents:
                zip_path = doc_entry.get("path", "")
                if zip_path not in zf.namelist():
                    continue
                data = json.loads(zf.read(zip_path))
                result.append(data)
            return result, None
    except zipfile.BadZipFile:
        return None, f"Invalid ZIP archive: {keleo_path}"
    except json.JSONDecodeError as e:
        return None, f"Invalid JSON in {keleo_path}: {e}"



def detect_kind(data):
    """Classify JSON by schema discrimination rules."""
    kind = data.get("kind", "")
    if kind in ("practice", "method", "practiceBaseline"):
        return kind
    if any(key in data for key in ("practices", "practiceNames", "baselinePractice")):
        return "method"
    if "baselinePracticeName" in data:
        return "practice"
    return "practiceBaseline"


def get_project_root():
    """Find the project root directory (containing .claude/ or CLAUDE.md)."""
    current = Path(__file__).resolve().parent.parent
    for ancestor in [current] + list(current.parents):
        if (ancestor / ".claude").is_dir() or (ancestor / "CLAUDE.md").is_file():
            return ancestor
    return current


def load_user_config():
    """Load user config from .claude/user-config.json. Returns dict (empty if missing)."""
    config_path = get_project_root() / ".claude" / "user-config.json"
    if not config_path.exists():
        return {}
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_user_config(config):
    """Save user config to .claude/user-config.json."""
    config_path = get_project_root() / ".claude" / "user-config.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
        f.write("\n")


def get_schema_version(schema_path=None):
    """Extract schemaVersion from the schema's $comment field.

    Returns the version string (e.g. '1.0.0') or None if not found.
    """
    if schema_path is None:
        schema_path = Path(__file__).resolve().parent.parent / "deps" / "language.schema.json"
    try:
        data = load_json(schema_path, exit_on_error=False)
        comment = data.get("$comment", "")
        if comment.startswith("schemaVersion:"):
            return comment.split(":", 1)[1].strip()
    except Exception:
        pass
    return None


def increment_version(version_str, bump="patch"):
    """Increment a semver version string.

    Args:
        version_str: Current version (e.g. '1.0.0', '1.0', '2').
        bump: 'patch', 'minor', or 'major'.

    Returns:
        Incremented three-part semver string.
    """
    parts = (version_str or "1.0.0").split(".")
    while len(parts) < 3:
        parts.append("0")
    major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])

    if bump == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump == "minor":
        minor += 1
        patch = 0
    else:
        patch += 1

    return f"{major}.{minor}.{patch}"


def build_dependency_versions(data):
    """Build dependencyVersions array from a document's declared dependencies.

    Scans the document's dependency declarations (baselinePracticeName,
    practiceDependencyNames, practiceNames) and builds version constraint
    entries using caret ranges from resolved dependency versions.

    Args:
        data: The document dict.

    Returns:
        List of DocumentVersionConstraint dicts, or empty list.
    """
    constraints = []
    seen = set()

    dep_names = []
    bpn = data.get("baselinePracticeName")
    if bpn:
        dep_names.append(bpn)
    dep_names.extend(data.get("practiceDependencyNames", []))
    dep_names.extend(data.get("practiceNames", []))
    for bpn_entry in data.get("baselinePracticeNames", []):
        dep_names.append(bpn_entry)

    for name in dep_names:
        if name and name not in seen:
            seen.add(name)
            constraints.append({
                "documentName": name,
                "versionRange": "",
            })

    return constraints
