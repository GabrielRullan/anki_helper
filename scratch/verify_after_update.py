import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('data/anki_extract.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

chars = data.get('characters', [])
with_paren = [c for c in chars if '(' in c.get('english', '') or '（' in c.get('english', '')]

print(f"Total characters with '(' in english now: {len(with_paren)}")

# Check for any broken / unclosed parentheses
unclosed = []
has_html = []
has_trailing_dot = []
missing_space = []

for c in with_paren:
    eng = c.get('english', '')
    if eng.count('(') != eng.count(')'):
        unclosed.append((c.get('hanzi'), eng))
    if '&nbsp;' in eng or '<' in eng:
        has_html.append((c.get('hanzi'), eng))
    if eng.strip().endswith('.'):
        has_trailing_dot.append((c.get('hanzi'), eng))
    import re
    if re.search(r'[A-Za-z0-9]\(', eng):
        missing_space.append((c.get('hanzi'), eng))

print(f"Unclosed parens: {len(unclosed)}")
for hz, eng in unclosed:
    print(f"  {hz}: '{eng}'")

print(f"Contains HTML: {len(has_html)}")
for hz, eng in has_html:
    print(f"  {hz}: '{eng}'")

print(f"Trailing dot: {len(has_trailing_dot)}")
for hz, eng in has_trailing_dot:
    print(f"  {hz}: '{eng}'")

print(f"Missing space before paren: {len(missing_space)}")
for hz, eng in missing_space:
    print(f"  {hz}: '{eng}'")

print("\n--- ALL CHARACTERS WITH '(' IN ENGLISH NOW ---")
for i, c in enumerate(with_paren, 1):
    print(f"{i:2d}. {c.get('hanzi')} [{c.get('pinyin')}]: \"{c.get('english')}\"")
