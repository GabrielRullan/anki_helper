import os
import sys
import json
import time
import urllib.request
import urllib.parse
import hashlib
import base64
import re
from collections import Counter, defaultdict
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel

sys.stdout.reconfigure(encoding='utf-8')

ANKICONNECT_URL = 'http://127.0.0.1:8765'
MODELS_TO_TRY = [
    'imagen-4.0-generate-001',
    'imagen-4.0-fast-generate-001',
    'imagen-4.0-ultra-generate-001'
]

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
                print(f"AnkiConnect Error: {res.get('error')}")
                return None
            return res.get('result')
    except Exception as e:
        print(f"AnkiConnect Request Failed: {e}")
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

def build_codebook(char_notes):
    initial_actors = defaultdict(list)
    final_sets = defaultdict(list)
    tone_locations = defaultdict(list)
    
    for note in char_notes:
        f = note.get('fields', {})
        pinyin_raw = f.get('Pinyin', {}).get('value', '').strip()
        if not pinyin_raw:
            continue
        pinyin_primary = pinyin_raw.split(',')[0].strip()
        initial, final = split_pinyin(pinyin_primary)
        
        actor = f.get('Actor', {}).get('value', '').strip()
        c_set = f.get('Set', {}).get('value', '').strip()
        tone = f.get('Tone', {}).get('value', '').strip()
        loc = f.get('Tone-Location', {}).get('value', '').strip()
        
        # Clean HTML tags
        actor = re.sub(r'<[^>]+>', '', actor).strip()
        c_set = re.sub(r'<[^>]+>', '', c_set).strip()
        loc = re.sub(r'<[^>]+>', '', loc).strip()
        
        if initial and actor and actor.lower() != 'unknown' and actor != '[EMPTY]':
            initial_actors[initial].append(actor)
        if final and c_set and c_set.lower() != 'unknown' and c_set != '[EMPTY]':
            final_sets[final].append(c_set)
        if tone and loc and loc.lower() != 'unknown' and loc != '[EMPTY]':
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

def generate_image_file(hanzi, scene_text, client, output_dir):
    filename = os.path.join(output_dir, f"{hanzi}.png")
    if os.path.exists(filename):
        return filename

    prompt_text = f"Minimalist Peanuts cartoon style illustration of: {scene_text}. On a plain white background, simple lines, flat colors, centered, no text, no letters."

    for model_id in MODELS_TO_TRY:
        print(f"  Trying model {model_id} for image generation...", end=" ", flush=True)
        for attempt in range(3):
            try:
                response = client.models.generate_images(
                    model=model_id,
                    prompt=prompt_text,
                    config=types.GenerateImagesConfig(
                        number_of_images=1,
                        output_mime_type="image/png",
                        aspect_ratio="1:1"
                    )
                )
                
                if response and response.generated_images:
                    image_bytes = response.generated_images[0].image.image_bytes
                    with open(filename, "wb") as f:
                        f.write(image_bytes)
                    print("Success!")
                    return filename
                else:
                    print("No images returned.")
                    break
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                    print(f"Rate limited (attempt {attempt+1}/3). Sleeping...", end=" ", flush=True)
                    time.sleep(10)
                else:
                    print(f"Error: {error_msg}")
                    break
    return None

class CharDetails(BaseModel):
    hanzi: str
    english_definition: str
    components: str
    common_words: str
    translation_of_words: str
    hsk_level: str
    frequency_rank: int
    mbp_level: str
    scene: str

class BatchCharDetails(BaseModel):
    items: list[CharDetails]

