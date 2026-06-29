import os
import json
import time
import sys
import re
import urllib.request
import urllib.parse
import hashlib
import base64
import csv
from dotenv import load_dotenv

# Reconfigure stdout to UTF-8
sys.stdout.reconfigure(encoding='utf-8')

ANKICONNECT_URL = 'http://127.0.0.1:8765'

# Try to load Gemini client if API key is present
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")
client = None
if API_KEY:
    try:
        from google import genai
        client = genai.Client(api_key=API_KEY)
        print("Gemini API client initialized successfully.")
    except Exception as e:
        print(f"Failed to initialize Gemini client: {e}")
else:
    print("Warning: GOOGLE_API_KEY not found in .env file. Gemini-based enrichments will be skipped.")

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
        with urllib.request.urlopen(req, timeout=20) as response:
            res = json.loads(response.read().decode('utf-8'))
            if res.get('error'):
                raise Exception(res.get('error'))
            return res.get('result')
    except Exception as e:
        print(f"AnkiConnect Request Failed: {e}")
        return None

def download_tts(text, lang='zh-CN'):
    url = "https://translate.google.com/translate_tts"
    # Replace newlines and extra spaces to avoid corrupting URL
    text_clean = re.sub(r'\s+', ' ', text).strip()
    if not text_clean:
        return None
    params = {
        'ie': 'UTF-8',
        'tl': lang,
        'client': 'tw-ob',
        'q': text_clean[:100] # Google Translate TTS limit is typically 100 chars
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

def split_pinyin(pinyin):
    pinyin = pinyin.lower().strip()
    pinyin = re.sub(r'<[^>]+>', '', pinyin)
    vowel_map = {
        'ā': 'a', 'á': 'a', 'ǎ': 'a', 'à': 'a',
        'ē': 'e', 'é': 'e', 'ě': 'e', 'è': 'e',
        'ī': 'i', 'í': 'i', 'ǐ': 'i', 'ì': 'i',
        'ō': 'o', 'ó': 'o', 'ǒ': 'o', 'ò': 'o',
        'ū': 'u', 'ú': 'u', 'ǔ': 'u', 'ù': 'u',
        'ǖ': 'v', 'ǘ': 'v', 'ǚ': 'v', 'ǜ': 'v',
        'ü': 'v'
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

def clean_pinyin_from_translation(text):
    if not text:
        return ""
    # Split by semicolon or newline or comma to check individual definitions
    parts = re.split(r'[;\n]+', text)
    cleaned_parts = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        # Check if there is a colon separating pinyin from definition
        if ':' in part:
            left, right = part.split(':', 1)
            left_clean = left.strip()
            # If the left side looks like pinyin (only contains pinyin letters, numbers, spaces, or tone marks)
            # we strip it and keep only the right side
            is_pinyin = re.match(r'^[a-zA-Zāáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜü1-5\s]+$', left_clean)
            if is_pinyin:
                cleaned_parts.append(right.strip())
                continue
        cleaned_parts.append(part)
    return "; ".join(cleaned_parts)

def batch_enrich_with_gemini(chars_list):
    if not client:
        return {}
    
    chars_input = []
    for c in chars_list:
        chars_input.append(f"{c['hanzi']} ({c['pinyin']})")
        
    prompt = f"""
Analyze the following Chinese characters:
{", ".join(chars_input)}

For each character, determine:
1. "hsk_level": Old HSK level (1 to 6) or 'Non-HSK'.
2. "frequency": Character frequency rank in modern Chinese (integer, e.g. 500 for very common, 3000 for rare).
3. "mbp_level": Mapped level range in the Mandarin Blueprint character course if you know it (e.g. '1-6', '7-12', '13-20', '21-30', '31-36', '37-58', '60'-'80'), or 'Immersion' if it is typically not in the standard course.

Format your response as a JSON object where the keys are the characters themselves (just the Hanzi), mapping to an object with keys "hsk_level", "frequency", and "mbp_level".
Return ONLY the raw JSON object, no markdown formatting.
"""
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config={'response_mime_type': 'application/json'}
        )
        data = json.loads(response.text.strip())
        return data
    except Exception as e:
        print(f"Error calling Gemini batch API: {e}")
        return {}

def main():
    print("Checking cards in Anki 'Chinese::Char is:new'...")
    card_ids = request_anki("findCards", query="deck:Chinese::Char is:new")
    if not card_ids:
        print("No new cards found.")
        return
        
    cards_info = request_anki("cardsInfo", cards=card_ids)
    note_ids = list(set(card['note'] for card in cards_info))
    notes_info = request_anki("notesInfo", notes=note_ids)
    
    print(f"Found {len(notes_info)} unique character notes in 'is:new' state.")
    
    # Pre-compile HSK 4 characters
    hsk4_chars = set()
    hsk4_csv_path = "c:\\Users\\gabri\\Documents\\anki_helper\\data\\hsk4_vocab.csv"
    if os.path.exists(hsk4_csv_path):
        with open(hsk4_csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                if row:
                    for char in row[0]:
                        if '\u4e00' <= char <= '\u9fff':
                            hsk4_chars.add(char)
                            
    success_count = 0
    updated_notes = []
    
    # We will gather character objects for batch Gemini lookup
    gemini_queue = []
    
    for idx, note in enumerate(notes_info, 1):
        fields = note['fields']
        hanzi = fields.get('Hanzi', {}).get('value', '').strip()
        pinyin = fields.get('Pinyin', {}).get('value', '').strip()
        
        if not hanzi:
            continue
            
        gemini_queue.append({
            'note_id': note['noteId'],
            'hanzi': hanzi,
            'pinyin': pinyin,
            'note': note
        })
        
    # Batch process with Gemini in chunks of 30 to stay within limits
    gemini_enrichments = {}
    if client and gemini_queue:
        chunk_size = 30
        print(f"Querying Gemini in batches of {chunk_size} for HSK level, frequency, and MBP level ranges...")
        for i in range(0, len(gemini_queue), chunk_size):
            chunk = gemini_queue[i:i+chunk_size]
            print(f" -> Processing batch {i//chunk_size + 1} / {len(gemini_queue)//chunk_size + 1}...")
            res = batch_enrich_with_gemini(chunk)
            if res:
                gemini_enrichments.update(res)
            time.sleep(1) # small pause
            
    # Process each note
    for idx, item in enumerate(gemini_queue, 1):
        note_id = item['note_id']
        hanzi = item['hanzi']
        pinyin = item['pinyin']
        note = item['note']
        fields = note['fields']
        
        # Get existing values
        actor = fields.get('Actor', {}).get('value', '').strip()
        components = fields.get('Components', {}).get('value', '').strip()
        translation_of_words = fields.get('Translation of Words', {}).get('value', '').strip()
        common_words = fields.get('Common Words', {}).get('value', '').strip()
        hsk_level = fields.get('HSK_2', {}).get('value', '').strip()
        mbp_level = fields.get('MBP_Level', {}).get('value', '').strip()
        frequency = fields.get('Frequency', {}).get('value', '').strip()
        words_sound = fields.get('Words_Sound', {}).get('value', '').strip()
        words_en_sound = fields.get('Words_English_Sound', {}).get('value', '').strip()
        
        changed = False
        updates = {}
        
        # 1. Actor Fix (for zero initials, set to Jackie Chan)
        if not actor:
            init, final = split_pinyin(pinyin)
            if not init: # zero initial!
                print(f"[{hanzi}] Setting Actor to 'Jackie Chan' (Zero-initial)")
                updates['Actor'] = 'Jackie Chan'
                changed = True
                
        # 2. Components Fix
        if not components:
            if hanzi == '长':
                updates['Components'] = '长'
                changed = True
            elif hanzi == '马':
                updates['Components'] = '马'
                changed = True
                
        # 3. Translation of Words Fix (Set directly without pinyin)
        if not translation_of_words:
            if hanzi == '吾':
                updates['Translation of Words'] = 'we; my country'
                changed = True
                translation_of_words = 'we; my country'
            elif hanzi == '谍':
                updates['Translation of Words'] = 'spy; intelligence'
                changed = True
                translation_of_words = 'spy; intelligence'
        else:
            # Clean pinyin if already exists
            cleaned_trans = clean_pinyin_from_translation(translation_of_words)
            if cleaned_trans != translation_of_words:
                print(f"[{hanzi}] Cleaning pinyin from Translation of Words: '{translation_of_words}' -> '{cleaned_trans}'")
                updates['Translation of Words'] = cleaned_trans
                translation_of_words = cleaned_trans
                changed = True
                
        # 4. HSK Level Fix
        # Check local HSK 4 first
        if not hsk_level:
            if hanzi in hsk4_chars:
                updates['HSK_2'] = '4'
                changed = True
            elif hanzi in gemini_enrichments:
                gemini_hsk = str(gemini_enrichments[hanzi].get('hsk_level', ''))
                if gemini_hsk:
                    updates['HSK_2'] = gemini_hsk
                    changed = True
                    
        # 5. Frequency & MBP Level range from Gemini
        if hanzi in gemini_enrichments:
            if not frequency:
                gemini_freq = str(gemini_enrichments[hanzi].get('frequency', ''))
                if gemini_freq:
                    updates['Frequency'] = gemini_freq
                    changed = True
            if not mbp_level or mbp_level.lower() == 'unknown':
                gemini_mbp = str(gemini_enrichments[hanzi].get('mbp_level', ''))
                if gemini_mbp:
                    updates['MBP_Level'] = gemini_mbp
                    changed = True
                    
        # 6. Generate Words_Sound TTS
        if common_words and not words_sound:
            print(f"[{hanzi}] Generating Words_Sound TTS for: {common_words}")
            zh_bytes = download_tts(common_words, lang='zh-CN')
            if zh_bytes:
                h_name = hashlib.sha1(common_words.encode('utf-8')).hexdigest()
                filename = f"zh_words_{h_name}.mp3"
                store_audio_in_anki(zh_bytes, filename)
                updates['Words_Sound'] = f"[sound:{filename}]"
                changed = True
                time.sleep(0.5)
                
        # 7. Generate Words_English_Sound TTS
        if translation_of_words and not words_en_sound:
            print(f"[{hanzi}] Generating Words_English_Sound TTS for: {translation_of_words}")
            en_bytes = download_tts(translation_of_words, lang='en')
            if en_bytes:
                h_name = hashlib.sha1(translation_of_words.encode('utf-8')).hexdigest()
                filename = f"en_words_{h_name}.mp3"
                store_audio_in_anki(en_bytes, filename)
                updates['Words_English_Sound'] = f"[sound:{filename}]"
                changed = True
                time.sleep(0.5)
                
        if changed:
            try:
                request_anki("updateNoteFields", note={"id": note_id, "fields": updates})
                success_count += 1
            except Exception as e:
                print(f"Failed to update note {note_id} ({hanzi}): {e}")
                
    print(f"\nCompleted! Enriched and cleaned {success_count} character notes in Anki.")
    
    # 8. Re-extract to CSV
    print("Re-extracting notes to new_characters.csv...")
    # Fetch latest fields
    notes_info = request_anki("notesInfo", notes=note_ids)
    field_names = set()
    for note in notes_info:
        field_names.update(note.get('fields', {}).keys())
    field_names = sorted(list(field_names))
    
    csv_path = "c:\\Users\\gabri\\Documents\\anki_helper\\data\\new_characters.csv"
    with open(csv_path, 'w', encoding='utf-8', newline='') as csvfile:
        writer = csv.writer(csvfile)
        header = ['Note_ID', 'Tags'] + field_names
        writer.writerow(header)
        for note in notes_info:
            row = [note.get('noteId'), ", ".join(note.get('tags', []))]
            for field in field_names:
                field_value = note.get('fields', {}).get(field, {}).get('value', '').strip()
                row.append(field_value)
            writer.writerow(row)
    print("new_characters.csv updated successfully.")

if __name__ == '__main__':
    main()
