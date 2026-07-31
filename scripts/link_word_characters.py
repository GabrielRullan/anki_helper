import os
import json
import urllib.request
import re
import sys
import time
import math
from collections import Counter, defaultdict
from dotenv import load_dotenv

# Reconfigure stdout to use UTF-8
sys.stdout.reconfigure(encoding='utf-8')

ANKICONNECT_URL = 'http://127.0.0.1:8765'

# Load Gemini client if API key is present
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")
client = None
if API_KEY:
    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=API_KEY)
        print("Gemini API client initialized successfully.")
    except Exception as e:
        print(f"Failed to initialize Gemini client: {e}")
else:
    print("Warning: GOOGLE_API_KEY not found in .env file. Gemini-based character creation will be skipped.")

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
        with urllib.request.urlopen(req, timeout=30) as response:
            res = json.loads(response.read().decode('utf-8'))
            if res.get('error'):
                print(f"Error in {action}: {res.get('error')}")
                return None
            return res.get('result')
    except Exception as e:
        print(f"Request failed in {action}: {e}")
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

def resolve_anki_model(candidates):
    models = request_anki("modelNames")
    if not models:
        return candidates[-1]
    for cand in candidates:
        if cand in models:
            return cand
    return candidates[-1]

def get_field_val(note, field_name):
    fields = note.get('fields', {})
    for k, v in fields.items():
        if k.lower() == field_name.lower():
            return v.get('value', '').strip()
    return ''

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
    return 5

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
        if actors:
            codebook['actors'][init] = Counter(actors).most_common(1)[0][0]
    for fin, sets in final_sets.items():
        if sets:
            codebook['sets'][fin] = Counter(sets).most_common(1)[0][0]
    for tone, locs in tone_locations.items():
        if locs:
            codebook['locations'][tone] = Counter(locs).most_common(1)[0][0]
        
    return codebook

def get_character_details_from_gemini(char):
    if not client:
        return None
    prompt = f"""
Analyze the Chinese character: '{char}'
We need the following details to create an Anki flashcard:
1. "pinyin": The pinyin with tone marks (e.g. "wú").
2. "english": English translation/meaning of the character (e.g. "I, me; my; our").
3. "components": A list of visual components/radicals that make up this character (e.g. ["口", "五"]).

Format your response as a JSON object with keys "pinyin", "english", and "components".
Return ONLY the raw JSON block, no markdown formatting.
"""
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        data = json.loads(response.text.strip())
        return data
    except Exception as e:
        print(f"Error fetching Gemini details for character '{char}': {e}")
        return None

