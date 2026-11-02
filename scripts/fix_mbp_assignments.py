import os
import re
import sys
import json
import time
import math
import urllib.request
from collections import Counter

sys.stdout.reconfigure(encoding='utf-8')

ANKICONNECT_URL = 'http://127.0.0.1:8765'

STANDARD_ACTORS = {
    '(null)': 'Jackie Chan',
    'B': 'Batman',
    'Bi': 'Captain Marvel (Brie Larson)',
    'Bu': 'Bugs Bunny',
    'P': 'Peter Griffin',
    'Pi': 'Pikachu',
    'Pu': 'Puar',
    'M': 'Luke Skywalker (Matt Hamill)',
    'Mi': 'Minnie Mouse',
    'Mu': 'Munchlax',
    'F': 'Morgan Freeman',
    'Fu': 'Bender (Futurama)',
    'D': 'Maui (Dwayne the Rock)',
    'Di': 'Diva',
    'Du': 'Dumbo',
    'T': 'Big bald black cop (Terry Crews)',
    'Ti': 'Tinkerbell',
    'Tu': 'Trunks (DBZ)',
    'N': 'Astrophysicist (Neil Degrasse Tyson)',
    'Ni': 'Amidala (Natalie Portman)',
    'Nu': 'Queen of England (Nu Wang)',
    'Nv': 'Queen of England (Nu Wang)',
    'L': 'Qui Gon Jinn (Liam Neeson)',
    'Li': 'Lisa Simpsons',
    'Lu': 'Lucario',
    'Lv': 'Lucario',
    'G': 'Chef (Gordon Ramsey)',
    'Gu': 'Growthlite',
    'K': 'Kevin Hart',
    'Ku': 'Kenny (South Park)',
    'H': 'Indiana Jones (Harrison Ford)',
    'Hu': 'Hulk',
    'Ji': 'Wednesdey Adams (Gena Ortega)',
    'Ju': 'Jimbey',
    'Qi': 'Chi-Chi (DBZ)',
    'Qu': 'Sanji',
    'Xi': "Alien's Ripley (Sigourney)",
    'Xu': 'Chopper',
    'Zh': 'Branch Trolls (J. Timberlake)',
    'Zhu': 'Daddy Pig 猪 (zhū)',
    'Ch': 'Chaplin',
    'Chu': 'Chewacca',
    'Sh': '007 (Connery)',
    'Shu': 'Shrek',
    'R': 'Edward Twilight (R. Pattinson)',
    'Ru': 'The Watcher (Ru Guo)',
    'Z': 'El Zorro',
    'Zu': 'Zoolander',
    'C': 'C-3P0',
    'Cu': 'Curation/Articuno',
    'S': 'Samuel L Jackson',
    'Su': 'Superman',
    'Y': 'Yelena (Black Widow)',
    'Yu': 'Usopp',
    'W': 'Su Wu kong',
}

VALID_SETS = {
    '-(Null)', '-a', '-o', '-e', '-ai', '-ei', '-ao', '-ou',
    '-an', '-en', '-ang', '-eng', '-ong', 'Childhood Home'
}

def clean_html(text):
    if not text:
        return ""
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('&nbsp;', ' ').replace('&#x27;', "'").replace('&quot;', '"').replace('&amp;', '&')
    return text.strip()

