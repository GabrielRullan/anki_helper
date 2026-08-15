import os
import json
import time
import sys
import re
import csv
import urllib.request
import urllib.parse
import hashlib
import base64
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Reconfigure stdout to UTF-8
sys.stdout.reconfigure(encoding='utf-8')

ANKICONNECT_URL = 'http://127.0.0.1:8765'

# Load configuration
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

if API_KEY:
    client = genai.Client(api_key=API_KEY)
else:
    client = None
    print("Warning: GOOGLE_API_KEY not found in .env file. Auto-translation using Gemini will be disabled.")

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
        print(f"API Request Failed for action '{action}': {e}")
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
        print(f"Error fetching TTS for '{text}' ({lang}): {e}")
        return None

def store_audio_in_anki(audio_bytes, filename):
    base64_data = base64.b64encode(audio_bytes).decode('utf-8')
    try:
        res = request_anki("storeMediaFile", filename=filename, data=base64_data)
        return res
    except Exception as e:
        print(f"Error storing media file '{filename}' in Anki: {e}")
        return None

def translate_sentence(phrase, client):
    if not client:
        print("Warning: Google API client is not initialized. Cannot translate.")
        return ""
    prompt = f"Translate the following Chinese sentence into clear, natural English for a language learner. Return ONLY the translated sentence, with no other text, explanation, or formatting:\n\n{phrase}"
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        return response.text.strip().strip('"').strip("'")
    except Exception as e:
        print(f"Error translating sentence '{phrase}': {e}")
        return ""

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
                existing_sentences[normalize_sentence(sentence_field)] = note.get('noteId')
        return existing_sentences
    except Exception as e:
        print(f"Error checking existing cards in deck '{deck_name}': {e}")
        return {}

def parse_new_grammar(filepath):
    if not os.path.exists(filepath):
        print(f"Error: {filepath} not found.")
        return []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if "## 🟡 Pendiente de incluir" not in content:
        print("Error: '## 🟡 Pendiente de incluir' section not found in file.")
        return []
    
    pending_part = content.split("## 🟡 Pendiente de incluir")[1]
    if "## 🟢 Incluido en Anki" in pending_part:
        pending_part = pending_part.split("## 🟢 Incluido en Anki")[0]
        
    pending_part = pending_part.strip()
    
    items = []
    current_item = None
    
    for line in pending_part.split('\n'):
        line_str = line.strip()
        if not line_str:
            continue
            
        gp_match = re.match(r'^[-*]\s*\*\*Grammar Point\*\*:\s*(.*)', line_str, re.IGNORECASE)
        if gp_match:
            if current_item:
                items.append(current_item)
            current_item = {
                'grammar_point': gp_match.group(1).strip(),
                'phrase': '',
                'translation': '',
                'orig_lines': [line]
            }
            continue
            
        phrase_match = re.match(r'^[-*]\s*\*\*Phrase\*\*:\s*(.*)', line_str, re.IGNORECASE)
        if phrase_match and current_item:
            current_item['phrase'] = phrase_match.group(1).strip()
            current_item['orig_lines'].append(line)
            continue
            
        trans_match = re.match(r'^[-*]\s*\*\*Translation\*\*:\s*(.*)', line_str, re.IGNORECASE)
        if trans_match and current_item:
            current_item['translation'] = trans_match.group(1).strip()
            current_item['orig_lines'].append(line)
            continue
            
        if current_item:
            current_item['orig_lines'].append(line)
            
    if current_item:
        items.append(current_item)
        
    valid_items = []
    for item in items:
        if item['grammar_point'] and item['phrase']:
            valid_items.append(item)
            
    return valid_items

def update_new_grammar_file(filepath, success_items, all_pending_items):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    header = content.split("## 🟡 Pendiente de incluir")[0].rstrip()
    
    incluido_part = ""
    if "## 🟢 Incluido en Anki" in content:
        incluido_part = content.split("## 🟢 Incluido en Anki")[1].strip()
        
    new_incluido_part = incluido_part
    if new_incluido_part:
        new_incluido_part += "\n"
        
    for item in success_items:
        new_incluido_part += f"- **Grammar Point**: {item['grammar_point']}\n"
        new_incluido_part += f"  - **Phrase**: {item['phrase']}\n"
        if item['translation']:
            new_incluido_part += f"  - **Translation**: {item['translation']}\n"
            
    success_phrases = {item['phrase'] for item in success_items}
    remaining_pending = [item for item in all_pending_items if item['phrase'] not in success_phrases]
    
    pendiente_section = "\n\n## 🟡 Pendiente de incluir\n"
    for item in remaining_pending:
        pendiente_section += f"- **Grammar Point**: {item['grammar_point']}\n"
        pendiente_section += f"  - **Phrase**: {item['phrase']}\n"
        if item['translation']:
            pendiente_section += f"  - **Translation**: {item['translation']}\n"
            
    final_content = (
        header + 
        pendiente_section + 
        "\n## 🟢 Incluido en Anki\n" + 
        new_incluido_part.strip() + "\n"
    )
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(final_content)

