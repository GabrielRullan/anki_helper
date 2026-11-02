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

# Find all cards in deck Chinese Char that were created today
today_cards = anki_req('findCards', query='deck:"Chinese Char" added:1')
print(f"Cards added today in 'Chinese Char': {len(today_cards)}")

# Breakdown by card template / ord / flags
cards_info = anki_req('cardsInfo', cards=today_cards)
print(f"Retrieved info for {len(cards_info)} cards")

by_card_type = {}
by_flags = {}

for c in cards_info:
    c_type = f"ord={c.get('ord')} ({c.get('cardTemplate')})"
    by_card_type[c_type] = by_card_type.get(c_type, 0) + 1
    
    fl = c.get('flags', 0)
    by_flags[fl] = by_flags.get(fl, 0) + 1

print("\nBy card type:", by_card_type)
print("By flag:", by_flags)

# Which ones are Recall cards (ord=1) without flag=2?
unflagged_recall = [c['cardId'] for c in cards_info if c.get('ord') == 1 and c.get('flags') != 2]
print(f"\nUnflagged Recall cards count: {len(unflagged_recall)}")

# Which ones are already flagged with flag=2?
flagged_recall = [c['cardId'] for c in cards_info if c.get('ord') == 1 and c.get('flags') == 2]
print(f"Already flagged with orange (flag=2): {len(flagged_recall)}")
