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

# Test supported actions on cards
try:
    print("Testing unsuspend on sample CID 1788529343944...")
    ankiconnect_request('unsuspend', cards=[1788529343944])
    print("Unsuspend successful!")
except Exception as e:
    print("Unsuspend error:", e)

# Test updating card details or info
try:
    card_info = ankiconnect_request('cardsInfo', cards=[1788529343944])
    print("Card info after unsuspend:", json.dumps(card_info[0], indent=2))
except Exception as e:
    print("Error getting card info:", e)
