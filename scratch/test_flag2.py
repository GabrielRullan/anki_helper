import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

def anki_req(action, **params):
    payload = {"action": action, "version": 6}
    if params:
        payload["params"] = params
    req = urllib.request.Request('http://127.0.0.1:8765', data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())

test_card = 1793571419813
res = anki_req('setSpecificValueOfCard', card=test_card, keys=['flags'], newValues=[2])
print("Result of setSpecificValueOfCard with 2:", res)

info = anki_req('cardsInfo', cards=[test_card])['result']
print("New flags:", info[0].get('flags'))
