#!/usr/bin/env python3
"""Test citation URLs and reference URIs; fix or remove broken ones.

Checks every citation with a `url` field and every reference link URI,
HEAD first and GET when HEAD fails. Each URL gets one of three verdicts:

    ok        the publisher served it
    broken    the publisher said it is gone (404 or 410)
    unknown   the check could not establish anything

The third verdict is the point. Publishers refuse HEAD, answer 403 to
unfamiliar user agents, and sit behind CDNs unreachable from some networks,
and none of that means a document has gone. Only `broken` is ever acted on:
`--fix` removes those URLs, `--remove-citations` removes those citations.
An `unknown` is reported and left alone, because deleting an authoritative
citation on the strength of a request the publisher simply did not like is a
worse outcome than leaving a stale URL in place.

`--replace old=new` applies to any citation or reference carrying `old`,
whatever its verdict — naming a URL is an explicit instruction, and the
common case is swapping a route that fails for one that works. A supplied
replacement is applied unless it is itself definitively gone, and a
replacement is never a reason to fall through to deleting the URL.

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
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils._shared import load_json, load_json_pair


# A plain library user agent, matching extract-html-text.py and
# resolve-doc-anchors.py. Documentation CDNs answer 403 both to unrecognised
# product strings like the "PracticeValidator/1.0" this used to send and to
# spoofed browser ones, but accept this.
USER_AGENT = f"Python-urllib/{sys.version_info.major}.{sys.version_info.minor}"

# Verdicts. "unknown" is the important one: the check could not establish
# anything, which is not the same as establishing the URL is broken.
OK, BROKEN, UNKNOWN = "ok", "broken", "unknown"


def _request(url, method, timeout):
    req = urllib.request.Request(url, method=method)
    req.add_header("User-Agent", USER_AGENT)
    req.add_header("Accept", "text/html,application/xhtml+xml,*/*")
    return urllib.request.urlopen(req, timeout=timeout)


def test_url(url, timeout=10):
    """Test a URL. Returns (verdict, status_code, error_message).

    HEAD first, then GET when HEAD fails. Plenty of publishers serve a
    document happily over GET while refusing or mishandling HEAD, and a
    citation checker that removes content on the strength of a HEAD is
    removing authoritative sources over a request nobody else makes.

    A host that cannot be reached at all returns UNKNOWN rather than BROKEN.
    Unreachable from here is not the same as gone, and the difference decides
    whether a citation gets deleted.
    """
    if not url or not url.startswith("http"):
        return OK, None, None

    last_code, last_error = None, None
    for method in ("HEAD", "GET"):
        try:
            resp = _request(url, method, timeout)
            resp.close()
            return OK, resp.status, None
        except urllib.error.HTTPError as e:
            last_code, last_error = e.code, str(e)
            # 404 and 410 are the publisher stating the document is gone, and
            # no method change will alter that. Anything else — 403, 405, 429,
            # 5xx — may just be this request, so fall through to GET.
            if e.code in (404, 410):
                return BROKEN, e.code, str(e)
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            last_code, last_error = None, str(e)

    if last_code is not None:
        # An HTTP status that is not a definite "gone". The document may well
        # be there; we were refused. Do not call that broken.
        return UNKNOWN, last_code, last_error
    return UNKNOWN, None, last_error


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


def normalize_url(url):
    """Repair URLs mangled by an extra round of percent-encoding.

    Sales Hub doccenter URLs legitimately carry a double-encoded path segment —
    the live form has ``%252F``, ``%252C`` and ``%253D``, because an already
    encoded path is encoded again to sit inside one segment. Something in the
    authoring chain encoded them a *third* time, storing ``%25252F`` and a
    doubled trailing slash. 31 authored documents carry it, including two
    shipped at v2.0.0, so it is systematic rather than a typo.

    The repair is mechanical and needs no network: collapse each surplus
    ``%25`` prefix until one encoding round remains, and fold a doubled
    trailing slash. Returns the URL unchanged when neither applies.
    """
    fixed = url
    # "%2525..." is always one round too many; loop in case of worse.
    while "%2525" in fixed:
        fixed = fixed.replace("%2525", "%25")
    # Guard the scheme's "//" by only touching a doubled slash at the very end.
    if fixed.endswith("//"):
        fixed = fixed[:-1]
    return fixed


def normalize_markdown(path):
    """Apply normalize_url to the URLs in a markdown file.

    The JSON sweep left the **analysis reports** untouched, and that was a real
    gap rather than a tidiness one: every Phase 2 agent in this run is told to
    take citation URLs from §11 of its analysis report rather than from an
    existing JSON, so a report carrying the over-escaped form feeds it straight
    back into a freshly generated document. Six reports still carried it after
    the JSON sweep, two of them for documents not yet mapped.

    Matches whole URL tokens so a doubled slash elsewhere in prose is untouched.
    """
    text = path.read_text(encoding="utf-8")
    changes = []

    def _sub(match):
        original = match.group(0)
        fixed = normalize_url(original)
        if fixed != original:
            changes.append((f"line {text[:match.start()].count(chr(10)) + 1}",
                            original, fixed))
        return fixed

    new_text = re.sub(r"https?://[^\s)\]\}\"'<>|]+", _sub, text)
    return new_text, changes


def normalize_file(path):
    """Apply normalize_url to every citation URL and reference link in one file.

    Offline and idempotent, which is why it is allowed to sweep a whole tree
    where --fix is not: there is no probe to misread, so there is no way for it
    to mistake a live SSO-gated URL for a broken one.
    """
    # A sweep reaches whatever *.json sits in the tree, including fragments and
    # scratch files that are not documents at all. One unparseable file must not
    # abort a corpus-wide normalisation, so read tolerantly and skip.
    data, err = load_json_pair(path)
    if err or not isinstance(data, dict):
        return None, []
    changes = []

    for citation in data.get("citations", []) or []:
        url = citation.get("url")
        if not isinstance(url, str):
            continue
        fixed = normalize_url(url)
        if fixed != url:
            citation["url"] = fixed
            changes.append((citation.get("name", "(unnamed citation)"), url, fixed))

    for entry in collect_reference_uris(data):
        fixed = normalize_url(entry["uri"])
        if fixed != entry["uri"]:
            entry["obj"][entry["field"]] = fixed
            changes.append((entry["path"], entry["uri"], fixed))

    return data, changes


def build_parser():
    parser = argparse.ArgumentParser(
        description="Test citation URLs and reference URIs; fix or remove broken ones"
    )
    parser.add_argument("json_file", nargs="*",
                        help="One or more practice/baseline/method JSON files")
    parser.add_argument("--dir", action="append", default=[], metavar="DIR",
                        help="Sweep every practice/baseline/method JSON in a directory "
                             "(repeatable; skips backups, ChangeRequests and "
                             "underscore-prefixed build artifacts)")
    parser.add_argument("--fix", action="store_true",
                        help="Apply fixes (remove broken URLs or citations)")
    parser.add_argument("--remove-citations", action="store_true",
                        help="Remove entire citations with broken URLs (not just the URL field)")
    parser.add_argument("--replace", action="append", default=[],
                        metavar="OLD=NEW",
                        help="Replace a URL with a new one, whatever its verdict "
                             "(repeatable)")
    parser.add_argument("--replace-only", action="store_true",
                        help="With --fix: apply only the --replace swaps and leave "
                             "every other broken URL alone. Use when fixing one "
                             "citation should not quietly strip others.")
    parser.add_argument("--timeout", type=int, default=10,
                        help="HTTP request timeout in seconds (default: 10)")
    parser.add_argument("--check-missing", action="store_true",
                        help="Detect citations missing URLs when source type suggests one should exist")
    parser.add_argument("--no-references", action="store_true",
                        help="Skip reference URI checks (citations only)")
    parser.add_argument("--normalize-escaping", action="store_true",
                        help="Repair over-percent-encoded URLs (%%25252F -> %%252F) and "
                             "doubled trailing slashes, offline. Safe to sweep with "
                             "--dir because it probes nothing; combine with --fix to "
                             "write, omit --fix to preview.")
    parser.add_argument("--json", action="store_true",
                        help="Output results as JSON")
    return parser


def process_file(path, args, replacements):
    """Check (and optionally fix) one document's citation and reference URLs.

    Returns 0 when everything resolved, 1 when anything was broken or unknown.
    """
    data = load_json(path)
    citations = data.get("citations", [])
    has_problems = False

    # Under --replace-only nothing but the named URLs can change, so testing
    # the rest buys nothing and costs a HEAD and a GET apiece — minutes, on a
    # document citing a host that is unreachable rather than merely slow.
    def worth_testing(url):
        return not (args.fix and args.replace_only) or url in replacements

    # --- Citation URL checks ---
    cit_results = []
    for i, cit in enumerate(citations):
        url = cit.get("url")
        if not url or not url.startswith("http"):
            continue
        if not worth_testing(url):
            continue
        verdict, status, error = test_url(url, timeout=args.timeout)
        cit_results.append({
            "index": i,
            "name": cit.get("name", f"citations[{i}]"),
            "url": url,
            "verdict": verdict,
            "ok": verdict == OK,
            "status": status,
            "error": error,
        })

    cit_broken = [r for r in cit_results if r["verdict"] == BROKEN]
    cit_unknown = [r for r in cit_results if r["verdict"] == UNKNOWN]
    cit_working = [r for r in cit_results if r["verdict"] == OK]

    # --- Reference URI checks ---
    ref_results = []
    ref_broken = []
    ref_unknown = []
    if not args.no_references:
        ref_uris = collect_reference_uris(data)
        for entry in ref_uris:
            if not worth_testing(entry["uri"]):
                continue
            verdict, status, error = test_url(entry["uri"], timeout=args.timeout)
            result = {
                "path": entry["path"],
                "ref_name": entry["ref_name"],
                "uri": entry["uri"],
                "verdict": verdict,
                "ok": verdict == OK,
                "status": status,
                "error": error,
                "obj": entry["obj"],
                "field": entry["field"],
            }
            ref_results.append(result)
        ref_broken = [r for r in ref_results if r["verdict"] == BROKEN]
        ref_unknown = [r for r in ref_results if r["verdict"] == UNKNOWN]

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
                "unknown": len(cit_unknown),
                "details": cit_results,
            },
        }
        if not args.no_references:
            ref_working = [r for r in ref_results if r["verdict"] == OK]
            output["references"] = {
                "tested": len(ref_results),
                "working": len(ref_working),
                "broken": len(ref_broken),
                "unknown": len(ref_unknown),
                "details": [{k: v for k, v in r.items() if k not in ("obj", "field")}
                            for r in ref_results],
            }
        if args.check_missing:
            output["missing_urls"] = missing_urls
        print(json.dumps(output, indent=2))
        if cit_broken or ref_broken or missing_urls:
            return 1
        return 0

    # --- Text output ---
    if not args.json:
        if cit_results:
            print(f"Citation URLs: {len(cit_working)} OK, {len(cit_broken)} broken, "
                  f"{len(cit_unknown)} unverifiable (of {len(cit_results)} tested)\n")
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
            if cit_unknown:
                print()
                for r in cit_unknown:
                    status_str = f" ({r['status']})" if r['status'] else ""
                    print(f"  [ ?  ] {r['name']}{status_str} — could not verify")
                    print(f"         {r['url']}")
                    if r["error"]:
                        print(f"         {r['error']}")
        elif not citations:
            print("No citations found.")
        else:
            print("No citation URLs to test.")

        if not args.no_references:
            ref_working = [r for r in ref_results if r["verdict"] == OK]
            if ref_results:
                print(f"\nReference URIs: {len(ref_working)} OK, {len(ref_broken)} broken, "
                      f"{len(ref_unknown)} unverifiable (of {len(ref_results)} tested)\n")
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
                if ref_unknown:
                    print()
                    for r in ref_unknown:
                        status_str = f" ({r['status']})" if r['status'] else ""
                        print(f"  [ ?  ] {r['ref_name']}{status_str} — could not verify")
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
        if cit_unknown or ref_unknown:
            print("\nUnverifiable URLs were not judged broken and nothing will be "
                  "removed for them. Check one in a browser before acting on it.")
        if cit_broken or ref_broken or missing_urls:
            hints = []
            if cit_broken or ref_broken:
                hints.append("--fix to remove broken URLs")
            if cit_broken:
                hints.append("--fix --remove-citations to remove entire citations")
            if hints:
                print(f"\nRun with {', or '.join(hints)}. "
                      "This applies only to the URLs reported broken above.")
            return 1
        if cit_unknown or ref_unknown:
            return 1
        return 0

    # --- Apply fixes ---
    fixes_applied = 0
    citations_removed = []
    replaced_urls = set()

    # Replacements first, and over every citation rather than only the ones
    # judged broken. Naming a URL on --replace is an explicit instruction; the
    # commonest case is swapping a route that resolves here for one that
    # resolves everywhere, and that URL never appears in the broken list.
    for cit in citations:
        url = cit.get("url")
        if not url or url not in replacements:
            continue
        new_url = replacements[url]
        verdict, _status, new_error = test_url(new_url, timeout=args.timeout)
        if verdict == BROKEN:
            if not args.json:
                print(f"\n  Replacement URL is gone for "
                      f"'{cit.get('name', '?')}': {new_url} ({new_error})")
            continue
        cit["url"] = new_url
        replaced_urls.add(url)
        fixes_applied += 1
        if not args.json:
            note = "" if verdict == OK else " (could not verify, applied as given)"
            print(f"\n  Replaced URL for '{cit.get('name', '?')}': {new_url}{note}")

    # Then whatever is still broken and was not replaced. A replacement the
    # caller supplied is never a reason to delete the URL instead.
    for r in [] if args.replace_only else cit_broken:
        if r["url"] in replaced_urls or r["url"] in replacements:
            continue
        cit = citations[r["index"]]

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

    # Reference URIs: replacements over every URI, for the same reason as
    # citations, then report whatever is still broken.
    ref_fixes = 0
    for r in ref_results:
        uri = r["uri"]
        if uri not in replacements:
            continue
        new_uri = replacements[uri]
        verdict, _status, new_error = test_url(new_uri, timeout=args.timeout)
        if verdict == BROKEN:
            if not args.json:
                print(f"\n  Replacement URI is gone for '{r['ref_name']}': "
                      f"{new_uri} ({new_error})")
            continue
        r["obj"][r["field"]] = new_uri
        ref_fixes += 1
        if not args.json:
            note = "" if verdict == OK else " (could not verify, applied as given)"
            print(f"\n  Replaced URI for '{r['ref_name']}': {new_uri}{note}")

    for r in ref_broken:
        if r["uri"] in replacements:
            continue
        if not args.json:
            print(f"\n  [SKIP] Cannot auto-fix reference URI '{r['ref_name']}' — use --replace")

    fixes_applied += ref_fixes

    if fixes_applied > 0:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
        if not args.json:
            print(f"\nWrote {fixes_applied} fixes to {path}")

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

    return 1 if (cit_broken or ref_broken) else 0


def collect_targets(files, dirs):
    """Resolve the documents to check from explicit files and swept directories.

    A sweep skips the same things the rest of the toolchain skips: backup
    directories, ChangeRequests (written as "<name>.changerequest.json" or
    "change-request-*.json") and underscore-prefixed build artifacts such as
    _effective-context.json, none of which are authored documents.
    """
    targets = [Path(f) for f in files]
    for d in dirs:
        base = Path(d)
        if not base.is_dir():
            print(f"Warning: not a directory, skipped: {d}", file=sys.stderr)
            continue
        for found in sorted(base.rglob("*.json")):
            if found.name.startswith("_") or found.name.startswith("change-request"):
                continue
            if found.name.endswith(".changerequest.json"):
                continue
            if "backup" in str(found).lower():
                continue
            targets.append(found)

    seen, unique = set(), []
    for t in targets:
        key = os.path.realpath(t)
        if key not in seen:
            seen.add(key)
            unique.append(t)
    return unique


def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.json_file and not args.dir:
        parser.error("give at least one JSON file or --dir DIR")

    replacements = {}
    for r in args.replace:
        if "=" not in r:
            print(f"Error: --replace value must be 'old=new', got: {r}", file=sys.stderr)
            sys.exit(1)
        old, new = r.split("=", 1)
        replacements[old] = new

    targets = collect_targets(args.json_file, args.dir)
    if not targets:
        print("No documents to check.", file=sys.stderr)
        sys.exit(1)

    # Normalisation is a self-contained mode: offline, idempotent, and therefore
    # exempt from the multi-document --fix guard below, which exists only because
    # network verdicts are unreliable against SSO-gated hosts.
    if args.normalize_escaping:
        total, touched = 0, []
        for path in targets:
            is_markdown = Path(path).suffix.lower() in (".md", ".markdown")
            if is_markdown:
                payload, changes = normalize_markdown(Path(path))
            else:
                payload, changes = normalize_file(path)
                # A JSON file that is not a document — a bare array, a refs
                # spec, any build artifact — has no citations or references for
                # the structured path to walk, so it came back untouched while
                # still carrying the defect. Five `_refs-spec*.json` files held
                # 78 over-escaped URLs this way. Fall back to the textual sweep,
                # which needs no shape at all.
                if payload is None:
                    payload, changes = normalize_markdown(Path(path))
                    is_markdown = True
            if not changes:
                continue
            touched.append(str(path))
            total += len(changes)
            if not args.json:
                print(f"\n{path}")
                for label, old, new in changes:
                    print(f"  {label}\n    - {old}\n    + {new}")
            if args.fix:
                if is_markdown:
                    Path(path).write_text(payload, encoding="utf-8")
                else:
                    with open(path, "w", encoding="utf-8") as f:
                        json.dump(payload, f, indent=2, ensure_ascii=False)
                        f.write("\n")
        if args.json:
            print(json.dumps({"normalized": total, "files": touched}, indent=2))
        else:
            verb = "normalized" if args.fix else "would normalize"
            print(f"\n{verb} {total} URL(s) across {len(touched)} document(s).")
            if not args.fix and total:
                print("(preview — add --fix to write)")
        sys.exit(0)

    # Hosts that sit behind SSO answer an unauthenticated probe with 404 or 403
    # even when the document is perfectly reachable to a signed-in reader, so a
    # sweep reads them as broken. Stripping those URLs would destroy working
    # citations wholesale, which is the opposite of the job.
    if args.fix and not args.replace_only and len(targets) > 1:
        print(
            "Refusing to --fix across several documents without --replace-only.\n"
            "Authenticated hosts (saleshub.redhat.com, source.redhat.com,\n"
            "content.redhat.com, docs.google.com) return 404/403 to an\n"
            "unauthenticated probe, so a sweep reports live URLs as broken and\n"
            "--fix would strip them. Sweep without --fix to get the report, verify\n"
            "each finding against the authenticated route, then fix one document at\n"
            "a time with --replace.",
            file=sys.stderr,
        )
        sys.exit(2)

    # A --replace swap names one specific URL, so applying it across a swept
    # set would be guesswork about which document meant it.
    if replacements and len(targets) > 1:
        parser.error("--replace works on a single document; name one file")

    failed = []
    for path in targets:
        if len(targets) > 1 and not args.json:
            print(f"\n{'=' * 70}\n{path}\n{'=' * 70}")
        try:
            if process_file(path, args, replacements):
                failed.append(str(path))
        except Exception as exc:                                  # noqa: BLE001
            print(f"Error processing {path}: {exc}", file=sys.stderr)
            failed.append(str(path))

    if len(targets) > 1 and not args.json:
        print(f"\n{len(targets) - len(failed)}/{len(targets)} documents clean.")
        for f in failed:
            print(f"  needs attention: {f}")

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
