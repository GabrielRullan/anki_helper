import urllib.request
import json

def ankiconnect_request(action, **params):
    req_data = json.dumps({'action': action, 'version': 6, 'params': params}).encode('utf-8')
    req = urllib.request.Request('http://localhost:8765', req_data)
    with urllib.request.urlopen(req) as response:
        res = json.loads(response.read().decode('utf-8'))
        if res.get('error'):
            raise Exception(res['error'])
        return res['result']

# Find notes in Chinese::Words
word_note_ids = ankiconnect_request('findNotes', query='deck:"Chinese::Words"')
print(f"Total notes in Chinese::Words: {len(word_note_ids)}")

if word_note_ids:
    notes_info = ankiconnect_request('notesInfo', notes=word_note_ids[:5])
    print("\nSample note from Chinese::Words:")
    print(json.dumps(notes_info[0], indent=2, ensure_ascii=False))

# Also check Chinese::Char
char_note_ids = ankiconnect_request('findNotes', query='deck:"Chinese::Char"')
print(f"\nTotal notes in Chinese::Char: {len(char_note_ids)}")

# Also check Chinese::Sent
sent_note_ids = ankiconnect_request('findNotes', query='deck:"Chinese::Sent"')
print(f"Total notes in Chinese::Sent: {len(sent_note_ids)}")
