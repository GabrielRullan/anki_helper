import json
import urllib.request
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

with open('scratch/all_anki_characters_raw.json', 'r', encoding='utf-8') as f:
    notes = json.load(f)

empty_notes = [n for n in notes if not n.get('common_words', '').strip()]

print(f"Found {len(empty_notes)} notes with empty Common Words:")
for n in empty_notes:
    print(f"  Note ID {n['note_id']}: Hanzi '{n['hanzi']}' ({n['pinyin']}) - English '{n['english']}'")

# Map words for these characters if any
fix_map = {
    '夌': ('高夌, 夌霄', 'High mound, Soar to the sky'),
    '雚': ('雚芦, 雚草', 'Heron/reeds, Reed grass'),
    '孛': ('彗孛, 孛星', 'Comet, Shooting star')
}

for n in empty_notes:
    h = n['hanzi']
    if h in fix_map:
        cw, tw = fix_map[h]
        invoke('updateNoteFields', note={
            'id': n['note_id'],
            'fields': {
                'Common Words': cw,
                'Translation of Words': tw
            }
        })
        print(f"Updated note ID {n['note_id']} for '{h}'")
