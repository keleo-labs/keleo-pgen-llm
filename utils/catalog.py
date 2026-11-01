#!/usr/bin/env python3
"""Build and consult private, structure-aware source and practice catalogs."""

import argparse
import hashlib
import json
import posixpath
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.request import urlopen
from zipfile import ZipFile
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "source-catalogs"
VERSION = "1.0.0"
HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
WORDS = re.compile(r"\w+", re.UNICODE)
GOOGLE = re.compile(r"docs\.google\.com/(document|presentation|spreadsheets)/d/([^/]+)")
COLLECTION_KINDS = {"focuses": "focus", "alphas": "alpha", "states": "state",
                    "workProducts": "workProduct", "levelsOfDetail": "levelOfDetail",
                    "activities": "activity", "activitySpaces": "activitySpace",
                    "personas": "persona", "personaGroups": "personaGroup",
                    "patterns": "pattern", "patternViews": "patternView",
                    "patternOrchestrations": "patternOrchestration",
                    "outcomes": "outcome", "narrativeTypes": "narrativeType",
                    "references": "reference", "citations": "citation",
                    "competencies": "competency", "competencyLevels": "competencyLevel",
                    "narrativeElements": "narrativeElement"}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def run(command):
    result = subprocess.run(command, capture_output=True, text=True, timeout=180)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "Extraction failed")
    return result.stdout


def pdf_text(path):
    pages = run(["pdftotext", "-layout", str(path), "-"]).split("\f")
    return "\n\n".join(f"## Page {number}\n{page.strip()}" for number, page in enumerate(pages, 1)
                         if page.strip())


def source_text(uri):
    """Return UTF-8 text with headings; extraction failures never erase a snapshot."""
    match = GOOGLE.search(uri)
    if match:
        kind, identifier = match.groups()
        if kind == "spreadsheets":
            metadata = json.loads(run(["gws", "sheets", "spreadsheets", "get", "--params",
                                       json.dumps({"spreadsheetId": identifier, "fields": "sheets.properties.title"})]))
            blocks = []
            for sheet in metadata.get("sheets", []):
                title = sheet["properties"]["title"]
                values = json.loads(run(["gws", "sheets", "spreadsheets", "values", "get", "--params",
                                         json.dumps({"spreadsheetId": identifier, "range": f"'{title}'"})]))
                blocks.append(f"## {title}\n" + "\n".join(" | ".join(row) for row in values.get("values", [])))
            return "\n\n".join(blocks)
        service, resource, key = ("docs", "documents", "documentId") if kind == "document" else (
            "slides", "presentations", "presentationId")
        payload = run(["gws", service, resource, "get", "--params", json.dumps({key: identifier})])
        with TemporaryDirectory() as temporary:
            path = Path(temporary) / "source.json"
            path.write_text(payload, encoding="utf-8")
            return run([sys.executable, str(ROOT / "utils/extract-gws-text.py"), str(path)])
    if uri.startswith(("https://", "http://")) and Path(uri.split("?", 1)[0]).suffix.lower() in {".docx", ".pptx"}:
        suffix = Path(uri.split("?", 1)[0]).suffix.lower()
        with TemporaryDirectory() as temporary:
            path = Path(temporary) / f"source{suffix}"
            with urlopen(uri, timeout=30) as response:
                path.write_bytes(response.read())
            return source_text(str(path))
    if uri.startswith(("https://", "http://")) and uri.split("?", 1)[0].lower().endswith(".pdf"):
        with TemporaryDirectory() as temporary:
            path = Path(temporary) / "source.pdf"
            with urlopen(uri, timeout=30) as response:
                path.write_bytes(response.read())
            return pdf_text(path)
    if uri.startswith(("https://", "http://")) or uri.lower().endswith((".html", ".htm")):
        return run([sys.executable, str(ROOT / "utils/extract-html-text.py"), uri])
    path = Path(uri).expanduser().resolve()
    suffix = path.suffix.lower()
    if suffix in {".md", ".markdown", ".txt"}:
        return path.read_text(encoding="utf-8-sig")
    if suffix == ".docx":
        return run([sys.executable, str(ROOT / "utils/extract-docx-text.py"), str(path)])
    if suffix == ".pdf":
        return pdf_text(path)
    if suffix == ".pptx":
        ns = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
        with ZipFile(path) as archive:
            slides = sorted((name for name in archive.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)),
                            key=lambda name: int(re.search(r"slide(\d+)", name).group(1)))
            blocks = []
            for number, name in enumerate(slides, 1):
                slide = ElementTree.fromstring(archive.read(name))
                lines = ["".join(node.text or "" for node in paragraph.iter(ns + "t"))
                         for paragraph in slide.iter(ns + "p")]
                relations = posixpath.join(posixpath.dirname(name), "_rels", posixpath.basename(name) + ".rels")
                if relations in archive.namelist():
                    for relation in ElementTree.fromstring(archive.read(relations)):
                        if relation.attrib.get("Type", "").endswith("/notesSlide"):
                            notes = posixpath.normpath(posixpath.join(posixpath.dirname(name), relation.attrib["Target"])).lstrip("/")
                            note = ElementTree.fromstring(archive.read(notes))
                            lines.extend("".join(node.text or "" for node in paragraph.iter(ns + "t"))
                                         for paragraph in note.iter(ns + "p"))
                blocks.append(f"## Slide {number}\n" + "\n".join(line for line in lines if line.strip()))
            return "\n\n".join(blocks)
    raise ValueError(f"Unsupported source format: {uri}")


