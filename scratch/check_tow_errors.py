import json
import sys
import re

sys.stdout.reconfigure(encoding='utf-8')

with open('data/anki_extract.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

chars = data.get('characters', [])
with_paren_tow = [c for c in chars if '(' in c.get('translation_of_words', '') or '（' in c.get('translation_of_words', '')]

print(f"Total with '(' in Translation of Words: {len(with_paren_tow)}")

# Check for syntax errors (unclosed parens, etc.) in Translation of Words
unclosed_tow = []
html_entities = []
for c in with_paren_tow:
    tow = c.get('translation_of_words', '')
    open_c = tow.count('(') + tow.count('（')
    close_c = tow.count(')') + tow.count('）')
    if open_c != close_c:
        unclosed_tow.append((c.get('hanzi'), c.get('pinyin'), tow, open_c, close_c))
    if '&nbsp;' in tow or '&#x' in tow or '&amp;' in tow:
        html_entities.append((c.get('hanzi'), c.get('pinyin'), tow))

print(f"Unclosed parens in Translation of Words: {len(unclosed_tow)}")
for hz, py, tow, oc, cc in unclosed_tow:
    print(f"  {hz} [{py}]: '{tow}' ({oc} open vs {cc} close)")

print(f"\nHTML entities in Translation of Words: {len(html_entities)}")
for hz, py, tow in html_entities[:10]:
    print(f"  {hz} [{py}]: '{tow}'")
