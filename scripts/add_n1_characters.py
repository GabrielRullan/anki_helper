import os
import sys
import json
import time
import urllib.request
import re
from collections import Counter, defaultdict

# Reconfigure stdout to use UTF-8 on Windows console
sys.stdout.reconfigure(encoding='utf-8')

ANKICONNECT_URL = 'http://localhost:8765'

def request_anki(action, **params):
    payload = {"action": action, "version": 6}
    if params:
        payload["params"] = params
    
    req = urllib.request.Request(
        ANKICONNECT_URL, 
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            res = json.loads(response.read().decode('utf-8'))
            if res.get('error'):
                print(f"AnkiConnect Error: {res.get('error')}")
                return None
            return res.get('result')
    except Exception as e:
        print(f"AnkiConnect Request Failed: {e}")
        return None

def resolve_anki_deck(candidates):
    decks = request_anki("deckNames")
    if not decks:
        return candidates[-1]
    
    def normalize_name(name):
        return name.replace('::', '\x1f').replace('/', '\x1f').replace('\\', '\x1f').lower().strip()
        
    normalized_decks = {normalize_name(d): d for d in decks}
    for cand in candidates:
        if normalize_name(cand) in normalized_decks:
            return normalized_decks[normalize_name(cand)]
    return candidates[-1]

# Import split_pinyin from mbp_profiler
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from mbp_profiler import split_pinyin
except ImportError:
    # Inline split_pinyin if import fails
    def split_pinyin(pinyin):
        pinyin = pinyin.lower().strip()
        vowel_map = {
            'ā': 'a', 'á': 'a', 'ǎ': 'a', 'à': 'a',
            'ē': 'e', 'é': 'e', 'ě': 'e', 'è': 'e',
            'ī': 'i', 'í': 'i', 'ǐ': 'i', 'ì': 'i',
            'ō': 'o', 'ó': 'o', 'ǒ': 'o', 'ò': 'o',
            'ū': 'u', 'ú': 'u', 'ǔ': 'u', 'ù': 'u',
            'ǖ': 'v', 'ǘ': 'v', 'ǚ': 'v', 'ǜ': 'v', 'ü': 'v'
        }
        clean_p = "".join(vowel_map.get(char, char) for char in pinyin)
        clean_p = re.sub(r'[^a-z]', '', clean_p)
        if not clean_p:
            return "", ""
        for double_init in ['zh', 'ch', 'sh']:
            if clean_p.startswith(double_init):
                return double_init, clean_p[2:]
        for init in 'bpmfdtnlgkhjqxrzcsyw':
            if clean_p.startswith(init):
                return init, clean_p[1:]
        return "", clean_p

def get_tone_number(pinyin):
    pinyin = pinyin.lower().strip()
    tone_marks = {
        'ā': 1, 'á': 2, 'ǎ': 3, 'à': 4,
        'ē': 1, 'é': 2, 'ě': 3, 'è': 4,
        'ī': 1, 'í': 2, 'ǐ': 3, 'ì': 4,
        'ō': 1, 'ó': 2, 'ǒ': 3, 'ò': 4,
        'ū': 1, 'ú': 2, 'ǔ': 3, 'ù': 4,
        'ǖ': 1, 'ǘ': 2, 'ǚ': 3, 'ǜ': 4
    }
    for char in pinyin:
        if char in tone_marks:
            return tone_marks[char]
    return 5 # neutral tone

def get_primary_pinyin(pinyin_str):
    if ',' in pinyin_str:
        return pinyin_str.split(',')[0].strip()
    return pinyin_str.strip()

def re_clean(text):
    if not text:
        return ""
    return re.sub(r'<[^>]+>', '', text).strip()

def build_codebook(char_notes):
    initial_actors = defaultdict(list)
    final_sets = defaultdict(list)
    tone_locations = defaultdict(list)
    
    for note in char_notes:
        f = note.get('fields', {})
        pinyin_raw = f.get('Pinyin', {}).get('value', '').strip()
        pinyin_primary = get_primary_pinyin(pinyin_raw)
        initial, final = split_pinyin(pinyin_primary)
        
        actor = f.get('Actor', {}).get('value', '').strip()
        c_set = f.get('Set', {}).get('value', '').strip()
        tone = f.get('Tone', {}).get('value', '').strip()
        loc = f.get('Tone-Location', {}).get('value', '').strip()
        
        actor = re_clean(actor)
        c_set = re_clean(c_set)
        loc = re_clean(loc)
        
        if initial and actor:
            initial_actors[initial].append(actor)
        if final and c_set:
            final_sets[final].append(c_set)
        if tone and loc:
            tone_locations[tone].append(loc)
            
    codebook = {
        'actors': {},
        'sets': {},
        'locations': {}
    }
    
    for init, actors in initial_actors.items():
        codebook['actors'][init] = Counter(actors).most_common(1)[0][0]
    for fin, sets in final_sets.items():
        codebook['sets'][fin] = Counter(sets).most_common(1)[0][0]
    for tone, locs in tone_locations.items():
        codebook['locations'][tone] = Counter(locs).most_common(1)[0][0]
        
    return codebook

def load_hsk4_chars():
    hsk4_chars = set()
    csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "hsk4_vocab.csv")
    if os.path.exists(csv_path):
        import csv
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader, None) # skip header
                for row in reader:
                    if row:
                        for c in row[0]:
                            if '\u4e00' <= c <= '\u9fff':
                                hsk4_chars.add(c)
        except Exception as e:
            print(f"Warning: could not read hsk4_vocab.csv ({e})")
    return hsk4_chars

