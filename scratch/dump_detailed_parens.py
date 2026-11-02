import json
import sys

with open('data/anki_extract.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

chars = data.get('characters', [])
with_paren = [c for c in chars if '(' in c.get('english', '') or '（' in c.get('english', '')]

with open('scratch/detailed_parens_utf8.txt', 'w', encoding='utf-8') as out:
    out.write(f"Total matching: {len(with_paren)}\n\n")
    for i, c in enumerate(with_paren, 1):
        out.write(f"--- #{i}: {c.get('hanzi')} [{c.get('pinyin')}] (Note ID: {c.get('note_id')}) ---\n")
        out.write(f"  English: {c.get('english')}\n")
        out.write(f"  HSK: {c.get('hsk_level', '')} | Suspended: {c.get('suspended')}\n")
        out.write(f"  Common Words: {c.get('common_words')}\n")
        out.write(f"  Translation of Words: {c.get('translation_of_words')}\n")
        out.write(f"  Scene: {c.get('scene')[:100]}...\n\n" if c.get('scene') else "  Scene: None\n\n")
