import os
import re
import sys
import json
import urllib.request

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath('scripts'))

from anki_db import AnkiConnection
from fix_mbp_assignments import clean_html, parse_mbp_pinyin
from apply_generated_scenes_and_images import get_media_filename

ANKICONNECT_URL = 'http://127.0.0.1:8765'

STANDARD_TONE_LOCS = {
    '1': 'In Front [1]',
    '2': 'Hall or Kitchen [2]',
    '3': 'Room [3]',
    '4': 'Backyard [4]',
    '5': 'Roof [5]'
}

def request_anki(action, **params):
    payload = {"action": action, "version": 6}
    if params:
        payload["params"] = params
    req = urllib.request.Request(
        ANKICONNECT_URL,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req, timeout=20) as response:
        res = json.loads(response.read().decode('utf-8'))
        if res.get('error'):
            raise RuntimeError(f"AnkiConnect error on {action}: {res['error']}")
        return res.get('result')

def main():
    # 1. Flag suspended card 耿 (cid=1786803212968) with Red Flag (1)
    print("1. Flagging suspended character card 耿 (cid=1786803212968) with Red Flag (1)...")
    request_anki("setSpecificValueOfCard", card=1786803212968, keys=["flags"], newValues=[1])

    # 2. Specific note field fixes
    specific_updates = {
        # Polyphone / typo notes where Initial/Actor/Set/Scene need correction
        1768474726047: { # 炮 (Cannon -> pào)
            'Pinyin': '<span class="tone4">pào</span> <!-- pao -->',
            'Initial': 'P',
            'Actor': 'Peter Griffin',
            'Set': '-ao',
            'Tone': '4',
            'Tone-Location': 'Backyard [4]',
            'Scene': 'In the Backyard [4] of the -ao set, **Peter Griffin** lights a **Torch** (火) under a tightly wrapped **Package** (包) and blasts it out of a massive **CANNON**.'
        },
        1768474726255: { # 楷 (Model / Pattern -> kǎi)
            'Pinyin': '<span class="tone3">kǎi</span> <!-- kai -->',
            'Initial': 'K',
            'Actor': 'Kevin Hart',
            'Set': '-ai',
            'Tone': '3',
            'Tone-Location': 'Room [3]',
            'Scene': 'In the Room [3] of the -ai set, **Kevin Hart** arranges **White Poker Chips** (白) and **spoons** (比) around a **Fig Tree** (木) into a precise **MODEL** and **PATTERN**.'
        },
        1785483667575: { # 衰 (Wane -> shuāi)
            'Pinyin': 'shuāi',
            'Initial': 'Shu',
            'Actor': 'Shrek',
            'Set': '-ai',
            'Tone': '1',
            'Tone-Location': 'In Front [1]',
            'Scene': "In Front [1] of the -ai set, **Shrek** wears a **Pickle top hat** (亠) and a **White crazy shirt** (衣) while **Kirby's Giant Mouth** (口) drains his energy, causing his strength to **WANE**."
        },
        1778227240421: { # 溃 (Crumble -> kuì)
            'Pinyin': 'kuì',
            'Initial': 'Ku',
            'Actor': 'Kenny (South Park)',
            'Set': '-ei',
            'Tone': '4',
            'Tone-Location': 'Backyard [4]',
            'Scene': 'In the Backyard [4] of the -ei set, **Kenny (South Park)** sprays a **Water hose** (氵) at a priceless **Expensive** (贵) statue until its base begins to **CRUMBLE** and collapse.'
        },
        1786803214878: { # 掺 (Mix; Blend -> chān, suspended)
            'Pinyin': 'chān',
            'Initial': 'Ch',
            'Actor': 'Chaplin',
            'Set': '-an',
            'Tone': '1',
            'Tone-Location': 'In Front [1]',
            'Scene': "In Front [1] of the -an set, **Chaplin** uses **Thing's hand** (扌) to stir **ginseng** (参) and **Cousin Itt's hair** (彡) together to **MIX** and **BLEND** a potion."
        },
        1786803215060: { # 诘 (Question; Interrogate -> jié, suspended)
            'Pinyin': 'jié',
            'Initial': 'Ji',
            'Actor': 'Wednesdey Adams (Gena Ortega)',
            'Set': '-e',
            'Tone': '2',
            'Tone-Location': 'Hall or Kitchen [2]',
            'Scene': 'In the Hall or Kitchen [2] of the -e set, **Wednesdey Adams (Gena Ortega)** speaks into a **microphone and megaphone** (讠) to **Auspicious** (吉) suspects to **QUESTION** and **INTERROGATE** them.'
        },
        # Pinyin / Tone / Tone-Location alignment fixes
        1768474724432: { # ⻢ (Horse -> mǎ)
            'Pinyin': 'mǎ'
        },
        1768474724953: { # 条 (Noodle -> tiáo)
            'Pinyin': 'tiáo'
        },
        1768474724984: { # 且 (Moreover -> qiě)
            'Pinyin': 'qiě'
        },
        1768474725684: { # 克 (Gram / Overcome -> kè, tone 4)
            'Tone': '4',
            'Tone-Location': 'Backyard [4]',
            'Scene': 'In the Backyard [4] of the -e set, **Kevin Hart** uses a **Christian Cross** (十) to **OVERCOME** an **elder brother** (兄) who weighs only one **GRAM**.'
        },
        1768474725729: { # 尽 (Exhaust / Finish -> jìn, tone 4)
            'Pinyin': '<span class="tone4">jìn</span> <!-- jin -->'
        },
        1768474725733: { # 观 (Look / View -> guān, tone 1)
            'Pinyin': '<span class="tone1">guān</span> <!-- guan -->'
        },
        1768474725777: { # 扇 (Fan -> shàn, tone 4)
            'Pinyin': '<span class="tone4">shàn</span> <!-- shan -->'
        },
        1768474725846: { # 载 (Load / Carry -> zài, tone 4)
            'Pinyin': '<span class="tone4">zài</span> <!-- zai -->'
        },
        1768474726046: { # 泡 (Bubble / Soak -> pào, tone 4)
            'Pinyin': '<span class="tone4">pào</span> <!-- pao -->'
        },
        1768474726063: { # 茄 (Eggplant -> qié, tone 2)
            'Pinyin': '<span class="tone2">qié</span> <!-- qie -->'
        },
        1778227240935: { # 呗 (Particle -> bai, tone 5)
            'Tone-Location': 'Roof [5]',
            'Scene': "On the Roof [5] of the -ai set, **Batman** uses **Kirby's Giant Mouth** (口) to point out the obvious conclusion of the **Shell** (贝) game."
        },
        # 2 active mbp_fixed notes missing Jackie Chan in Scene
        1778227240380: { # 噩 (Startling -> è, Jackie Chan)
            'Scene': 'In the Backyard [4] of the -e set, **Jackie Chan** helps the **King** (王) fight off four ravenous **Giant Mouths** (口口口口) in a **STARTLING** and terrifying ambush.'
        },
        1778227240505: { # 殴 (Beat Up / Hit Someone -> ōu, Jackie Chan)
            'Scene': 'In Front [1] of the -ou set, **Jackie Chan** dodges a **Medical Lance** (殳) inside a **Monopoly Map zone** (区) as rival fighters try to **BEAT UP** and **HIT SOMEONE**.'
        },
        # 8 descriptive-actor scenes -> add explicit canonical actor name for 100% consistency
        1768474724474: { # 讨
            'Scene': "Big bald black cop (Terry Crews) uses loud speech (讠) while standing only an inch (寸) from a suspect's face to discuss a crime."
        },
        1768474725107: { # 括
            'Scene': 'Kenny (South Park), the boy in the orange parka, uses his hand (扌) to grab his own giant tongue (舌) to make sure it is included in the family photo.'
        },
        1768474725125: { # 扩
            'Scene': 'Kenny (South Park), the boy in the orange parka, uses his hand (扌) to stretch a broad (广) sheet of rubber until it expands and violently explodes.'
        },
        1768474725310: { # 赖
            'Scene': 'Qui Gon Jinn (Liam Neeson), the wise bearded Jedi master, drops a heavy bundle (束) in defeat (负) and points his finger to blame his apprentice.'
        },
        1768474726363: { # 跪
            'Scene': 'Growthlite, the fiery dog creature, hurts its foot (足) while running from a terrible danger (危), forcing it to kneel on the ground in pain.'
        },
        1768474726380: { # 袭
            'Scene': "Alien's Ripley (Sigourney), the tough space marine, wears a legendary suit of clothing (衣) made of dragon (龙) scales, which allows her to survive a massive alien attack."
        },
        1768474726385: { # 绒
            'Scene': 'Edward Twilight (R. Pattinson), the pale vampire, weaves silk threads (纟) around military weapons (戎) to create soft velvet covers so they do not sparkle in the sun.'
        },
        1768474726397: { # 饲
            'Scene': 'Samuel L Jackson takes a giant plate of food (饣) and fiercely manages (司) to feed it to a pack of wild raptors he is trying to raise.'
        }
    }

    # Also find all 39 notes with non-standard Tone-Location wording
    with AnkiConnection(profile_name="Main") as anki:
        char_notes = anki.get_notes_in_deck(anki.best_match_deck(["Chinese::Char"]))

    for cn in char_notes:
        nid = cn['id']
        cur_tone = clean_html(cn['fields'].get('Tone', ''))
        cur_tloc = clean_html(cn['fields'].get('Tone-Location', ''))
        exp_tloc = STANDARD_TONE_LOCS.get(cur_tone)
        if exp_tloc and cur_tloc != exp_tloc and nid not in specific_updates:
            specific_updates[nid] = {'Tone-Location': exp_tloc}
        elif exp_tloc and cur_tloc != exp_tloc and 'Tone-Location' not in specific_updates[nid]:
            specific_updates[nid]['Tone-Location'] = exp_tloc

    actions = [
        {"action": "updateNoteFields", "params": {"note": {"id": nid, "fields": flds}}}
        for nid, flds in specific_updates.items()
    ]
    print(f"2. Applying field updates to {len(actions)} notes via AnkiConnect...")
    request_anki("multi", actions=actions)

    # Tag the 8 active notes that need new/updated images with needs_image_update
    regen_nids = [
        1768474726047, # 炮
        1768474726255, # 楷
        1785483667575, # 衰
        1778227240421, # 溃
        1768474725684, # 克
        1778227240935, # 呗
        1778227240380, # 噩
        1778227240505, # 殴
    ]
    request_anki("addTags", notes=regen_nids, tags="needs_image_update")
    print(f"3. Tagged {len(regen_nids)} active notes with 'needs_image_update'.")

    # Update data/active_scenes_merged.json and delete stale regenerated images for 炮, 楷, 衰
    regen_dir = os.path.abspath(os.path.join('imagenes_vocabulario', 'mbp_regenerated'))
    merged_path = 'data/active_scenes_merged.json'
    merged = json.load(open(merged_path, encoding='utf-8'))
    merged_by_nid = {item['note_id']: item for item in merged}

    char_by_nid = {n['id']: n for n in char_notes}
    for nid in regen_nids:
        cn = char_by_nid[nid]
        f = cn['fields'].copy()
        f.update(specific_updates.get(nid, {}))
        h = clean_html(f['Hanzi'])
        eng = clean_html(f['English'])
        fname = get_media_filename(h, eng)
        stale_path = os.path.join(regen_dir, fname)
        if os.path.exists(stale_path):
            os.remove(stale_path)
            print(f"   Removed stale image {fname} so it will be regenerated with the corrected Actor.")
        # Also remove any old artifact nid_<nid>_* so prepare_next_image_wave doesn't re-copy the old image!
        artifact_dir = r'C:\Users\gabri\.gemini\antigravity\brain\20ac4fc3-656b-4a42-b283-4a8aef7a6354'
        import glob
        for old_art in glob.glob(os.path.join(artifact_dir, f"nid_{nid}_*.*")):
            try:
                os.remove(old_art)
                print(f"   Removed old artifact {os.path.basename(old_art)}")
            except OSError:
                pass

        if nid in merged_by_nid:
            merged_by_nid[nid]['actor'] = clean_html(f['Actor'])
            merged_by_nid[nid]['initial'] = clean_html(f['Initial'])
            merged_by_nid[nid]['set'] = clean_html(f['Set'])
            merged_by_nid[nid]['tone_location'] = clean_html(f['Tone-Location'])
            merged_by_nid[nid]['scene'] = f['Scene']
        else:
            new_entry = {
                'note_id': nid,
                'hanzi': h,
                'pinyin': clean_html(f['Pinyin']),
                'english': eng,
                'initial': clean_html(f['Initial']),
                'actor': clean_html(f['Actor']),
                'set': clean_html(f['Set']),
                'tone': clean_html(f['Tone']),
                'tone_location': clean_html(f['Tone-Location']),
                'components': clean_html(f.get('Components', '')),
                'resolved_props': [],
                'old_scene': clean_html(cn['fields'].get('Scene', '')),
                'scene': f['Scene']
            }
            merged.append(new_entry)
            merged_by_nid[nid] = new_entry

    with open(merged_path, 'w', encoding='utf-8') as f_out:
        json.dump(merged, f_out, ensure_ascii=False, indent=2)
    print(f"4. Updated {merged_path} (total items: {len(merged)}).")

if __name__ == "__main__":
    main()
