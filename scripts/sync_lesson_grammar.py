import os
import sys
import json
import re
import urllib.request
import urllib.parse
import base64
import hashlib
import time
from dotenv import load_dotenv

# Reconfigure stdout to UTF-8
sys.stdout.reconfigure(encoding='utf-8')

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
        print(f"AnkiConnect Request Failed: {e}")
        return None

def download_tts(text, lang='zh-CN'):
    url = "https://translate.google.com/translate_tts"
    text_clean = re.sub(r'\s+', ' ', text).strip()
    if not text_clean:
        return None
    params = {
        'ie': 'UTF-8',
        'tl': lang,
        'client': 'tw-ob',
        'q': text_clean[:100]
    }
    query_string = urllib.parse.urlencode(params)
    full_url = f"{url}?{query_string}"
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    req = urllib.request.Request(full_url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.read()
    except Exception as e:
        print(f"Error fetching TTS for '{text_clean}' ({lang}): {e}")
        return None

def store_audio_in_anki(audio_bytes, filename):
    base64_data = base64.b64encode(audio_bytes).decode('utf-8')
    try:
        res = request_anki("storeMediaFile", filename=filename, data=base64_data)
        return res
    except Exception as e:
        print(f"Error storing media file '{filename}': {e}")
        return None

def parse_markdown_blocks(filepath):
    if not os.path.exists(filepath):
        print(f"Error: File not found: {filepath}")
        return []
        
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Split by empty lines to find blocks
    blocks_raw = re.split(r'\n\s*\n', content)
    blocks = []
    
    for block_raw in blocks_raw:
        block_raw = block_raw.strip()
        if not block_raw:
            continue
            
        fields = {}
        for line in block_raw.split('\n'):
            line = line.strip()
            if not line or ':' not in line:
                continue
            key, val = line.split(':', 1)
            # Map standard keys
            key_clean = key.strip().lower()
            val_clean = val.strip()
            
            # Map variations in keys
            if key_clean == 'english__transaltion':
                key_clean = 'english_translation'
            elif key_clean == 'spanish_transaltion':
                key_clean = 'spanish_translation'
            elif key_clean == 'gramma_point_desc':
                key_clean = 'grammar_point_desc'
                
            fields[key_clean] = val_clean
            
        # Ensure we have the minimum fields required (sentence and grammar_point)
        if fields.get('sentence') and fields.get('grammar_point'):
            blocks.append(fields)
            
    return blocks

def normalize_sentence(sentence):
    if not sentence:
        return ""
    clean = sentence.replace("**", "").replace("*", "").replace(" ", "").strip()
    clean = re.sub(r'[^\w\s\u4e00-\u9fff]', '', clean)
    return clean

def get_existing_sentences(deck_name):
    try:
        decks = request_anki("deckNames")
        if deck_name not in decks:
            print(f"Deck '{deck_name}' does not exist. Creating...")
            request_anki("createDeck", deck=deck_name)
            return {}
            
        note_ids = request_anki("findNotes", query=f'deck:"{deck_name}"')
        if not note_ids:
            return {}
            
        notes_info = request_anki("notesInfo", notes=note_ids)
        existing = {}
        for note in notes_info:
            fields = note.get('fields', {})
            s = fields.get('Sentence', {}).get('value', '').strip()
            if s:
                existing[normalize_sentence(s)] = note.get('noteId')
        return existing
    except Exception as e:
        print(f"Error checking existing notes: {e}")
        return {}

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/sync_lesson_grammar.py <path_to_markdown_file> [deck_name_override]")
        sys.exit(1)
        
    md_path = sys.argv[1]
    
    # Resolve deck name dynamically
    filename = os.path.basename(md_path)
    match = re.search(r'Lección\s+([\d\s\w\-y]+)', filename, re.IGNORECASE)
    if len(sys.argv) >= 3:
        deck_name = sys.argv[2]
    elif match:
        lesson_label = match.group(1).replace('.md', '').strip()
        deck_name = f"HSK 4::Lección {lesson_label}"
    else:
        deck_name = "Chinese::Sent"
        
    print(f"Target Deck: {deck_name}")
    print(f"Parsing grammar blocks from: {md_path}")
    
    blocks = parse_markdown_blocks(md_path)
    if not blocks:
        print("No valid grammar blocks found.")
        return
        
    print(f"Parsed {len(blocks)} grammar blocks.")
    
    # Establish local audio directories
    md_dir = os.path.dirname(os.path.abspath(md_path))
    audio_dir = os.path.join(md_dir, "anki_audio")
    os.makedirs(audio_dir, exist_ok=True)
    
    # Get existing notes to avoid duplicates
    existing_sentences = get_existing_sentences(deck_name)
    print(f"Found {len(existing_sentences)} existing sentences in deck '{deck_name}'.")
    
    model_name = "Chinese Sentence - Double"
    models = request_anki("modelNames")
    if model_name not in models:
        print(f"Error: Note type '{model_name}' not found in Anki.")
        sys.exit(1)
        
    added_count = 0
    
    for idx, block in enumerate(blocks, 1):
        sentence = block['sentence']
        normalized = normalize_sentence(sentence)
        
        if normalized in existing_sentences:
            print(f"[{idx}/{len(blocks)}] Skipping duplicate: {sentence}")
            continue
            
        print(f"[{idx}/{len(blocks)}] Processing: {sentence}")
        
        grammar_point = block['grammar_point']
        desc = block.get('grammar_point_desc', '')
        english = block.get('english_translation', '')
        
        # Audio generation or lookup
        zh_audio_filename = ""
        en_audio_filename = ""
        
        # 1. Chinese Sentence Audio
        # Parse potential filename from [sound:xxx.mp3]
        sound_ch = block.get('audio_chinese', '')
        ch_match = re.search(r'\[sound:(.*?)\]', sound_ch)
        if ch_match:
            zh_audio_filename = ch_match.group(1)
        else:
            # Generate hash-based filename
            h_name = hashlib.sha1(sentence.encode('utf-8')).hexdigest()
            zh_audio_filename = f"zh_sent_{h_name}.mp3"
            
        zh_audio_path = os.path.join(audio_dir, zh_audio_filename)
        zh_audio_bytes = None
        
        if os.path.exists(zh_audio_path):
            with open(zh_audio_path, 'rb') as af:
                zh_audio_bytes = af.read()
        else:
            print(f"  -> Downloading Chinese TTS...")
            zh_audio_bytes = download_tts(sentence, lang='zh-CN')
            if zh_audio_bytes:
                with open(zh_audio_path, 'wb') as af:
                    af.write(zh_audio_bytes)
                    
        if zh_audio_bytes:
            store_audio_in_anki(zh_audio_bytes, zh_audio_filename)
            
        # 2. English Sentence Audio
        if english:
            sound_en = block.get('audio_english', '')
            en_match = re.search(r'\[sound:(.*?)\]', sound_en)
            if en_match:
                en_audio_filename = en_match.group(1)
            else:
                h_name = hashlib.sha1(english.encode('utf-8')).hexdigest()
                en_audio_filename = f"en_sent_{h_name}.mp3"
                
            en_audio_path = os.path.join(audio_dir, en_audio_filename)
            en_audio_bytes = None
            
            if os.path.exists(en_audio_path):
                with open(en_audio_path, 'rb') as af:
                    en_audio_bytes = af.read()
            else:
                print(f"  -> Downloading English TTS...")
                en_audio_bytes = download_tts(english, lang='en')
                if en_audio_bytes:
                    with open(en_audio_path, 'wb') as af:
                        af.write(en_audio_bytes)
                        
            if en_audio_bytes:
                store_audio_in_anki(en_audio_bytes, en_audio_filename)
                
        # 3. Create Note Payload
        note_payload = {
            "deckName": deck_name,
            "modelName": model_name,
            "fields": {
                "Sentence": sentence,
                "Translated_Sentence": english,
                "Notes": desc,
                "Images": "",
                "Definitions": "",
                "Sentence_Audio": f"[sound:{zh_audio_filename}]" if zh_audio_filename else "",
                "Grammar_Point": grammar_point,
                "Translated_Audio": f"[sound:{en_audio_filename}]" if en_audio_filename else ""
            },
            "options": {
                "allowDuplicate": False
            },
            "tags": ["grammar", "hsk4"]
        }
        
        try:
            note_id = request_anki("addNote", note=note_payload)
            if note_id:
                print(f"  -> Success! Card ID: {note_id}")
                added_count += 1
                time.sleep(1.0)
        except Exception as e:
            print(f"  -> Failed to add note: {e}")
            
    print(f"\nFinished! Added {added_count} new notes to deck '{deck_name}'.")

if __name__ == '__main__':
    main()