def sections(text, source_id, revision):
    entries, parents, current = [], [], None
    for line_number, line in enumerate(text.splitlines(), 1):
        heading = HEADING.match(line)
        if heading:
            if current:
                current["text"] = current["text"].strip()
                entries.append(current)
            level, title = len(heading[1]), heading[2]
            parents = parents[:level - 1] + [title]
            locator = title.lower() if title.startswith(("Page ", "Slide ")) else f"line {line_number}"
            current = {"id": f"{source_id}@{revision}#L{line_number}", "path": list(parents),
                       "locator": locator, "text": ""}
        else:
            if current is None:
                current = {"id": f"{source_id}@{revision}#L1", "path": ["Introduction"],
                           "locator": "line 1", "text": ""}
            current["text"] += line + "\n"
    if current:
        current["text"] = current["text"].strip()
        entries.append(current)
    return entries


def source_id(uri):
    location = uri if uri.startswith(("http://", "https://")) else str(Path(uri).expanduser().resolve())
    return digest(location.encode())[:16]


def input_digest(uri, extracted):
    if uri.startswith(("http://", "https://")):
        return digest(extracted.encode())
    return digest(Path(uri).expanduser().resolve().read_bytes())


def add_source(uri, workspace):
    uri = uri if uri.startswith(("http://", "https://")) else str(Path(uri).expanduser().resolve())
    identifier = source_id(uri)
    directory = workspace / identifier
    pointer = directory / "latest.json"
    try:
        text = source_text(uri)
        if not text.strip():
            raise ValueError("Source has no extractable text")
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
        if pointer.exists():
            state = json.loads(pointer.read_text())
            state.update(status="stale", checkedAt=now(), error=str(error))
            pointer.write_text(json.dumps(state, indent=2) + "\n")
            print(f"stale: {uri}: {error}", file=sys.stderr)
            return directory / state["snapshot"]
        raise
    revision = digest(text.encode())
    catalog = {"schemaVersion": VERSION, "source": {"id": identifier, "uri": uri,
               "revision": revision, "inputSha256": input_digest(uri, text)},
               "sections": sections(text, identifier, revision)}
    directory.mkdir(parents=True, exist_ok=True)
    snapshot = directory / f"{revision}.json"
    if not snapshot.exists():
        snapshot.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    pointer.write_text(json.dumps({"snapshot": snapshot.name, "status": "fresh", "checkedAt": now()}, indent=2) + "\n")
    return snapshot


def source_catalogs(workspace, latest_only=False):
    for pointer in workspace.glob("*/latest.json"):
        state = json.loads(pointer.read_text())
        snapshots = [pointer.parent / state["snapshot"]] if latest_only else pointer.parent.glob("*.json")
        for snapshot in snapshots:
            if snapshot.name == "latest.json":
                continue
            effective = state if snapshot.name == state["snapshot"] else {"status": "stale"}
            catalog = json.loads(snapshot.read_text())
            uri = catalog["source"]["uri"]
            if effective["status"] == "fresh" and not uri.startswith(("http://", "https://")):
                try:
                    if input_digest(uri, "") != catalog["source"]["inputSha256"]:
                        effective = {"status": "stale"}
                except OSError:
                    effective = {"status": "stale"}
            yield catalog, effective


def practice_entries(value, pointer="", kind=None):
    if isinstance(value, list):
        for index, child in enumerate(value):
            yield from practice_entries(child, f"{pointer}/{index}", kind)
    elif isinstance(value, dict):
        if kind and value.get("name"):
            content = json.dumps(value, ensure_ascii=False)
            yield {"pointer": pointer, "kind": kind, "name": value["name"],
                   "text": content, "sourceSections": []}
        for key, child in value.items():
            if isinstance(child, (dict, list)):
                escaped = key.replace("~", "~0").replace("/", "~1")
                child_kind = COLLECTION_KINDS.get(key, key[:-1] if isinstance(child, list) and key.endswith("s") else None)
                yield from practice_entries(child, f"{pointer}/{escaped}", child_kind)


