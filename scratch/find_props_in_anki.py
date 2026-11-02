import sys
import os
import json
import urllib.request

sys.stdout.reconfigure(encoding='utf-8')
ANKICONNECT_URL = 'http://127.0.0.1:8765'

def request_anki(action, **params):
    payload = {"action": action, "version": 6}
    if params:
        payload["params"] = params
    req = urllib.request.Request(
        ANKICONNECT_URL,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode('utf-8')).get('result')

print("Model names in Anki:", request_anki("modelNames"))
print("Deck names in Anki:", request_anki("deckNames"))

# Check sample prop note id from anki_extract.json: 1775412213565
info = request_anki("notesInfo", notes=[1775412213565])
print("Note 1775412213565 in Anki:", info)
