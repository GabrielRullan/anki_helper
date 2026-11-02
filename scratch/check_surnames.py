import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('data/anki_extract.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

chars = data.get('characters', [])

for c in chars:
    eng = c.get('english', '')
    if 'surname' in eng.lower():
        print(f"{c.get('hanzi')} [{c.get('pinyin')}]: '{eng}'")
