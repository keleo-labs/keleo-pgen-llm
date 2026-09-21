#!/usr/bin/env python3
"""Test citation URLs and reference URIs; fix or remove broken ones.

Checks every citation with a `url` field and every reference link URI
using HTTP HEAD requests. URLs returning 4xx/5xx are flagged as broken.
In --fix mode, broken URLs are removed from the citation (the citation
itself is preserved unless --remove-citations is also passed, which
removes the entire citation and all citationNames references to it).

Additionally, --check-missing detects citations whose `source` field
suggests a public URL should exist (blogs, press releases, documentation)
but that lack a `url` field.

Usage:
    # Dry-run: report broken URLs (citations + reference URIs)
    python3 utils/fix-citation-urls.py <file.json>

    # Fix: remove broken URL fields from citations
    python3 utils/fix-citation-urls.py <file.json> --fix

    # Fix: remove entire citations with broken URLs (and their references)
    python3 utils/fix-citation-urls.py <file.json> --fix --remove-citations

    # Replace specific broken URLs
    python3 utils/fix-citation-urls.py <file.json> --fix --replace "old-url=new-url"

    # Check for citations missing URLs
    python3 utils/fix-citation-urls.py <file.json> --check-missing

    # Skip reference URI checks (citations only)
    python3 utils/fix-citation-urls.py <file.json> --no-references
"""

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils._shared import load_json


def test_url(url, timeout=10):
    """Test a URL. Returns (ok, status_code, error_message)."""
    if not url or not url.startswith("http"):
        return True, None, None
    try:
        req = urllib.request.Request(url, method="HEAD")
        req.add_header("User-Agent", "PracticeValidator/1.0")
        resp = urllib.request.urlopen(req, timeout=timeout)
        return True, resp.status, None
    except urllib.error.HTTPError as e:
        return False, e.code, str(e)
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return False, None, str(e)


def remove_citation_references(data, citation_name):
    """Remove all citationNames references to a citation throughout the JSON."""
    removed = 0

    def walk(obj):
        nonlocal removed
        if isinstance(obj, dict):
            if "citationNames" in obj and isinstance(obj["citationNames"], list):
                before = len(obj["citationNames"])
                obj["citationNames"] = [
                    cn for cn in obj["citationNames"] if cn != citation_name
                ]
                removed += before - len(obj["citationNames"])
                if not obj["citationNames"]:
                    del obj["citationNames"]
            for v in obj.values():
                walk(v)
        elif isinstance(obj, list):
            for item in obj:
                walk(item)

    walk(data)
    return removed


SOURCE_PATTERNS_EXPECTING_URL = [
    re.compile(r"\bblog\b", re.IGNORECASE),
    re.compile(r"\bpress\s+release\b", re.IGNORECASE),
    re.compile(r"\bdocumentation\b", re.IGNORECASE),
    re.compile(r"\bwebsite\b", re.IGNORECASE),
    re.compile(r"\bweb\s+page\b", re.IGNORECASE),
    re.compile(r"\bonline\b", re.IGNORECASE),
    re.compile(r"\bnewsroom\b", re.IGNORECASE),
]


def check_missing_urls(citations):
    """Detect citations whose source type suggests a public URL should exist."""
    missing = []
    for i, cit in enumerate(citations):
        if cit.get("url"):
            continue
        source = cit.get("source", "")
        for pattern in SOURCE_PATTERNS_EXPECTING_URL:
            if pattern.search(source):
                missing.append({
                    "index": i,
                    "name": cit.get("name", f"citations[{i}]"),
                    "source": source,
                    "matched": pattern.pattern,
                })
                break
    return missing


def collect_reference_uris(data):
    """Collect all URIs from references[].links[] and references[].evidenceBy[].links[]."""
    uris = []
    for ri, ref in enumerate(data.get("references", [])):
        ref_name = ref.get("name", f"references[{ri}]")
        for li, link in enumerate(ref.get("links", [])):
            uri = link.get("uri")
            if uri and uri.startswith("http"):
                uris.append({
                    "path": f"references[{ri}].links[{li}].uri",
                    "ref_name": ref_name,
                    "uri": uri,
                    "obj": link,
                    "field": "uri",
                })
        for ei, ev in enumerate(ref.get("evidenceBy", [])):
            ev_name = ev.get("name", f"evidenceBy[{ei}]")
            for li, link in enumerate(ev.get("links", [])):
                uri = link.get("uri")
                if uri and uri.startswith("http"):
                    uris.append({
                        "path": f"references[{ri}].evidenceBy[{ei}].links[{li}].uri",
                        "ref_name": f"{ref_name} / {ev_name}",
                        "uri": uri,
                        "obj": link,
                        "field": "uri",
                    })
    return uris


