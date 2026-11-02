import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('data/anki_extract.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

chars = data.get('characters', [])
print(f"Total characters: {len(chars)}")

in_english = [c for c in chars if '(' in c.get('english', '') or '（' in c.get('english', '')]
print(f"Characters with '(' in english: {len(in_english)}")

active_in_english = [c for c in in_english if not c.get('suspended', False)]
print(f"Active characters with '(' in english: {len(active_in_english)}")

print("\n=== ALL CHARACTERS WITH '(' IN ENGLISH ===")
for i, c in enumerate(in_english, 1):
    susp = " [SUSPENDED]" if c.get('suspended') else ""
    print(f"{i:3d}. {c.get('hanzi')} [{c.get('pinyin')}]: \"{c.get('english')}\"{susp} (id: {c.get('note_id')})")
