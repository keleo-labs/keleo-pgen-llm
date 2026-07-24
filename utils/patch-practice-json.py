#!/usr/bin/env python3
"""
Patch a practice/baseline JSON file by merging content at a specified path.

Usage:
    # Merge keys at root level (set/overwrite top-level keys)
    python3 utils/patch-practice-json.py target.json --patch-file patch.json

    # Set a specific top-level key from a patch file containing just the value
    python3 utils/patch-practice-json.py target.json --set-key assets --patch-file assets.json

    # Append items to an existing array
    python3 utils/patch-practice-json.py target.json --append-key assets --patch-file more-assets.json

    # Patch a named element (alpha, activity, workProduct, pattern, etc.)
    python3 utils/patch-practice-json.py target.json --element-path "alphas[Platform]" --patch-file alpha-patch.json

    # Patch a narrative context by element name (field=value syntax)
    python3 utils/patch-practice-json.py target.json \
      --element-path "activities[Install Operator].narratives[0].narrativeContexts[narrativeElementName=Common Pitfalls]" \
      --patch-file context-patch.json

    # Read patch from stdin
    cat patch.json | python3 utils/patch-practice-json.py target.json --set-key assets

    # Preview changes without writing
    python3 utils/patch-practice-json.py target.json --patch-file patch.json --dry-run

    # Create a new file from patch (skeleton creation)
    python3 utils/patch-practice-json.py new-file.json --patch-file skeleton.json --create

    # Delete a top-level key
    python3 utils/patch-practice-json.py target.json --delete-key kind

    # Deep find-and-replace across all string values
    python3 utils/patch-practice-json.py target.json --replace "old text" "new text"

    # Bulk replacements from a JSON file (array of [old, new] pairs)
    python3 utils/patch-practice-json.py target.json --replace-file replacements.json
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils._shared import load_json


def resolve_element_path(data, path):
    """Resolve a dotted path like 'alphas[Platform]' or 'alphas[0].states[Ready]'.

    Supports:
      - 'key' — top-level key
      - 'key[Name]' — find item in array by name field
      - 'key[0]' — array index
      - 'key[Name].subkey' — chained access
      - 'key[Name].subkey[SubName]' — nested named lookup

    Returns (parent, key_or_index) so caller can do parent[key_or_index] = patch.
    """
    segments = re.findall(r'([^.\[\]]+)|\[([^\]]+)\]', path)
    tokens = []
    for bare, bracketed in segments:
        if bare:
            tokens.append(bare)
        elif bracketed:
            tokens.append(int(bracketed) if bracketed.isdigit() else bracketed)

    current = data
    for i, token in enumerate(tokens[:-1]):
        current = _navigate(current, token)

    return current, tokens[-1]


def _navigate(current, token):
    if isinstance(current, dict):
        return current[token]
    if isinstance(current, list):
        if isinstance(token, int):
            return current[token]
        if isinstance(token, str) and "=" in token:
            field, value = token.split("=", 1)
            for item in current:
                if isinstance(item, dict) and str(item.get(field)) == value:
                    return item
            raise KeyError(f"No element with {field}='{value}' in array")
        for item in current:
            if isinstance(item, dict) and item.get("name") == token:
                return item
        raise KeyError(f"No element with name '{token}' in array")
    raise KeyError(f"Cannot navigate into {type(current).__name__} with '{token}'")


def deep_replace(obj, old, new):
    """Recursively replace old with new in all string values."""
    if isinstance(obj, str):
        return obj.replace(old, new)
    if isinstance(obj, list):
        return [deep_replace(item, old, new) for item in obj]
    if isinstance(obj, dict):
        return {k: deep_replace(v, old, new) for k, v in obj.items()}
    return obj


def summarize_changes(key, value):
    if isinstance(value, list):
        return f"  {key}: set to array with {len(value)} items"
    if isinstance(value, dict):
        return f"  {key}: set to object with keys {list(value.keys())}"
    return f"  {key}: set to {json.dumps(value)[:80]}"


def main():
    parser = argparse.ArgumentParser(
        description="Patch a practice/baseline JSON file by merging content"
    )
    parser.add_argument("target", help="Target JSON file to patch")
    parser.add_argument("--patch-file", "-p",
                        help="JSON file containing patch content (default: read from stdin)")
    parser.add_argument("--set-key", "-k", metavar="KEY",
                        help="Set a specific top-level key to the patch value")
    parser.add_argument("--append-key", "-a", metavar="KEY",
                        help="Append patch array items to an existing array at KEY")
    parser.add_argument("--element-path", "-e", metavar="PATH",
                        help="Merge patch into element at PATH (e.g., 'alphas[Platform]')")
    parser.add_argument("--delete-key", "-d", metavar="KEY",
                        help="Delete a top-level key (no patch input needed)")
    parser.add_argument("--replace", nargs=2, metavar=("OLD", "NEW"),
                        help="Deep find-and-replace across all string values")
    parser.add_argument("--replace-file", metavar="FILE",
                        help="Bulk replacements from JSON file (array of [old, new] pairs)")
    parser.add_argument("--create", action="store_true",
                        help="Create target file if it doesn't exist")
    parser.add_argument("--dry-run", "-n", action="store_true",
                        help="Preview changes without writing")
    parser.add_argument("--output", "-o",
                        help="Write to a different file instead of patching in place")
    args = parser.parse_args()

    needs_patch = not (args.delete_key or args.replace or args.replace_file)

    if needs_patch:
        if args.patch_file:
            patch = load_json(args.patch_file)
        elif not sys.stdin.isatty():
            patch = json.load(sys.stdin)
        else:
            print("Error: provide --patch-file or pipe JSON to stdin", file=sys.stderr)
            sys.exit(1)
    else:
        patch = None

    target_path = Path(args.target)
    if target_path.exists():
        data = load_json(args.target)
    elif args.create:
        data = {}
    else:
        print(f"Error: {args.target} not found (use --create for new files)",
              file=sys.stderr)
        sys.exit(1)

    changes = []

    if args.delete_key:
        if args.delete_key in data:
            del data[args.delete_key]
            changes.append(f"  {args.delete_key}: deleted")
        else:
            changes.append(f"  {args.delete_key}: not present (no-op)")

    if args.replace:
        old_text, new_text = args.replace
        data = deep_replace(data, old_text, new_text)
        changes.append(
            f"  replace: \"{old_text[:60]}\" -> \"{new_text[:60]}\""
        )

    if args.replace_file:
        replacements = load_json(args.replace_file)
        if not isinstance(replacements, list):
            print("Error: --replace-file must contain a JSON array of [old, new] pairs",
                  file=sys.stderr)
            sys.exit(1)
        for pair in replacements:
            if not isinstance(pair, list) or len(pair) != 2:
                print(f"Error: each replacement must be [old, new], got: {pair}",
                      file=sys.stderr)
                sys.exit(1)
            data = deep_replace(data, pair[0], pair[1])
        changes.append(f"  replace-file: applied {len(replacements)} replacements")

    if needs_patch:
        if args.element_path:
            parent, final_key = resolve_element_path(data, args.element_path)
            target_obj = _navigate(parent, final_key) if not isinstance(final_key, int) or isinstance(parent, list) else parent[final_key]
            if isinstance(patch, dict) and isinstance(target_obj, dict):
                for k, v in patch.items():
                    target_obj[k] = v
                    changes.append(summarize_changes(f"{args.element_path}.{k}", v))
            else:
                if isinstance(parent, list) and isinstance(final_key, int):
                    parent[final_key] = patch
                elif isinstance(parent, dict):
                    parent[final_key] = patch
                else:
                    for i, item in enumerate(parent):
                        if isinstance(item, dict) and item.get("name") == final_key:
                            parent[i] = patch
                            break
                changes.append(summarize_changes(args.element_path, patch))

        elif args.set_key:
            data[args.set_key] = patch
            changes.append(summarize_changes(args.set_key, patch))

        elif args.append_key:
            if not isinstance(patch, list):
                patch = [patch]
            existing = data.get(args.append_key, [])
            if not isinstance(existing, list):
                print(f"Error: '{args.append_key}' is not an array", file=sys.stderr)
                sys.exit(1)
            before_count = len(existing)
            existing.extend(patch)
            data[args.append_key] = existing
            changes.append(
                f"  {args.append_key}: appended {len(patch)} items "
                f"({before_count} -> {len(existing)})"
            )

        elif isinstance(patch, dict):
            for k, v in patch.items():
                data[k] = v
                changes.append(summarize_changes(k, v))
        else:
            print("Error: root-level merge requires a JSON object as patch",
                  file=sys.stderr)
            sys.exit(1)

    out_path = args.output or args.target
    if args.dry_run:
        print("Dry run — changes that would be applied:")
        for c in changes:
            print(c)
        print(f"\nTarget: {out_path} (not written)")
    else:
        with open(out_path, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print(f"Patched {out_path}:")
        for c in changes:
            print(c)


if __name__ == "__main__":
    main()
