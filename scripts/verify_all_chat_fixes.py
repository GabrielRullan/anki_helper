import os
import re
import sys
import json
from collections import Counter

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath('scripts'))

from anki_db import AnkiConnection
from fix_mbp_assignments import STANDARD_ACTORS, VALID_SETS, clean_html, parse_mbp_pinyin

ACTOR_KEYWORDS = {
    'Jackie Chan': ['jackie chan', 'jackie'],
    'Batman': ['batman', 'bruce wayne'],
    'Captain Marvel (Brie Larson)': ['captain marvel', 'brie larson'],
    'Bugs Bunny': ['bugs bunny'],
    'Peter Griffin': ['peter griffin'],
    'Pikachu': ['pikachu'],
    'Puar': ['puar'],
    'Luke Skywalker (Matt Hamill)': ['luke skywalker', 'skywalker', 'matt hamill', 'mark hamill'],
    'Minnie Mouse': ['minnie mouse', 'minnie'],
    'Munchlax': ['munchlax'],
    'Morgan Freeman': ['morgan freeman'],
    'Bender (Futurama)': ['bender'],
    'Maui (Dwayne the Rock)': ['maui', 'dwayne', 'the rock'],
    'Diva': ['diva', 'd.va'],
    'Dumbo': ['dumbo'],
    'Big bald black cop (Terry Crews)': ['terry crews', 'bald black cop'],
    'Tinkerbell': ['tinkerbell', 'tinker bell'],
    'Trunks (DBZ)': ['trunks'],
    'Astrophysicist (Neil Degrasse Tyson)': ['neil degrasse', 'tyson', 'astrophysicist'],
    'Amidala (Natalie Portman)': ['amidala', 'natalie portman', 'padme', 'padmé'],
    'Queen of England (Nu Wang)': ['queen of england', 'nu wang', 'the queen', 'queen elizabeth'],
    'Qui Gon Jinn (Liam Neeson)': ['qui gon', 'qui-gon', 'liam neeson'],
    'Lisa Simpsons': ['lisa simpson', 'lisa'],
    'Lucario': ['lucario'],
    'Chef (Gordon Ramsey)': ['gordon ramsey', 'gordon ramsay', 'ramsey', 'ramsay', 'chef'],
    'Growthlite': ['growthlite', 'growlithe'],
    'Kevin Hart': ['kevin hart'],
    'Kenny (South Park)': ['kenny'],
    'Indiana Jones (Harrison Ford)': ['indiana jones', 'harrison ford', 'indy'],
    'Hulk': ['hulk'],
    'Wednesdey Adams (Gena Ortega)': ['wednesdey', 'wednesday', 'ortega'],
    'Jimbey': ['jimbey', 'jinbe', 'jimbei'],
    'Chi-Chi (DBZ)': ['chi-chi', 'chichi'],
    'Sanji': ['sanji'],
    "Alien's Ripley (Sigourney)": ['ripley', 'sigourney'],
    'Chopper': ['chopper'],
    'Branch Trolls (J. Timberlake)': ['branch', 'timberlake'],
    'Daddy Pig 猪 (zhū)': ['daddy pig'],
    'Chaplin': ['chaplin'],
    'Chewacca': ['chewacca', 'chewbacca'],
    '007 (Connery)': ['007', 'connery', 'james bond'],
    'Shrek': ['shrek'],
    'Edward Twilight (R. Pattinson)': ['edward', 'pattinson', 'twilight'],
    'The Watcher (Ru Guo)': ['the watcher', 'ru guo', 'watcher'],
    'El Zorro': ['zorro'],
    'Zoolander': ['zoolander'],
    'C-3P0': ['c-3p0', 'c-3po', 'c3po'],
    'Curation/Articuno': ['curation', 'articuno'],
    'Samuel L Jackson': ['samuel l', 'jackson'],
    'Superman': ['superman'],
    'Yelena (Black Widow)': ['yelena', 'black widow'],
    'Usopp': ['usopp'],
    'Su Wu kong': ['su wu kong', 'sun wukong', 'wukong'],
}

def check_actor_in_scene(expected_actor, scene_text):
    s = scene_text.lower()
    kws = ACTOR_KEYWORDS.get(expected_actor, [expected_actor.lower()])
    return any(kw in s for kw in kws)

