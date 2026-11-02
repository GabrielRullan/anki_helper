import json
import re

with open('data/anki_extract.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

chars = data.get('characters', [])
with_paren = [c for c in chars if '(' in c.get('english', '') or '（' in c.get('english', '')]

print(f"Total matching: {len(with_paren)}")

# Let's inspect each one
results = []
for c in with_paren:
    eng = c.get('english', '')
    note_id = c.get('note_id')
    hanzi = c.get('hanzi')
    pinyin = c.get('pinyin')
    results.append({
        'note_id': note_id,
        'hanzi': hanzi,
        'pinyin': pinyin,
        'english': eng,
        'suspended': c.get('suspended', False),
        'hsk': c.get('hsk_level', '')
    })

with open('scratch/all_113_analysis.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print("Saved all 113 to scratch/all_113_analysis.json")