def main():
    workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    new_grammar_path = os.path.join(workspace_dir, "new_grammar.md")
    
    print(f"Reading pending grammar from {new_grammar_path}...")
    pending_items = parse_new_grammar(new_grammar_path)
    
    if not pending_items:
        print("No pending grammar phrases found.")
        return
        
    print(f"Found {len(pending_items)} phrases to process.")
    
    deck_name = "Chinese::Sent"
    model_name = "Chinese Sentence - Double"
    
    print(f"Checking existing cards in deck '{deck_name}'...")
    existing_sentences = get_existing_sentences(deck_name)
    print(f"Found {len(existing_sentences)} existing sentences in Anki.")
    
    # Check if target model type exists
    try:
        models = request_anki("modelNames")
        if model_name not in models:
            print(f"Error: '{model_name}' note type not found in Anki. Available models: {models}")
            sys.exit(1)
    except Exception as e:
        print(f"Anki connection check failed: {e}")
        return
        
    queue = [item for item in pending_items if normalize_sentence(item['phrase']) not in existing_sentences]
    print(f"Already in Anki: {len(pending_items) - len(queue)}")
    print(f"Queue to add: {len(queue)}")
    print("-" * 40)
    
    if not queue:
        print("All phrases are already in Anki! Nothing to do.")
        return
        
    success_items = []
    
    for idx, item in enumerate(queue, 1):
        phrase = item['phrase']
        grammar_point = item['grammar_point']
        translation = item['translation']
        
        print(f"\n[{idx}/{len(queue)}] Processing: {phrase}...")
        
        # 1. Translate if not provided
        if not translation:
            print(" -> Translating with Gemini... ", end="", flush=True)
            translation = translate_sentence(phrase, client)
            if translation:
                item['translation'] = translation
                print(f"Done: {translation}")
            else:
                print("Failed.")
                continue
        else:
            print(f" -> Using provided translation: {translation}")
            
        # Generate hash-based filenames for TTS audio files
        phrase_hash = hashlib.sha1(phrase.encode('utf-8')).hexdigest()
        trans_hash = hashlib.sha1(translation.encode('utf-8')).hexdigest()
        
        zh_audio_filename = f"zh_tts_{phrase_hash}.mp3"
        en_audio_filename = f"en_tts_{trans_hash}.mp3"
        
        # 2. Download and upload Chinese TTS
        print(" -> Generating Chinese TTS... ", end="", flush=True)
        zh_audio_bytes = download_tts(phrase, lang='zh-CN')
        if zh_audio_bytes:
            store_audio_in_anki(zh_audio_bytes, zh_audio_filename)
            print("Done.")
        else:
            zh_audio_filename = ""
            print("Failed.")
            
        # 3. Download and upload English TTS
        print(" -> Generating English TTS... ", end="", flush=True)
        en_audio_bytes = download_tts(translation, lang='en')
        if en_audio_bytes:
            store_audio_in_anki(en_audio_bytes, en_audio_filename)
            print("Done.")
        else:
            en_audio_filename = ""
            print("Failed.")
            
        # 4. Construct payload and add card to Anki
        print(" -> Adding card to Anki... ", end="", flush=True)
        note_payload = {
            "deckName": deck_name,
            "modelName": model_name,
            "fields": {
                "Sentence": phrase,
                "Translated_Sentence": translation,
                "Notes": "",
                "Images": "",
                "Definitions": "",
                "Sentence_Audio": f"[sound:{zh_audio_filename}]" if zh_audio_filename else "",
                "Grammar_Point": grammar_point,
                "Translated_Audio": f"[sound:{en_audio_filename}]" if en_audio_filename else ""
            },
            "options": {
                "allowDuplicate": True
            },
            "tags": ["grammar"]
        }
        
        try:
            note_id = request_anki("addNote", note=note_payload)
            if note_id:
                print(f"Success! Card ID: {note_id}")
                success_items.append(item)
                # Pause to avoid hitches and rate limits
                time.sleep(1.5)
        except Exception as e:
            print(f"Failed to add note: {e}")
            continue

    if success_items:
        print(f"\nUpdating new_grammar.md with {len(success_items)} successfully added cards...")
        try:
            update_new_grammar_file(new_grammar_path, success_items, pending_items)
            print("new_grammar.md updated successfully!")
        except Exception as e:
            print(f"Failed to update new_grammar.md: {e}")
            
    print(f"\nSync Job Complete! Added {len(success_items)} cards to Anki.")

