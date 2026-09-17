import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('scratch/all_anki_characters_raw.json', 'r', encoding='utf-8') as f:
    notes = json.load(f)

empty_cw = 0
has_cw = 0

tags_count = {}

for n in notes:
    cw = n.get('common_words', '').strip()
    if cw:
        has_cw += 1
    else:
        empty_cw += 1

    tags = n.get('tags', [])
    for t in tags:
        tags_count[t] = tags_count.get(t, 0) + 1

print(f"Total Character Cards in Anki: {len(notes)}")
print(f"  Has Common Words: {has_cw}")
print(f"  Empty Common Words: {empty_cw}")

# Sample top tags
sorted_tags = sorted(tags_count.items(), key=lambda x: x[1], reverse=True)
print("\nTop Tags sample:")
for t, cnt in sorted_tags[:20]:
    print(f"  {t}: {cnt}")
