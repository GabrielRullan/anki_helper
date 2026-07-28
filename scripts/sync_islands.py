import os
import sys
import re
import json
import csv
import hashlib
import time
import urllib.request
import urllib.parse
import base64

# Reconfigure stdout to use UTF-8 on Windows console
sys.stdout.reconfigure(encoding='utf-8')

# Adjust path to find local modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from anki_db import AnkiConnection

ANKICONNECT_URL = 'http://127.0.0.1:8765'

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
                raise Exception(res.get('error'))
            return res.get('result')
    except Exception as e:
        print(f"AnkiConnect Request Failed for action '{action}': {e}")
        raise

def download_tts(text, lang='zh-CN'):
    url = "https://translate.google.com/translate_tts"
    params = {
        'ie': 'UTF-8',
        'tl': lang,
        'client': 'tw-ob',
        'q': text
    }
    query_string = urllib.parse.urlencode(params)
    full_url = f"{url}?{query_string}"
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    req = urllib.request.Request(full_url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.read()
    except Exception as e:
        print(f"Error fetching TTS: {e}")
        return None

def store_audio_in_anki(audio_bytes, filename):
    audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
    try:
        request_anki(
            "storeMediaFile",
            filename=filename,
            data=audio_base64
        )
    except Exception as e:
        print(f"Error storing media file {filename}: {e}")

def normalize_sentence(text):
    if not text:
        return ""
    # Strip basic punctuation and whitespace for robust duplicate matching
    text = re.sub(r'[，。！？、；：""''（）\s.,!?;:()\-—/]', '', text)
    return text.strip().lower()

def get_existing_sentences(deck_name):
    try:
        decks = request_anki("deckNames")
        if deck_name not in decks:
            print(f"Deck '{deck_name}' does not exist yet. It will be created.")
            request_anki("createDeck", deck=deck_name)
            return {}
            
        note_ids = request_anki("findNotes", query=f'deck:"{deck_name}"')
        if not note_ids:
            return {}
            
        notes_info = request_anki("notesInfo", notes=note_ids)
        existing_sentences = {}
        for note in notes_info:
            fields = note.get('fields', {})
            sentence_field = fields.get('Sentence', {}).get('value', '').strip()
            if sentence_field:
                # Store normalized version mapping to note ID
                existing_sentences[normalize_sentence(sentence_field)] = note.get('noteId')
        return existing_sentences
    except Exception as e:
        print(f"Error checking existing cards in deck '{deck_name}': {e}")
        return {}

def clean_hanzi(text):
    if not text:
        return []
    # Clean HTML first
    text = re.sub(r'<[^>]+>', '', text)
    return [char for char in text if '\u4e00' <= char <= '\u9fff']

def load_learned_characters():
    learned_chars = set()
    # Read from live DB profile
    try:
        with AnkiConnection(profile_name="Gabriel") as anki:
            char_deck = anki.best_match_deck(["Chinese::Char", "Chinese\x1fChar", "Characters"])
            char_notes = anki.get_notes_in_deck(char_deck)
            for note in char_notes:
                hz = note['fields'].get('Hanzi', '').strip()
                if hz:
                    learned_chars.add(hz)
                simp = note['fields'].get('Simplified', '').strip()
                if simp:
                    learned_chars.add(simp)
            print(f"Successfully loaded {len(learned_chars)} characters from local Anki database.")
    except Exception as e:
        print(f"Warning: Could not read Anki database ({e}). Character checks will proceed using only csv.")
        
    # Read from CSV backup if exists
    known_chars_csv = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "known_characters.csv")
    if os.path.exists(known_chars_csv):
        try:
            with open(known_chars_csv, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader, None) # skip header
                for row in reader:
                    if not row:
                        continue
                    char = row[0].strip()
                    if char:
                        learned_chars.add(char)
            print(f"Loaded additional characters from known_characters.csv. Total known: {len(learned_chars)}")
        except Exception as e:
            print(f"Warning: Could not read known_characters.csv ({e})")
            
    return learned_chars