def build_practice(path, workspace, links_path=None):
    raw = path.read_bytes()
    document = json.loads(raw)
    output = path.parent / "practice-catalog.json"
    previous = json.loads(output.read_text()) if output.exists() else {}
    old_links = {entry["pointer"]: entry for entry in previous.get("elements", [])}
    links = json.loads(links_path.read_text()) if links_path else {}
    entries = list(practice_entries(document))
    by_pointer = {entry["pointer"]: entry for entry in entries}
    for entry in entries:
        old = old_links.get(entry["pointer"])
        if old and old["name"] == entry["name"] and old["kind"] == entry["kind"]:
            entry["sourceSections"] = old["sourceSections"]
    valid = {section["id"] for catalog, _ in source_catalogs(workspace) for section in catalog["sections"]}
    for pointer, ids in links.items():
        if pointer not in by_pointer:
            raise ValueError(f"Unknown practice element: {pointer}")
        unknown = set(ids) - valid
        if unknown:
            raise ValueError(f"Missing source sections: {', '.join(sorted(unknown))}")
        by_pointer[pointer]["sourceSections"] = ids
    result = {"schemaVersion": VERSION, "practice": {"kind": document["kind"],
              "name": document["name"], "version": document["version"], "sha256": digest(raw),
              "path": path.name}, "elements": entries}
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    return output


def search_practices(query):
    terms = {word.lower() for word in WORDS.findall(query) if len(word) > 1}
    matches = []
    for parent in (ROOT / "practices", ROOT / "baselines"):
        for path in parent.glob("*/practice-catalog.json"):
            catalog = json.loads(path.read_text())
            practice = catalog["practice"]
            current = path.parent / practice["path"]
            if not current.exists() or digest(current.read_bytes()) != practice["sha256"]:
                continue
            for entry in catalog["elements"]:
                body = entry["text"].lower()
                score = sum(5 * entry["name"].lower().count(term) + min(body.count(term), 5)
                            for term in terms)
                if score:
                    matches.append({"practice": practice["name"], "pointer": entry["pointer"],
                                    "name": entry["name"], "kind": entry["kind"],
                                    "sourceSections": entry["sourceSections"], "score": score})
    return sorted(matches, key=lambda item: (-item["score"], item["practice"], item["pointer"]))


def search(workspace, query):
    terms = {word.lower() for word in WORDS.findall(query) if len(word) > 1}
    matches = []
    for catalog, state in source_catalogs(workspace, latest_only=True):
        for section in catalog["sections"]:
            heading, body = " ".join(section["path"]).lower(), section["text"].lower()
            score = sum(5 * heading.count(term) + min(body.count(term), 5) for term in terms)
            if score:
                matches.append({"id": section["id"], "source": catalog["source"]["uri"],
                                "path": section["path"], "score": score, "status": state["status"]})
    return sorted(matches, key=lambda item: (-item["score"], item["id"]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=SOURCE_ROOT)
    commands = parser.add_subparsers(dest="command", required=True)
    add = commands.add_parser("add-source")
    add.add_argument("uri")
    toc = commands.add_parser("toc")
    find = commands.add_parser("search")
    find.add_argument("query")
    find_practice = commands.add_parser("search-practices")
    find_practice.add_argument("query")
    show = commands.add_parser("show")
    show.add_argument("section_id")
    build = commands.add_parser("build-practice")
    build.add_argument("document", type=Path)
    build.add_argument("--links", type=Path, help="JSON map from practice JSON pointers to source section IDs")
    outline = commands.add_parser("outline-practice")
    outline.add_argument("document", type=Path)
    check = commands.add_parser("check-practice")
    check.add_argument("document", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "add-source":
            print(add_source(args.uri, args.workspace))
        elif args.command == "build-practice":
            print(build_practice(args.document, args.workspace, args.links))
        elif args.command == "outline-practice":
            for entry in practice_entries(json.loads(args.document.read_text())):
                print(f"{entry['pointer']}  {entry['kind']}  {entry['name']}")
        elif args.command == "check-practice":
            catalog = json.loads((args.document.parent / "practice-catalog.json").read_text())
            if catalog["practice"]["sha256"] != digest(args.document.read_bytes()):
                raise ValueError("Practice changed since catalog build; rebuild the catalog")
            valid = {section["id"] for source, _ in source_catalogs(args.workspace)
                     for section in source["sections"]}
            for entry in catalog["elements"]:
                if set(entry["sourceSections"]) - valid:
                    raise ValueError(f"Missing source section for {entry['pointer']}")
            print("catalog current")
        elif args.command == "search":
            print(json.dumps(search(args.workspace, args.query)[:10], ensure_ascii=False, indent=2))
        elif args.command == "search-practices":
            print(json.dumps(search_practices(args.query)[:10], ensure_ascii=False, indent=2))
        elif args.command == "toc":
            for catalog, state in source_catalogs(args.workspace, latest_only=True):
                print(f"{catalog['source']['uri']} [{state['status']}]")
                for section in catalog["sections"]:
                    print(f"  {section['id']} {' > '.join(section['path'])}")
        elif args.command == "show":
            for catalog, state in source_catalogs(args.workspace):
                for section in catalog["sections"]:
                    if section["id"] == args.section_id:
                        print(f"{catalog['source']['uri']} [{state['status']}] {section['locator']}\n"
                              f"{' > '.join(section['path'])}\n\n{section['text']}")
                        return
            raise ValueError(f"Section not found: {args.section_id}")
    except (OSError, ValueError, RuntimeError, KeyError, subprocess.TimeoutExpired) as error:
        parser.exit(1, f"error: {error}\n")


if __name__ == "__main__":
    main()
