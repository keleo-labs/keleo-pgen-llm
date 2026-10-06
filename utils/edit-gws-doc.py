#!/usr/bin/env python3
"""Apply find/replace edits to a Google Doc via the gws CLI.

Edits body copy in place, preserving all styling, headings, tables and
links. Intended for copy passes over an already-shared document (style
fixes, terminology changes, repositioning passes) where regenerating the
document from source would lose comments, suggestions and sharing state.

Every edit is verified before and after the write:

  * Pre-flight counts each `find` string across the document text. A string
    that matches nothing is an error by default, because a silent no-op edit
    is the common failure mode of a bulk copy pass.
  * Post-flight re-fetches the document and reports any `find` string that
    survived, which catches ordering collisions between edits.

Usage:
    # Report what would change, write nothing
    python3 utils/edit-gws-doc.py <document-id> --edits edits.json --dry-run

    # Apply the edits
    python3 utils/edit-gws-doc.py <document-id> --edits edits.json

    # Apply and rename the Drive file
    python3 utils/edit-gws-doc.py <document-id> --edits edits.json \
        --rename "Project Keleo: From prototype to strategic capability"

    # Tolerate edits that match nothing (e.g. re-running a partly applied set)
    python3 utils/edit-gws-doc.py <document-id> --edits edits.json --allow-missing

Edits file format — a JSON array, applied in order:

    [
      {"find": "old text", "replace": "new text", "note": "exec summary"},
      {"find": "drop this sentence. ", "replace": "", "note": "cut"}
    ]

`find` edits are case-sensitive by default; set `"matchCase": false` on an
edit to fold case. An empty `replace` deletes the matched text.

Match strings must not span a paragraph break: the Docs API matches within
a single text run sequence, and a newline in `find` will never hit. Edit one
paragraph at a time.

Exit codes: 0 success, 1 pre-flight or post-flight failure, 2 bad input.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

from _shared import GWS as GWS_PATH
TIMEOUT = 120


def run_gws(args, parse=True):
    """Invoke the gws CLI and return parsed JSON, stripping its stdout preamble."""
    result = subprocess.run(
        [GWS_PATH, *args], capture_output=True, text=True, timeout=TIMEOUT
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise RuntimeError(f"gws {' '.join(args[:3])} failed: {detail[:500]}")
    if not parse:
        return result.stdout
    # gws prints "Using keyring backend: ..." before the JSON body.
    raw = result.stdout
    start = next((i for i, ch in enumerate(raw) if ch in "{["), None)
    if start is None:
        return {}
    try:
        return json.loads(raw[start:])
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"gws returned unparseable output: {raw[start:][:300]}"
        ) from exc


def fetch_document(document_id):
    return run_gws(
        ["docs", "documents", "get",
         "--params", json.dumps({"documentId": document_id,
                                 "includeTabsContent": True})]
    )


def _text_runs(node):
    """Yield every textRun content string nested anywhere under `node`."""
    if isinstance(node, dict):
        run = node.get("textRun")
        if isinstance(run, dict) and "content" in run:
            yield run["content"]
        for value in node.values():
            yield from _text_runs(value)
    elif isinstance(node, list):
        for item in node:
            yield from _text_runs(item)


def document_text(document):
    """Return the document's full text, including every tab and table cell."""
    return "".join(_text_runs(document))


def preflight(edits, text, allow_missing):
    """Report what each edit will do. Returns True when all are applicable."""
    ok = True
    print(f"{'#':>3}  {'hits':>4}  edit")
    print("-" * 72)
    for i, edit in enumerate(edits, 1):
        find = edit["find"]
        haystack = text if edit.get("matchCase", True) else text.lower()
        needle = find if edit.get("matchCase", True) else find.lower()
        hits = haystack.count(needle)
        label = edit.get("note") or (find[:52] + ("…" if len(find) > 52 else ""))
        flag = ""
        if hits == 0:
            flag = "  <-- NO MATCH"
            if "\n" in find:
                flag += " (contains a newline; edits cannot span paragraphs)"
            if not allow_missing:
                ok = False
        print(f"{i:>3}  {hits:>4}  {label}{flag}")
    return ok


def build_requests(edits):
    """Translate edits into Docs API requests, preserving file order."""
    return [
        {
            "replaceAllText": {
                "containsText": {
                    "text": edit["find"],
                    "matchCase": edit.get("matchCase", True),
                },
                "replaceText": edit["replace"],
            }
        }
        for edit in edits
    ]


def load_edits(path):
    try:
        edits = json.loads(Path(path).read_text())
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot read edits file {path}: {exc}", file=sys.stderr)
        sys.exit(2)
    if not isinstance(edits, list):
        print("ERROR: edits file must contain a JSON array", file=sys.stderr)
        sys.exit(2)
    for i, edit in enumerate(edits, 1):
        if not isinstance(edit, dict):
            print(f"ERROR: edit {i} must be an object", file=sys.stderr)
            sys.exit(2)
        if "find" not in edit or not edit["find"]:
            print(f"ERROR: edit {i} needs a non-empty 'find' field", file=sys.stderr)
            sys.exit(2)
        if "replace" not in edit:
            print(f"ERROR: edit {i} needs a 'replace' field", file=sys.stderr)
            sys.exit(2)
    return edits


def main():
    parser = argparse.ArgumentParser(
        description="Apply find/replace edits to a Google Doc in place."
    )
    parser.add_argument("document_id", help="Google Docs document ID")
    parser.add_argument("--edits", required=True, help="JSON file of edits")
    parser.add_argument("--dry-run", action="store_true",
                        help="report match counts and exit without writing")
    parser.add_argument("--allow-missing", action="store_true",
                        help="do not fail when an edit matches nothing")
    parser.add_argument("--rename", metavar="TITLE",
                        help="also rename the Drive file to TITLE")
    args = parser.parse_args()

    edits = load_edits(args.edits)

    print(f"Fetching document {args.document_id} ...")
    document = fetch_document(args.document_id)
    text = document_text(document)
    print(f"Title: {document.get('title', '?')}")
    print(f"Body chars: {len(text)}\n")

    if not preflight(edits, text, args.allow_missing):
        print("\nERROR: one or more edits matched nothing. Fix the 'find' strings "
              "or pass --allow-missing.", file=sys.stderr)
        sys.exit(1)

    if args.dry_run:
        print(f"\nDry run: {len(edits)} edit(s) would be applied. Nothing written.")
        return

    print(f"\nApplying {len(edits)} edit(s) ...")
    result = run_gws(
        ["docs", "documents", "batchUpdate",
         "--params", json.dumps({"documentId": args.document_id}),
         "--json", json.dumps({"requests": build_requests(edits)})]
    )
    changed = sum(
        r.get("replaceAllText", {}).get("occurrencesChanged", 0)
        for r in result.get("replies", [])
    )
    print(f"Occurrences changed: {changed}")

    if args.rename:
        run_gws(
            ["drive", "files", "update",
             "--params", json.dumps({"fileId": args.document_id, "fields": "id,name"}),
             "--json", json.dumps({"name": args.rename})]
        )
        print(f"Renamed to: {args.rename}")

    print("\nVerifying ...")
    after = document_text(fetch_document(args.document_id))
    residual = [
        e for e in edits
        if after.count(e["find"]) > 0 and e["find"] not in e["replace"]
    ]
    if residual:
        print(f"WARNING: {len(residual)} edit(s) did not take effect:", file=sys.stderr)
        for e in residual:
            print(f"  - {e.get('note') or e['find'][:60]}", file=sys.stderr)
        sys.exit(1)
    print("All edits verified applied.")


if __name__ == "__main__":
    main()