def parse_islands_file(filepath):
    if not os.path.exists(filepath):
        print(f"Error: {filepath} not found.")
        return []
        
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    blocks = []
    current_block = {}
    last_seen = None
    
    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue
            
        if line_clean.startswith('<<<') or line_clean.startswith('===') or line_clean.startswith('>>>'):
            continue
        if line_clean.startswith('#'):
            continue
            
        q_match = re.match(r'^Q:\s*(.*)', line_clean, re.IGNORECASE)
        if q_match:
            if current_block and 'q' in current_block:
                blocks.append(current_block)
            current_block = {'q': q_match.group(1).strip()}
            last_seen = 'q'
            continue
            
        a_match = re.match(r'^A:\s*(.*)', line_clean, re.IGNORECASE)
        if a_match and current_block:
            current_block['a'] = a_match.group(1).strip()
            last_seen = 'a'
            continue
            
        pinyin_match = re.match(r'^Pinyin:\s*(.*)', line_clean, re.IGNORECASE)
        if pinyin_match and current_block:
            p_val = pinyin_match.group(1).strip()
            if last_seen == 'q':
                current_block['q_pinyin'] = p_val
            elif last_seen == 'a':
                current_block['a_pinyin'] = p_val
            continue
            
        en_match = re.match(r'^EN:\s*(.*)', line_clean, re.IGNORECASE)
        if en_match and current_block:
            en_val = en_match.group(1).strip()
            current_block['en'] = en_val
            
    if current_block and 'q' in current_block:
        blocks.append(current_block)
        
    # Process and split translation by '->'
    valid_blocks = []
    for b in blocks:
        if 'q' in b and 'a' in b:
            en_raw = b.get('en', '')
            if '->' in en_raw:
                en_q, en_a = en_raw.split('->', 1)
                b['en_q'] = en_q.strip()
                b['en_a'] = en_a.strip()
            else:
                b['en_q'] = en_raw.strip()
                b['en_a'] = ""
            valid_blocks.append(b)
            
    return valid_blocks

