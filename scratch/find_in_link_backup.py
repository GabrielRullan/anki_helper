import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('data/link_notes_backup.json', 'r', encoding='utf-8') as f:
    items = json.load(f)

print(f"Total items in link_notes_backup.json: {len(items)}")

found = 0
for item in items:
    f = item.get('fields', {})
    if f.get('ID') == '28' or f.get('Hanzi') == '⻢':
        print("Found 28/⻢:")
        print("Fields:")
        for k, v in f.items():
            print(f"  {k}: {repr(v)}")
        found += 1
        
print(f"Total matching items: {found}")
