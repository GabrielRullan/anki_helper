import urllib.request
import json
import os
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

print("Fetching ALL character notes from Anki...")

all_note_ids = invoke('findNotes', query='note:"Chinese Character - Double"')
print(f"Found {len(all_note_ids)} character notes in total.")

# Retrieve in batches of 500
all_character_data = []
batch_size = 500

for i in range(0, len(all_note_ids), batch_size):
    batch = all_note_ids[i:i+batch_size]
    notes_info = invoke('notesInfo', notes=batch)
    for info in notes_info:
        fields = info['fields']
        h = fields.get('Hanzi', {}).get('value', '').strip() or fields.get('Simplified', {}).get('value', '').strip()
        p = fields.get('Pinyin', {}).get('value', '').strip()
        e = fields.get('English', {}).get('value', '').strip()
        cw = fields.get('Common Words', {}).get('value', '').strip()
        tw = fields.get('Translation of Words', {}).get('value', '').strip()
        mbp_lvl = fields.get('MBP_Level', {}).get('value', '').strip()
        tags = info.get('tags', [])

        all_character_data.append({
            'note_id': info['noteId'],
            'hanzi': h,
            'pinyin': p,
            'english': e,
            'common_words': cw,
            'translation_words': tw,
            'mbp_level': mbp_lvl,
            'tags': tags
        })

print(f"Extracted {len(all_character_data)} character notes.")

# Save raw extraction to JSON
with open('scratch/all_anki_characters_raw.json', 'w', encoding='utf-8') as f:
    json.dump(all_character_data, f, ensure_ascii=False, indent=2)

print("Saved raw extraction to scratch/all_anki_characters_raw.json")
