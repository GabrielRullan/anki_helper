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
        return json.loads(r.read())['result']

# Find all cards with flag:2 across entire collection
flag2_cards = anki_req('findCards', query='flag:2')
print(f"Total cards with flag:2: {len(flag2_cards)}")

# Look at card 1793571419725 (ID=28 Recall card)
info_28 = anki_req('cardsInfo', cards=[1793571419725])
print("Card 1793571419725 info:")
if info_28:
    c = info_28[0]
    print(f"  cardId: {c.get('cardId')}, ord: {c.get('ord')}, deck: {c.get('deckName')}, flag: {c.get('flags')}")

# Let's find all cards created with id > 1793570000000
# Can we search all cards in "Chinese Char" or "card:2"?
all_recall_cards = anki_req('findCards', query='"card:Recall"')
print(f"Total Recall cards in collection: {len(all_recall_cards)}")

# Check cardsInfo for all_recall_cards where id > 1793570000000
recent_recall = [cid for cid in all_recall_cards if cid > 1793570000000]
print(f"Recent Recall cards (id > 1793570000000): {len(recent_recall)}")

recent_info = anki_req('cardsInfo', cards=recent_recall)
flags_count = {}
for c in recent_info:
    fl = c.get('flags', 0)
    flags_count[fl] = flags_count.get(fl, 0) + 1
print("Flag counts among recent recall cards:", flags_count)