def query_gemini_for_batch(batch_items, client):
    prompt = """
You are an expert Chinese study assistant helping to clean up character study notes.
For each character in the input list, analyze the character and determine:
1. "english_definition": A high-quality, clear, extremely concise and clean English definition/meaning for the character itself. It must be brief and clean for a flashcard (avoid wordy explanations or excessive dictionary definitions). Use proper capitalization and spelling when necessary (e.g., capitalize names or proper nouns).
2. "components": The visual components/radicals of the character (e.g. 鸟, 昔, 口).
3. "common_words": Choose exactly two of the most common, standard, everyday vocabulary words or phrases containing this character. Do NOT choose obscure idioms, classical/rare words, or phrases that a beginner-to-intermediate learner is unlikely to see. They must be words actually used in daily life. Separate them by a comma (e.g. "下雪, 雪花").
4. "translation_of_words": High-quality, clean, and concise English translations of those two common words, separated by a comma (e.g. "snowing, snowflakes"). The translations MUST be in the exact same order as the words in "common_words" (i.e. the first translation corresponds to the first word, and the second translation corresponds to the second word). Keep it brief and clean for a flashcard, and use proper capital letters where appropriate.
5. "hsk_level": Old HSK level (1 to 6) or 'Non-HSK'.
6. "frequency_rank": Estimate of the character frequency rank in modern Chinese (integer, e.g. 500 for very common, 3000 for rare).
7. "mbp_level": Mapped level range in the Mandarin Blueprint character course if you know it (e.g. '1-6', '7-12', '13-20', '21-30', '31-36', '37-58', '60-80'), or 'Immersion' if it is typically not in the standard course.
8. "scene": Create a vivid, memorable, single-sentence mnemonic story (Scene) in English that integrates:
   - The Actor (given in the input)
   - The Set (given in the input)
   - The Tone-Location (given in the input)
   - The Props (which are the components of the character)
   - The English meaning of the character.
   Keep it extremely concise and clean for a card, using proper capitalization and punctuation.

Input character list:
"""
    input_data = []
    for item in batch_items:
        input_data.append({
            "hanzi": item["hanzi"],
            "pinyin": item["pinyin"],
            "actor": item["actor"],
            "set": item["set"],
            "tone_location": item["tone_location"]
        })
        
    prompt += json.dumps(input_data, ensure_ascii=False, indent=2)
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=BatchCharDetails
            )
        )
        data = json.loads(response.text.strip())
        return data.get('items', [])
    except Exception as e:
        print(f"Error querying Gemini for batch: {e}")
        return []

