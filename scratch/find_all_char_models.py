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

model_names = invoke('modelNames')
print("Model names in Anki:", model_names)

char_models = [m for m in model_names if 'Char' in m or 'Kanzi' in m or 'Kanji' in m]
print("Character models:", char_models)

# Get notes for each character model
for m in char_models:
    n_ids = invoke('findNotes', query=f'note:"{m}"')
    print(f"Model '{m}': {len(n_ids)} notes")
