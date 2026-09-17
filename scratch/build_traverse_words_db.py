import json
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('scratch/levels_68_88.json', 'r', encoding='utf-8') as f:
    levels_data = json.load(f)

with open('scratch/annotated_anki_68_88.json', 'r', encoding='utf-8') as f:
    anki_annotated = json.load(f)

# Build word status lookup
word_anki_status = {}
for lvl_str, ldata in anki_annotated.items():
    for w_obj in ldata.get('words', []):
        word_anki_status[w_obj['word']] = w_obj['in_anki']

traverse_words_list = []

grammatical_categories = [
    'Nouns 名词', 'Verbs 动词', 'Adjectives 形容词', 'Adverbs 副词',
    'Pronouns 代词', 'Measure 量词', 'Numbers 数词', 'Prepositions 介词',
    'Conjunction 连词', 'Particles 助词', 'Mood 语气词'
]

for lvl in range(68, 89):
    lvl_str = str(lvl)
    lvl_data = levels_data.get(lvl_str, {})
    all_new_words = lvl_data.get('All Words', {}).get('new', [])

    # Map word -> classification for this level
    word_class_map = {}

    for cat in grammatical_categories:
        cat_words = lvl_data.get(cat, {}).get('new', [])
        for w in cat_words:
            word_class_map[w] = cat

    for w in all_new_words:
        classification = word_class_map.get(w, 'Other 其他')
        related_hanzi = [c for c in w if '\u4e00' <= c <= '\u9fff']
        in_anki = word_anki_status.get(w, False)

        traverse_words_list.append({
            'word': w,
            'lesson': lvl,
            'classification': classification,
            'related_hanzi': related_hanzi,
            'in_anki': in_anki
        })

print(f"Compiled {len(traverse_words_list)} Traverse words across Lessons 68 to 88.")
print("Sample entries:")
for item in traverse_words_list[:5]:
    print(" ", item)

with open('data/traverse_words_db.json', 'w', encoding='utf-8') as f:
    json.dump(traverse_words_list, f, ensure_ascii=False, indent=2)

print("Saved database to data/traverse_words_db.json")
