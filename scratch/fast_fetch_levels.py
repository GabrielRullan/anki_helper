import urllib.request
import json
import sys
from concurrent.futures import ThreadPoolExecutor

sys.stdout.reconfigure(encoding='utf-8')
url = 'https://us-central1-alley-d0944.cloudfunctions.net/getLevelProgress'

def fetch_level(lvl):
    body = json.dumps({"data": {"level": str(lvl)}}).encode('utf-8')
    req = urllib.request.Request(url, data=body, headers={'Content-Type': 'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(req) as resp:
            res = json.loads(resp.read().decode('utf-8'))
            return lvl, res.get('result')
    except Exception as e:
        return lvl, None

def main():
    levels_data = {}
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(fetch_level, range(68, 89))
        for lvl, data in results:
            levels_data[lvl] = data

    # Save to JSON file for analysis
    with open('scratch/levels_68_88.json', 'w', encoding='utf-8') as f:
        json.dump(levels_data, f, ensure_ascii=False, indent=2)

    print("Saved all levels 68-88 to scratch/levels_68_88.json")

    for lvl in range(68, 89):
        data = levels_data.get(lvl)
        if not data:
            print(f"Level {lvl}: NO DATA")
            continue
        print(f"=== Level {lvl} ===")
        for sec_name, items in data.items():
            old_count = len(items.get('old', []))
            new_count = len(items.get('new', []))
            new_items = items.get('new', [])
            print(f"  Section '{sec_name}': old={old_count}, new={new_count}, new_items={new_items}")

if __name__ == '__main__':
    main()
