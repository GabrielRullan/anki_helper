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

for lvl in [68, 72, 88]:
    notes = invoke('findNotes', query=f'tag:MBP-{lvl}')
    print(f"Notes with tag 'MBP-{lvl}': {len(notes)}")
    if notes:
        info = invoke('notesInfo', notes=[notes[0]])
        hanzi = info[0]['fields'].get('Hanzi', {}).get('value', '')
        tags = info[0]['tags']
        print(f"  Sample note: Hanzi '{hanzi}', Tags: {tags}")
