#!/usr/bin/env python3
"""
Fix contributesTo arrays in Alpha definitions.

The schema defines Alpha.contributesTo as a STRING (0..1), not an array.
This script converts arrays like ["Platform Asset"] to the string "Platform Asset".

Usage:
    python3 fix-contributesto-arrays.py <practice-file>.json
"""

import json
import sys
from pathlib import Path

def fix_alpha_contributesto(alphas):
    """Convert contributesTo arrays to strings in alpha definitions."""
    if not alphas:
        return alphas

    for alpha in alphas:
        if 'contributesTo' in alpha:
            if isinstance(alpha['contributesTo'], list):
                if len(alpha['contributesTo']) > 0:
                    # Take first element if array
                    alpha['contributesTo'] = alpha['contributesTo'][0]
                else:
                    # Remove empty array
                    del alpha['contributesTo']

    return alphas

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 fix-contributesto-arrays.py <practice-file>.json")
        sys.exit(1)

    file_path = Path(sys.argv[1])

    if not file_path.exists():
        print(f"Error: File not found: {file_path}")
        sys.exit(1)

    print(f"Loading {file_path}...")

    with open(file_path, 'r') as f:
        practice = json.load(f)

    print("Fixing Alpha.contributesTo arrays → strings...")

    if 'alphas' in practice:
        practice['alphas'] = fix_alpha_contributesto(practice['alphas'])
        print(f"  Fixed {len(practice['alphas'])} alphas")

    print(f"\nSaving fixed JSON to {file_path}...")
    with open(file_path, 'w') as f:
        json.dump(practice, f, indent=2)

    print("✓ All fixes applied successfully")

if __name__ == '__main__':
    main()
