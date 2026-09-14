import csv
import json
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('scratch/tagging_results.json', 'r', encoding='utf-8') as f:
    tagging_data = json.load(f)

missing_63_tuple = []
for lvl in range(68, 89):
    lvl_str = str(lvl)
    items = tagging_data.get(lvl_str, {}).get('missing_items', [])
    for h in items:
        missing_63_tuple.append((lvl, h))

junda_map = {}
with open('data/junda_freq.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        c = row['character']
        if c:
            junda_map[c] = row

# Standard MBP Actor mapping
actor_map = {
    'b': 'Batman',
    'p': 'Peter Parker (Spider-Man)',
    'm': 'Marilyn Monroe',
    'f': 'Fred Flintstone',
    'd': 'Dr. Phil',
    't': 'Tiger Woods',
    'n': 'Nicolas Cage',
    'l': 'Lady Gaga',
    'g': 'Gandalf',
    'k': 'Kermit the Frog',
    'h': 'Hulk',
    'j': 'Jackie Chan',
    'q': 'Quentin Tarantino',
    'x': 'Xena',
    'zh': 'Zorro',
    'ch': 'Charlie Chaplin',
    'sh': 'Samuel L. Jackson',
    'r': 'Ronald Reagan',
    'z': 'Mark Zuckerberg',
    'c': 'Captain America',
    's': 'Snoop Dogg',
    'y': 'Yelena (Black Widow)',
    'w': 'Wonder Woman',
    '': 'Childhood Hero / Neutral'
}

# Standard MBP Tone Locations
tone_loc_map = {
    1: 'Front Yard / Entrance [1]',
    2: 'Hallway / Kitchen [2]',
    3: 'Bedroom / Bathroom [3]',
    4: 'Backyard [4]',
    5: 'Roof / Neutral [5]'
}

vowel_tone_map = {
    'ā': ('a', 1), 'á': ('a', 2), 'ǎ': ('a', 3), 'à': ('a', 4),
    'ē': ('e', 1), 'é': ('e', 2), 'ě': ('e', 3), 'è': ('e', 4),
    'ī': ('i', 1), 'í': ('i', 2), 'ǐ': ('i', 3), 'ì': ('i', 4),
    'ō': ('o', 1), 'ó': ('o', 2), 'ǒ': ('o', 3), 'ò': ('o', 4),
    'ū': ('u', 1), 'ú': ('u', 2), 'ǔ': ('u', 3), 'ù': ('u', 4),
    'ǖ': ('v', 1), 'ǘ': ('v', 2), 'ǚ': ('v', 3), 'ǜ': ('v', 4),
    'ü': ('v', 5)
}

def parse_pinyin(p_str):
    p_str = p_str.strip()
    tone = 5
    clean_p = p_str.lower()
    for char in p_str:
        if char in vowel_tone_map:
            tone = vowel_tone_map[char][1]
            break

    # Replace accented vowels with plain
    for char, (plain, t) in vowel_tone_map.items():
        clean_p = clean_p.replace(char, plain)

    clean_p = re.sub(r'[^a-z]', '', clean_p)

    initial = ""
    final = clean_p
    for double_init in ['zh', 'ch', 'sh']:
        if clean_p.startswith(double_init):
            initial = double_init
            final = clean_p[2:]
            break
    if not initial:
        for init in 'bpmfdtnlgkhjqxrzcsyw':
            if clean_p.startswith(init):
                initial = init
                final = clean_p[1:]
                break

    return initial, final, tone

proposed_cards = []

for lvl, h in missing_63_tuple:
    j = junda_map.get(h, {})
    pinyin = j.get('pinyin', '')
    definition = j.get('definition', '')
    hsk = j.get('hsk_level', '')
    rank = j.get('frequency_rank', '')
    radical = j.get('radical', '')

    if not pinyin:
        # Fallback definitions for rare ones
        if h == '夌':
            pinyin = 'líng'
            definition = 'high mound; soar'
            radical = '夂'
        elif h == '刨':
            pinyin = 'páo'
            definition = 'plane; dig, scoop out'
            radical = '刂'
        else:
            pinyin = 'zhī'
            definition = 'character'
            radical = ''

    initial, final, tone = parse_pinyin(pinyin)
    actor = actor_map.get(initial, initial.upper() if initial else 'Self')
    tone_loc = tone_loc_map.get(tone, f'Location [{tone}]')
    set_name = f"-{final}" if final else "Default Set"

    scene = f"{actor} is at {tone_loc} (Tone {tone}) on the '{set_name}' set, using radical/component [{radical or h}] to depict '{definition[:60]}'."

    card_info = {
        'lesson': lvl,
        'tag': f"MBP-{lvl}",
        'hanzi': h,
        'pinyin': pinyin,
        'english': definition,
        'initial': initial.upper(),
        'actor': actor,
        'set': set_name,
        'tone': str(tone),
        'tone_location': tone_loc,
        'components': radical or h,
        'scene': scene,
        'hsk': hsk or 'Non-HSK',
        'frequency_rank': rank
    }
    proposed_cards.append(card_info)

with open('scratch/proposed_63_cards.json', 'w', encoding='utf-8') as f:
    json.dump(proposed_cards, f, ensure_ascii=False, indent=2)

print(f"Generated {len(proposed_cards)} proposed character cards!")
