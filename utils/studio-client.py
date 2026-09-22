#!/usr/bin/env python3
"""API client for keleo-studio-gas remote bundle management.

Manages remote package index, version comparison, bundle download/upload,
and authentication configuration for keleo-studio-gas instances.

Usage:
    python3 utils/studio-client.py --status
    python3 utils/studio-client.py --index [--max-age 3600]
    python3 utils/studio-client.py --check [name]
    python3 utils/studio-client.py --pull "Practice Name"
    python3 utils/studio-client.py --push bundles/practice.keleo
    python3 utils/studio-client.py --configure
"""

import argparse
import base64
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _shared import load_user_config, save_user_config, get_project_root

REMOTE_INDEX_PATH = "bundles/.remote-index.json"
DEFAULT_MAX_AGE = 3600


def _api_get(base_url, token, api, params=None):
    """Make a GET request to the keleo-studio-gas REST API."""
    url = f"{base_url}?api={api}"
    if params:
        for k, v in params.items():
            url += f"&{k}={urllib.request.quote(str(v))}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
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


def _handle_auth_error():
    """Print auth expiry message and exit."""
    print("Error: Authentication token has expired.", file=sys.stderr)
    print("Get a fresh token from your keleo-studio-gas instance", file=sys.stderr)
    print("(Settings → API Token) and run:", file=sys.stderr)
    print("  python3 utils/studio-client.py --configure", file=sys.stderr)
    sys.exit(1)


