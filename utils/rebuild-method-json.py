#!/usr/bin/env python3
"""
Rebuild Method JSON from individual practice JSON files.

This script assembles a complete Method object by reading individual practice
JSON files and combining them with method-level metadata.

Usage:
    # From method directory with practice-N-*.json files
    python3 rebuild-method-json.py

    # Or specify method name and practice files
    python3 rebuild-method-json.py method-name.json practice-1.json practice-2.json ...

Expects:
- Method skeleton JSON with metadata (can be minimal)
- Individual practice JSON files (practice-1-*.json, practice-2-*.json, etc.)

Produces:
- Complete method JSON with embedded practices array
"""

import json
import os
import sys
from pathlib import Path


def find_practice_files():
    """Auto-discover practice JSON files in current directory."""
    practice_files = sorted([
        f for f in os.listdir('.')
        if f.startswith('practice-') and f.endswith('.json')
    ])
    return practice_files


def find_method_file():
    """Auto-discover method JSON file (not starting with 'practice-')."""
    method_files = [
        f for f in os.listdir('.')
        if f.endswith('.json')
        and not f.startswith('practice-')
        and not f.startswith('cross-reference')
    ]

    if len(method_files) == 1:
        return method_files[0]
    elif len(method_files) == 0:
        return None
    else:
        # Multiple candidates - try to find the most likely one
        for f in method_files:
            if '-' in f and not f.startswith('rebuild'):
                return f
        return method_files[0]


def main():
    if len(sys.argv) > 1:
        # Explicit file specification
        method_file = sys.argv[1]
        practice_files = sys.argv[2:] if len(sys.argv) > 2 else find_practice_files()
    else:
        # Auto-discovery mode
        method_file = find_method_file()
        practice_files = find_practice_files()

    if not method_file:
        print("Error: Could not find method JSON file.")
        print("Usage: python3 rebuild-method-json.py [method.json practice-1.json ...]")
        sys.exit(1)

    if not practice_files:
        print("Error: No practice JSON files found.")
        print("Expected files: practice-1-*.json, practice-2-*.json, etc.")
        sys.exit(1)

    print(f"Rebuilding Method JSON: {method_file}")
    print(f"Found {len(practice_files)} practice file(s):\n")

    # Read method metadata
    with open(method_file, 'r') as f:
        method_data = json.load(f)

    # Read practice files
    practices = []
    for practice_file in practice_files:
        print(f"  Reading {practice_file}...")
        with open(practice_file, 'r') as f:
            practice_data = json.load(f)
            practices.append(practice_data)

    # Update method with practices
    method_data['practices'] = practices

    # Write complete method JSON
    output_file = method_file
    print(f"\nWriting complete Method JSON to {output_file}...")
    with open(output_file, 'w') as f:
        json.dump(method_data, f, indent=2)

    print(f"\n✓ Success! Method JSON rebuilt with {len(practices)} practice(s).")
    print(f"File size: {os.path.getsize(output_file):,} bytes")


if __name__ == "__main__":
    main()
