import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')
ANKICONNECT_URL = 'http://127.0.0.1:8765'

def invoke(action, **params):
    req = urllib.request.Request(
        ANKICONNECT_URL,
        data=json.dumps({'action': action, 'version': 6, 'params': params}).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        if res.get('error'):
            raise Exception(res['error'])
        return res.get('result')

with open('scratch/levels_68_88.json', 'r', encoding='utf-8') as f:
    levels_data = json.load(f)

print("Fetching all character notes from Anki...")
all_char_note_ids = invoke('findNotes', query='note:"Chinese Character - Double"')
print(f"Total character notes found: {len(all_char_note_ids)}")

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

total_tagged = 0

for lvl in range(68, 89):
    lvl_str = str(lvl)
    lesson_tag = f"lesson_{lvl}"
    hanzi_list = levels_data.get(lvl_str, {}).get('All Characters', {}).get('new', [])

    notes_to_tag = []
    for h in hanzi_list:
        if h in hanzi_to_noteid:
            notes_to_tag.append(hanzi_to_noteid[h])

    if notes_to_tag:
        invoke('addTags', notes=notes_to_tag, tags=lesson_tag)
        total_tagged += len(notes_to_tag)
        print(f"Lesson {lvl}: Applied tag '{lesson_tag}' to {len(notes_to_tag)} / {len(hanzi_list)} Hanzi notes.")

print(f"\nFINISHED! Total character notes tagged with lesson_xx: {total_tagged}")
