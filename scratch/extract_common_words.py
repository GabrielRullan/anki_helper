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

print("Fetching character notes for Lessons 68 to 88...")

# Query notes tagged MBP-68 through MBP-88
all_character_notes = []
for lvl in range(68, 89):
    notes = invoke('findNotes', query=f'tag:MBP-{lvl}')
    if notes:
        info_list = invoke('notesInfo', notes=notes)
        for info in info_list:
            fields = info['fields']
            h = fields.get('Hanzi', {}).get('value', '').strip() or fields.get('Simplified', {}).get('value', '').strip()
            p = fields.get('Pinyin', {}).get('value', '').strip()
            e = fields.get('English', {}).get('value', '').strip()
            cw = fields.get('Common Words', {}).get('value', '').strip()
            tw = fields.get('Translation of Words', {}).get('value', '').strip()

            all_character_notes.append({
                'lesson': lvl,
                'tag': f"MBP-{lvl}",
                'hanzi': h,
                'pinyin': p,
                'english': e,
                'common_words': cw,
                'translation_words': tw
            })

print(f"Retrieved {len(all_character_notes)} character notes across Lessons 68-88.")

# Check sample entries
for item in all_character_notes[:10]:
    print(f"Lesson {item['lesson']} | {item['hanzi']} ({item['pinyin']}): Common Words -> '{item['common_words']}' | Translations -> '{item['translation_words']}'")

# Save extracted common words to JSON
with open('scratch/extracted_common_words.json', 'w', encoding='utf-8') as f:
    json.dump(all_character_notes, f, ensure_ascii=False, indent=2)

print("Saved extracted common words to scratch/extracted_common_words.json")
