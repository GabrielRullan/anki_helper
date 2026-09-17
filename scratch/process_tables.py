import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('scratch/levels_68_88.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Level summary:")
total_new_words = 0
total_new_hanzi = 0

for lvl in range(68, 89):
    lvl_str = str(lvl)
    lvl_data = data.get(lvl_str, {})
    new_words = lvl_data.get('All Words', {}).get('new', [])
    new_hanzi = lvl_data.get('All Characters', {}).get('new', [])
    total_new_words += len(new_words)
    total_new_hanzi += len(new_hanzi)
    print(f"Level {lvl}: {len(new_hanzi)} Hanzi, {len(new_words)} Words")

print(f"\nTOTAL across 68-88: {total_new_hanzi} Hanzi, {total_new_words} Words")
