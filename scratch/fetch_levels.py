import urllib.request
import json
import sys

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

url = 'https://us-central1-alley-d0944.cloudfunctions.net/getLevelProgress'

def fetch_level(lvl):
    body = json.dumps({"data": {"level": str(lvl)}}).encode('utf-8')
    req = urllib.request.Request(url, data=body, headers={'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        return res.get('result')

data68 = fetch_level(68)
print(f"Level 68 structure keys: {list(data68.keys()) if data68 else None}")
print(json.dumps(data68, ensure_ascii=False, indent=2))