def main():
    with AnkiConnection(profile_name="Main") as anki:
        char_deck = anki.best_match_deck(["Chinese::Char", "Chinese\x1fChar", "Characters"])
        word_deck = anki.best_match_deck(["Chinese::Words", "Chinese\x1fWords", "Words"])
        char_notes = anki.get_notes_in_deck(char_deck)
        word_notes = anki.get_notes_in_deck(word_deck)

        # Also query card-level flags and queues for Chinese::Char
        cur = anki.conn.cursor()
        decks = anki.get_decks()
        char_did = [d for d, name in decks.items() if name == char_deck][0]
        cur.execute("""
            SELECT c.id, c.nid, c.queue, c.flags
            FROM cards c
            WHERE c.did = ? OR c.odid = ?
        """, (char_did, char_did))
        card_rows = cur.fetchall()

        media_dir = os.path.join(os.path.dirname(anki.db_path), "collection.media")

    nid_to_cards = {}
    for cid, nid, queue, flags in card_rows:
        nid_to_cards.setdefault(nid, []).append({
            'cid': cid,
            'queue': queue,
            'flags': flags & 7
        })

    print(f"=== 1. SUSPENDED CHARACTERS PRESENT IN WORD CARDS ===")
    word_char_map = {}
    for wn in word_notes:
        w = clean_html(wn['fields'].get('Word', ''))
        for ch in set(w):
            if '\u4e00' <= ch <= '\u9fff':
                word_char_map.setdefault(ch, []).append(w)

    susp_in_words_notes = 0
    susp_in_words_cards = 0
    unflagged_susp_cards = []
    for cn in char_notes:
        nid = cn['id']
        cards = nid_to_cards.get(nid, [])
        susp_cards = [c for c in cards if c['queue'] == -1]
        if not susp_cards:
            continue
        h = cn['fields'].get('Hanzi', '').strip()
        simp = cn['fields'].get('Simplified', '').strip()
        words = list(word_char_map.get(h, []))
        if simp and simp != h:
            for w in word_char_map.get(simp, []):
                if w not in words:
                    words.append(w)
        if words:
            susp_in_words_notes += 1
            susp_in_words_cards += len(susp_cards)
            for sc in susp_cards:
                if sc['flags'] != 1:
                    unflagged_susp_cards.append((nid, h, sc['cid'], sc['flags']))

    print(f"Suspended character notes in words: {susp_in_words_notes}")
    print(f"Suspended character cards in words: {susp_in_words_cards}")
    print(f"Unflagged suspended cards (missing Red Flag 1): {len(unflagged_susp_cards)}")
    if unflagged_susp_cards:
        print("  Unflagged details:", unflagged_susp_cards)

    print(f"\n=== 2. USER'S SPECIFIC REPORTED EXAMPLES ===")
    target_ids = {'junda_2356_40718', 'junda_2612_40667', 'mbp_84_惦'}
    for cn in char_notes:
        cid_field = clean_html(cn['fields'].get('ID', ''))
        h = clean_html(cn['fields'].get('Hanzi', ''))
        if cid_field in target_ids or h in ('徊', '绰', '惦'):
            print(f"- Note {cn['id']} | ID={cid_field} | Hanzi={h} | Pinyin={clean_html(cn['fields'].get('Pinyin', ''))}")
            print(f"  Suspended: {cn['suspended']} | Tags: {cn['tags']}")
            print(f"  Initial={clean_html(cn['fields'].get('Initial', ''))} | Actor={clean_html(cn['fields'].get('Actor', ''))} | Set={clean_html(cn['fields'].get('Set', ''))} | ToneLoc={clean_html(cn['fields'].get('ToneLocation', ''))}")
            print(f"  Scene: {clean_html(cn['fields'].get('Scene', ''))}")
            print(f"  Image: {cn['fields'].get('Image', '')}")

    print(f"\n=== 3. FULL MBP CODEBOOK & SCENE AUDIT ACROSS ALL {len(char_notes)} NOTES ===")
    init_mismatches = []
    actor_mismatches = []
    set_mismatches = []
    empty_scenes = []
    tags_counter = Counter()
    scene_missing_expected_actor = []
    mbp_fixed_scene_missing_actor = []
    active_mbp_fixed_scene_missing_actor = []
    missing_media_files = []

    for cn in char_notes:
        nid = cn['id']
        for t in cn['tags']:
            tags_counter[t] += 1
        fields = cn['fields']
        h = clean_html(fields.get('Hanzi', ''))
        pinyin = fields.get('Pinyin', '')
        c_init, c_set, tone = parse_mbp_pinyin(pinyin)
        if not c_init or c_init not in STANDARD_ACTORS:
            continue
        exp_init = 'Nu' if c_init == 'Nv' else ('Lu' if c_init == 'Lv' else c_init)
        exp_actor = STANDARD_ACTORS[c_init]
        exp_set = c_set

        cur_init = clean_html(fields.get('Initial', ''))
        cur_actor = clean_html(fields.get('Actor', ''))
        cur_set = clean_html(fields.get('Set', ''))
        cur_scene = clean_html(fields.get('Scene', ''))
        cur_img = fields.get('Image', '')

        if cur_init != exp_init:
            init_mismatches.append((nid, h, cur_init, exp_init))
        if cur_actor != exp_actor:
            actor_mismatches.append((nid, h, cur_actor, exp_actor))
        if cur_set != exp_set:
            set_mismatches.append((nid, h, cur_set, exp_set))
        if not cur_scene:
            empty_scenes.append((nid, h))
        else:
            if not check_actor_in_scene(exp_actor, cur_scene):
                scene_missing_expected_actor.append((nid, h, exp_actor, cur_scene, cn['suspended'], cn['tags']))
                if 'mbp_fixed' in cn['tags']:
                    mbp_fixed_scene_missing_actor.append((nid, h, exp_actor, cur_scene, cn['suspended'], cn['tags']))
                    if not cn['suspended']:
                        active_mbp_fixed_scene_missing_actor.append((nid, h, exp_actor, cur_scene, cn['tags']))

        # Check media file existence if Image field has <img src="...">
        m = re.search(r'src="([^"]+)"', cur_img)
        if m:
            fname = m.group(1)
            if not os.path.exists(os.path.join(media_dir, fname)):
                missing_media_files.append((nid, h, fname))

    print(f"Initial mismatches: {len(init_mismatches)}")
    print(f"Actor mismatches: {len(actor_mismatches)}")
    print(f"Set mismatches: {len(set_mismatches)}")
    print(f"Empty scenes: {len(empty_scenes)}")
    print(f"Tag counts: mbp_fixed={tags_counter['mbp_fixed']}, needs_scene_update={tags_counter['needs_scene_update']}, needs_image_update={tags_counter['needs_image_update']}")
    print(f"Missing media files in collection.media: {len(missing_media_files)}")
    print(f"Total notes where Scene does not literally contain expected Actor keyword: {len(scene_missing_expected_actor)}")
    print(f"  - Among 'mbp_fixed' notes: {len(mbp_fixed_scene_missing_actor)}")
    print(f"  - Among ACTIVE (non-suspended) 'mbp_fixed' notes: {len(active_mbp_fixed_scene_missing_actor)}")

    if scene_missing_expected_actor:
        print("\nAll notes where Scene doesn't contain expected Actor keyword:")
        for item in scene_missing_expected_actor:
            print(f"  nid={item[0]} {item[1]} | susp={item[4]} | tags={item[5]} | expected={item[2]} | scene={item[3]}")

    print("\n=== 4. TONE & TONE-LOCATION AUDIT ===")
    STANDARD_TONE_LOCS = {
        1: 'In Front [1]',
        2: 'Hall or Kitchen [2]',
        3: 'Room [3]',
        4: 'Backyard [4]',
        5: 'Roof [5]'
    }
    tone_discrepancies = []
    nonstandard_tloc_format = []
    for cn in char_notes:
        f = cn['fields']
        h = clean_html(f.get('Hanzi', ''))
        p = f.get('Pinyin', '')
        c_init, c_set, exp_tone = parse_mbp_pinyin(p)
        cur_tone = clean_html(f.get('Tone', ''))
        cur_tloc = clean_html(f.get('Tone-Location', ''))
        if exp_tone is None or cur_tone != str(exp_tone) or str(exp_tone) not in cur_tloc:
            tone_discrepancies.append((cn, h, clean_html(p), exp_tone, cur_tone, cur_tloc))
        elif cur_tloc != STANDARD_TONE_LOCS.get(exp_tone):
            nonstandard_tloc_format.append((cn['id'], h, exp_tone, cur_tloc, STANDARD_TONE_LOCS.get(exp_tone)))

    print(f"Tone or Tone-Location number discrepancies: {len(tone_discrepancies)}")
    for cn, h, p_clean, exp_tone, cur_tone, cur_tloc in tone_discrepancies:
        f = cn['fields']
        print(f"  nid={cn['id']} {h} | susp={cn['suspended']} | Pinyin={p_clean} | English={clean_html(f.get('English',''))} | Words={clean_html(f.get('Common Words',''))} | Init={clean_html(f.get('Initial',''))} | Actor={clean_html(f.get('Actor',''))} | Set={clean_html(f.get('Set',''))} | Tone={cur_tone} (from pinyin: {exp_tone}) | ToneLoc={cur_tloc}")
        print(f"    Scene: {clean_html(f.get('Scene',''))}")

    print(f"\nNon-standard Tone-Location string wording (e.g. 'Front Yard / Entrance [1]' vs 'In Front [1]'): {len(nonstandard_tloc_format)}")
    for item in nonstandard_tloc_format[:10]:
        print(" ", item)

    print("\n=== 5. POLYPHONE / TYPO NOTES INSPECTION ===")
    poly_nids = [1768474725920, 1768474726047, 1768474726255, 1778227240421, 1778227240603, 1785483667575, 1786803210717, 1786803211177, 1786803211622, 1786803211074, 1786803211312, 1786803211319, 1786803211466, 1786803211903, 1786803213258, 1786803213642, 1786803213885, 1786803214211, 1786803214878, 1786803214883, 1786803215060, 1786803215227, 1786803215247, 1789384645608, 1786803213033]
    char_by_id = {n['id']: n for n in char_notes}
    for nid in poly_nids:
        cn = char_by_id[nid]
        f = cn['fields']
        print(f"nid={nid} {clean_html(f['Hanzi'])} | ID={clean_html(f['ID'])} | susp={cn['suspended']} | tags={cn['tags']}")
        print(f"  Pinyin={clean_html(f['Pinyin'])} | English={clean_html(f['English'])} | CW={clean_html(f['Common Words'])}")
        print(f"  Init={clean_html(f['Initial'])} | Actor={clean_html(f['Actor'])} | Set={clean_html(f['Set'])} | Tone={clean_html(f['Tone'])} | ToneLoc={clean_html(f['Tone-Location'])}")
        print(f"  Scene={clean_html(f['Scene'])}")

if __name__ == "__main__":
    main()
