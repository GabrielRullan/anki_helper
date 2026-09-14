import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('scratch/extracted_common_words.json', 'r', encoding='utf-8') as f:
    items = json.load(f)

empty_cw_count = 0
has_cw_count = 0
empty_items = []

for item in items:
    cw = item.get('common_words', '').strip()
    if cw:
        has_cw_count += 1
    else:
        empty_cw_count += 1
        empty_items.append(item)

print(f"Total character notes: {len(items)}")
print(f"Has Common Words: {has_cw_count}")
print(f"Empty Common Words: {empty_cw_count}")

if empty_items:
    print("Sample empty items:")
    for e in empty_items[:10]:
        print(f"  Lesson {e['lesson']} | {e['hanzi']} ({e['pinyin']}): {e['english']}")
