import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')
url = 'https://us-central1-alley-d0944.cloudfunctions.net/getLevelProgress'

def fetch_level(lvl):
    body = json.dumps({"data": {"level": str(lvl)}}).encode('utf-8')
    req = urllib.request.Request(url, data=body, headers={'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        return res.get('result')

for lvl in range(68, 89):
    data = fetch_level(lvl)
    if not data:
        print(f"Level {lvl}: NO DATA")
        continue
    print(f"=== Level {lvl} ===")
    for sec_name, items in data.items():
        old_count = len(items.get('old', []))
        new_count = len(items.get('new', []))
        new_sample = items.get('new', [])[:5]
        print(f"  Section '{sec_name}': old={old_count}, new={new_count}, new_sample={new_sample}")
