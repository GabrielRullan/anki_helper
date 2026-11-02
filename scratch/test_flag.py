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

# Find one unflagged recent recall card
all_recall_cards = anki_req('findCards', query='"card:Recall"')['result']
recent_recall = [cid for cid in all_recall_cards if cid > 1793570000000]
recent_info = anki_req('cardsInfo', cards=recent_recall)['result']

unflagged = [c for c in recent_info if c.get('flags', 0) == 0]
print(f"Total unflagged cards: {len(unflagged)}")

if unflagged:
    test_card = unflagged[0]['cardId']
    print(f"Testing on cardId: {test_card}")
    # Try setSpecificValueOfCard
    res = anki_req('setSpecificValueOfCard', card=test_card, keys=['flags'], newValues=['2'])
    print("Result of setSpecificValueOfCard with '2':", res)
    
    # Check if flag updated
    info = anki_req('cardsInfo', cards=[test_card])['result']
    print("New flags:", info[0].get('flags'))