if __name__ == "__main__":
    main()


def parse_semana_md(filepath):
    if not os.path.exists(filepath):
        alt_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "chinese", "lessons", "semana.md")
        if os.path.exists(alt_path):
            filepath = alt_path
        else:
            return []

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    sections = re.split(r'(?m)^###\s+', content)
    items = []

    for sec in sections:
        sec_str = sec.strip()
        if not sec_str or not re.match(r'^\d+\.', sec_str):
            continue

        lines = [l.strip() for l in sec_str.split('\n') if l.strip()]
        header = lines[0]

        m_id = re.match(r'^(\d+)\.\s*(.*)$', header)
        if not m_id:
            continue

        item_id = m_id.group(1)
        header_text = m_id.group(2).strip()

        if header_text.endswith(')'):
            last_paren = header_text.rfind('(')
            if last_paren != -1:
                pattern = header_text[:last_paren].strip()
                meaning_raw = header_text[last_paren + 1:-1].strip()
            else:
                pattern = header_text
                meaning_raw = ""
        else:
            pattern = header_text
            meaning_raw = ""

        if "/" in meaning_raw:
            meaning = meaning_raw.split("/")[-1].strip()
        else:
            meaning = meaning_raw

        es_map = {}
        en_map = {}
        zh_map = {}
        notes = []

        for line in lines[1:]:
            note_match = re.match(r'^\*\s*\*?Note:\s*(.*?)\*?$', line, re.IGNORECASE)
            if note_match:
                notes.append(note_match.group(1).strip())
                continue

            es_m = re.match(r'^\*\s*\*\*ES(?:\s*\((.*?)\))?:\*\*\s*(.*)$', line)
            if es_m:
                label = es_m.group(1).strip() if es_m.group(1) else ""
                es_map[label] = es_m.group(2).strip()
                continue

            en_m = re.match(r'^\*\s*\*\*EN(?:\s*\((.*?)\))?:\*\*\s*(.*)$', line)
            if en_m:
                label = en_m.group(1).strip() if en_m.group(1) else ""
                en_map[label] = en_m.group(2).strip()
                continue

            zh_m = re.match(r'^\*\s*\*\*ZH(?:\s*\((.*?)\))?:\*\*\s*(.*)$', line)
            if zh_m:
                label = zh_m.group(1).strip() if zh_m.group(1) else ""
                zh_map[label] = zh_m.group(2).strip()
                continue

        labels = list(en_map.keys()) if en_map else [""]
        note_str = " ".join(notes)

        for label in labels:
            sub_label = label
            es_val = es_map.get(label, list(es_map.values())[0] if es_map else "")
            en_val = en_map.get(label, list(en_map.values())[0] if en_map else "")

            zh_val = ""
            if label in zh_map:
                zh_val = zh_map[label]
            else:
                clean_lbl = label.split(" - ")[0].strip() if " - " in label else label
                if clean_lbl in zh_map:
                    zh_val = zh_map[clean_lbl]
                else:
                    zh_val = list(zh_map.values())[0] if zh_map else ""

            items.append({
                'id': item_id,
                'grammar_pattern': pattern,
                'grammar_meaning': meaning,
                'sub_label': sub_label,
                'spanish': es_val,
                'english': en_val,
                'chinese': zh_val,
                'notes': note_str
            })

    return items


def generate_csv(items, output_path):
    headers = ['Word', 'Grammar Point', 'Sentence', 'Translated Sentence', 'Definitions', 'Notes']
    rows = []
    for item in items:
        notes_val = ""
        if item.get('notes'):
            notes_val = f"Explanation: {item['notes']}"

        rows.append({
            'Word': '',
            'Grammar Point': item.get('grammar_pattern', ''),
            'Sentence': item.get('chinese', ''),
            'Translated Sentence': item.get('english', ''),
            'Definitions': item.get('grammar_meaning', ''),
            'Notes': notes_val
        })

    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)

