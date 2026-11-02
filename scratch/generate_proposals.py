import json
import re

with open('data/anki_extract.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

chars = data.get('characters', [])
with_paren = [c for c in chars if '(' in c.get('english', '') or '（' in c.get('english', '')]

# Map each character to its proposed improvement and rationale
proposals = {
    # 1. Syntax / Typos / HTML / Spacing
    "鸣": {
        "new": "Chirp / Cry (birds)",
        "reason": "Fix unclosed paren '(of Birds', strange capitalization, and make concise keyword matching scene ('Bird opens mouth to chirp/cry')."
    },
    "啪": {
        "new": "Sound of Clap / Slap",
        "reason": "Fix unclosed paren '(sound Of A Clap; Slap' and odd title casing."
    },
    "烹": {
        "new": "Cook / Boil / Steam",
        "reason": "Fix unclosed paren '(boil; Steam' and odd title casing."
    },
    "辛": {
        "new": "Hard (difficult) / Pungent",
        "reason": "Remove trailing HTML entity '&nbsp;'."
    },
    "弹": {
        "new": "Bullet / Play (tán)",
        "reason": "Add missing space before '(tán)'."
    },
    "盛": {
        "new": "Flourishing / Fill (chéng)",
        "reason": "Add missing space before '(chéng)'."
    },
    "莽": {
        "new": "Uncouth / Reckless / Lush (vegetation)",
        "reason": "Remove trailing period and unify separators with standard slash formatting."
    },

    # 2. Incomplete / Inconsistent Surnames
    "刘": {
        "new": "Surname Liu",
        "reason": "Fix bare '(Surname)' to match deck standard (Surname Jiang, Surname Wu, etc.). Scene specifically references the Liu clan."
    },
    "吕": {
        "new": "Surname Lu",
        "reason": "Fix bare '(Surname)' to match deck standard. Scene specifically references surname 吕."
    },
    "曹": {
        "new": "Surname Cao",
        "reason": "Fix bare '(Surname)' to match deck standard. Scene specifically references surname 曹."
    },
    "李": {
        "new": "Plum / Surname Li",
        "reason": "Fix bare '(Surname)' to match deck standard. Scene specifically references 'Li (Plum)'."
    },
    "肖": {
        "new": "Resemble / Surname Xiao",
        "reason": "Clean verbose dictionary gloss 'To resemble; To be like (surname)'."
    },
    "董": {
        "new": "Supervise / Director / Surname Dong",
        "reason": "Clean verbose dictionary gloss 'To supervise; To direct; Director (surname)'."
    },

    # 3. Measure Words Consistency
    "枚": {
        "new": "M.W. (coins, rings, stamps) / Trunk",
        "reason": "Standardize 'Measure word for small flat objects, coins, stamps, rings; Trunk (of tree)' to standard 'M.W. (...)' format."
    },
    "轴": {
        "new": "Axis / Axle / M.W. (scrolls, spools)",
        "reason": "Standardize '(Classifier for spools, scrolls, etc.)' to standard 'M.W. (...)' format."
    },
    "艘": {
        "new": "M.W. (boats, ships)",
        "reason": "Standardize '(measure Word For Boats; Ships)' to standard 'M.W. (...)' format and fix casing."
    },

    # 4. Dictionary Dumps / Artifacts / Over-capitalization
    "菇": {
        "new": "Mushroom",
        "reason": "Remove dictionary tag '(Bound form)'."
    },
    "虐": {
        "new": "Brutal / Oppressive / Harsh",
        "reason": "Remove dictionary tag '(Bound form)'."
    },
    "妆": {
        "new": "Adorn Oneself / Makeup",
        "reason": "Clean dictionary gloss '(Of a woman) to adorn oneself'."
    },
    "呦": {
        "new": "Oh! (dismay) / Deer Bleat",
        "reason": "Clean verbose dictionary gloss 'Oh! (exclamation of dismay etc)'."
    },
    "绸": {
        "new": "Silk (light)",
        "reason": "Clean '(Light) silk' to standard Hanzi keyword."
    },
    "嫁": {
        "new": "Marry (of a woman)",
        "reason": "Remove leading 'To ' to match concise MBP keyword style."
    },
    "啰": {
        "new": "Verbose / Chatter (onomatopoeia)",
        "reason": "Clean lengthy dictionary gloss '(Used as an onomatopoeia for continuous talking); Verbose'."
    },
    "馨": {
        "new": "Fragrant / Aromatic",
        "reason": "Clean verbose dictionary gloss 'Fragrant; Aromatic (often used for pleasant, far-reaching fragrance)'."
    },
    "蝴": {
        "new": "Butterfly (húdié)",
        "reason": "Clean 'Butterfly (as in 蝴蝶)' to concise format."
    },
    "瞒": {
        "new": "Conceal / Hide (from)",
        "reason": "Clean 'To hide; To conceal (from)'."
    },
    "嗨": {
        "new": "Hey / Hi / Alas",
        "reason": "Remove dictionary tag '(interjection)' and leading 'To '."
    },
    "臼": {
        "new": "Mortar (for pounding) / Socket",
        "reason": "Clean separators to slash formatting."
    },
    "募": {
        "new": "Recruit / Raise (funds) / Solicit",
        "reason": "Remove leading 'To ' and clean formatting."
    },
    "呸": {
        "new": "Ptooey / Spit (contempt)",
        "reason": "Clean lengthy dictionary explanation 'Pooh (an expression of contempt or disgust)'."
    },
    "哎": {
        "new": "Exclamation (surprise/regret) / Alas",
        "reason": "Clean verbose dictionary explanation 'Exclamatory particle (indicating surprise, regret, or a call)'."
    },
    "橙": {
        "new": "Orange (fruit or color)",
        "reason": "Clean 'Orange (color or fruit)'."
    },
    "耍": {
        "new": "Play / Juggle / Show Off",
        "reason": "Clean entire dictionary entry dump 'To play, to play with; To juggle; To brandish; To employ (tricks); To show off'."
    },
    "咋": {
        "new": "How / Why / What (dialect)",
        "reason": "Clean 'How, why, what (dialectal); To make a noise'."
    },
    "遛": {
        "new": "Walk (an animal) / Stroll",
        "reason": "Remove leading 'To ' and add stroll."
    },
    "咯": {
        "new": "Particle (obviousness) / Cluck",
        "reason": "Clean '(particle Indicating Obviousness; Often Rhetorical Or Used For Sound)'."
    },
    "奘": {
        "new": "Stout / Bulky / Great",
        "reason": "Clean 'Stout; Bulky (often in names)'."
    },
    "娜": {
        "new": "Elegant / Graceful (in names)",
        "reason": "Clean 'Elegant; Graceful (often used in names)'."
    },
    "拎": {
        "new": "Lift / Carry (with handle)",
        "reason": "Remove leading 'To ' and clean 'To lift; To carry (with a handle)'."
    },
    "敞": {
        "new": "Open / Spacious (room/door)",
        "reason": "Clean 'Open, spacious, wide (e.g., of a room, a door)'."
    },
    "昊": {
        "new": "Vast Sky / Grand (heaven)",
        "reason": "Clean 'Vast, grand (referring to the sky/heaven)'."
    },
    "楠": {
        "new": "Phoebe Tree / Nanmu",
        "reason": "Clean 'Phoebe (a type of tree, often associated with valuable timber)'."
    },
    "榨": {
        "new": "Squeeze / Press (liquid) / Extract",
        "reason": "Clean 'Squeeze, press (to extract liquid); Extract'."
    },
    "湛": {
        "new": "Crystal Clear / Deep (water)",
        "reason": "Clean 'Clear, profound, deep (of water/color)'."
    },
    "熄": {
        "new": "Extinguish / Put Out (fire)",
        "reason": "Clean 'Extinguish, put out (fire), stop'."
    },
    "玛": {
        "new": "Agate / Transliteration (Mary)",
        "reason": "Clean 'Agate; Used in transliterations (e.g., Mary)'."
    },
    "睁": {
        "new": "Open (eyes)",
        "reason": "Remove leading 'To '."
    },
    "绽": {
        "new": "Burst / Split Open",
        "reason": "Clean 'To burst, split, crack (open)'."
    },
    "琢": {
        "new": "Polish (jade, stone)",
        "reason": "Remove leading 'To '."
    },
    "妾": {
        "new": "Concubine / Servant Girl (old)",
        "reason": "Clean 'Concubine; Servant girl (old term)'."
    },
    "铸": {
        "new": "Cast (metal) / Mint",
        "reason": "Remove leading 'To '."
    },
    "斋": {
        "new": "Studio / Study / Vegetarian Fast",
        "reason": "Clean 'Studio; Study; (In temples) fast; Vegetarian meal'."
    },
    "洛": {
        "new": "Luo River / Luoyang",
        "reason": "Clean 'Luoyang (river/place name)'."
    },
    "孟": {
        "new": "First (month/season) / Surname Meng",
        "reason": "Fix casing and punctuation in 'First (month; Season)' and include surname."
    },
    "伽": {
        "new": "Transliteration (yoga) / G-sound",
        "reason": "Fix semicolon typo and strange casing in 'Suffix For Transliterations (e.g; Yoga)'."
    },
    "哉": {
        "new": "Particle (exclamatory/interrogative)",
        "reason": "Fix lowercase start and title-cased interior in '(exclamatory; Interrogative Particle)'."
    },
    "鳞": {
        "new": "Scales (fish, dragons)",
        "reason": "Fix capitalization and semicolon in 'Scales (of Fish; Dragon)'."
    },
    "兮": {
        "new": "Poetic Particle",
        "reason": "Clean '(Poetic particle)'."
    },
    "娅": {
        "new": "Used in Names (women)",
        "reason": "Fix capitalization in '(used In Names; Usually For Women)'."
    },
    "唔": {
        "new": "Interjection (agreement/disagreement)",
        "reason": "Fix capitalization in '(interjection Of Agreement; Disagreement)'."
    },
    "砌": {
        "new": "Build / Lay (bricks, stones)",
        "reason": "Fix semicolon and capitalization in 'Build (with Bricks; Stones)'."
    },
    "彈": {
        "new": "Bullet / Bomb / Pluck (strings) / Bounce",
        "reason": "Standardize semicolon/comma mix to slash keywords."
    },
    "娲": {
        "new": "Goddess Nuwa (mythology)",
        "reason": "Clean 'goddess in Chinese mythology (Nüwa)'."
    },
    "瑰": {
        "new": "Rose Gem / Extraordinary Jade",
        "reason": "Replace vague '(Semiprecious stone)' with meaningful keyword matching 玫瑰 and character sense."
    },
    "玫": {
        "new": "Rose Gem / Fine Jade",
        "reason": "Replace vague '(Fine jade)' with meaningful keyword matching 玫瑰 and character sense."
    },
    "籽": {
        "new": "Seed (plant)",
        "reason": "Clean 'Seed (of a plant)'."
    },
    "叮": {
        "new": "Sting / Bite (insect)",
        "reason": "Clean verbose dictionary gloss 'To sting or bite (of mosquito, bee etc)'."
    },
    "揍": {
        "new": "Hit / Beat (sb)",
        "reason": "Remove leading 'To ' and standardize."
    },
    "涂": {
        "new": "Apply / Spread (paint)",
        "reason": "Clean 'To apply (paint etc)'."
    },
    "矣": {
        "new": "Final Particle",
        "reason": "Clean '(Final particle)'."
    }
}

output_list = []
for c in with_paren:
    hz = c.get('hanzi')
    curr = c.get('english')
    prop = proposals.get(hz)
    output_list.append({
        'note_id': c.get('note_id'),
        'hanzi': hz,
        'pinyin': c.get('pinyin'),
        'current_english': curr,
        'proposed_english': prop['new'] if prop else curr,
        'changed': prop is not None,
        'reason': prop['reason'] if prop else "Keep as is (already clean, accurate disambiguation keyword)"
    })

changed_count = sum(1 for it in output_list if it['changed'])
kept_count = sum(1 for it in output_list if not it['changed'])

print(f"Total analyzed: {len(output_list)}")
print(f"Proposed improvements: {changed_count}")
print(f"Kept as is: {kept_count}")

with open('scratch/detailed_proposals.json', 'w', encoding='utf-8') as f:
    json.dump(output_list, f, ensure_ascii=False, indent=2)

print("Saved detailed proposals to scratch/detailed_proposals.json")