def parse_mbp_pinyin(pinyin_raw):
    """
    Parses a primary pinyin syllable into Mandarin Blueprint (mbp_initial, mbp_set, tone).
    """
    if not pinyin_raw:
        return None, None, None
    cleaned = clean_html(pinyin_raw)
    if not cleaned:
        return None, None, None
    # Take first reading if separated by comma, slash, semicolon, or whitespace
    p = re.split(r'[,/;\s]+', cleaned)[0].strip().lower()
    if not p:
        return None, None, None

    tone_marks = {
        'ā': ('a', 1), 'á': ('a', 2), 'ǎ': ('a', 3), 'à': ('a', 4),
        'ē': ('e', 1), 'é': ('e', 2), 'ě': ('e', 3), 'è': ('e', 4),
        'ī': ('i', 1), 'í': ('i', 2), 'ǐ': ('i', 3), 'ì': ('i', 4),
        'ō': ('o', 1), 'ó': ('o', 2), 'ǒ': ('o', 3), 'ò': ('o', 4),
        'ū': ('u', 1), 'ú': ('u', 2), 'ǔ': ('u', 3), 'ù': ('u', 4),
        'ǖ': ('v', 1), 'ǘ': ('v', 2), 'ǚ': ('v', 3), 'ǜ': ('v', 4),
        'ü': ('v', None),
        'ń': ('n', 2), 'ň': ('n', 3), 'ǹ': ('n', 4),
        'ḿ': ('m', 2),
    }
    tone = 5
    clean_p = ""
    for ch in p:
        if ch in tone_marks:
            base, t = tone_marks[ch]
            clean_p += base
            if t is not None:
                tone = t
        elif ch.isdigit() and ch in '12345':
            tone = int(ch)
        elif 'a' <= ch <= 'z':
            clean_p += ch

    if not clean_p:
        return None, None, None

    # Special nasal interjections (嗯 ng/n)
    if clean_p in ('ng', 'n', 'hm', 'hng'):
        return 'N', '-(Null)', tone
    if clean_p == 'm':
        return 'M', '-(Null)', tone

    # er -> Jackie Chan in Childhood Home
    if clean_p == 'er':
        return '(null)', 'Childhood Home', tone

    raw_init = ""
    raw_fin = clean_p
    for dbl in ('zh', 'ch', 'sh'):
        if clean_p.startswith(dbl):
            raw_init = dbl
            raw_fin = clean_p[2:]
            break
    if not raw_init:
        for sgl in 'bpmfdtnlgkhjqxrzcsyw':
            if clean_p.startswith(sgl):
                raw_init = sgl
                raw_fin = clean_p[1:]
                break

    if raw_init == 'y':
        if raw_fin.startswith('u') or raw_fin.startswith('v'):
            rest = raw_fin[1:]
            fin_map = {
                '': '-(Null)',
                'e': '-e',
                'an': '-an',
                'n': '-en',
            }
            return 'Yu', fin_map.get(rest, f'-{rest}'), tone
        else:
            fin_map = {
                'i': '-(Null)',
                'a': '-a',
                'o': '-o',
                'e': '-e',
                'ao': '-ao',
                'ou': '-ou',
                'an': '-an',
                'in': '-en',
                'ang': '-ang',
                'ing': '-eng',
                'ong': '-ong',
            }
            return 'Y', fin_map.get(raw_fin, f'-{raw_fin}'), tone

    if raw_init == 'w':
        fin_map = {
            'u': '-(Null)',
            'a': '-a',
            'o': '-o',
            'ai': '-ai',
            'ei': '-ei',
            'an': '-an',
            'en': '-en',
            'ang': '-ang',
            'eng': '-eng',
        }
        return 'W', fin_map.get(raw_fin, f'-{raw_fin}'), tone

    if raw_init in ('j', 'q', 'x'):
        if raw_fin.startswith('u') or raw_fin.startswith('v'):
            rest = raw_fin[1:]
            fin_map = {
                '': '-(Null)',
                'e': '-e',
                'an': '-an',
                'n': '-en',
            }
            return raw_init.capitalize() + 'u', fin_map.get(rest, f'-{rest}'), tone
        elif raw_fin.startswith('i'):
            rest = raw_fin[1:]
            fin_map = {
                '': '-(Null)',
                'a': '-a',
                'e': '-e',
                'ao': '-ao',
                'u': '-ou',
                'an': '-an',
                'n': '-en',
                'ang': '-ang',
                'ng': '-eng',
                'ong': '-ong',
            }
            return raw_init.capitalize() + 'i', fin_map.get(rest, f'-{rest}'), tone

    if raw_init == '':
        return '(null)', f'-{raw_fin}', tone

    if raw_fin == 'i' and raw_init in ('zh', 'ch', 'sh', 'r', 'z', 'c', 's'):
        return raw_init.capitalize(), '-(Null)', tone

    if raw_fin.startswith('i'):
        rest = raw_fin[1:]
        fin_map = {
            '': '-(Null)',
            'a': '-a',
            'e': '-e',
            'ao': '-ao',
            'u': '-ou',
            'an': '-an',
            'n': '-en',
            'ang': '-ang',
            'ng': '-eng',
        }
        return raw_init.capitalize() + 'i', fin_map.get(rest, f'-{rest}'), tone

    if raw_fin.startswith('u'):
        rest = raw_fin[1:]
        fin_map = {
            '': '-(Null)',
            'a': '-a',
            'o': '-o',
            'ai': '-ai',
            'i': '-ei',
            'an': '-an',
            'n': '-en',
            'ang': '-ang',
        }
        return raw_init.capitalize() + 'u', fin_map.get(rest, f'-{rest}'), tone

    if raw_fin.startswith('v'):
        rest = raw_fin[1:]
        fin_map = {
            '': '-(Null)',
            'e': '-e',
        }
        return raw_init.capitalize() + 'v', fin_map.get(rest, f'-{rest}'), tone

    return raw_init.capitalize(), f'-{raw_fin}', tone

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

