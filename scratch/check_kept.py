import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('scratch/detailed_proposals.json', 'r', encoding='utf-8') as f:
    items = json.load(f)

kept = [it for it in items if not it['changed']]
print(f"Total kept as is: {len(kept)}\n")

for i, it in enumerate(kept, 1):
    print(f"{i:2d}. {it['hanzi']} [{it['pinyin']}]: \"{it['current_english']}\"")
