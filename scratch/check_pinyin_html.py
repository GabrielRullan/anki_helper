import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('data/anki_extract.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

chars = data.get('characters', [])
for c in chars:
    py = c.get('pinyin', '')
    if '<span' in py or '<!--' in py:
        print(f"HTML in pinyin: {c.get('hanzi')} -> {py}")
