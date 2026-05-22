#!/usr/bin/env python3
"""Check for floating alphas (new alphas without contributesTo)"""
import json
import sys

# Load baseline alphas
with open('deps/platform-adoption-kernel.json') as f:
    baseline = json.load(f)
    baseline_alpha_names = {alpha['name'] for alpha in baseline['alphas']}

print(f"Found {len(baseline_alpha_names)} baseline alphas")
print()

# Check practice file
practice_file = sys.argv[1] if len(sys.argv) > 1 else 'practices/red-hat-ai-3/red-hat-ai-3.json'

with open(practice_file) as f:
    data = json.load(f)

# Check if it's a method or practice
if 'practices' in data:
    # Method - check each practice
    print(f"Checking Method: {data.get('name', 'Unknown')}")
    print()

    for practice in data['practices']:
        print(f"Practice: {practice.get('name', 'Unknown')}")
        alphas = practice.get('alphas', [])

        floating_alphas = []
        for alpha in alphas:
            alpha_name = alpha['name']
            contributes_to = alpha.get('contributesTo')

            # If alpha is NOT in baseline AND has no contributesTo, it's floating
            if alpha_name not in baseline_alpha_names:
                if not contributes_to or len(contributes_to) == 0:
                    floating_alphas.append(alpha_name)

        if floating_alphas:
            print(f"  ❌ FLOATING ALPHAS (new alphas without contributesTo):")
            for name in floating_alphas:
                print(f"     - {name}")
        else:
            print(f"  ✅ No floating alphas")
        print()
else:
    # Single practice
    print(f"Checking Practice: {data.get('name', 'Unknown')}")
    alphas = data.get('alphas', [])

    floating_alphas = []
    for alpha in alphas:
        alpha_name = alpha['name']
        contributes_to = alpha.get('contributesTo')

        # If alpha is NOT in baseline AND has no contributesTo, it's floating
        if alpha_name not in baseline_alpha_names:
            if not contributes_to or len(contributes_to) == 0:
                floating_alphas.append(alpha_name)

    if floating_alphas:
        print(f"❌ FLOATING ALPHAS (new alphas without contributesTo):")
        for name in floating_alphas:
            print(f"   - {name}")
    else:
        print(f"✅ No floating alphas")
