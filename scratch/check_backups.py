import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

for fname in [r'data\char_translation_backup.json', r'data\link_notes_backup.json']:
    print(f"=== Inspecting {fname} ===")
    with open(fname, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print("List length:", len(data))
    for item in data:
        # Check if item relates to ID 28
        fields = item.get('fields', {})
        if fields.get('ID') == '28' or fields.get('Hanzi') in ['⻢', '马']:
            print(f"Match found in {fname}:")
            print("Note ID:", item.get('id'))
            print("Notetype:", item.get('notetype'))
            print("Fields:")
            for k, v in fields.items():
                if v:
                    print(f"  {k}: {v}")
            print("-" * 40)