def main():
    print("Connecting to AnkiConnect...")
    version = request_anki("version")
    if not version:
        print("[ERROR] Please ensure Anki is open and running with AnkiConnect enabled.")
        sys.exit(1)
    print(f"Connected to Anki version {version}.")
    
    # 1. Resolve character deck
    char_deck = resolve_anki_deck(["Chinese::Char", "Chinese\x1fChar", "Characters"])
    print(f"Using Character deck: '{char_deck}'")
    
    # 2. Fetch existing notes to build the codebook and map existing characters
    print("Fetching existing character notes...")
    char_ids = request_anki("findNotes", query=f'deck:"{char_deck}"')
    if not char_ids:
        print("[ERROR] No character notes found in the Character deck.")
        sys.exit(1)
    char_notes = request_anki("notesInfo", notes=char_ids)
    
    # Map existing characters to avoid duplicates
    existing_hanzi = set()
    for note in char_notes:
        hz = note['fields'].get('Hanzi', {}).get('value', '').strip()
        simp = note['fields'].get('Simplified', {}).get('value', '').strip()
        if hz:
            existing_hanzi.add(hz)
        if simp:
            existing_hanzi.add(simp)
            
    print(f"Found {len(existing_hanzi)} unique characters in Anki.")
    
    # Build standard MBP codebook mappings
    print("Building standard MBP codebook...")
    codebook = build_codebook(char_notes)
    
    # 3. Load mined character details
    details_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "n1_missing_chars_details.json")
    if not os.path.exists(details_path):
        print(f"[ERROR] Mined characters details file not found at {details_path}.")
        sys.exit(1)
        
    with open(details_path, 'r', encoding='utf-8') as f:
        mined_chars = json.load(f)
        
    print(f"Loaded {len(mined_chars)} character details from JSON.")
    
    # Load HSK 4 characters
    hsk4_chars = load_hsk4_chars()
    
    # 4. Filter out characters that are already in Anki
    to_add = []
    for item in mined_chars:
        char = item['character']
        if char in existing_hanzi:
            continue
        to_add.append(item)
        
    print(f"Filtered down to {len(to_add)} characters that are missing from Anki.")
    if not to_add:
        print("No new characters to add. Exiting.")
        return
        
    # 5. Build note payloads
    notes_payload = []
    timestamp_sec = int(time.time())
    
    for idx, item in enumerate(to_add):
        char = item['character']
        pinyin_raw = item['pinyin']
        english = item['english']
        components_list = item.get('components', [])
        
        # Primary reading for MBP lookup
        pinyin_primary = get_primary_pinyin(pinyin_raw)
        initial, final = split_pinyin(pinyin_primary)
        tone = get_tone_number(pinyin_primary)
        
        # Look up mappings
        actor = codebook['actors'].get(initial, '')
        c_set = codebook['sets'].get(final, '')
        tone_location = codebook['locations'].get(str(tone), '')
        
        # Determine HSK level
        hsk_level = '4' if char in hsk4_chars else ''
        
        # Unique sequential field ID
        field_id = str(timestamp_sec + idx)
        
        # Field dictionary (all 24 fields)
        fields = {
            'ID': field_id,
            'Hanzi': char,
            'Pinyin': pinyin_raw,
            'English': english,
            'Initial': initial.upper(),
            'Actor': actor,
            'Set': c_set,
            'Tone': str(tone),
            'Tone-Location': tone_location,
            'Components': ", ".join(components_list),
            'Scene': '',
            'MBP_Phase': 'Unknown',
            'MBP_Level': 'Unknown',
            'HSK_2': hsk_level,
            'Common Words': '',
            'Translation of Words': '',
            'Simplified': char,
            'Traditional': char,
            'Frequency': '',
            'Sound': '',
            'Words_Sound': '',
            'Words_English_Sound': '',
            'Image': '',
            'Notes': ''
        }
        
        note = {
            "deckName": char_deck,
            "modelName": "Chinese (Characters)",
            "fields": fields,
            "options": {
                "allowDuplicate": False
            },
            "tags": ["n1_added", "immersion"]
        }
        notes_payload.append(note)
        
    # 6. Bulk add notes using addNotes action
    print(f"Adding {len(notes_payload)} notes to deck '{char_deck}'...")
    result = request_anki("addNotes", notes=notes_payload)
    
    if result:
        added_count = sum(1 for r in result if r is not None)
        failed_count = len(result) - added_count
        print(f"Successfully added {added_count} character notes to Anki.")
        if failed_count > 0:
            print(f"Failed to add {failed_count} notes (possibly duplicates or errors).")
    else:
        print("[ERROR] Failed to add notes via AnkiConnect.")

if __name__ == "__main__":
    main()
