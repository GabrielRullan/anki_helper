import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('data/anki_extract.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

chars = data.get('characters', [])
with_paren_tow = [c for c in chars if '(' in c.get('translation_of_words', '') or '（' in c.get('translation_of_words', '')]

print(f"Total with '(' in Translation of Words: {len(with_paren_tow)}")
for c in with_paren_tow[:20]:
    print(f"{c.get('hanzi')} [{c.get('pinyin')}]: '{c.get('translation_of_words')}'")
