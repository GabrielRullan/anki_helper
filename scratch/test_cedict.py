import urllib.request
import json
import gzip
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

print("Testing fetching CC-CEDICT dictionary...")

cedict_urls = [
    'https://raw.githubusercontent.com/scriptin/mdbg-cedict-json/master/cedict.json',
    'https://cdn.jsdelivr.net/gh/scriptin/mdbg-cedict-json@master/cedict.json'
]

cedict_data = None
for url in cedict_urls:
    print(f"Trying {url}...")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            cedict_data = json.loads(resp.read().decode('utf-8'))
            print("Successfully downloaded cedict.json! Items count:", len(cedict_data))
            break
    except Exception as e:
        print(f"Failed {url}: {e}")

if cedict_data:
    with open('data/cedict.json', 'w', encoding='utf-8') as f:
        json.dump(cedict_data, f, ensure_ascii=False)
    print("Saved dictionary to data/cedict.json")
