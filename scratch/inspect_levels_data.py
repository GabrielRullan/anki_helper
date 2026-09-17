import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

for fname in ['scratch/levels_68_88.json', 'scratch/annotated_anki_68_88.json']:
    if os.path.exists(fname):
        with open(fname, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"=== {fname} ===")
        print("Type:", type(data))
        if isinstance(data, dict):
            print("Keys count:", len(data))
            print("Sample keys:", list(data.keys())[:10])
            first_val = list(data.values())[0]
            print("Sample val:", first_val)
        elif isinstance(data, list):
            print("List length:", len(data))
            print("Sample item:", data[0])
