#!/usr/bin/env python3
"""API client for keleo-studio-gas remote bundle management.

Manages remote package index, version comparison, bundle download/upload,
and authentication configuration for keleo-studio-gas instances.

Usage:
    python3 utils/studio-client.py --status
    python3 utils/studio-client.py --index [--max-age 3600]
    python3 utils/studio-client.py --docs [--kind practice]
    python3 utils/studio-client.py --check [name] [--deep]
    python3 utils/studio-client.py --check-embedded "Platform Adoption Essentials"
    python3 utils/studio-client.py --link "Practice Name" ["Other Name" ...] [--markdown]
    python3 utils/studio-client.py --link "Practice A" "Practice B" --attribution
    python3 utils/studio-client.py --pull "Practice Name"
    python3 utils/studio-client.py --push bundles/practice.keleo
    python3 utils/studio-client.py --configure
"""

import argparse
import base64
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _shared import GWS, load_user_config, save_user_config, get_project_root

REMOTE_INDEX_PATH = "bundles/.remote-index.json"
REMOTE_DOCS_PATH = "bundles/.remote-documents.json"
DEFAULT_MAX_AGE = 3600


def _api_get(base_url, token, api, params=None):
    """Make a GET request to the keleo-studio-gas REST API."""
    url = f"{base_url}?api={api}"
    if params:
        for k, v in params.items():
            url += f"&{k}={urllib.request.quote(str(v))}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read()), None
    except urllib.error.HTTPError as e:
        if e.code == 401:
            return None, "auth_expired"
        return None, f"HTTP {e.code}: {e.reason}"
    except urllib.error.URLError as e:
        return None, f"Connection error: {e.reason}"
    except Exception as e:
        return None, str(e)


def _api_post(base_url, token, api, body):
    """Make a POST request to the keleo-studio-gas REST API."""
    url = f"{base_url}?api={api}"
    data = body.encode("utf-8") if isinstance(body, str) else body
    req = urllib.request.Request(
        url, data=data, method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "text/plain",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read()), None
    except urllib.error.HTTPError as e:
        if e.code == 401:
            return None, "auth_expired"
        return None, f"HTTP {e.code}: {e.reason}"
    except urllib.error.URLError as e:
        return None, f"Connection error: {e.reason}"
    except Exception as e:
        return None, str(e)


def _get_credentials():
    """Load URL and token from user config. Returns (url, token) or exits."""
    config = load_user_config()
    url = config.get("keleoStudioGasUrl")
    token = config.get("keleoStudioGasToken")
    if not url or not token:
        print("Error: keleo-studio-gas not configured.", file=sys.stderr)
        print("Run: python3 utils/studio-client.py --configure", file=sys.stderr)
        sys.exit(1)
    return url, token


AUTH_EXPIRED_HINT = (
    "Get a fresh token from your keleo-studio-gas instance "
    "(Settings → API Token) and run:\n"
    "  python3 utils/studio-client.py --configure --token <token>"
)


def _handle_auth_error():
    """Print auth expiry message and exit."""
    print("Error: Authentication token has expired.", file=sys.stderr)
    print(AUTH_EXPIRED_HINT, file=sys.stderr)
    sys.exit(1)


