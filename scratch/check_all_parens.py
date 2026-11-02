import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('data/anki_extract.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

chars = data.get('characters', [])

print(f"Total character notes: {len(chars)}")

with_paren_eng = [c for c in chars if '(' in c.get('english', '') or '（' in c.get('english', '')]
print(f"Notes with '(' in English: {len(with_paren_eng)}")

with_paren_tow = [c for c in chars if '(' in c.get('translation_of_words', '') or '（' in c.get('translation_of_words', '')]
print(f"Notes with '(' in Translation of Words: {len(with_paren_tow)}")

# Let's also check if there are words in Chinese::Words with '(' in translation / definition
words = data.get('immersion_cards', [])
words_with_paren = [w for w in words if '(' in w.get('definition', '') or '(' in w.get('sentence_translation', '')]
print(f"Immersion cards: {len(words)}, with '(' in definition: {len([w for w in words if '(' in w.get('definition', '')])}")

