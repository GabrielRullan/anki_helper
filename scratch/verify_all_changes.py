import json
import re
import sys

with open('scratch/detailed_proposals.json', 'r', encoding='utf-8') as f:
    proposals = json.load(f)

with open('data/anki_extract.json', 'r', encoding='utf-8') as f:
    anki_data = json.load(f)

char_map = {c['note_id']: c for c in anki_data.get('characters', [])}

changed = [p for p in proposals if p['changed']]

with open('scratch/verify_output_utf8.txt', 'w', encoding='utf-8') as f:
    f.write(f"Total proposed changes: {len(changed)}\n\n")
    for i, p in enumerate(changed, 1):
        c = char_map[p['note_id']]
        scene = c.get('scene', '')
        clean_scene = re.sub(r'<[^>]+>', '', scene)
        f.write(f"=== {i}. {p['hanzi']} [{p['pinyin']}] (Note ID: {p['note_id']}) ===\n")
        f.write(f"  Current : \"{p['current_english']}\"\n")
        f.write(f"  Proposed: \"{p['proposed_english']}\"\n")
        f.write(f"  Reason  : {p['reason']}\n")
        f.write(f"  Scene   : {clean_scene[:140]}...\n\n")

print(f"Written {len(changed)} to scratch/verify_output_utf8.txt")
