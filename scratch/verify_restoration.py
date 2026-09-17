import urllib.request
import json
import time

# Give AnkiConnect 2 seconds to initialize
time.sleep(2)

def ankiconnect_request(action, **params):
    req_data = json.dumps({'action': action, 'version': 6, 'params': params}).encode('utf-8')
    req = urllib.request.Request('http://localhost:8765', req_data)
    with urllib.request.urlopen(req) as response:
        res = json.loads(response.read().decode('utf-8'))
        if res.get('error'):
            raise Exception(res['error'])
        return res['result']

print("--- Verifying restored card for '耶' (junda_1174_32822) ---")
note_ids = ankiconnect_request('findNotes', query='junda_1174_32822')
if note_ids:
    n_info = ankiconnect_request('notesInfo', notes=note_ids)
    card_ids = n_info[0]['cards']
    print(f"Cards for note {note_ids[0]}: {card_ids}")
    
    c_info = ankiconnect_request('cardsInfo', cards=card_ids)
    for c in c_info:
        print(f"\nCard ID: {c['cardId']} (ord={c['ord']}):")
        print(f"  Type    : {c['type']} (2=Review, 0=New)")
        print(f"  Queue   : {c['queue']} (2=Review, -1=Suspended)")
        print(f"  Reps    : {c['reps']}")
        print(f"  Lapses  : {c['lapses']}")
        print(f"  Interval: {c['interval']} days")
        print(f"  Factor  : {c['factor']}")
        print(f"  Due Day : {c['due']}")
