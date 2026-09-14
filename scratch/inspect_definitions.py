import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

print("Checking available definition files...")

files_to_check = [
    'data/hsk4_cache.json',
    'data/chinese_defs_to_update.json',
    'data/english_defs_map.json',
    'data/all_words_to_translate.txt'
]

for fp in files_to_check:
    if os.path.exists(fp):
        size = os.path.getsize(fp)
        print(f"File {fp}: size = {size} bytes")
        if fp.endswith('.json'):
            try:
                with open(fp, 'r', encoding='utf-8') as f:
                    d = json.load(f)
                    print(f"  JSON keys/items count: {len(d)}")
                    if isinstance(d, dict):
                        k0 = list(d.keys())[0]
                        print(f"  Sample key '{k0}': {d[k0]}")
                    elif isinstance(d, list):
                        print(f"  Sample item 0: {d[0]}")
            except Exception as e:
                print(f"  Error reading {fp}: {e}")
