import urllib.request
import json

ANKICONNECT_URL = 'http://localhost:8765'

def request(action, **params):
    payload = {"action": action, "version": 6}
    if params:
        payload["params"] = params
    
    req = urllib.request.Request(
        ANKICONNECT_URL, 
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            res = json.loads(response.read().decode('utf-8'))
            if res.get('error'):
                print(f"Error from Anki: {res.get('error')}")
                return None
            return res.get('result')
    except Exception as e:
        print(f"Connection failed: {e}")
        return None

def main():
    print("Testing connection to AnkiConnect...")
    decks = request("deckNames")
    if decks:
        print(f"Connection successful! Decks found: {decks}")
    else:
        print("Failed to get decks. Is Anki running with AnkiConnect addon installed?")

if __name__ == "__main__":
    main()
