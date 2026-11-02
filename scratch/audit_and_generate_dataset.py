import json
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('data/anki_extract.json', 'r', encoding='utf-8') as f:
    anki_data = json.load(f)

chars = anki_data.get('characters', [])
char_map = {c['note_id']: c for c in chars}

# Full dictionary of proposed updates for characters with '(' in english
# Every proposed change has been carefully checked against:
# 1. Deck convention (MBP concise keywords, 'Surname <Name>', 'M.W. (<objects>)')
# 2. Card scene (mnemonic integrity)
# 3. Syntax validity (closed parens, clean spacing, no raw HTML, no trailing periods)

UPDATES = {
    # --- Category 1: Syntax & Formatting Errors (unclosed parens, HTML entities, bad spacing, trailing punctuation) ---
    1786803211071: { # 鸣 [míng]
        "new_english": "Chirp / Cry (birds)",
        "category": "Syntax & Formatting",
        "reason": "Fix unclosed paren '(of Birds', strange capitalization, and format as concise MBP keyword."
    },
    1786803213198: { # 啪 [pā]
        "new_english": "Sound of Clap / Slap",
        "category": "Syntax & Formatting",
        "reason": "Fix unclosed paren '(sound Of A Clap; Slap' and odd title casing."
    },
    1786803215169: { # 烹 [pēng]
        "new_english": "Cook / Boil / Steam",
        "category": "Syntax & Formatting",
        "reason": "Fix unclosed paren '(boil; Steam' and odd title casing."
    },
    1768474725173: { # 辛 [xīn]
        "new_english": "Hard (difficult) / Pungent",
        "category": "Syntax & Formatting",
        "reason": "Remove trailing raw HTML entity '&nbsp;'."
    },
    1768474725065: { # 弹 [dàn]
        "new_english": "Bullet / Play (tán)",
        "category": "Syntax & Formatting",
        "reason": "Add missing space before '(tán)'."
    },
    1768474725749: { # 盛 [shèng]
        "new_english": "Flourishing / Fill (chéng)",
        "category": "Syntax & Formatting",
        "reason": "Add missing space before '(chéng)'."
    },
    1786803213010: { # 莽 [mǎng]
        "new_english": "Uncouth / Reckless / Lush (vegetation)",
        "category": "Syntax & Formatting",
        "reason": "Remove trailing period and unify with standard slash keyword format."
    },

    # --- Category 2: Incomplete Surnames ---
    1768474725348: { # 刘 [liú]
        "new_english": "Surname Liu",
        "category": "Surname Standardization",
        "reason": "Replace bare '(Surname)' with 'Surname Liu' to match deck standard (Surname Jiang, Surname Wu, etc.)."
    },
    1768474725577: { # 吕 [lǚ]
        "new_english": "Surname Lu",
        "category": "Surname Standardization",
        "reason": "Replace bare '(Surname)' with 'Surname Lu' to match deck standard."
    },
    1768474726050: { # 曹 [cáo]
        "new_english": "Surname Cao",
        "category": "Surname Standardization",
        "reason": "Replace bare '(Surname)' with 'Surname Cao' to match deck standard."
    },
    1768474725814: { # 李 [lǐ]
        "new_english": "Plum / Surname Li",
        "category": "Surname Standardization",
        "reason": "Replace bare '(Surname)' with 'Surname Li' to match deck standard."
    },
    1778227240807: { # 肖 [xiāo]
        "new_english": "Resemble / Surname Xiao",
        "category": "Surname Standardization",
        "reason": "Standardize verbose 'To resemble; To be like (surname)'."
    },
    1778227240839: { # 董 [dǒng]
        "new_english": "Supervise / Director / Surname Dong",
        "category": "Surname Standardization",
        "reason": "Standardize verbose 'To supervise; To direct; Director (surname)'."
    },

    # --- Category 3: Measure Word Consistency ---
    1781004427320: { # 枚 [méi]
        "new_english": "M.W. (coins, rings, stamps) / Trunk",
        "category": "Measure Word Standardization",
        "reason": "Replace lengthy dictionary sentence with standard 'M.W. (...)' format matching other cards."
    },
    1785483643441: { # 轴 [zhóu]
        "new_english": "Axis / Axle / M.W. (scrolls, spools)",
        "category": "Measure Word Standardization",
        "reason": "Replace '(Classifier for spools, scrolls, etc.)' with standard 'M.W. (...)' format."
    },
    1786803210974: { # 艘 [sōu]
        "new_english": "M.W. (boats, ships)",
        "category": "Measure Word Standardization",
        "reason": "Replace '(measure Word For Boats; Ships)' with clean 'M.W. (boats, ships)'."
    },

    # --- Category 4: Grammar & Particle Tagging Cleanup ---
    1768474726373: { # 矣 [yǐ]
        "new_english": "Final Particle",
        "category": "Particle & Grammar Cleanup",
        "reason": "Replace '(Final particle)' with clean 'Final Particle'."
    },
    1781004427228: { # 咯 [lo, gē]
        "new_english": "Particle (obviousness) / Cluck",
        "category": "Particle & Grammar Cleanup",
        "reason": "Replace verbose '(particle Indicating Obviousness; Often Rhetorical Or Used For Sound)'."
    },
    1786803213074: { # 哉 [zāi]
        "new_english": "Particle (exclamatory/interrogative)",
        "category": "Particle & Grammar Cleanup",
        "reason": "Clean '(exclamatory; Interrogative Particle)' and fix casing."
    },
    1786803213093: { # 兮 [xī]
        "new_english": "Poetic Particle",
        "category": "Particle & Grammar Cleanup",
        "reason": "Clean '(Poetic particle)'."
    },
    1786803213326: { # 娅 [yà]
        "new_english": "Used in Names (women)",
        "category": "Particle & Grammar Cleanup",
        "reason": "Fix capitalization in '(used In Names; Usually For Women)'."
    },
    1786803214050: { # 唔 [wú]
        "new_english": "Interjection (agreement/disagreement)",
        "category": "Particle & Grammar Cleanup",
        "reason": "Fix capitalization in '(interjection Of Agreement; Disagreement)'."
    },
    1786803212724: { # 伽 [jiā]
        "new_english": "Transliteration (yoga) / G-sound",
        "category": "Particle & Grammar Cleanup",
        "reason": "Fix semicolon typo and casing in 'Suffix For Transliterations (e.g; Yoga)'."
    },
    1786803211013: { # 孟 [mèng]
        "new_english": "First (month/season) / Surname Meng",
        "category": "Particle & Grammar Cleanup",
        "reason": "Fix casing/semicolon in 'First (month; Season)' and include surname."
    },
    1786803213080: { # 鳞 [lín]
        "new_english": "Scales (fish, dragons)",
        "category": "Particle & Grammar Cleanup",
        "reason": "Fix capitalization and semicolon in 'Scales (of Fish; Dragon)'."
    },
    1786803214103: { # 砌 [qì]
        "new_english": "Build / Lay (bricks, stones)",
        "category": "Particle & Grammar Cleanup",
        "reason": "Fix capitalization and semicolon in 'Build (with Bricks; Stones)'."
    },

    # --- Category 5: Dictionary Gloss Artifacts & Overly Verbose Entries ---
    1778227239468: { # 菇 [gū]
        "new_english": "Mushroom",
        "category": "Concise Keyword Cleanup",
        "reason": "Remove dictionary tag '(Bound form)'."
    },
    1778227240065: { # 虐 [nüè]
        "new_english": "Brutal / Oppressive / Harsh",
        "category": "Concise Keyword Cleanup",
        "reason": "Remove dictionary tag '(Bound form)'."
    },
    1778227240054: { # 妆 [zhuāng]
        "new_english": "Adorn Oneself / Makeup",
        "category": "Concise Keyword Cleanup",
        "reason": "Clean dictionary gloss '(Of a woman) to adorn oneself'."
    },
    1778227240127: { # 呦 [yōu]
        "new_english": "Oh! (dismay) / Deer Bleat",
        "category": "Concise Keyword Cleanup",
        "reason": "Clean verbose dictionary gloss 'Oh! (exclamation of dismay etc)'."
    },
    1778227239763: { # 哟 [yō]
        "new_english": "Oh! (surprise)",
        "category": "Concise Keyword Cleanup",
        "reason": "Clean verbose dictionary gloss 'Oh! (interjection indicating slight surprise)'."
    },
    1778227240161: { # 绸 [chóu]
        "new_english": "Silk (light)",
        "category": "Concise Keyword Cleanup",
        "reason": "Format '(Light) silk' as clean keyword."
    },
    1778227240761: { # 嫁 [jià]
        "new_english": "Marry (of a woman)",
        "category": "Concise Keyword Cleanup",
        "reason": "Remove leading 'To '."
    },
    1778227240793: { # 啰 [luō]
        "new_english": "Verbose / Chatter (onomatopoeia)",
        "category": "Concise Keyword Cleanup",
        "reason": "Clean verbose explanation '(Used as an onomatopoeia for continuous talking); Verbose'."
    },
    1778227240816: { # 馨 [xīn]
        "new_english": "Fragrant / Aromatic",
        "category": "Concise Keyword Cleanup",
        "reason": "Clean verbose explanation 'Fragrant; Aromatic (often used for pleasant, far-reaching fragrance)'."
    },
    1778227240834: { # 蝴 [hú]
        "new_english": "Butterfly (húdié)",
        "category": "Concise Keyword Cleanup",
        "reason": "Clean 'Butterfly (as in 蝴蝶)'."
    },
    1778227240858: { # 瞒 [mán]
        "new_english": "Conceal / Hide (from)",
        "category": "Concise Keyword Cleanup",
        "reason": "Clean 'To hide; To conceal (from)'."
    },
    1778227240884: { # 嗨 [hāi]
        "new_english": "Hey / Hi / Alas",
        "category": "Concise Keyword Cleanup",
        "reason": "Remove dictionary tag '(interjection)'."
    },
    1778227240908: { # 臼 [jiù]
        "new_english": "Mortar (for pounding) / Socket",
        "category": "Concise Keyword Cleanup",
        "reason": "Standardize semicolon to slash formatting."
    },
    1778227240917: { # 募 [mù]
        "new_english": "Recruit / Raise (funds) / Solicit",
        "category": "Concise Keyword Cleanup",
        "reason": "Remove leading 'To ' and standardize."
    },
    1778227240943: { # 呸 [pēi]
        "new_english": "Ptooey / Spit (contempt)",
        "category": "Concise Keyword Cleanup",
        "reason": "Clean dictionary gloss 'Pooh (an expression of contempt or disgust)'."
    },
    1778227240953: { # 哎 [āi]
        "new_english": "Exclamation (surprise/regret) / Alas",
        "category": "Concise Keyword Cleanup",
        "reason": "Clean verbose dictionary gloss 'Exclamatory particle (indicating surprise, regret, or a call)'."
    },
    1778227240962: { # 橙 [chéng]
        "new_english": "Orange (fruit or color)",
        "category": "Concise Keyword Cleanup",
        "reason": "Clarify 'Orange (color or fruit)'."
    },
    1778227240986: { # 耍 [shuǎ]
        "new_english": "Play / Juggle / Show Off",
        "category": "Concise Keyword Cleanup",
        "reason": "Prune whole dictionary entry dump into concise keywords."
    },
    1778227240991: { # 咋 [zǎ]
        "new_english": "How / Why / What (dialect)",
        "category": "Concise Keyword Cleanup",
        "reason": "Clean 'How, why, what (dialectal); To make a noise'."
    },
    1778227241044: { # 遛 [liú]
        "new_english": "Walk (an animal) / Stroll",
        "category": "Concise Keyword Cleanup",
        "reason": "Remove leading 'To ' and add stroll matching scene."
    },
    1781004427249: { # 奘 [zàng, zhuàng]
        "new_english": "Stout / Bulky / Great",
        "category": "Concise Keyword Cleanup",
        "reason": "Clean 'Stout; Bulky (often in names)'."
    },
    1781004427253: { # 娜 [nà]
        "new_english": "Elegant / Graceful (in names)",
        "category": "Concise Keyword Cleanup",
        "reason": "Clean 'Elegant; Graceful (often used in names)'."
    },
    1781004427285: { # 拎 [līn]
        "new_english": "Lift / Carry (with handle)",
        "category": "Concise Keyword Cleanup",
        "reason": "Remove leading 'To '."
    },
    1781004427299: { # 敞 [chǎng]
        "new_english": "Open / Spacious (room/door)",
        "category": "Concise Keyword Cleanup",
        "reason": "Clean 'Open, spacious, wide (e.g., of a room, a door)'."
    },
    1781004427310: { # 昊 [hào]
        "new_english": "Vast Sky / Grand (heaven)",
        "category": "Concise Keyword Cleanup",
        "reason": "Clean 'Vast, grand (referring to the sky/heaven)'."
    },
    1781004427327: { # 楠 [nán]
        "new_english": "Phoebe Tree / Nanmu",
        "category": "Concise Keyword Cleanup",
        "reason": "Clean 'Phoebe (a type of tree, often associated with valuable timber)'."
    },
    1781004427331: { # 榨 [zhà]
        "new_english": "Squeeze / Press (liquid) / Extract",
        "category": "Concise Keyword Cleanup",
        "reason": "Clean 'Squeeze, press (to extract liquid); Extract'."
    },
    1781004427338: { # 湛 [zhàn]
        "new_english": "Crystal Clear / Deep (water)",
        "category": "Concise Keyword Cleanup",
        "reason": "Clean 'Clear, profound, deep (of water/color)'."
    },
    1781004427345: { # 熄 [xī]
        "new_english": "Extinguish / Put Out (fire)",
        "category": "Concise Keyword Cleanup",
        "reason": "Clean 'Extinguish, put out (fire), stop'."
    },
    1781004427352: { # 玛 [mǎ]
        "new_english": "Agate / Transliteration (Mary)",
        "category": "Concise Keyword Cleanup",
        "reason": "Clean 'Agate; Used in transliterations (e.g., Mary)'."
    },
    1781004427364: { # 睁 [zhēng]
        "new_english": "Open (eyes)",
        "category": "Concise Keyword Cleanup",
        "reason": "Remove leading 'To '."
    },
    1781004427383: { # 绽 [zhàn]
        "new_english": "Burst / Split Open",
        "category": "Concise Keyword Cleanup",
        "reason": "Clean 'To burst, split, crack (open)'."
    },
    1785483539446: { # 琢 [zhuó]
        "new_english": "Polish (jade, stone)",
        "category": "Concise Keyword Cleanup",
        "reason": "Remove leading 'To '."
    },
    1785483541813: { # 妾 [qiè]
        "new_english": "Concubine / Servant Girl (old)",
        "category": "Concise Keyword Cleanup",
        "reason": "Clean 'Concubine; Servant girl (old term)'."
    },
    1785483605338: { # 铸 [zhù]
        "new_english": "Cast (metal) / Mint",
        "category": "Concise Keyword Cleanup",
        "reason": "Remove leading 'To '."
    },
    1785483652272: { # 斋 [zhāi]
        "new_english": "Studio / Study / Vegetarian Fast",
        "category": "Concise Keyword Cleanup",
        "reason": "Clean 'Studio; Study; (In temples) fast; Vegetarian meal'."
    },
    1786803210722: { # 洛 [luò]
        "new_english": "Luo River / Luoyang",
        "category": "Concise Keyword Cleanup",
        "reason": "Clean 'Luoyang (river/place name)'."
    },
    1787514324361: { # 彈 [dàn, tán]
        "new_english": "Bullet / Bomb / Pluck (strings) / Bounce",
        "category": "Concise Keyword Cleanup",
        "reason": "Standardize semicolon/comma mix to slash keywords."
    },
    1787581231369: { # 娲 [wā]
        "new_english": "Goddess Nuwa (mythology)",
        "category": "Concise Keyword Cleanup",
        "reason": "Clean 'goddess in Chinese mythology (Nüwa)'."
    },
    1778227239705: { # 瑰 [guī]
        "new_english": "Rose Gem / Extraordinary Jade",
        "category": "Concise Keyword Cleanup",
        "reason": "Replace vague '(Semiprecious stone)' with meaningful keyword matching 玫瑰 and character sense."
    },
    1778227239972: { # 玫 [méi]
        "new_english": "Rose Gem / Fine Jade",
        "category": "Concise Keyword Cleanup",
        "reason": "Replace vague '(Fine jade)' with meaningful keyword matching 玫瑰 and character sense."
    },
    1778227239500: { # 籽 [zǐ]
        "new_english": "Seed (plant)",
        "category": "Concise Keyword Cleanup",
        "reason": "Clean 'Seed (of a plant)'."
    },
    1778227239630: { # 叮 [dīng]
        "new_english": "Sting / Bite (insect)",
        "category": "Concise Keyword Cleanup",
        "reason": "Clean verbose dictionary gloss 'To sting or bite (of mosquito, bee etc)'."
    },
    1778227240089: { # 揍 [zòu]
        "new_english": "Hit / Beat (sb)",
        "category": "Concise Keyword Cleanup",
        "reason": "Remove leading 'To ' and standardize."
    },
    1778227240103: { # 涂 [tú]
        "new_english": "Apply / Spread (paint)",
        "category": "Concise Keyword Cleanup",
        "reason": "Clean 'To apply (paint etc)'."
    },
    1768474725833: { # 斯 [sī]
        "new_english": "This / Suffix",
        "category": "Concise Keyword Cleanup",
        "reason": "Clean 'This / (Suffix)' to standard keyword format."
    },
    1768474726375: { # 唉 [āi]
        "new_english": "Alas / Sigh",
        "category": "Concise Keyword Cleanup",
        "reason": "Clean 'Alas / (Sigh)' to standard keyword format."
    },
    1768474726376: { # 诶 [èi]
        "new_english": "Hey / Interjection",
        "category": "Concise Keyword Cleanup",
        "reason": "Clean 'Hey / (Interjection)' to standard keyword format."
    },
    1768474726147: { # 哇 [wa]
        "new_english": "Wow / Particle",
        "category": "Concise Keyword Cleanup",
        "reason": "Clean 'Wow / (Particle)' to standard keyword format."
    }
}

