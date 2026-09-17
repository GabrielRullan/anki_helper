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

info = invoke('notesInfo', notes=[1786803210901, 1785483591772])
for n in info:
    print("Note ID:", n['noteId'])
    print("Model Name:", n['modelName'])
    print("Tags:", n['tags'])
    print("Fields:")
    for fname, fval in n['fields'].items():
        if fval['value']:
            print(f"  {fname}: {fval['value'][:80]}")
    print("---")
