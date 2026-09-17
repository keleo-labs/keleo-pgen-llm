#!/usr/bin/env python3
"""Test citation URLs and fix or remove broken ones.

Checks every citation with a `url` field using HTTP HEAD requests.
URLs returning 4xx/5xx are flagged as broken. In --fix mode, broken
URLs are removed from the citation (the citation itself is preserved
unless --remove-citations is also passed, which removes the entire
citation and all citationNames references to it).

Usage:
    # Dry-run: report broken URLs
    python3 utils/fix-citation-urls.py <file.json>

    # Fix: remove broken URL fields from citations
    python3 utils/fix-citation-urls.py <file.json> --fix

    # Fix: remove entire citations with broken URLs (and their references)
    python3 utils/fix-citation-urls.py <file.json> --fix --remove-citations

    # Replace specific broken URLs
    python3 utils/fix-citation-urls.py <file.json> --fix --replace "old-url=new-url"
"""

import argparse
import json
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


def main():
    parser = argparse.ArgumentParser(
        description="Test citation URLs and fix or remove broken ones"
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

    if not citations:
        if args.json:
            print(json.dumps({"tested": 0, "broken": 0, "fixed": 0}))
        else:
            print("No citations found.")
        return

    results = []
    for i, cit in enumerate(citations):
        url = cit.get("url")
        if not url or not url.startswith("http"):
            continue

        ok, status, error = test_url(url, timeout=args.timeout)
        results.append({
            "index": i,
            "name": cit.get("name", f"citations[{i}]"),
            "url": url,
            "ok": ok,
            "status": status,
            "error": error,
        })

    broken = [r for r in results if not r["ok"]]
    working = [r for r in results if r["ok"]]

    if args.json and not args.fix:
        print(json.dumps({
            "tested": len(results),
            "working": len(working),
            "broken": len(broken),
            "details": results,
        }, indent=2))
        return

    if not args.json:
        print(f"Tested {len(results)} citation URLs: {len(working)} OK, {len(broken)} broken\n")

        if working:
            for r in working:
                print(f"  [  OK] {r['name']}")
                print(f"         {r['url']}")

        if broken:
            print()
            for r in broken:
                status_str = f" ({r['status']})" if r['status'] else ""
                print(f"  [FAIL] {r['name']}{status_str}")
                print(f"         {r['url']}")
                if r["error"]:
                    print(f"         {r['error']}")

    if not args.fix:
        if broken:
            print(f"\nRun with --fix to remove broken URLs, or --fix --remove-citations to remove entire citations.")
            sys.exit(1)
        return

    fixes_applied = 0
    citations_removed = []

    for r in broken:
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

    if fixes_applied > 0:
        with open(args.json_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
        if not args.json:
            print(f"\nWrote {fixes_applied} fixes to {args.json_file}")

    if args.json:
        print(json.dumps({
            "tested": len(results),
            "broken": len(broken),
            "fixed": fixes_applied,
            "removed_citations": [r["name"] for r in citations_removed],
        }, indent=2))


if __name__ == "__main__":
    main()
