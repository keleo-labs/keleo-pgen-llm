#!/usr/bin/env python3
"""Convert a Studio MCP get_document response into a local language document."""

import argparse
import json
import re
from pathlib import Path


__version__ = "1.0.0"
CACHE = Path(__file__).resolve().parents[1] / "bundles" / ".studio-documents"
SLUG = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*\Z")
STUDIO_FIELDS = {"id", "bundleSlug", "documentPath", "validationWarnings"}


def materialize(source, cache=CACHE):
    data = json.loads(Path(source).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not data.get("name") or not data.get("version"):
        raise ValueError("Studio response needs a document name and version")
    slug = data.get("bundleSlug", "")
    identifier = data.get("id", "")
    prefix = f"bundle:{slug}/"
    # Studio can report another bundle member in documentPath; id identifies this response.
    if not isinstance(identifier, str) or not identifier.startswith(prefix):
        raise ValueError("Studio response ID does not match its bundle slug")
    # shortcut: cache flattens document paths, extend names if a bundle repeats a basename.
    filename = Path(identifier[len(prefix):]).name
    if not SLUG.fullmatch(slug) or not filename.endswith(".json") or not SLUG.fullmatch(filename):
        raise ValueError("Studio response has an invalid bundle slug or document path")
    if data.get("kind") == "baseline":
        data["kind"] = "practiceBaseline"
        if "baselineDependencyNames" in data:
            dependencies = data.pop("baselineDependencyNames")
            if dependencies:
                data["baselinePracticeNames"] = dependencies
    elif data.get("kind") not in {"practice", "method"}:
        raise ValueError(f"Unsupported Studio document kind: {data.get('kind')}")
    for field in STUDIO_FIELDS:
        data.pop(field, None)
    if Path(cache).is_symlink():
        raise ValueError("Studio cache root is a symlink")
    directory = Path(cache) / slug
    if directory.is_symlink():
        raise ValueError("Studio cache directory is a symlink")
    directory.mkdir(parents=True, exist_ok=True)
    output = directory / filename
    if output.is_symlink():
        raise ValueError("Studio cache document is a symlink")
    temporary = output.with_suffix(".json.tmp")
    if temporary.is_symlink():
        raise ValueError("Studio cache temporary file is a symlink")
    temporary.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(output)
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", help="Raw JSON returned by Studio MCP get_document")
    args = parser.parse_args()
    try:
        print(materialize(args.source))
    except (OSError, ValueError, json.JSONDecodeError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
