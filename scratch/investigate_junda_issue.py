import json
import urllib.request

def ankiconnect_request(action, **params):
    req_data = json.dumps({'action': action, 'version': 6, 'params': params}).encode('utf-8')
    req = urllib.request.Request('http://localhost:8765', req_data)
    with urllib.request.urlopen(req) as response:
        res = json.loads(response.read().decode('utf-8'))
        if res.get('error'):
            raise Exception(res['error'])
        return res['result']

print("--- Searching for note containing junda_1174_32822 ---")
# Try searching by text or tag
notes_by_tag = ankiconnect_request('findNotes', query='tag:*junda*')
print(f"Notes with tag *junda*: {len(notes_by_tag)}")

notes_by_text = ankiconnect_request('findNotes', query='junda_1174_32822')
print(f"Notes with text junda_1174_32822: {len(notes_by_text)}")

if not notes_by_text:
    notes_by_text = ankiconnect_request('findNotes', query='*1174_32822*')
    print(f"Notes matching *1174_32822*: {len(notes_by_text)}")

if not notes_by_text:
    notes_by_text = ankiconnect_request('findNotes', query='*junda*')
    print(f"Notes matching *junda*: {len(notes_by_text)}")

target_note_ids = notes_by_text if notes_by_text else notes_by_tag
if target_note_ids:
    print(f"\nFound {len(target_note_ids)} matching notes.")
    # Inspect first 5
    info = ankiconnect_request('notesInfo', notes=target_note_ids[:5])
    for n in info:
        print(f"\n--- Note ID {n['noteId']} (Model: {n['modelName']}, Tags: {n['tags']}) ---")
        print("Fields:")
        for fname, fval in n['fields'].items():
            print(f"  {fname}: {fval['value'][:100]}")
        print(f"Cards count: {len(n['cards'])}")
        # Inspect card info
        cards_info = ankiconnect_request('cardsInfo', cards=n['cards'])
        for c in cards_info:
            print(f"  Card ID {c['cardId']}: ord={c['ord']}, type={c['type']}, queue={c['queue']}, reps={c['reps']}, lapses={c['lapses']}, due={c['due']}")
