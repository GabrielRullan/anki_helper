import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('scratch/tagging_results.json', 'r', encoding='utf-8') as f:
    tagging_data = json.load(f)

missing_hanzi_by_lesson = {}
all_missing_hanzi = []

for lvl in range(68, 89):
    lvl_str = str(lvl)
    t_info = tagging_data.get(lvl_str, {})
    missing_items = t_info.get('missing_items', [])
    if missing_items:
        missing_hanzi_by_lesson[lvl] = missing_items
        for h in missing_items:
            all_missing_hanzi.append((lvl, h))

print(f"Total missing Hanzi: {len(all_missing_hanzi)}")
for lvl, items in missing_hanzi_by_lesson.items():
    print(f"  Lesson {lvl} ({len(items)}): {', '.join(items)}")
