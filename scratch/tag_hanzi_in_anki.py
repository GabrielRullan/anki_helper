import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

def invoke(action, **params):
    req = urllib.request.Request(
        'http://127.0.0.1:8765',
        data=json.dumps({'action': action, 'version': 6, 'params': params}).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        if res.get('error'):
            raise Exception(res['error'])
        return res.get('result')

with open('scratch/levels_68_88.json', 'r', encoding='utf-8') as f:
    levels_data = json.load(f)

# First build a map of Hanzi -> NoteID for all notes of model "Chinese Character - Double"
print("Fetching all character notes from Anki...")
all_char_note_ids = invoke('findNotes', query='note:"Chinese Character - Double"')
print(f"Total character notes found: {len(all_char_note_ids)}")

# Retrieve notes info in batches of 500
hanzi_to_noteid = {}
batch_size = 500
for i in range(0, len(all_char_note_ids), batch_size):
    batch_ids = all_char_note_ids[i:i+batch_size]
    notes_info = invoke('notesInfo', notes=batch_ids)
    for info in notes_info:
        note_id = info['noteId']
        hanzi_val = info['fields'].get('Hanzi', {}).get('value', '').strip()
        if not hanzi_val:
            hanzi_val = info['fields'].get('Simplified', {}).get('value', '').strip()
        if hanzi_val:
            hanzi_to_noteid[hanzi_val] = note_id

print(f"Mapped {len(hanzi_to_noteid)} unique Hanzi to note IDs.")

tagged_summary = {}
total_tagged_count = 0

for lvl in range(68, 89):
    lvl_str = str(lvl)
    tag_name = f"MBP-{lvl}"
    data = levels_data.get(lvl_str, {})
    hanzi_list = data.get('All Characters', {}).get('new', [])

    tagged_in_this_level = []
    missing_in_this_level = []

    notes_to_tag = []

    for h in hanzi_list:
        if h in hanzi_to_noteid:
            n_id = hanzi_to_noteid[h]
            notes_to_tag.append(n_id)
            tagged_in_this_level.append((h, n_id))
        else:
            missing_in_this_level.append(h)

    if notes_to_tag:
        # Add tag via AnkiConnect
        invoke('addTags', notes=notes_to_tag, tags=tag_name)
        total_tagged_count += len(notes_to_tag)

    tagged_summary[lvl] = {
        'tag': tag_name,
        'total_hanzi': len(hanzi_list),
        'tagged_count': len(tagged_in_this_level),
        'tagged_items': [item[0] for item in tagged_in_this_level],
        'missing_count': len(missing_in_this_level),
        'missing_items': missing_in_this_level
    }

    print(f"Lesson {lvl} [{tag_name}]: Tagged {len(tagged_in_this_level)}/{len(hanzi_list)} Hanzi (Missing {len(missing_in_this_level)})")

print(f"\nFINISHED! Total Hanzi tagged with MBP-xx: {total_tagged_count}")

# Save detailed tagging log
with open('scratch/tagging_results.json', 'w', encoding='utf-8') as f:
    json.dump(tagged_summary, f, ensure_ascii=False, indent=2)

print("Saved tagging report to scratch/tagging_results.json")
