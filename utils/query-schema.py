#!/usr/bin/env python3
"""Query Practice Language schema definitions.

Extracts and displays $defs type definitions from language.schema.json.
Auto-discovers the schema at deps/language.schema.json relative to the
project root.

Usage:
    python3 utils/query-schema.py Method
    python3 utils/query-schema.py Asset --properties
    python3 utils/query-schema.py --list
    python3 utils/query-schema.py Method --json
"""

import argparse
import json
import sys
from pathlib import Path


def find_schema():
    """Auto-discover language.schema.json relative to this script."""
    script_dir = Path(__file__).resolve().parent
    candidates = [
        script_dir.parent / "deps" / "language.schema.json",
        script_dir / "language.schema.json",
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


def resolve_ref(schema, ref):
    """Resolve a $ref string to the target definition."""
    if not ref.startswith("#/"):
        return None
    parts = ref.lstrip("#/").split("/")
    target = schema
    for part in parts:
        if isinstance(target, dict):
            target = target.get(part)
        else:
            return None
    return target


def format_type(prop, schema):
    """Format a property's type as a compact string."""
    if "$ref" in prop:
        ref = prop["$ref"]
        return ref.split("/")[-1]
    t = prop.get("type", "")
    if t == "array":
        items = prop.get("items", {})
        if "$ref" in items:
            return f"[{items['$ref'].split('/')[-1]}]"
        return f"[{items.get('type', '?')}]"
    if "enum" in prop:
        vals = prop["enum"]
        if len(vals) <= 5:
            return f"enum({', '.join(repr(v) for v in vals)})"
        return f"enum({len(vals)} values)"
    if "oneOf" in prop:
        parts = []
        for option in prop["oneOf"]:
            if "$ref" in option:
                parts.append(option["$ref"].split("/")[-1])
            else:
                parts.append(option.get("type", "?"))
        return " | ".join(parts)
    if "const" in prop:
        return f"const({prop['const']!r})"
    if "pattern" in prop and t == "string":
        return f"string(/{prop['pattern']}/)"
    return t or "?"


def display_definition(name, defn, schema, show_properties=False, as_json=False):
    """Display a single schema definition."""
    if as_json:
        print(json.dumps({name: defn}, indent=2))
        return

    desc = defn.get("description", "")
    dtype = defn.get("type", "")

    print(f"=== {name} ===")
    if desc:
        print(f"  {desc}")
    if dtype:
        print(f"  Type: {dtype}")

    if "enum" in defn:
        print(f"  Values: {', '.join(repr(v) for v in defn['enum'])}")
        return

    props = defn.get("properties", {})
    required = set(defn.get("required", []))

    if "allOf" in defn:
        for part in defn["allOf"]:
            if "$ref" in part:
                ref_name = part["$ref"].split("/")[-1]
                resolved = resolve_ref(schema, part["$ref"])
                if resolved:
                    props = {**resolved.get("properties", {}), **props}
                    required = required | set(resolved.get("required", []))
                print(f"  Extends: {ref_name}")
            elif "properties" in part:
                props = {**props, **part["properties"]}
                required = required | set(part.get("required", []))

    if not props:
        return

    print(f"\n  Properties ({len(props)}):")
    for pname in sorted(props.keys()):
        pdef = props[pname]
        marker = "*" if pname in required else " "
        ptype = format_type(pdef, schema)
        line = f"    {marker} {pname}: {ptype}"
        if show_properties and pdef.get("description"):
            desc_text = pdef["description"]
            if len(desc_text) > 80:
                desc_text = desc_text[:77] + "..."
            line += f"  — {desc_text}"
        print(line)

    if required:
        print(f"\n  (* = required)")


def main():
    parser = argparse.ArgumentParser(
        description="Query Practice Language schema definitions"
    )
    parser.add_argument("type_name", nargs="?",
                        help="Name of the $defs type to display (e.g., Method, Asset, Alpha)")
    parser.add_argument("--schema", metavar="FILE",
                        help="Path to language.schema.json (default: auto-discover)")
    parser.add_argument("--list", action="store_true",
                        help="List all available $defs type names")
    parser.add_argument("--properties", action="store_true",
                        help="Show property descriptions (compact view)")
    parser.add_argument("--json", action="store_true",
                        help="Output raw JSON definition")
    args = parser.parse_args()

    schema_path = Path(args.schema) if args.schema else find_schema()
    if not schema_path or not schema_path.exists():
        print("Error: Cannot find language.schema.json. Use --schema to specify.",
              file=sys.stderr)
        sys.exit(1)

    with open(schema_path) as f:
        schema = json.load(f)

    defs = schema.get("$defs", {})
    if not defs:
        print("Error: No $defs found in schema.", file=sys.stderr)
        sys.exit(1)

    if args.list:
        for name in sorted(defs.keys()):
            desc = defs[name].get("description", "")
            if desc and len(desc) > 60:
                desc = desc[:57] + "..."
            print(f"  {name:35s} {desc}")
        print(f"\n{len(defs)} types available")
        return

    if not args.type_name:
        parser.print_help()
        sys.exit(1)

    if args.type_name not in defs:
        matches = [n for n in defs if args.type_name.lower() in n.lower()]
        if matches:
            print(f"Type '{args.type_name}' not found. Did you mean:", file=sys.stderr)
            for m in matches:
                print(f"  {m}", file=sys.stderr)
        else:
            print(f"Type '{args.type_name}' not found. Use --list to see available types.",
                  file=sys.stderr)
        sys.exit(1)

    display_definition(args.type_name, defs[args.type_name], schema,
                       show_properties=args.properties, as_json=args.json)


if __name__ == "__main__":
    main()
