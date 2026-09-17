import urllib.request
import json

def check_anki():
    try:
        req = urllib.request.Request(
            'http://localhost:8765',
            json.dumps({'action': 'deckNames', 'version': 6}).encode('utf-8')
        )
        response = urllib.request.urlopen(req)
        res = json.loads(response.read().decode('utf-8'))
        print("AnkiConnect Deck Names:", res.get('result'))
    except Exception as e:
        print("AnkiConnect error / not running:", e)

check_anki()