def actor_mentioned_in_scene(old_actor, scene_text):
    if not old_actor or not scene_text:
        return False
    scene_lower = scene_text.lower()
    # Extract key tokens from old_actor
    keywords = {
        'Indiana Jones (Harrison Ford)': ['indiana jones', 'harrison ford', 'indy'],
        'Lisa Simpsons': ['lisa simpson', 'lisa'],
        'Batman': ['batman', 'bruce wayne'],
        'Morgan Freeman': ['morgan freeman'],
        'Wednesdey Adams (Gena Ortega)': ['wednesday', 'wednesdey', 'ortega'],
        'Yelena (Black Widow)': ['yelena', 'black widow'],
        'Branch Trolls (J. Timberlake)': ['branch', 'timberlake', 'troll'],
        'Chaplin': ['chaplin'],
        'Charlie Chaplin': ['chaplin'],
        '007 (Connery)': ['007', 'connery', 'james bond', 'bond'],
        'Chef (Gordon Ramsey)': ['gordon', 'ramsey', 'ramsay', 'chef'],
        'Kevin Hart': ['kevin hart'],
        'Luke Skywalker (Matt Hamill)': ['luke skywalker', 'skywalker'],
        'Samuel L Jackson': ['samuel l', 'jackson'],
        'Samuel L. Jackson': ['samuel l', 'jackson'],
        'Peter Griffin': ['peter griffin'],
        'Big bald black cop (Terry Crews)': ['terry crews', 'bald black cop'],
        "Alien's Ripley (Sigourney)": ['ripley', 'sigourney'],
        'C-3P0': ['c-3p0', 'c-3po', 'c3po'],
        'Edward Twilight (R. Pattinson)': ['edward', 'pattinson', 'twilight'],
        'Astrophysicist (Neil Degrasse Tyson)': ['astrophysicist', 'neil degrasse', 'tyson'],
        'Chi-Chi (DBZ)': ['chi-chi', 'chichi'],
        'El Zorro': ['zorro'],
        'Zorro': ['zorro'],
        'Dr. Phil': ['dr. phil', 'dr phil'],
        'Lady Gaga': ['lady gaga'],
        'Gandalf': ['gandalf'],
        'Fred Flintstone': ['fred flintstone', 'flintstone'],
        'Peter Parker (Spider-Man)': ['peter parker', 'spider-man', 'spiderman'],
        'Quentin Tarantino': ['quentin tarantino', 'tarantino'],
        'Snoop Dogg': ['snoop dogg'],
        'Xena': ['xena'],
        'Mark Zuckerberg': ['zuckerberg'],
        'Childhood Hero / Neutral': ['childhood hero'],
        'Kermit the Frog': ['kermit'],
        'Wonder Woman': ['wonder woman'],
        'Nicolas Cage': ['nicolas cage'],
        'Ronald Reagan': ['ronald reagan', 'reagan'],
        'Captain America': ['captain america'],
    }
    for kw in keywords.get(old_actor, [old_actor.lower()]):
        if kw in scene_lower:
            return True
    return False