def _load_cached_index(path=REMOTE_INDEX_PATH):
    """Load a cached remote index if it exists."""
    index_path = get_project_root() / path
    if not index_path.exists():
        return None
    try:
        with open(index_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def _save_index(data, path=REMOTE_INDEX_PATH):
    """Save a remote index to its cache file."""
    index_path = get_project_root() / path
    index_path.parent.mkdir(parents=True, exist_ok=True)
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def _index_age_seconds(cached):
    """Return age of cached index in seconds, or infinity if missing."""
    if not cached or "_fetchedAt" not in cached:
        return float("inf")
    try:
        fetched = datetime.fromisoformat(cached["_fetchedAt"].replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - fetched).total_seconds()
    except (ValueError, TypeError):
        return float("inf")


def _slugify(name):
    """Convert a document name to a filesystem-safe slug."""
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return slug


def _parse_semver(version_str):
    """Parse a version string into a comparable tuple."""
    if not version_str:
        return (0, 0, 0)
    parts = version_str.split(".")
    result = []
    for p in parts[:3]:
        try:
            result.append(int(p))
        except ValueError:
            result.append(0)
    while len(result) < 3:
        result.append(0)
    return tuple(result)


def cmd_configure(url=None, token=None):
    """Configure keleo-studio-gas credentials.

    Prompts for whatever is not supplied as an argument, so redeploying can be
    recorded with `--configure --url <new URL>` without retyping the token.
    """
    config = load_user_config()
    current_url = config.get("keleoStudioGasUrl", "")
    current_token = config.get("keleoStudioGasToken", "")
    interactive = not (url or token)

    if interactive:
        print("Configure keleo-studio-gas connection")
        print("=" * 40)
        url = input(f"Deployment URL [{current_url}]: ").strip()
        token = input("API token (from Settings → API Token): ").strip()

    url = url or current_url
    token = token or current_token
    if not url:
        print("Error: URL is required.", file=sys.stderr)
        sys.exit(1)
    if not token:
        print("Error: Token is required.", file=sys.stderr)
        sys.exit(1)

    url_changed = url != current_url
    config["keleoStudioGasUrl"] = url
    config["keleoStudioGasToken"] = token
    save_user_config(config)
    print(f"Saved to .claude/user-config.json")

    # A new deployment serves a different library; the caches no longer apply.
    if url_changed:
        for path in (REMOTE_INDEX_PATH, REMOTE_DOCS_PATH):
            cache = get_project_root() / path
            if cache.exists():
                cache.unlink()
                print(f"Cleared stale cache: {path}")

    data, err = _api_get(url, token, "packages")
    if err == "auth_expired":
        print("Warning: Token appears to be expired.", file=sys.stderr)
    elif err:
        print(f"Warning: Connection test failed: {err}", file=sys.stderr)
    else:
        count = len(data.get("bundles", []))
        print(f"Connection OK — {count} packages available")


def cmd_status(as_json=False):
    """Show connection status and index freshness."""
    config = load_user_config()
    url = config.get("keleoStudioGasUrl", "")
    token = config.get("keleoStudioGasToken", "")
    cached = _load_cached_index()
    age = _index_age_seconds(cached)

    status = {
        "configured": bool(url and token),
        "url": url or None,
        "tokenPresent": bool(token),
        "indexCached": cached is not None,
        "indexAge": round(age) if age != float("inf") else None,
        "indexBundleCount": len(cached.get("bundles", [])) if cached else 0,
        "indexFetchedAt": cached.get("_fetchedAt") if cached else None,
    }

    if as_json:
        print(json.dumps(status, indent=2))
        return

    if not status["configured"]:
        print("Status: NOT CONFIGURED")
        print("Run: python3 utils/studio-client.py --configure")
        return

    print(f"URL:    {url}")
    print(f"Token:  {'present' if token else 'missing'}")

    if cached:
        if age < 60:
            age_str = f"{int(age)}s ago"
        elif age < 3600:
            age_str = f"{int(age / 60)}m ago"
        else:
            age_str = f"{int(age / 3600)}h ago"
        print(f"Index:  {status['indexBundleCount']} packages (fetched {age_str})")
    else:
        print("Index:  not cached")
        print("Run: python3 utils/studio-client.py --index")


def cmd_index(max_age=DEFAULT_MAX_AGE, as_json=False):
    """Fetch remote package listing and cache locally."""
    cached = _load_cached_index()
    age = _index_age_seconds(cached)

    if age < max_age and cached:
        if as_json:
            print(json.dumps(cached, indent=2))
        else:
            count = len(cached.get("bundles", []))
            print(f"Index is fresh ({int(age)}s old, max-age {max_age}s) — {count} packages")
        return cached

    url, token = _get_credentials()
    data, err = _api_get(url, token, "packages")
    if err == "auth_expired":
        _handle_auth_error()
    if err:
        print(f"Error fetching index: {err}", file=sys.stderr)
        sys.exit(1)

    index_data = {
        "_fetchedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "_sourceUrl": url,
        "bundles": data.get("bundles", []),
    }
    _save_index(index_data)

    if as_json:
        print(json.dumps(index_data, indent=2))
    else:
        count = len(index_data["bundles"])
        print(f"Fetched remote index: {count} packages")

    return index_data


def _fetch_documents(max_age=DEFAULT_MAX_AGE):
    """Return (documents, error) for the remote document listing.

    Falls back to the cached listing when the remote is unreachable, so callers
    that only need name resolution can degrade instead of failing. Auth expiry
    is returned rather than raised, for the same reason — the caller decides
    whether an unverified answer is still useful.
    """
    cached = _load_cached_index(REMOTE_DOCS_PATH)
    if _index_age_seconds(cached) < max_age and cached:
        return cached.get("documents", []), None

    url, token = _get_credentials()
    data, err = _api_get(url, token, "index")
    if err:
        if cached:
            return cached.get("documents", []), f"{err} (using cached listing)"
        return None, err

    docs_data = {
        "_fetchedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "_sourceUrl": url,
        "documents": data.get("documents", []),
    }
    _save_index(docs_data, REMOTE_DOCS_PATH)
    return docs_data["documents"], None


def cmd_docs(kind=None, max_age=DEFAULT_MAX_AGE, as_json=False):
    """Fetch the remote document listing (every document in every bundle)."""
    documents, err = _fetch_documents(max_age)
    if err == "auth_expired":
        _handle_auth_error()
    if documents is None:
        print(f"Error fetching document index: {err}", file=sys.stderr)
        sys.exit(1)
    if err:
        print(f"Warning: {err}", file=sys.stderr)

    if kind:
        documents = [d for d in documents if d.get("kind") == kind]

    if as_json:
        print(json.dumps({"documents": documents}, indent=2))
    else:
        for d in sorted(documents, key=lambda d: d.get("name", "")):
            version = d.get("version") or "—"
            print(f"  {d.get('name', ''):45s} {d.get('kind', ''):18s} v{version}")
        print(f"{len(documents)} documents")

    return documents


def _deep_link(base_url, doc_name, element=None):
    """Build a keleo-studio-gas deep link for a document (and optional element)."""
    url = f"{base_url}?doc={urllib.parse.quote(doc_name, safe='')}"
    if element:
        url += f"&element={urllib.parse.quote(element, safe='')}"
    return url


def _attribution_line(links):
    """Render the closing framework attribution line for a report."""
    parts = [f"[{l['name']}]({l['url']})" for l in links]
    if len(parts) == 1:
        joined, noun = parts[0], "framework"
    else:
        joined = f"{', '.join(parts[:-1])}{',' if len(parts) > 2 else ''} and {parts[-1]}"
        noun = "frameworks"
    return f"*Structured using the {joined} {noun}.*"


def cmd_link(names, element=None, markdown=False, attribution=False,
             as_json=False, max_age=DEFAULT_MAX_AGE, strict=False):
    """Build deep links into keleo-studio-gas for named practices/methods.

    Names are matched against the remote document index so that a link is only
    emitted for a document that is actually published. Matching is exact first,
    then case-insensitive; the resolved name is used in the URL.

    When the index cannot be reached, links are still built from the names as
    given and marked unverified — a report should not be blocked by a transient
    remote failure.
    """
    config = load_user_config()
    base_url = config.get("keleoStudioGasUrl")
    if not base_url:
        print("Error: keleo-studio-gas URL not configured.", file=sys.stderr)
        print("Run: python3 utils/studio-client.py --configure", file=sys.stderr)
        sys.exit(1)

    if element and len(names) > 1:
        print("Error: --element applies to a single document only.", file=sys.stderr)
        sys.exit(1)

    documents, err = _fetch_documents(max_age)
    by_exact, by_fold = {}, {}
    for d in documents or []:
        by_exact.setdefault(d.get("name", ""), d)
        by_fold.setdefault(d.get("name", "").casefold(), d)

    links = []
    for name in names:
        doc = by_exact.get(name) or by_fold.get(name.casefold())
        resolved = doc.get("name", name) if doc else name
        links.append({
            "requested": name,
            "name": resolved,
            "url": _deep_link(base_url, resolved, element),
            # None when the index was unavailable: the link is unverified.
            "found": None if documents is None else bool(doc),
            "kind": doc.get("kind") if doc else None,
            "version": doc.get("version") if doc else None,
            "bundleSlug": doc.get("bundleSlug") if doc else None,
        })

    missing = [l["requested"] for l in links if l["found"] is False]

    if as_json:
        print(json.dumps({
            "baseUrl": base_url,
            "links": links,
            "attribution": _attribution_line(links),
        }, indent=2))
    elif attribution:
        print(_attribution_line(links))
    elif markdown:
        for link in links:
            print(f"[{link['name']}]({link['url']})")
    else:
        for link in links:
            mark = {True: "", False: "  (NOT PUBLISHED)", None: "  (unverified)"}
            print(f"  {link['name']:45s} {link['url']}{mark[link['found']]}")

    if documents is None:
        reason = ("the API token has expired" if err == "auth_expired" else err)
        print(f"Warning: document index unavailable ({reason}) — links are "
              f"unverified", file=sys.stderr)
        if err == "auth_expired":
            print(AUTH_EXPIRED_HINT, file=sys.stderr)
    elif err:
        print(f"Warning: {err}", file=sys.stderr)
    if missing:
        print(f"Warning: not in the remote library: {', '.join(missing)}",
              file=sys.stderr)
    if strict and (missing or documents is None):
        sys.exit(1)

    return links


def _build_local_versions():
    """Build a name→version mapping from local bundles/ directory."""
    bundles_dir = get_project_root() / "bundles"
    versions = {}
    if not bundles_dir.is_dir():
        return versions

    for keleo_file in bundles_dir.glob("*.keleo"):
        try:
            with zipfile.ZipFile(keleo_file, "r") as zf:
                if "manifest.json" not in zf.namelist():
                    continue
                manifest = json.loads(zf.read("manifest.json"))
                pkg = manifest.get("package", {})
                name = manifest.get("name") or pkg.get("name", "")
                version = manifest.get("version") or pkg.get("version", "")
                if name:
                    existing = versions.get(name)
                    if existing is None or _parse_semver(version) > _parse_semver(existing["version"]):
                        versions[name] = {
                            "version": version,
                            "path": str(keleo_file),
                            "slug": keleo_file.stem,
                        }
        except (zipfile.BadZipFile, json.JSONDecodeError, KeyError):
            continue

    return versions


def cmd_check(name=None, as_json=False, deep=False):
    """Compare local vs remote versions, and with deep=True their content too."""
    cached = _load_cached_index()
    if not cached or _index_age_seconds(cached) > DEFAULT_MAX_AGE:
        cached = cmd_index(max_age=DEFAULT_MAX_AGE, as_json=False)

    remote_by_name = {}
    for b in cached.get("bundles", []):
        bname = b.get("name", "")
        if bname:
            existing = remote_by_name.get(bname)
            if existing is None or _parse_semver(b.get("version", "")) > _parse_semver(existing.get("version", "")):
                remote_by_name[bname] = b

    local_versions = _build_local_versions()

    all_names = sorted(set(list(remote_by_name.keys()) + list(local_versions.keys())))
    if name:
        matches = [n for n in all_names if name.lower() in n.lower()]
        if not matches:
            print(f"No documents matching '{name}' found locally or remotely.", file=sys.stderr)
            sys.exit(1)
        all_names = matches

    results = []
    for doc_name in all_names:
        local = local_versions.get(doc_name)
        remote = remote_by_name.get(doc_name)
        local_ver = local["version"] if local else None
        remote_ver = remote.get("version") if remote else None

        if local_ver and remote_ver:
            lv = _parse_semver(local_ver)
            rv = _parse_semver(remote_ver)
            if lv == rv:
                status = "up-to-date"
            elif rv > lv:
                status = "remote-newer"
            else:
                status = "local-newer"
        elif local_ver and not remote_ver:
            status = "local-only"
        elif remote_ver and not local_ver:
            status = "remote-only"
        else:
            status = "unknown"

        entry = {
            "name": doc_name,
            "localVersion": local_ver,
            "remoteVersion": remote_ver,
            "status": status,
            "localPath": local["path"] if local else None,
            "remoteSlug": remote.get("slug") if remote else None,
        }

        # Version equality says nothing about content: a bundle republished
        # without a version bump still reads as up to date. Only --deep can
        # tell the difference, and only where both sides exist.
        if deep and status == "up-to-date":
            comparison = _compare_bundle_content(doc_name, local["path"])
            if comparison["error"]:
                entry["contentCheckError"] = comparison["error"]
            elif not comparison["match"]:
                entry["status"] = "same-version-content-differs"
                entry["differingDocuments"] = comparison["differingDocuments"]
            else:
                entry["contentVerified"] = True

        results.append(entry)

    if as_json:
        print(json.dumps({"results": results}, indent=2))
        return results

    for r in results:
        lv = r["localVersion"] or "—"
        rv = r["remoteVersion"] or "—"
        indicator = {
            "up-to-date": "  ✓ up to date" + (" (content verified)" if r.get("contentVerified") else ""),
            "same-version-content-differs": "  ! SAME VERSION, CONTENT DIFFERS",
            "remote-newer": "  ← REMOTE NEWER",
            "local-newer": "  → LOCAL NEWER",
            "local-only": "  → LOCAL ONLY",
            "remote-only": "  ← REMOTE ONLY",
        }.get(r["status"], "")
        print(f"  {r['name']:40s} local: {lv:8s} remote: {rv:8s}{indicator}")
        for doc in r.get("differingDocuments", []):
            print(f"      differs: {doc}")
        if r.get("contentCheckError"):
            print(f"      content check failed: {r['contentCheckError']}")

    return results


def _local_document_version(doc_name):
    """Return the on-disk version of a document by name, or None.

    Looks in baselines/ and practices/, which is where the definitive copies
    live; bundles only ever carry snapshots of these.
    """
    root = get_project_root()
    for sub in ("baselines", "practices"):
        base = root / sub
        if not base.is_dir():
            continue
        for path in base.glob("*/*.json"):
            if "backup-" in str(path):
                continue
            try:
                with open(path) as fh:
                    doc = json.load(fh)
            except (json.JSONDecodeError, OSError):
                continue
            if isinstance(doc, dict) and doc.get("name") == doc_name:
                return doc.get("version"), str(path)
    return None, None


def cmd_check_embedded(doc_name, max_age=DEFAULT_MAX_AGE, as_json=False):
    """Report which remote packages embed a stale copy of a named document.

    The remote keeps every published version as its own slug, so older slugs
    are historical snapshots rather than drift. Only the newest slug per
    package name is compared — that is the one a fresh download resolves to.
    """
    documents, err = _fetch_documents(max_age)
    if err == "auth_expired":
        _handle_auth_error()
    if documents is None:
        print(f"Error fetching document index: {err}", file=sys.stderr)
        sys.exit(1)
    if err:
        print(f"Warning: {err}", file=sys.stderr)

    cached = _load_cached_index()
    if not cached or _index_age_seconds(cached) > max_age:
        cached = cmd_index(max_age=max_age, as_json=False)

    # slug → package identity, and package name → newest slug
    by_slug = {b.get("slug"): b for b in cached.get("bundles", []) if b.get("slug")}
    newest_slug = {}
    for bundle in by_slug.values():
        pkg = bundle.get("name", "")
        if not pkg:
            continue
        current = newest_slug.get(pkg)
        if current is None or _parse_semver(bundle.get("version", "")) > _parse_semver(current.get("version", "")):
            newest_slug[pkg] = bundle

    current_slugs = {b["slug"] for b in newest_slug.values()}
    local_version, local_path = _local_document_version(doc_name)
    local_versions = _build_local_versions()

    results, superseded = [], 0
    for entry in documents:
        if entry.get("name") != doc_name:
            continue
        slug = entry.get("bundleSlug")
        if slug not in current_slugs:
            superseded += 1
            continue
        bundle = by_slug.get(slug, {})
        pkg = bundle.get("name", slug)
        embedded = entry.get("version")
        stale = bool(local_version and embedded
                     and _parse_semver(embedded) < _parse_semver(local_version))
        local_bundle = local_versions.get(pkg)
        results.append({
            "package": pkg,
            "remoteSlug": slug,
            "remotePackageVersion": bundle.get("version"),
            "embeddedVersion": embedded,
            "stale": stale,
            "localBundlePath": local_bundle["path"] if local_bundle else None,
            "localBundleVersion": local_bundle["version"] if local_bundle else None,
        })

    results.sort(key=lambda r: r["package"].lower())
    stale_results = [r for r in results if r["stale"]]
    pushable = [r for r in stale_results if r["localBundlePath"]]
    summary = {
        "document": doc_name,
        "localVersion": local_version,
        "localPath": local_path,
        "currentPackages": len(results),
        "stalePackages": len(stale_results),
        "pushable": len(pushable),
        "noLocalSource": len(stale_results) - len(pushable),
        "supersededSlugsSkipped": superseded,
    }

    if as_json:
        print(json.dumps({"summary": summary, "results": results}, indent=2))
        return results

    if not local_version:
        print(f"Warning: no on-disk copy of '{doc_name}' found; "
              "cannot judge staleness.", file=sys.stderr)
    print(f"Document: {doc_name}  (on disk: v{local_version or '—'})")
    print(f"Current remote packages embedding it: {len(results)}\n")
    for r in results:
        mark = "STALE " if r["stale"] else "ok    "
        local = f"local bundle v{r['localBundleVersion']}" if r["localBundlePath"] else "NO LOCAL BUNDLE"
        print(f"  {mark} {r['package']:45s} embeds v{r['embeddedVersion'] or '—':8s} {local}")
    print(f"\n--- Summary ---")
    print(f"Current packages:    {summary['currentPackages']}")
    print(f"Stale:               {summary['stalePackages']}")
    print(f"  pushable locally:  {summary['pushable']}")
    print(f"  no local source:   {summary['noLocalSource']}")
    print(f"Superseded slugs skipped: {superseded}")

    return results


def _fetch_bundle(name, output_path, quiet=False):
    """Download a remote .keleo bundle to output_path.

    Returns (path, None) on success or (None, reason) on failure. Unlike
    cmd_pull this never exits, so callers that treat a download failure as
    non-fatal (--deep) can carry on with the remaining bundles.
    """
    url, token = _get_credentials()

    data, err = _api_get(url, token, "download", {"name": name})
    if err == "auth_expired":
        _handle_auth_error()
    if err:
        return None, err

    download_url = data.get("downloadUrl")
    if not download_url:
        return None, "no download URL returned (document may not exist remotely)"

    file_id_match = re.search(r"/d/([^/]+)/", download_url)
    if not file_id_match:
        file_id_match = re.search(r"id=([^&]+)", download_url)
    if not file_id_match:
        return None, "cannot extract file ID from download URL"

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    gws_cmd = [
        GWS, "drive", "files", "get",
        "--params", json.dumps({"fileId": file_id_match.group(1), "alt": "media"}),
        "--output", str(output_path),
    ]

    try:
        result = subprocess.run(gws_cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            return None, f"download failed: {result.stderr.strip()}"
    except FileNotFoundError:
        return None, f"gws CLI not found at {GWS} (download manually: {download_url})"
    except subprocess.TimeoutExpired:
        return None, "download timed out after 60s"

    if not output_path.exists() or output_path.stat().st_size == 0:
        return None, "download produced an empty file"

    if not zipfile.is_zipfile(output_path):
        output_path.unlink()
        return None, "downloaded file is not a valid ZIP archive"

    with zipfile.ZipFile(output_path, "r") as zf:
        if "manifest.json" not in zf.namelist():
            output_path.unlink()
            return None, "downloaded archive has no manifest.json"

    return output_path, None


def _document_hashes(keleo_path):
    """Map document filename → SHA-256 of its canonicalised JSON.

    Canonicalising (sorted keys, fixed separators) means formatting-only
    differences — indentation, key order, trailing newline — do not register
    as content changes.
    """
    hashes = {}
    with zipfile.ZipFile(keleo_path, "r") as zf:
        for entry in sorted(zf.namelist()):
            if not entry.startswith("documents/") or not entry.endswith(".json"):
                continue
            try:
                doc = json.loads(zf.read(entry))
            except json.JSONDecodeError:
                hashes[entry] = "unparseable"
                continue
            canonical = json.dumps(doc, sort_keys=True, separators=(",", ":"))
            hashes[entry] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return hashes


def _compare_bundle_content(name, local_path):
    """Compare local and remote bundle document content.

    Returns a dict with 'match' (bool or None if undetermined), the differing
    document names, and any error encountered.
    """
    # The gws CLI refuses an --output path outside its working directory, so
    # the scratch dir has to live under cwd rather than the system temp dir.
    with tempfile.TemporaryDirectory(dir=Path.cwd(), prefix=".keleo-deep-") as tmpdir:
        remote_path, err = _fetch_bundle(name, Path(tmpdir) / "remote.keleo")
        if err:
            return {"match": None, "error": err}

        try:
            local_hashes = _document_hashes(local_path)
            remote_hashes = _document_hashes(remote_path)
        except (zipfile.BadZipFile, KeyError) as e:
            return {"match": None, "error": f"could not read documents: {e}"}

    differing = sorted(
        set(local_hashes) ^ set(remote_hashes)
        | {k for k in set(local_hashes) & set(remote_hashes)
           if local_hashes[k] != remote_hashes[k]}
    )
    return {"match": not differing, "differingDocuments": differing, "error": None}


def cmd_pull(name, as_json=False):
    """Download a .keleo bundle from remote into bundles/."""
    slug = _slugify(name)
    output_path = get_project_root() / "bundles" / f"{slug}.keleo"

    output_path, err = _fetch_bundle(name, output_path)
    if err:
        print(f"Error: {err}", file=sys.stderr)
        sys.exit(1)

    try:
        with zipfile.ZipFile(output_path, "r") as zf:
            manifest = json.loads(zf.read("manifest.json"))
            pkg = manifest.get("package", {})
            version = manifest.get("version") or pkg.get("version", "?")
            doc_count = len(manifest.get("documents", []))
    except (zipfile.BadZipFile, json.JSONDecodeError) as e:
        print(f"Error: Invalid bundle: {e}", file=sys.stderr)
        output_path.unlink()
        sys.exit(1)

    report = {
        "name": name,
        "version": version,
        "slug": slug,
        "path": str(output_path),
        "documentCount": doc_count,
    }

    if as_json:
        print(json.dumps(report, indent=2))
    else:
        print(f"Downloaded: {name} v{version} ({doc_count} documents)")
        print(f"  → {output_path}")

    return report


def cmd_push_many(file_paths, as_json=False, delay=0):
    """Upload several bundles, continuing past individual failures.

    A partial upload is the normal failure mode on a long run, so each result
    is recorded and a non-zero exit reports that some did not land.

    `delay` paces the uploads. Back-to-back pushes of large bundles have been
    seen to return success without the write landing — the remote drops them
    under load — so spacing the requests is the difference between a reported
    success and an actual one. Always verify with --check-embedded afterwards.
    """
    if len(file_paths) == 1:
        return cmd_push(file_paths[0], as_json=as_json)

    reports, failures = [], []
    for i, file_path in enumerate(file_paths, 1):
        if delay and i > 1:
            time.sleep(delay)
        if not as_json:
            print(f"[{i}/{len(file_paths)}] {file_path}", flush=True)
        try:
            reports.append(cmd_push(file_path, as_json=False, _exit_on_error=False))
        except _PushError as exc:
            failures.append({"path": file_path, "error": str(exc)})
            print(f"  FAILED: {exc}", file=sys.stderr, flush=True)

    if as_json:
        print(json.dumps({"uploaded": reports, "failed": failures}, indent=2))
    else:
        print(f"\n--- Summary ---")
        print(f"Uploaded: {len(reports)}  Failed: {len(failures)}")
        for f in failures:
            print(f"  FAILED {f['path']}: {f['error']}")

    if failures:
        sys.exit(1)
    return reports


class _PushError(Exception):
    """A single bundle failed to upload."""


def cmd_push(file_path, as_json=False, _exit_on_error=True):
    """Upload a .keleo bundle to remote."""
    def _fail(message):
        if _exit_on_error:
            print(f"Error: {message}", file=sys.stderr)
            sys.exit(1)
        raise _PushError(message)

    path = Path(file_path)
    if not path.exists():
        _fail(f"File not found: {path}")

    if not zipfile.is_zipfile(path):
        _fail(f"Not a valid .keleo archive: {path}")

    try:
        with zipfile.ZipFile(path, "r") as zf:
            manifest = json.loads(zf.read("manifest.json"))
            pkg = manifest.get("package", {})
            local_name = manifest.get("name") or pkg.get("name", path.stem)
            local_version = manifest.get("version") or pkg.get("version", "?")
    except (zipfile.BadZipFile, json.JSONDecodeError, KeyError) as e:
        _fail(f"Error reading bundle: {e}")

    url, token = _get_credentials()

    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")

    data, err = _api_post(url, token, "upload", b64)
    if err == "auth_expired":
        _handle_auth_error()
    if err:
        _fail(f"Error uploading: {err}")

    report = {
        "name": local_name,
        "version": local_version,
        "path": str(path),
        "remote": data.get("bundle", {}),
    }

    if as_json:
        print(json.dumps(report, indent=2))
    else:
        print(f"Uploaded: {local_name} v{local_version}")
        remote_name = data.get("bundle", {}).get("name", "")
        if remote_name:
            print(f"  Remote: {remote_name}")

    return report


def main():
    parser = argparse.ArgumentParser(
        description="keleo-studio-gas remote bundle management"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--configure", action="store_true",
                       help="Set/update remote URL and API token")
    group.add_argument("--status", action="store_true",
                       help="Show connection status and index freshness")
    group.add_argument("--index", action="store_true",
                       help="Fetch and cache remote package listing")
    group.add_argument("--docs", action="store_true",
                       help="Fetch and cache the remote document listing")
    group.add_argument("--check", nargs="?", const="", metavar="NAME",
                       help="Compare local vs remote versions (all or specific name)")
    group.add_argument("--check-embedded", metavar="NAME",
                       help="Report which current remote packages embed a "
                            "stale copy of the named document, comparing "
                            "against the on-disk version")
    group.add_argument("--link", nargs="+", metavar="NAME",
                       help="Build deep links into keleo-studio-gas for the "
                            "named practices/methods")
    group.add_argument("--pull", metavar="NAME",
                       help="Download a .keleo bundle from remote")
    group.add_argument("--push", nargs="+", metavar="FILE",
                       help="Upload one or more .keleo bundles to remote")

    parser.add_argument("--max-age", type=int, default=DEFAULT_MAX_AGE,
                        help=f"Max age in seconds for cached index (default: {DEFAULT_MAX_AGE})")
    parser.add_argument("--url", metavar="URL",
                        help="With --configure: set the deployment URL without "
                             "prompting (keeps the stored token)")
    parser.add_argument("--token", metavar="TOKEN",
                        help="With --configure: set the API token without "
                             "prompting (keeps the stored URL)")
    parser.add_argument("--kind", metavar="KIND",
                        help="With --docs: filter by kind (practice, method, "
                             "baselinePractice)")
    parser.add_argument("--element", metavar="NAME",
                        help="With --link: also select an element in the document")
    parser.add_argument("--markdown", action="store_true",
                        help="With --link: emit markdown links, one per line")
    parser.add_argument("--deep", action="store_true",
                        help="With --check: also compare document content for "
                             "bundles whose versions match, reporting "
                             "same-version-content-differs where they diverge. "
                             "Downloads each matching bundle, so scope it with "
                             "a NAME rather than running it over the library")
    parser.add_argument("--attribution", action="store_true",
                        help="With --link: emit the closing report attribution "
                             "line with every framework hyperlinked")
    parser.add_argument("--strict", action="store_true",
                        help="With --link: exit 1 if any name is unpublished")
    parser.add_argument("--delay", type=float, default=0, metavar="SECONDS",
                        help="With --push: pause between uploads. Paces long "
                             "runs, which the remote otherwise drops silently")
    parser.add_argument("--json", action="store_true",
                        help="Output as JSON")

    args = parser.parse_args()

    if args.configure:
        cmd_configure(url=args.url, token=args.token)
    elif args.status:
        cmd_status(as_json=args.json)
    elif args.index:
        cmd_index(max_age=args.max_age, as_json=args.json)
    elif args.docs:
        cmd_docs(kind=args.kind, max_age=args.max_age, as_json=args.json)
    elif args.link:
        cmd_link(args.link, element=args.element, markdown=args.markdown,
                 attribution=args.attribution, as_json=args.json,
                 max_age=args.max_age, strict=args.strict)
    elif args.check_embedded:
        cmd_check_embedded(args.check_embedded, max_age=args.max_age,
                           as_json=args.json)
    elif args.check is not None:
        cmd_check(name=args.check or None, as_json=args.json, deep=args.deep)
    elif args.pull:
        cmd_pull(args.pull, as_json=args.json)
    elif args.push:
        cmd_push_many(args.push, as_json=args.json, delay=args.delay)


if __name__ == "__main__":
    main()
