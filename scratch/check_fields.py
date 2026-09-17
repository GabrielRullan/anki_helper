import json, urllib.request, sys
sys.stdout.reconfigure(encoding='utf-8')

def req(action, **params):
    payload = {'action': action, 'version': 6}
    if params: payload['params'] = params
    r = urllib.request.Request('http://127.0.0.1:8765', data=json.dumps(payload).encode('utf-8'), headers={'Content-Type':'application/json'})
    return json.loads(urllib.request.urlopen(r).read().decode('utf-8')).get('result')

nids = req('findNotes', query='deck:Chinese::Char')
notes = []
for i in range(0, len(nids), 500):
    notes.extend(req('notesInfo', notes=nids[i:i+500]))

print(f"Total notes in Chinese::Char: {len(notes)}")

for n in notes[:15]:
    f = n['fields']
    hz = f.get('Hanzi', {}).get('value', '')
    ft = f.get('FrequencyTier', {}).get('value', '')
    fr = f.get('FrequencyRank', {}).get('value', '')
    print(f"Note {n['noteId']}: Hanzi={hz:3s} | FrequencyTier={repr(ft)} | FrequencyRank={repr(fr)}")