def main(dry_run=False):
    if dry_run:
        from anki_db import AnkiConnection
        with AnkiConnection(profile_name="Main") as anki:
            char_deck = anki.best_match_deck(["Chinese::Char", "Chinese\x1fChar", "Characters"])
            db_notes = anki.get_notes_in_deck(char_deck)
        notes = [
            {
                'noteId': n['id'],
                'fields': {k: {'value': v} for k, v in n['fields'].items()}
            }
            for n in db_notes
        ]
        print(f"Loaded {len(notes)} notes from local SQLite copy of Chinese::Char.")
    else:
        char_nids = request_anki("findNotes", query='deck:"Chinese::Char"')
        print(f"Fetched {len(char_nids)} notes from Chinese::Char via AnkiConnect.")
        notes = request_anki("notesInfo", notes=char_nids)

    updates = []
    nids_fixed = []
    nids_scene_mismatch = []
    summary = Counter()

    for note in notes:
        nid = note['noteId']
        fields = note.get('fields', {})
        pinyin_raw = fields.get('Pinyin', {}).get('value', '')
        c_init, c_set, _ = parse_mbp_pinyin(pinyin_raw)
        if not c_init or c_init not in STANDARD_ACTORS:
            continue

        expected_init = 'Nu' if c_init == 'Nv' else ('Lu' if c_init == 'Lv' else c_init)
        expected_actor = STANDARD_ACTORS[c_init]
        expected_set = c_set

        if expected_set not in VALID_SETS:
            print(f"[WARN] Unexpected set '{expected_set}' for {fields.get('Hanzi', {}).get('value')} ({pinyin_raw})")
            continue

        cur_init = fields.get('Initial', {}).get('value', '').strip()
        cur_actor_raw = fields.get('Actor', {}).get('value', '').strip()
        cur_actor_clean = clean_html(cur_actor_raw)
        cur_set = fields.get('Set', {}).get('value', '').strip()
        cur_scene = clean_html(fields.get('Scene', {}).get('value', ''))

        new_fields = {}
        substantive_fix = False

        if cur_init != expected_init:
            new_fields['Initial'] = expected_init
            if cur_init.lower() != expected_init.lower():
                summary['initial_changed'] += 1
                substantive_fix = True
            else:
                summary['initial_case_normalized'] += 1

        if cur_actor_raw != expected_actor:
            new_fields['Actor'] = expected_actor
            if cur_actor_clean != expected_actor:
                summary['actor_changed'] += 1
                substantive_fix = True
                if actor_mentioned_in_scene(cur_actor_clean, cur_scene):
                    nids_scene_mismatch.append(nid)
            else:
                summary['actor_html_normalized'] += 1

        if cur_set != expected_set:
            new_fields['Set'] = expected_set
            summary['set_changed'] += 1
            substantive_fix = True

        if new_fields:
            updates.append({
                'id': nid,
                'fields': new_fields
            })
            if substantive_fix:
                nids_fixed.append(nid)

    print(f"Notes requiring field updates: {len(updates)}")
    print(f"Notes with substantive fixes (to be tagged 'mbp_fixed'): {len(nids_fixed)}")
    print(f"Breakdown: {dict(summary)}")
    print(f"Notes where Scene mentions the old/wrong Actor (to be tagged 'needs_scene_update'): {len(nids_scene_mismatch)}")

    if dry_run:
        return

    batch_size = 50
    total_batches = math.ceil(len(updates) / batch_size)
    updated_count = 0

    for i in range(0, len(updates), batch_size):
        batch = updates[i:i+batch_size]
        actions = [
            {"action": "updateNoteFields", "params": {"note": u}}
            for u in batch
        ]
        b_num = i // batch_size + 1
        print(f"Applying batch {b_num}/{total_batches} ({len(batch)} notes)...", end=" ", flush=True)
        res = request_anki("multi", actions=actions)
        if res is not None:
            updated_count += len(batch)
            print("OK")
        else:
            print("FAILED")
        time.sleep(0.1)

    if nids_fixed:
        print(f"Adding tag 'mbp_fixed' to {len(nids_fixed)} fixed notes...")
        request_anki("addTags", notes=nids_fixed, tags="mbp_fixed")

    if nids_scene_mismatch:
        print(f"Adding tag 'needs_scene_update' to {len(nids_scene_mismatch)} notes whose Scene references the old actor...")
        request_anki("addTags", notes=nids_scene_mismatch, tags="needs_scene_update")

    print(f"\nDone! Updated {updated_count} notes in Anki.")

if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    main(dry_run=dry)
