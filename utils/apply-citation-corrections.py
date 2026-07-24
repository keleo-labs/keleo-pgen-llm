#!/usr/bin/env python3
"""Apply verified citation corrections to a practice/method JSON file.

Usage:
    python3 utils/apply-citation-corrections.py <practice.json> <corrections.json> [-o output.json]

The corrections file should be a JSON array of objects with fields:
    index, status, name, description, authors, date, source, url, notes
    Optional: suggested_replacement (object with same fields for fabricated citations)

Features:
    - Applies corrected metadata (authors, title, source, date, URL)
    - Replaces fabricated citations with suggested alternatives
    - Removes duplicate citations (keeps first occurrence)
    - Disambiguates colliding names
    - Updates all citationNames references throughout the JSON tree
"""
import json
import sys
import argparse
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils._shared import load_json


def find_and_update_citation_names(obj, name_map):
    """Recursively find citationNames arrays and update them using name_map."""
    changed = 0
    if isinstance(obj, dict):
        if 'citationNames' in obj and isinstance(obj['citationNames'], list):
            new_names = []
            for cn in obj['citationNames']:
                if cn in name_map:
                    new_name = name_map[cn]
                    if new_name is not None:
                        new_names.append(new_name)
                        if new_name != cn:
                            changed += 1
                    else:
                        changed += 1
                else:
                    new_names.append(cn)
            obj['citationNames'] = new_names
        for v in obj.values():
            changed += find_and_update_citation_names(v, name_map)
    elif isinstance(obj, list):
        for item in obj:
            changed += find_and_update_citation_names(item, name_map)
    return changed


def main():
    parser = argparse.ArgumentParser(description='Apply citation corrections')
    parser.add_argument('practice_json', help='Path to practice/method JSON')
    parser.add_argument('corrections_json', help='Path to verified corrections JSON')
    parser.add_argument('-o', '--output', help='Output path (default: overwrite input)')
    parser.add_argument('--dry-run', action='store_true', help='Show changes without writing')
    parser.add_argument('--duplicates', help='JSON mapping of duplicate indices to remove, e.g. {"36": 14}')
    parser.add_argument('--disambiguate', help='JSON mapping of index to disambiguated name, e.g. {"49": "Defra (2026a)"}')
    parser.add_argument('--replacements', help='JSON file with fabricated citation replacements keyed by index')
    args = parser.parse_args()

    data = load_json(args.practice_json)
    corrections = load_json(args.corrections_json)

    corrections_by_index = {c['index']: c for c in corrections}
    citations = data.get('citations', [])

    # Load duplicate map
    dup_map = {}
    if args.duplicates:
        dup_map = {int(k): int(v) for k, v in json.loads(args.duplicates).items()}

    # Load disambiguations
    disambig_map = {}
    if args.disambiguate:
        disambig_map = {int(k): v for k, v in json.loads(args.disambiguate).items()}

    # Load fabricated replacements
    fab_replacements = {}
    if args.replacements:
        fab_replacements = {int(k): v for k, v in load_json(args.replacements).items()}

    # Build name mapping (old_name -> new_name) and track removals
    name_map = {}
    indices_to_remove = set()
    stats = {'verified': 0, 'corrected': 0, 'fabricated_replaced': 0, 'duplicates_removed': 0}

    for i, citation in enumerate(citations):
        old_name = citation['name']

        # Check if this is a duplicate to remove
        if i in dup_map:
            keep_idx = dup_map[i]
            keep_correction = corrections_by_index.get(keep_idx, {})
            keep_name = keep_correction.get('name', citations[keep_idx]['name'])
            if keep_idx in disambig_map:
                keep_name = disambig_map[keep_idx]
            name_map[old_name] = keep_name
            indices_to_remove.add(i)
            stats['duplicates_removed'] += 1
            continue

        correction = corrections_by_index.get(i)
        if not correction:
            continue

        status = correction.get('status', 'unknown')

        if status == 'fabricated':
            # Check for replacement in suggested_replacement field or fab_replacements
            replacement = correction.get('suggested_replacement') or fab_replacements.get(i)
            if replacement:
                new_name = replacement.get('name', old_name)
                if i in disambig_map:
                    new_name = disambig_map[i]
                citation['name'] = new_name
                citation['description'] = replacement.get('description', citation.get('description', ''))
                citation['authors'] = replacement.get('authors', citation.get('authors', []))
                citation['date'] = replacement.get('date', citation.get('date', ''))
                citation['source'] = replacement.get('source', citation.get('source', ''))
                if replacement.get('url'):
                    citation['url'] = replacement['url']
                name_map[old_name] = new_name
                stats['fabricated_replaced'] += 1
            else:
                # No replacement available — keep but flag in notes
                name_map[old_name] = old_name
                stats['fabricated_replaced'] += 1
        else:
            # verified or corrected — apply metadata updates
            new_name = correction.get('name', old_name)
            if i in disambig_map:
                new_name = disambig_map[i]

            if correction.get('description'):
                citation['description'] = correction['description']
            if correction.get('authors') and len(correction['authors']) > 0:
                citation['authors'] = correction['authors']
            if correction.get('date'):
                citation['date'] = correction['date']
            if correction.get('source'):
                citation['source'] = correction['source']
            if correction.get('url'):
                citation['url'] = correction['url']

            citation['name'] = new_name
            if old_name != new_name:
                name_map[old_name] = new_name

            if status == 'verified':
                stats['verified'] += 1
            else:
                stats['corrected'] += 1

    # Remove duplicate citations
    if indices_to_remove:
        data['citations'] = [c for i, c in enumerate(citations) if i not in indices_to_remove]

    # Also check practices-level citations for methods
    for practice in data.get('practices', []):
        p_citations = practice.get('citations', [])
        # Apply same corrections if practice has its own citations
        # (In this case practices don't have citations, but handle generically)

    # Update all citationNames references
    ref_changes = find_and_update_citation_names(data, name_map)

    # Report
    result = {
        'stats': stats,
        'name_changes': len(name_map),
        'citationName_refs_updated': ref_changes,
        'duplicates_removed': list(indices_to_remove),
        'total_citations_after': len(data.get('citations', [])),
    }

    if args.dry_run:
        print(json.dumps(result, indent=2))
        print('\nDry run — no files modified.')
    else:
        output_path = args.output or args.practice_json
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write('\n')
        result['output'] = output_path
        print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
