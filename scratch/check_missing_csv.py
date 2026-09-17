import csv
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('scratch/get_missing_items.py', 'r', encoding='utf-8') as f:
    pass

with open('scratch/tagging_results.json', 'r', encoding='utf-8') as f:
    tagging_data = json.load(f)

missing_63 = []
for lvl in range(68, 89):
    lvl_str = str(lvl)
    items = tagging_data.get(lvl_str, {}).get('missing_items', [])
    for h in items:
        missing_63.append((lvl, h))

print(f"63 Missing Hanzi list: {[h for lvl, h in missing_63]}")

# Check data/new_characters.csv
csv_data = {}
csv_path = 'data/new_characters.csv'
if os.path.exists(csv_path):
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            char = row.get('Hanzi') or row.get('Simplified') or row.get('Character')
            if char:
                csv_data[char] = row

found_in_csv = 0
for lvl, h in missing_63:
    if h in csv_data:
        found_in_csv += 1
        print(f"Found '{h}' in csv! Pinyin: {csv_data[h].get('Pinyin')}, Meaning: {csv_data[h].get('English') or csv_data[h].get('Meaning')}")
    else:
        print(f"Not in csv: '{h}' (Lesson {lvl})")

print(f"\nFound {found_in_csv} / 63 missing characters in data/new_characters.csv!")
