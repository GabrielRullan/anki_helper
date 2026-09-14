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

notes = invoke('findNotes', query='tag:lesson_10')
if notes:
    info = invoke('notesInfo', notes=[notes[0]])[0]
    print("Lesson 10 note fields:")
    for k, v in info['fields'].items():
        if 'http' in v['value'] or 'mandarin' in v['value'].lower():
            print(f"  Field {k}: {v['value']}")

notes_with_link = invoke('findNotes', query='model:"Chinese Character - Double" mandarin')
print("Notes matching query 'mandarin':", len(notes_with_link))
notes_with_http = invoke('findNotes', query='model:"Chinese Character - Double" http')
print("Notes matching query 'http':", len(notes_with_http))