def main():
    parser = argparse.ArgumentParser(
        description="Test citation URLs and reference URIs; fix or remove broken ones"
    )
    parser.add_argument("json_file", help="Practice/baseline/method JSON file")
    parser.add_argument("--fix", action="store_true",
                        help="Apply fixes (remove broken URLs or citations)")
    parser.add_argument("--remove-citations", action="store_true",
                        help="Remove entire citations with broken URLs (not just the URL field)")
    parser.add_argument("--replace", action="append", default=[],
                        metavar="OLD=NEW",
                        help="Replace a broken URL with a new one (repeatable)")
    parser.add_argument("--timeout", type=int, default=10,
                        help="HTTP request timeout in seconds (default: 10)")
    parser.add_argument("--check-missing", action="store_true",
                        help="Detect citations missing URLs when source type suggests one should exist")
    parser.add_argument("--no-references", action="store_true",
                        help="Skip reference URI checks (citations only)")
    parser.add_argument("--json", action="store_true",
                        help="Output results as JSON")
    args = parser.parse_args()

    replacements = {}
    for r in args.replace:
        if "=" not in r:
            print(f"Error: --replace value must be 'old=new', got: {r}", file=sys.stderr)
            sys.exit(1)
        old, new = r.split("=", 1)
        replacements[old] = new

    data = load_json(args.json_file)
    citations = data.get("citations", [])
    has_problems = False

    # --- Citation URL checks ---
    cit_results = []
    for i, cit in enumerate(citations):
        url = cit.get("url")
        if not url or not url.startswith("http"):
            continue
        ok, status, error = test_url(url, timeout=args.timeout)
        cit_results.append({
            "index": i,
            "name": cit.get("name", f"citations[{i}]"),
            "url": url,
            "ok": ok,
            "status": status,
            "error": error,
        })

    cit_broken = [r for r in cit_results if not r["ok"]]
    cit_working = [r for r in cit_results if r["ok"]]

    # --- Reference URI checks ---
    ref_results = []
    ref_broken = []
    if not args.no_references:
        ref_uris = collect_reference_uris(data)
        for entry in ref_uris:
            ok, status, error = test_url(entry["uri"], timeout=args.timeout)
            result = {
                "path": entry["path"],
                "ref_name": entry["ref_name"],
                "uri": entry["uri"],
                "ok": ok,
                "status": status,
                "error": error,
                "obj": entry["obj"],
                "field": entry["field"],
            }
            ref_results.append(result)
        ref_broken = [r for r in ref_results if not r["ok"]]

    # --- Missing URL checks ---
    missing_urls = []
    if args.check_missing:
        missing_urls = check_missing_urls(citations)

    # --- JSON output (dry-run) ---
    if args.json and not args.fix:
        output = {
            "citations": {
                "tested": len(cit_results),
                "working": len(cit_working),
                "broken": len(cit_broken),
                "details": cit_results,
            },
        }
        if not args.no_references:
            ref_working = [r for r in ref_results if r["ok"]]
            output["references"] = {
                "tested": len(ref_results),
                "working": len(ref_working),
                "broken": len(ref_broken),
                "details": [{k: v for k, v in r.items() if k not in ("obj", "field")}
                            for r in ref_results],
            }
        if args.check_missing:
            output["missing_urls"] = missing_urls
        print(json.dumps(output, indent=2))
        if cit_broken or ref_broken or missing_urls:
            sys.exit(1)
        return

    # --- Text output ---
    if not args.json:
        if cit_results:
            print(f"Citation URLs: {len(cit_working)} OK, {len(cit_broken)} broken (of {len(cit_results)} tested)\n")
            if cit_working:
                for r in cit_working:
                    print(f"  [  OK] {r['name']}")
                    print(f"         {r['url']}")
            if cit_broken:
                print()
                for r in cit_broken:
                    status_str = f" ({r['status']})" if r['status'] else ""
                    print(f"  [FAIL] {r['name']}{status_str}")
                    print(f"         {r['url']}")
                    if r["error"]:
                        print(f"         {r['error']}")
        elif not citations:
            print("No citations found.")
        else:
            print("No citation URLs to test.")

        if not args.no_references:
            ref_working = [r for r in ref_results if r["ok"]]
            if ref_results:
                print(f"\nReference URIs: {len(ref_working)} OK, {len(ref_broken)} broken (of {len(ref_results)} tested)\n")
                if ref_working:
                    for r in ref_working:
                        print(f"  [  OK] {r['ref_name']}")
                        print(f"         {r['uri']}")
                if ref_broken:
                    print()
                    for r in ref_broken:
                        status_str = f" ({r['status']})" if r['status'] else ""
                        print(f"  [FAIL] {r['ref_name']}{status_str}")
                        print(f"         {r['path']}: {r['uri']}")
                        if r["error"]:
                            print(f"         {r['error']}")
            else:
                print("\nNo reference URIs to test.")

        if args.check_missing and missing_urls:
            print(f"\nCitations missing URLs ({len(missing_urls)}):\n")
            for m in missing_urls:
                print(f"  [MISS] {m['name']}")
                print(f"         source: {m['source']}")

    if not args.fix:
        if cit_broken or ref_broken or missing_urls:
            hints = []
            if cit_broken or ref_broken:
                hints.append("--fix to remove broken URLs")
            if cit_broken:
                hints.append("--fix --remove-citations to remove entire citations")
            print(f"\nRun with {', or '.join(hints)}.")
            sys.exit(1)
        return

    # --- Apply fixes ---
    fixes_applied = 0
    citations_removed = []

    # Fix broken citation URLs
    for r in cit_broken:
        cit = citations[r["index"]]
        url = r["url"]

        if url in replacements:
            new_url = replacements[url]
            new_ok, new_status, new_error = test_url(new_url, timeout=args.timeout)
            if new_ok:
                cit["url"] = new_url
                fixes_applied += 1
                if not args.json:
                    print(f"\n  Replaced URL for '{r['name']}': {new_url}")
                continue
            else:
                if not args.json:
                    print(f"\n  Replacement URL also broken for '{r['name']}': {new_url} ({new_error})")

        if args.remove_citations:
            citations_removed.append(r)
        else:
            if "url" in cit:
                del cit["url"]
                fixes_applied += 1
                if not args.json:
                    print(f"\n  Removed broken URL from '{r['name']}'")

    if citations_removed:
        names_to_remove = {r["name"] for r in citations_removed}
        refs_removed = 0
        for name in names_to_remove:
            refs_removed += remove_citation_references(data, name)

        data["citations"] = [
            c for c in citations if c.get("name") not in names_to_remove
        ]
        fixes_applied += len(citations_removed)

        if not args.json:
            for r in citations_removed:
                print(f"\n  Removed citation '{r['name']}' and {refs_removed} references")

    # Fix broken reference URIs
    ref_fixes = 0
    for r in ref_broken:
        uri = r["uri"]
        if uri in replacements:
            new_uri = replacements[uri]
            new_ok, _, new_error = test_url(new_uri, timeout=args.timeout)
            if new_ok:
                r["obj"][r["field"]] = new_uri
                ref_fixes += 1
                if not args.json:
                    print(f"\n  Replaced URI for '{r['ref_name']}': {new_uri}")
                continue
            else:
                if not args.json:
                    print(f"\n  Replacement URI also broken for '{r['ref_name']}': {new_uri} ({new_error})")
        if not args.json:
            print(f"\n  [SKIP] Cannot auto-fix reference URI '{r['ref_name']}' — use --replace")

    fixes_applied += ref_fixes

    if fixes_applied > 0:
        with open(args.json_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
        if not args.json:
            print(f"\nWrote {fixes_applied} fixes to {args.json_file}")

    if args.json:
        print(json.dumps({
            "citations": {
                "tested": len(cit_results),
                "broken": len(cit_broken),
                "fixed": fixes_applied - ref_fixes,
                "removed_citations": [r["name"] for r in citations_removed],
            },
            "references": {
                "tested": len(ref_results),
                "broken": len(ref_broken),
                "fixed": ref_fixes,
            },
            **({"missing_urls": missing_urls} if args.check_missing else {}),
        }, indent=2))


if __name__ == "__main__":
    main()
