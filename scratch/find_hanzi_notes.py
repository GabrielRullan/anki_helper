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

# Test finding a few notes in character decks or chinese decks
notes_char_deck = invoke('findNotes', query='deck:"*Char*"')
print(f"Found {len(notes_char_deck)} notes in *Char* deck.")

if notes_char_deck:
    info = invoke('notesInfo', notes=[notes_char_deck[0]])
    print("Sample note info in Char deck:")
    print(json.dumps(info, ensure_ascii=False, indent=2))