def create_character_card(char, codebook, char_deck, char_model, next_seq_id):
    print(f"Creating card for character '{char}'...")
    details = get_character_details_from_gemini(char)
    if not details:
        print(f"Could not retrieve details for character '{char}' from Gemini.")
        return None
        
    pinyin = details.get('pinyin', '').strip()
    english = details.get('english', '').strip()
    components = details.get('components', [])
    
    pinyin_primary = get_primary_pinyin(pinyin)
    initial, final = split_pinyin(pinyin_primary)
    tone = get_tone_number(pinyin_primary)
    
    actor = codebook['actors'].get(initial, '')
    c_set = codebook['sets'].get(final, '')
    tone_location = codebook['locations'].get(str(tone), '')
    
    # zero-initial fallback
    if not initial and not actor:
        actor = 'Jackie Chan'
        
    fields = {
        'ID': str(next_seq_id),
        'Hanzi': char,
        'Pinyin': pinyin,
        'English': english,
        'Initial': initial.upper(),
        'Actor': actor,
        'Set': c_set,
        'Tone': str(tone),
        'Tone-Location': tone_location,
        'Components': ", ".join(components),
        'Scene': '',
        'MBP_Phase': 'Unknown',
        'MBP_Level': 'Unknown',
        'HSK_2': '',
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
    
    note_payload = {
        "deckName": char_deck,
        "modelName": char_model,
        "fields": fields,
        "options": {
            "allowDuplicate": False
        },
        "tags": ["linked_characters", "immersion"]
    }
    
    nid = request_anki("addNote", note=note_payload)
    if nid:
        print(f"Successfully created character note '{char}' (ID: {nid}).")
        return nid
    else:
        print(f"Failed to create character note '{char}' in Anki.")
        return None

def main():
    print("Checking connection to AnkiConnect...")
    version = request_anki("version")
    if not version:
        print("[ERROR] Could not connect to Anki. Make sure Anki is open and AnkiConnect is active.")
        sys.exit(1)
    print(f"Connected to Anki (version {version}).")

    char_deck = resolve_anki_deck(["Chinese::Char", "Chinese\x1fChar", "Characters"])
    word_deck = resolve_anki_deck(["Chinese::Words", "Chinese\x1fWords", "Migaku"])
    char_model = resolve_anki_model(["Chinese Character", "Chinese (Characters)"])
    print(f"Using character deck: '{char_deck}'")
    print(f"Using word deck: '{word_deck}'")
    print(f"Using character model: '{char_model}'")
    
    print(f"Fetching character notes from deck '{char_deck}'...")
    char_ids = request_anki("findNotes", query=f'deck:"{char_deck}"')
    if not char_ids:
        print(f"No notes found in character deck '{char_deck}'")
        return
    char_notes = request_anki("notesInfo", notes=char_ids)
    
    # Map each Hanzi/Simplified character to its note ID
    char_to_nid = {}
    for note in char_notes:
        nid = note['noteId']
        hanzi = get_field_val(note, 'Hanzi')
        simp = get_field_val(note, 'Simplified')
        if hanzi:
            char_to_nid[hanzi] = nid
        if simp and simp != hanzi:
            char_to_nid[simp] = nid
            
    print(f"Mapped {len(char_to_nid)} unique characters from character deck.")
    print("Building standard MBP codebook from existing characters...")
    codebook = build_codebook(char_notes)
    
    print(f"Fetching word notes from deck '{word_deck}'...")
    word_ids = request_anki("findNotes", query=f'deck:"{word_deck}"')
    if not word_ids:
        print(f"No notes found in word deck '{word_deck}'")
        return
    word_notes = request_anki("notesInfo", notes=word_ids)
    
    notes_to_update = []
    created_char_count = 0
    next_seq_id = int(time.time())
    
    for idx, note in enumerate(word_notes):
        nid = note['noteId']
        word = get_field_val(note, 'Word')
        # Strip HTML from word
        word_clean = re.sub(r'<[^>]+>', '', word).strip()
        
        # We look for notes where the "Characters" field is empty or missing a link for a character
        chars_val = get_field_val(note, 'Characters')
        
        needs_processing = False
        if not chars_val:
            needs_processing = True
        else:
            for char in word_clean:
                if '\u4e00' <= char <= '\u9fff':
                    if f"[{char}|nid" not in chars_val:
                        needs_processing = True
                        break
                        
        if needs_processing:
            # Generate links for characters in the word
            linked_chars = []
            for char in word_clean:
                # Check if it's a Chinese character
                if '\u4e00' <= char <= '\u9fff':
                    if char in char_to_nid:
                        linked_chars.append(f"[{char}|nid{char_to_nid[char]}]")
                    else:
                        # Character does not exist! Create it!
                        if client:
                            new_nid = create_character_card(char, codebook, char_deck, char_model, next_seq_id)
                            next_seq_id += 1
                            if new_nid:
                                char_to_nid[char] = new_nid
                                created_char_count += 1
                                linked_chars.append(f"[{char}|nid{new_nid}]")
                                # sleep briefly to respect rate limits
                                time.sleep(1)
                            else:
                                linked_chars.append(char)
                        else:
                            linked_chars.append(char)
                else:
                    linked_chars.append(char)
            
            new_chars_val = "".join(linked_chars)
            if new_chars_val:
                notes_to_update.append({
                    "id": nid,
                    "fields": {
                        "Characters": new_chars_val
                    }
                })
                
    if not notes_to_update:
        print("No notes require updating (all notes already have 'Characters' populated).")
        return
        
    print(f"Found {len(notes_to_update)} notes in word deck to populate with linked characters.")
    print(f"Created {created_char_count} new character cards.")
    
    # Update word notes in batches
    batch_size = 50
    success_count = 0
    total_batches = math.ceil(len(notes_to_update) / batch_size)
    
    print("Starting word card updates...")
    for i in range(0, len(notes_to_update), batch_size):
        batch = notes_to_update[i:i+batch_size]
        actions = [
            {
                "action": "updateNoteFields",
                "params": {
                    "note": note
                }
            }
            for note in batch
        ]
        
        batch_num = (i // batch_size) + 1
        print(f"Applying batch {batch_num}/{total_batches}...", end=" ", flush=True)
        
        res = request_anki("multi", actions=actions)
        if res:
            success_count += len(batch)
            print("Success.")
        else:
            print("Failed batch update. Retrying individually for this batch...")
            batch_success = 0
            for note in batch:
                res_ind = request_anki("updateNoteFields", note=note)
                if res_ind is not None:
                    batch_success += 1
                    success_count += 1
            print(f"Batch {batch_num} individual success: {batch_success}/{len(batch)}")
            
        time.sleep(0.1)
        
    print(f"\nProcessing Complete!")
    print(f"Successfully updated {success_count} word notes.")
    print(f"Created {created_char_count} character notes.")

if __name__ == '__main__':
    main()
