import json
import re
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Tone marks converter for numbered pinyin
pinyin_tone_map = {
    'a': ['a', 'ā', 'á', 'ǎ', 'à', 'a'],
    'e': ['e', 'ē', 'é', 'ě', 'è', 'e'],
    'i': ['i', 'ī', 'í', 'ǐ', 'ì', 'i'],
    'o': ['o', 'ō', 'ó', 'ǒ', 'ò', 'o'],
    'u': ['u', 'ū', 'ú', 'ǔ', 'ù', 'u'],
    'v': ['ü', 'ǖ', 'ǘ', 'ǚ', 'ǜ', 'ü'],
    'u:': ['ü', 'ǖ', 'ǘ', 'ǚ', 'ǜ', 'ü']
}

def num_pinyin_to_tone(pinyin_str):
    tokens = pinyin_str.lower().split()
    converted = []
    for token in tokens:
        tone_match = re.search(r'[1-5]$', token)
        if tone_match:
            tone = int(tone_match.group(0))
            syllable = token[:-1]
        else:
            tone = 5
            syllable = token

        # Replace u: with v
        syllable = syllable.replace('u:', 'v')

        # Find vowel to put tone mark on (priority: a, e, o, or last of iu/ui)
        target_vowel = None
        for v in ['a', 'e', 'o']:
            if v in syllable:
                target_vowel = v
                break
        if not target_vowel:
            if 'iu' in syllable:
                target_vowel = 'u'
            elif 'ui' in syllable:
                target_vowel = 'i'
            else:
                for v in ['i', 'u', 'v']:
                    if v in syllable:
                        target_vowel = v
                        break

        if target_vowel and tone in range(1, 6):
            accented = pinyin_tone_map[target_vowel][tone]
            syllable = syllable.replace(target_vowel, accented, 1)

        converted.append(syllable)

    return ' '.join(converted)

print("Parsing CC-CEDICT dictionary...")
cedict_lookup = {}

with open('data/cedict_ts.u8', 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        # Format: Traditional Simplified [pinyin] /def1/def2/
        m = re.match(r'^(\S+)\s+(\S+)\s+\[(.*?)\]\s+/(.*)/$', line)
        if m:
            trad, simp, pyn, defs_str = m.groups()
            defs = [d.strip() for d in defs_str.split('/') if d.strip()]
            # Filter out surname / variant notes if primary definition exists
            clean_defs = [d for d in defs if not d.startswith('variant of') and not d.startswith('surname ')]
            if not clean_defs:
                clean_defs = defs

            meaning_text = '; '.join(clean_defs[:3])
            accented_pinyin = num_pinyin_to_tone(pyn)

            # Store by Simplified word
            if simp not in cedict_lookup:
                cedict_lookup[simp] = {
                    'pinyin': accented_pinyin,
                    'meaning': meaning_text
                }

print(f"Loaded {len(cedict_lookup)} entries from CC-CEDICT.")

# Load traverse_words_db.json
with open('data/traverse_words_db.json', 'r', encoding='utf-8') as f:
    traverse_words = json.load(f)

print(f"Enriching {len(traverse_words)} Traverse words with Pinyin and Meaning...")

matched_count = 0
unmatched = []

for item in traverse_words:
    w = item['word']
    if w in cedict_lookup:
        item['pinyin'] = cedict_lookup[w]['pinyin']
        item['meaning'] = cedict_lookup[w]['meaning']
        matched_count += 1
    else:
        # Fallback for individual characters or unlisted compounds
        item['pinyin'] = ''
        item['meaning'] = 'Word introduced in lesson'
        unmatched.append(item)

print(f"Matched {matched_count} / {len(traverse_words)} words directly in CC-CEDICT!")
print(f"Unmatched count: {len(unmatched)}")

if unmatched:
    print("Sample unmatched words:")
    for u in unmatched[:10]:
        print(f"  Lesson {u['lesson']} | {u['word']} (Hanzi: {u['related_hanzi']})")

# Save enriched database
with open('data/traverse_words_db.json', 'w', encoding='utf-8') as f:
    json.dump(traverse_words, f, ensure_ascii=False, indent=2)

print("Saved enriched database to data/traverse_words_db.json")