print(f"Total defined updates: {len(UPDATES)}")

# Verify all note IDs exist in anki_data
missing_nids = [nid for nid in UPDATES if nid not in char_map]
if missing_nids:
    print(f"ERROR: {len(missing_nids)} note IDs not found in anki_data: {missing_nids}")
    sys.exit(1)

# Check all chars with '(' in English
all_with_paren = [c for c in chars if '(' in c.get('english', '') or '（' in c.get('english', '')]
print(f"Total characters with '(' in english: {len(all_with_paren)}")

kept_chars = [c for c in all_with_paren if c['note_id'] not in UPDATES]
print(f"Characters kept as is (optimal clarifiers): {len(kept_chars)}")

print("\n--- Summary of Kept Characters ---")
for c in kept_chars:
    print(f"  {c['hanzi']} [{c['pinyin']}]: \"{c['english']}\"")

# Save definitive dataset
dataset = {
    "total_with_paren": len(all_with_paren),
    "total_improved": len(UPDATES),
    "total_kept": len(kept_chars),
    "updates": [
        {
            "note_id": nid,
            "hanzi": char_map[nid]['hanzi'],
            "pinyin": char_map[nid]['pinyin'],
            "old_english": char_map[nid]['english'],
            "new_english": u["new_english"],
            "category": u["category"],
            "reason": u["reason"]
        }
        for nid, u in UPDATES.items()
    ],
    "kept": [
        {
            "note_id": c['note_id'],
            "hanzi": c['hanzi'],
            "pinyin": c['pinyin'],
            "english": c['english'],
            "reason": "Accurate, concise semantic disambiguator (e.g. distinguishing from homophones/near-synonyms)"
        }
        for c in kept_chars
    ]
}

with open('data/char_translation_improvements.json', 'w', encoding='utf-8') as f:
    json.dump(dataset, f, ensure_ascii=False, indent=2)

print("\nSaved dataset to data/char_translation_improvements.json")