def main():
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("[ERROR] GOOGLE_API_KEY not found in .env.")
        sys.exit(1)
        
    client = genai.Client(api_key=api_key)
    
    # Check Anki Connect
    version = request_anki("version")
    if not version:
        print("[ERROR] Anki must be running with AnkiConnect enabled.")
        sys.exit(1)
    print(f"Connected to Anki (version {version}).")
    
    # 1. Fetch all notes to build codebook
    print("Fetching all notes in Chinese::Char to build codebook...")
    all_note_ids = request_anki("findNotes", query="deck:Chinese::Char")
    if not all_note_ids:
        print("No notes found in Chinese::Char.")
        return
    
    # Query in batches of 500 to not overload AnkiConnect
    all_notes_info = []
    chunk_size = 500
    for i in range(0, len(all_note_ids), chunk_size):
        chunk = all_note_ids[i:i+chunk_size]
        res = request_anki("notesInfo", notes=chunk)
        if res:
            all_notes_info.extend(res)
            
    print(f"Loaded {len(all_notes_info)} notes to build codebook.")
    codebook = build_codebook(all_notes_info)
    print(f"Codebook built with {len(codebook['actors'])} actors, {len(codebook['sets'])} sets, {len(codebook['locations'])} locations.")
    
    # 2. Get the latest 200 notes
    all_note_ids.sort(reverse=True)
    latest_200_ids = all_note_ids[:200]
    latest_200_info = request_anki("notesInfo", notes=latest_200_ids)
    print(f"Loaded details for the latest 200 notes.")
    
    # 3. Prepare notes for processing
    to_enrich = []
    for note in latest_200_info:
        fields = note['fields']
        hanzi = fields.get('Hanzi', {}).get('value', '').strip()
        pinyin_raw = fields.get('Pinyin', {}).get('value', '').strip()
        if not hanzi or not pinyin_raw:
            continue
            
        pinyin = pinyin_raw.split(',')[0].strip()
        init, final = split_pinyin(pinyin)
        tone = get_tone_number(pinyin)
        
        # Determine actor, set, location
        actor = fields.get('Actor', {}).get('value', '').strip()
        if not actor or actor.lower() == 'unknown' or actor == '[EMPTY]':
            actor = codebook['actors'].get(init, 'Jackie Chan' if not init else 'Unknown')
            
        c_set = fields.get('Set', {}).get('value', '').strip()
        if not c_set or c_set.lower() == 'unknown' or c_set == '[EMPTY]':
            c_set = codebook['sets'].get(final, 'Unknown')
            
        tone_loc = fields.get('Tone-Location', {}).get('value', '').strip()
        if not tone_loc or tone_loc.lower() == 'unknown' or tone_loc == '[EMPTY]':
            tone_loc = codebook['locations'].get(str(tone), 'Unknown')
            
        to_enrich.append({
            'note_id': note['noteId'],
            'hanzi': hanzi,
            'pinyin': pinyin_raw,
            'actor': actor,
            'set': c_set,
            'tone': str(tone),
            'tone_location': tone_loc,
            'fields': fields
        })
        
    print(f"Identified {len(to_enrich)} valid notes to process.")
    
    # 4. Batch query Gemini
    gemini_details_map = {}
    gemini_batch_size = 20
    print(f"Querying Gemini 2.5 Flash in batches of {gemini_batch_size}...")
    for i in range(0, len(to_enrich), gemini_batch_size):
        chunk = to_enrich[i:i+gemini_batch_size]
        print(f" -> Querying batch {i//gemini_batch_size + 1} / {len(to_enrich)//gemini_batch_size + 1}...")
        res = query_gemini_for_batch(chunk, client)
        if res:
            for item in res:
                gemini_details_map[item['hanzi']] = item
        time.sleep(2)
        
    # 5. Enrich cards, generate TTS and Images
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "imagenes_vocabulario")
    os.makedirs(output_dir, exist_ok=True)
    
    updated_count = 0
    
    for idx, item in enumerate(to_enrich, 1):
        hz = item['hanzi']
        nid = item['note_id']
        fields = item['fields']
        
        g_detail = gemini_details_map.get(hz)
        if not g_detail:
            print(f"[{idx}/{len(to_enrich)}] No Gemini details found for {hz}. Skipping.")
            continue
            
        print(f"\n[{idx}/{len(to_enrich)}] Processing character: {hz}")
        
        updates = {}
        
        # Update Actor, Set, Tone-Location, Tone
        updates['Actor'] = item['actor']
        updates['Set'] = item['set']
        updates['Tone-Location'] = item['tone_location']
        updates['Tone'] = item['tone']
        updates['Initial'] = split_pinyin(item['pinyin'].split(',')[0].strip())[0].upper()
        
        # English translation
        updates['English'] = g_detail.get('english_definition', '')
        
        # Components
        updates['Components'] = g_detail.get('components', '')
        
        # Common Words and Translations
        updates['Common Words'] = g_detail.get('common_words', '')
        updates['Translation of Words'] = g_detail.get('translation_of_words', '')
        
        # HSK Level
        updates['HSK_2'] = g_detail.get('hsk_level', '')
        
        # Frequency rank
        freq_str = "uncommon"
        freq_rank = g_detail.get('frequency_rank', 3000)
        if freq_rank <= 500:
            freq_str = "very basic"
        elif freq_rank <= 1500:
            freq_str = "basic"
        elif freq_rank <= 3000:
            freq_str = "common"
        elif freq_rank <= 5000:
            freq_str = "uncommon"
        else:
            freq_str = "advanced"
        updates['Frequency'] = f'<div class="freq freq-{freq_str.replace(" ", "-")}">{freq_str}</div>'
        
        # MBP Level and Phase
        updates['MBP_Level'] = g_detail.get('mbp_level', '')
        updates['MBP_Phase'] = "Unknown"
        
        # Scene story
        existing_scene = fields.get('Scene', {}).get('value', '').strip()
        scene_text = existing_scene if (existing_scene and existing_scene.lower() != 'unknown' and existing_scene != '[EMPTY]') else g_detail.get('scene', '')
        updates['Scene'] = scene_text
        
        # Simplified and Traditional fields if empty
        if not fields.get('Simplified', {}).get('value', '').strip():
            updates['Simplified'] = hz
        if not fields.get('Traditional', {}).get('value', '').strip():
            updates['Traditional'] = hz
            
        # --- Media Generations ---
        
        # 1. Sound TTS (Character pronunciation)
        existing_sound = fields.get('Sound', {}).get('value', '').strip()
        if not existing_sound or '[sound:' not in existing_sound:
            print(f"  Generating character pronunciation TTS for '{hz}'...")
            zh_bytes = download_tts(hz, lang='zh-CN')
            if zh_bytes:
                h_name = hashlib.sha1(hz.encode('utf-8')).hexdigest()
                filename = f"zh_char_{hz}_{h_name}.mp3"
                store_audio_in_anki(zh_bytes, filename)
                updates['Sound'] = f"[sound:{filename}]"
                time.sleep(0.3)
                
        # 2. Words_Sound TTS (Common Words)
        existing_words_sound = fields.get('Words_Sound', {}).get('value', '').strip()
        words_to_speak = g_detail.get('common_words', '')
        h_name = hashlib.sha1(words_to_speak.encode('utf-8')).hexdigest()
        expected_words_filename = f"zh_words_{hz}_{h_name}.mp3"
        
        if words_to_speak and (not existing_words_sound or expected_words_filename not in existing_words_sound):
            print(f"  Generating common words TTS for '{words_to_speak}'...")
            w_bytes = download_tts(words_to_speak, lang='zh-CN')
            if w_bytes:
                store_audio_in_anki(w_bytes, expected_words_filename)
                updates['Words_Sound'] = f"[sound:{expected_words_filename}]"
                time.sleep(0.3)
                
        # 3. Words_English_Sound TTS (Translation of Words)
        existing_en_sound = fields.get('Words_English_Sound', {}).get('value', '').strip()
        en_to_speak = g_detail.get('translation_of_words', '')
        h_name_en = hashlib.sha1(en_to_speak.encode('utf-8')).hexdigest()
        expected_en_filename = f"en_words_{hz}_{h_name_en}.mp3"
        
        if en_to_speak and (not existing_en_sound or expected_en_filename not in existing_en_sound):
            print(f"  Generating translation TTS for '{en_to_speak}'...")
            en_bytes = download_tts(en_to_speak, lang='en')
            if en_bytes:
                store_audio_in_anki(en_bytes, expected_en_filename)
                updates['Words_English_Sound'] = f"[sound:{expected_en_filename}]"
                time.sleep(0.3)
                
        # 4. Image Illustration (Imagen 4.0)
        existing_img = fields.get('Image', {}).get('value', '').strip()
        if not existing_img or '<img' not in existing_img:
            print(f"  Generating illustration for scene: '{scene_text[:60]}...'")
            meaning_keyword = re.sub(r'[^a-zA-Z]', '', g_detail.get('english_definition', 'char').split(',')[0].split(';')[0].strip()).lower()
            if not meaning_keyword:
                meaning_keyword = "char"
            media_filename = f"mbp_{hz}_{meaning_keyword}.png"
            
            img_path = generate_image_file(hz, scene_text, client, output_dir)
            if img_path:
                print("    Storing image in Anki media...")
                try:
                    res = request_anki("storeMediaFile", filename=media_filename, path=os.path.abspath(img_path))
                    if res:
                        updates['Image'] = f'<img src="{media_filename}">'
                except Exception as e:
                    print(f"    Failed to store image: {e}")
            time.sleep(4) # Pause between image generations to protect rate limits
            
        # Submit updates to Anki
        if updates:
            print(f"  Updating Anki note {nid}...")
            try:
                request_anki("updateNoteFields", note={"id": nid, "fields": updates})
                updated_count += 1
            except Exception as e:
                print(f"  Failed to update note {nid}: {e}")
                
    print(f"\nSuccessfully updated {updated_count} notes.")
    
    # 6. Rebuild dashboard and export
    print("\nRebuilding CSV and dashboard...")
    scripts_dir = os.path.dirname(os.path.abspath(__file__))
    os.system(f'python "{os.path.join(scripts_dir, "extract_anki_data.py")}"')
    os.system(f'python "{os.path.join(scripts_dir, "generate_dashboard.py")}"')
    print("Done!")

if __name__ == "__main__":
    main()