def main():
    # 1. Load learned characters for vocab check
    learned_chars = load_learned_characters()
    
    # 2. Parse islands.md
    islands_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "islands.md")
    print(f"Parsing islands from {islands_path}...")
    blocks = parse_islands_file(islands_path)
    print(f"Found {len(blocks)} Q&A blocks in islands.md.")
    
    if not blocks:
        print("No valid Q&A blocks found. Exiting.")
        return
        
    # 3. Connection Check to Anki
    try:
        version = request_anki("version")
        print(f"Connected to Anki (version {version}).")
    except Exception as e:
        print(f"[ERROR] Could not connect to Anki. Make sure Anki is open and AnkiConnect is active.")
        sys.exit(1)
        
    deck_name = "Chinese::Sent"
    model_name = "Chinese Sentence - Double"
    
    # Check if target model type exists
    models = request_anki("modelNames")
    if model_name not in models:
        print(f"[ERROR] Model type '{model_name}' not found in Anki. Available: {models}")
        sys.exit(1)
        
    # 4. Fetch existing sentences in Chinese::Sent
    print("Checking existing sentences in Anki...")
    existing_sentences = get_existing_sentences(deck_name)
    
    # 5. Process blocks
    success_count = 0
    skipped_vocab_count = 0
    skipped_dup_count = 0
    
    for idx, b in enumerate(blocks, 1):
        q_raw = b['q']
        a_raw = b['a']
        q_pinyin = b.get('q_pinyin', '')
        a_pinyin = b.get('a_pinyin', '')
        en_q = b.get('en_q', '')
        en_a = b.get('en_a', '')
        
        # Clean phrases to check characters
        q_chars = clean_hanzi(q_raw)
        a_chars = clean_hanzi(a_raw)
        
        # Find missing characters
        missing_q = [c for c in q_chars if c not in learned_chars]
        missing_a = [c for c in a_chars if c not in learned_chars]
        all_missing = list(set(missing_q + missing_a))
        
        ignore_vocab_check = "--force" in sys.argv or "--ignore-vocab-check" in sys.argv
        
        if all_missing and not ignore_vocab_check:
            print(f"\n[{idx}/{len(blocks)}] ⚠️ SKIP (VOCAB GAP): Block containing Q: '{q_raw}'")
            print(f"  Missing characters in deck: {', '.join(all_missing)}")
            skipped_vocab_count += 1
            continue
        elif all_missing and ignore_vocab_check:
            print(f"\n[{idx}/{len(blocks)}] ⚠️ WARNING (VOCAB GAP - FORCED): Q: '{q_raw}'")
            print(f"  Missing characters (proceeding anyway): {', '.join(all_missing)}")
            
        print(f"\n[{idx}/{len(blocks)}] Processing: {q_raw}")
        
        # We will create two separate notes:
        # Note 1: The Question Card
        # Note 2: The Answer Card
        
        # Normalized versions for duplicate checking
        q_norm = normalize_sentence(q_raw)
        a_norm = normalize_sentence(a_raw)
        
        # Prepare card payloads
        # We want to cross-reference Q and A in the Notes field
        notes_for_q = f"[Answer] {a_raw}"
        notes_for_a = f"[Question] {q_raw}"
        
        # Generates unique hash filenames for audios
        hash_q_zh = hashlib.sha1(q_raw.encode('utf-8')).hexdigest()
        hash_q_en = hashlib.sha1(en_q.encode('utf-8')).hexdigest()
        hash_a_zh = hashlib.sha1(a_raw.encode('utf-8')).hexdigest()
        hash_a_en = hashlib.sha1(en_a.encode('utf-8')).hexdigest()
        
        # Question card audio filenames
        aud_q_zh = f"zh_tts_q_{hash_q_zh}.mp3"
        aud_q_en = f"en_tts_q_{hash_q_en}.mp3"
        
        # Answer card audio filenames
        aud_a_zh = f"zh_tts_a_{hash_a_zh}.mp3"
        aud_a_en = f"en_tts_a_{hash_a_en}.mp3"
        
        # --- Create Note 1: Question Card ---
        if q_norm in existing_sentences:
            print(f"  -> Question card already in Anki. Skipping Question note.")
            skipped_dup_count += 0.5
        else:
            print("  -> Creating Question Card...")
            # Download TTS
            zh_q_bytes = download_tts(q_raw, lang='zh-CN')
            if zh_q_bytes:
                store_audio_in_anki(zh_q_bytes, aud_q_zh)
            else:
                aud_q_zh = ""
                
            en_q_bytes = download_tts(en_q, lang='en')
            if en_q_bytes:
                store_audio_in_anki(en_q_bytes, aud_q_en)
            else:
                aud_q_en = ""
                
            # Construct Question Card Payload
            q_payload = {
                "deckName": deck_name,
                "modelName": model_name,
                "fields": {
                    "Sentence": q_raw,
                    "Translated_Sentence": en_q,
                    "Notes": notes_for_q,
                    "Images": "",
                    "Definitions": q_pinyin,
                    "Sentence_Audio": f"[sound:{aud_q_zh}]" if aud_q_zh else "",
                    "Grammar_Point": "Language Island - Question",
                    "Translated_Audio": f"[sound:{aud_q_en}]" if aud_q_en else ""
                },
                "options": {
                    "allowDuplicate": False
                },
                "tags": ["island", "island-question"]
            }
            try:
                nid = request_anki("addNote", note=q_payload)
                if nid:
                    print(f"    Added Question Card (ID: {nid})")
                    success_count += 1
            except Exception as e:
                print(f"    Failed to add Question Card: {e}")
                
        # --- Create Note 2: Answer Card ---
        if a_norm in existing_sentences:
            print(f"  -> Answer card already in Anki. Skipping Answer note.")
            skipped_dup_count += 0.5
        else:
            print("  -> Creating Answer Card...")
            # Download TTS
            zh_a_bytes = download_tts(a_raw, lang='zh-CN')
            if zh_a_bytes:
                store_audio_in_anki(zh_a_bytes, aud_a_zh)
            else:
                aud_a_zh = ""
                
            en_a_bytes = download_tts(en_a, lang='en')
            if en_a_bytes:
                store_audio_in_anki(en_a_bytes, aud_a_en)
            else:
                aud_a_en = ""
                
            # Construct Answer Card Payload
            a_payload = {
                "deckName": deck_name,
                "modelName": model_name,
                "fields": {
                    "Sentence": a_raw,
                    "Translated_Sentence": en_a,
                    "Notes": notes_for_a,
                    "Images": "",
                    "Definitions": a_pinyin,
                    "Sentence_Audio": f"[sound:{aud_a_zh}]" if aud_a_zh else "",
                    "Grammar_Point": "Language Island - Answer",
                    "Translated_Audio": f"[sound:{aud_a_en}]" if aud_a_en else ""
                },
                "options": {
                    "allowDuplicate": False
                },
                "tags": ["island", "island-answer"]
            }
            try:
                nid = request_anki("addNote", note=a_payload)
                if nid:
                    print(f"    Added Answer Card (ID: {nid})")
                    success_count += 1
            except Exception as e:
                print(f"    Failed to add Answer Card: {e}")
                
        # Small delay to prevent issues
        time.sleep(1)
        
    print("\n" + "=" * 40)
    print("Sync Summary:")
    print(f"  Successfully Added Notes: {success_count}")
    print(f"  Skipped (Vocab Gaps):    {skipped_vocab_count}")
    print(f"  Skipped (Duplicates):    {int(skipped_dup_count)}")
    print("=" * 40)

if __name__ == "__main__":
    main()
