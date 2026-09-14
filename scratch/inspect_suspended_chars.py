import urllib.request
import json
import re
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

print("Fetching suspended character notes from Anki...")

# Query suspended character notes
suspended_note_ids = invoke('findNotes', query='is:suspended note:"Chinese Character - Double"')
print(f"Found {len(suspended_note_ids)} suspended notes of model 'Chinese Character - Double'.")

if not suspended_note_ids:
    print("Trying query 'is:suspended deck:\"Chinese::Char\"'...")
    suspended_note_ids = invoke('findNotes', query='is:suspended deck:"Chinese::Char"')
    print(f"Found {len(suspended_note_ids)} suspended notes in Chinese::Char deck.")

# Retrieve notes info
if suspended_note_ids:
    info_list = invoke('notesInfo', notes=suspended_note_ids[:30])
    print("\nSample suspended character notes:")
    for info in info_list[:15]:
        fields = info['fields']
        h = fields.get('Hanzi', {}).get('value', '').strip() or fields.get('Simplified', {}).get('value', '').strip()
        eng = fields.get('English', {}).get('value', '').strip()
        print(f"  Note ID {info['noteId']} | Hanzi: '{h}' | Current English: '{eng}'")
