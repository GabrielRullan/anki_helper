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

for lvl in [68, 72, 80, 88]:
    notes = invoke('findNotes', query=f'tag:lesson_{lvl}')
    print(f"Notes with tag 'lesson_{lvl}': {len(notes)}")
    if notes:
        info = invoke('notesInfo', notes=[notes[0]])
        hanzi = info[0]['fields'].get('Hanzi', {}).get('value', '')
        tags = info[0]['tags']
        print(f"  Sample note: Hanzi '{hanzi}', Tags: {tags}")