def _load_cached_index():
    """Load the cached remote index if it exists."""
    index_path = get_project_root() / REMOTE_INDEX_PATH
    if not index_path.exists():
        return None
    try:
        with open(index_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def _save_index(data):
    """Save remote index to cache file."""
    index_path = get_project_root() / REMOTE_INDEX_PATH
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


def cmd_configure():
    """Interactive configuration of keleo-studio-gas credentials."""
    config = load_user_config()
    current_url = config.get("keleoStudioGasUrl", "")

    print("Configure keleo-studio-gas connection")
    print("=" * 40)

    url = input(f"Deployment URL [{current_url}]: ").strip()
    if not url:
        url = current_url
    if not url:
        print("Error: URL is required.", file=sys.stderr)
        sys.exit(1)

    token = input("API token (from Settings → API Token): ").strip()
    if not token:
        print("Error: Token is required.", file=sys.stderr)
        sys.exit(1)

    config["keleoStudioGasUrl"] = url
    config["keleoStudioGasToken"] = token
    save_user_config(config)
    print(f"\nSaved to .claude/user-config.json")

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


def cmd_check(name=None, as_json=False):
    """Compare local vs remote versions."""
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

        results.append({
            "name": doc_name,
            "localVersion": local_ver,
            "remoteVersion": remote_ver,
            "status": status,
            "localPath": local["path"] if local else None,
            "remoteSlug": remote.get("slug") if remote else None,
        })

    if as_json:
        print(json.dumps({"results": results}, indent=2))
        return results

    for r in results:
        lv = r["localVersion"] or "—"
        rv = r["remoteVersion"] or "—"
        indicator = {
            "up-to-date": "  ✓ up to date",
            "remote-newer": "  ← REMOTE NEWER",
            "local-newer": "  → LOCAL NEWER",
            "local-only": "  → LOCAL ONLY",
            "remote-only": "  ← REMOTE ONLY",
        }.get(r["status"], "")
        print(f"  {r['name']:40s} local: {lv:8s} remote: {rv:8s}{indicator}")

    return results


def cmd_pull(name, as_json=False):
    """Download a .keleo bundle from remote into bundles/."""
    url, token = _get_credentials()

    data, err = _api_get(url, token, "download", {"name": name})
    if err == "auth_expired":
        _handle_auth_error()
    if err:
        print(f"Error: {err}", file=sys.stderr)
        sys.exit(1)

    download_url = data.get("downloadUrl")
    if not download_url:
        print(f"Error: No download URL returned for '{name}'.", file=sys.stderr)
        print("The document may not exist on the remote.", file=sys.stderr)
        sys.exit(1)

    file_id_match = re.search(r"/d/([^/]+)/", download_url)
    if not file_id_match:
        file_id_match = re.search(r"id=([^&]+)", download_url)
    if not file_id_match:
        print(f"Error: Cannot extract file ID from download URL.", file=sys.stderr)
        sys.exit(1)

    file_id = file_id_match.group(1)
    slug = _slugify(name)
    bundles_dir = get_project_root() / "bundles"
    bundles_dir.mkdir(parents=True, exist_ok=True)
    output_path = bundles_dir / f"{slug}.keleo"

    gws_cmd = [
        "/opt/homebrew/bin/gws", "drive", "files", "get",
        "--params", json.dumps({"fileId": file_id, "alt": "media"}),
        "--output", str(output_path),
    ]

    try:
        result = subprocess.run(gws_cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            print(f"Error downloading bundle: {result.stderr.strip()}", file=sys.stderr)
            sys.exit(1)
    except FileNotFoundError:
        print("Error: gws CLI not found at /opt/homebrew/bin/gws", file=sys.stderr)
        print("Install it or download manually from:", file=sys.stderr)
        print(f"  {download_url}", file=sys.stderr)
        sys.exit(1)

    if not output_path.exists() or output_path.stat().st_size == 0:
        print(f"Error: Download produced empty file.", file=sys.stderr)
        sys.exit(1)

    if not zipfile.is_zipfile(output_path):
        print(f"Error: Downloaded file is not a valid ZIP archive.", file=sys.stderr)
        output_path.unlink()
        sys.exit(1)

    try:
        with zipfile.ZipFile(output_path, "r") as zf:
            if "manifest.json" not in zf.namelist():
                print(f"Error: Downloaded archive has no manifest.json.", file=sys.stderr)
                output_path.unlink()
                sys.exit(1)
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


def cmd_push(file_path, as_json=False):
    """Upload a .keleo bundle to remote."""
    path = Path(file_path)
    if not path.exists():
        print(f"Error: File not found: {path}", file=sys.stderr)
        sys.exit(1)

    if not zipfile.is_zipfile(path):
        print(f"Error: Not a valid .keleo archive: {path}", file=sys.stderr)
        sys.exit(1)

    try:
        with zipfile.ZipFile(path, "r") as zf:
            manifest = json.loads(zf.read("manifest.json"))
            pkg = manifest.get("package", {})
            local_name = manifest.get("name") or pkg.get("name", path.stem)
            local_version = manifest.get("version") or pkg.get("version", "?")
    except (zipfile.BadZipFile, json.JSONDecodeError, KeyError) as e:
        print(f"Error reading bundle: {e}", file=sys.stderr)
        sys.exit(1)

    url, token = _get_credentials()

    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")

    data, err = _api_post(url, token, "upload", b64)
    if err == "auth_expired":
        _handle_auth_error()
    if err:
        print(f"Error uploading: {err}", file=sys.stderr)
        sys.exit(1)

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
    group.add_argument("--check", nargs="?", const="", metavar="NAME",
                       help="Compare local vs remote versions (all or specific name)")
    group.add_argument("--pull", metavar="NAME",
                       help="Download a .keleo bundle from remote")
    group.add_argument("--push", metavar="FILE",
                       help="Upload a .keleo bundle to remote")

    parser.add_argument("--max-age", type=int, default=DEFAULT_MAX_AGE,
                        help=f"Max age in seconds for cached index (default: {DEFAULT_MAX_AGE})")
    parser.add_argument("--json", action="store_true",
                        help="Output as JSON")

    args = parser.parse_args()

    if args.configure:
        cmd_configure()
    elif args.status:
        cmd_status(as_json=args.json)
    elif args.index:
        cmd_index(max_age=args.max_age, as_json=args.json)
    elif args.check is not None:
        cmd_check(name=args.check or None, as_json=args.json)
    elif args.pull:
        cmd_pull(args.pull, as_json=args.json)
    elif args.push:
        cmd_push(args.push, as_json=args.json)


if __name__ == "__main__":
    main()
