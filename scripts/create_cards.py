import os
import json
import time
import sys
import io
import re
import urllib.request
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Fix for terminal encoding issues
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Load configuration
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY or API_KEY == "YOUR_API_KEY_HERE":
    print("Error: GOOGLE_API_KEY not found in .env file.")
    exit(1)

client = genai.Client(api_key=API_KEY)
ANKICONNECT_URL = 'http://127.0.0.1:8765'

# List of models to try in order of preference
MODELS_TO_TRY = [
    'imagen-4.0-fast-generate-001',
    'imagen-4.0-generate-001',
    'imagen-4.0-ultra-generate-001'
]

ERROR_LOG_PATH = "data/image_generation_errors.log"

def download_tts(text, lang='zh-CN'):
    url = "https://translate.google.com/translate_tts"
    params = {
        'ie': 'UTF-8',
        'tl': lang,
        'client': 'tw-ob',
        'q': text
    }
    import urllib.parse
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

def log_error(word, prompt, error_msg):
    os.makedirs("data", exist_ok=True)
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(ERROR_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] Word: {word}\n")
        f.write(f"Prompt: {prompt}\n")
        f.write(f"Error: {error_msg}\n")
        f.write("-" * 50 + "\n")

def generate_image_file(word, prompt_text, output_dir):
    filename = os.path.join(output_dir, f"{word}.png")
    if os.path.exists(filename):
        return filename

    for model_id in MODELS_TO_TRY:
        print(f"Using model {model_id}...", end=" ", flush=True)
        
        attempts = 3
        for attempt in range(attempts):
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
                    for generated_image in response.generated_images:
                        image_bytes = generated_image.image.image_bytes
                        with open(filename, "wb") as f:
                            f.write(image_bytes)
                        return filename
                else:
                    msg = f"Warning: {model_id} returned no images"
                    log_error(word, prompt_text, msg)
                    break
                    
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                    if attempt < attempts - 1:
                        sleep_time = 15 * (attempt + 1)
                        print(f"Rate limited. Sleeping {sleep_time}s and retrying...", end=" ", flush=True)
                        time.sleep(sleep_time)
                    else:
                        print(f"Quota exceeded for {model_id} after {attempts} attempts...", end=" ", flush=True)
                else:
                    msg = f"Error with {model_id}: {error_msg}"
                    log_error(word, prompt_text, msg)
                    print(f"{msg}", end=" ", flush=True)
                    break
                    
    return None

def parse_new_words(file_path):
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return []

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    try:
        parts = content.split('## 🟡 Pendiente de incluir')
        pendiente_section = parts[-1].split('## 🔴 Suelto')[0]
    except IndexError:
        print("Error: Sections missing in markdown.")
        return []

    items = []
    current_item = None
    
    for line in pendiente_section.splitlines():
        line_stripped = line.strip()
        if not line_stripped:
            continue
            
        root_match = re.match(r'^[-*]\s+(?:\*\*)?([^*()]+?)(?:\*\*)?\s*\(([^)]+)\)(?:\s*(?:—|-)\s*(.+))?', line)
        if root_match:
            if current_item:
                items.append(current_item)
            word = root_match.group(1).strip()
            pinyin = root_match.group(2).strip().replace('_', '').replace('*', '').strip()
            translation = root_match.group(3).strip() if root_match.group(3) else ""
            current_item = {
                'word': word,
                'pinyin': pinyin,
                'translation': translation,
                'frase': "",
                'traduccion': "",
                'desc': "",
                'prompt': "",
                'orig_line': line.strip()
            }
            continue
            
        if current_item:
            frase_match = re.match(r'^\s*[-*]\s*(?:\*\*|\*|_|__)Frase:(?:\*\*|\*|_|__)\s*(.+)', line)
            if frase_match:
                current_item['frase'] = frase_match.group(1).strip()
                continue
                
            traduccion_es_match = re.match(r'^\s*[-*]\s*(?:\*\*|\*|_|__)Traducción Español:(?:\*\*|\*|_|__)\s*(.+)', line)
            if traduccion_es_match:
                current_item['traduccion'] = traduccion_es_match.group(1).strip()
                continue
                
            traduccion_generic_match = re.match(r'^\s*[-*]\s*(?:\*\*|\*|_|__)Traducción:(?:\*\*|\*|_|__)\s*(.+)', line)
            if traduccion_generic_match and not current_item['traduccion']:
                current_item['traduccion'] = traduccion_generic_match.group(1).strip()
                continue

            desc_match = re.match(r'^\s*[-*]\s*(?:\*\*|\*|_|__)Descripción:(?:\*\*|\*|_|__)\s*(.+)', line)
            if desc_match:
                current_item['desc'] = desc_match.group(1).strip()
                continue
                
            prompt_match = re.match(r'^\s*[-*]\s*(?:\*\*|\*|_|__)Prompt:(?:\*\*|\*|_|__)\s*(.+)', line)
            if prompt_match:
                current_item['prompt'] = prompt_match.group(1).strip()
                continue

    if current_item:
        items.append(current_item)
        
    return items

def generate_missing_fields(word, translation, frase, frase_translation, client):
    needed_fields = []
    if not translation:
        needed_fields.append("translation (translate the Chinese word to Spanish and English, format as 'Spanish / English')")
    needed_fields.append("visual_description (a simple, visual scene in English representing the sentence, suitable for a Peanuts/Charlie Brown cartoon style illustration, focusing on a single character/action, no abstract concepts)")

    prompt = f"""
Analyze this Chinese vocabulary word and sentence:
Word: {word}
Current Translation: {translation if translation else "Unknown"}
Sentence: {frase}
Sentence Translation: {frase_translation}

We need to generate the following missing fields:
{chr(10).join(f"- {f}" for f in needed_fields)}

Format your response as a JSON object with these keys (if needed):
- "translation": (string, only if missing)
- "visual_description": (string, single visual sentence describing the scene in English, e.g., "A child looking under a couch with a magnifying glass.")

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
        print(f"Error generating fields for {word}: {e}")
        return {}

def main():
    workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    new_words_path = os.path.join(workspace_dir, "new_words.md")
    output_dir = os.path.join(workspace_dir, "imagenes_vocabulario")
    os.makedirs(output_dir, exist_ok=True)
    
    print("Reading new_words.md...")
    pending_items = parse_new_words(new_words_path)
    
    if not pending_items:
        print("No pending words found.")
        return
        
    print(f"Found {len(pending_items)} words to process.")
    
    # Check existing cards in Chinese::Words to prevent duplicate insertion
    print("Checking existing cards in Chinese::Words...")
    try:
        note_ids = request_anki("findNotes", query='deck:"Chinese::Words" "note:Migaku Word"')
        notes_info = request_anki("notesInfo", notes=note_ids)
        existing_words = set()
        for note in notes_info:
            w = note.get('fields', {}).get('Word', {}).get('value', '').strip()
            if w:
                # split by commas in case multiple words are grouped in the first field
                for sub_w in w.split(','):
                    existing_words.add(sub_w.strip())
        print(f"Found {len(existing_words)} existing words in Anki.")
    except Exception as e:
        print(f"Error connecting to Anki: {e}")
        return

    # Filter queue
    queue = [item for item in pending_items if item['word'] not in existing_words]
    print(f"Total Pending: {len(pending_items)}")
    print(f"Already in Anki: {len(pending_items) - len(queue)}")
    print(f"Queue to add: {len(queue)}")
    print("-" * 30)

    if not queue:
        print("All cards are already in Anki! Nothing to do.")
        return

    success_words = []
    
    for index, item in enumerate(queue, 1):
        word = item['word']
        pinyin = item['pinyin']
        translation = item['translation']
        frase = item['frase']
        traduccion = item['traduccion']
        desc = item['desc']
        prompt = item['prompt']
        
        print(f"\n[{index}/{len(queue)}] Processing: {word}...")
        
        # Fill missing fields via Gemini
        if not translation or not desc or not prompt:
            print(" -> Generating missing fields with Gemini... ", end="", flush=True)
            generated = generate_missing_fields(word, translation, frase, traduccion, client)
            if 'translation' in generated and not translation:
                translation = generated['translation'].strip()
                item['translation'] = translation
                print(f"[Translation: {translation}] ", end="")
            if 'visual_description' in generated and not desc:
                desc = generated['visual_description'].strip()
                item['desc'] = desc
                print("[Visual Description generated] ", end="")
            if desc and not prompt:
                prompt = (
                    f"Minimalist Peanuts cartoon style illustration for a language learning flashcard. "
                    f"The image must be extremely simple, focusing only on {desc}. "
                    f"Strict requirements: "
                    f"- Absolutely no text, no letters, no words, no speech bubbles, and no characters from any alphabet (Latin, Chinese, etc.). "
                    f"- Plain, solid, completely white background. "
                    f"- Clean line art with minimal, flat colors. "
                    f"- Plenty of empty white space around the centered characters."
                )
                item['prompt'] = prompt
                print("[Prompt constructed] ", end="")
            print("Done.")

        # 1. Generate the image (Bypassed / Ignored as requested)
        filename = ""
            
        # 3. Generate and store TTS audio for Word and Sentence (Bypassed / Ignored as requested)
        word_audio_filename = ""
        sentence_audio_filename = ""
        frase_clean = frase.replace('*', '').replace('-', '').replace('_', '')
            
        # 4. Create the Anki card payload
        print(" -> Adding card to Anki... ", end="", flush=True)
        definitions_html = f"<p>{word} ({pinyin})</p><p>∙ {translation}</p>"
        traduccion_clean = traduccion.replace('*', '').replace('-', '').replace('_', '')
        
        note_payload = {
            "deckName": "Chinese::Words",
            "modelName": "Migaku Word",
            "fields": {
                "Word": word,
                "Sentence": frase_clean,
                "Translated Sentence": traduccion_clean,
                "Definitions": definitions_html,
                "Example Sentences": "",
                "Notes": desc,
                "Images": f'<img src="{filename}">' if filename else "",
                "Sentence Audio": f"[sound:{sentence_audio_filename}]" if sentence_audio_filename else "",
                "Word Audio": f"[sound:{word_audio_filename}]" if word_audio_filename else ""
            },
            "options": {
                "allowDuplicate": False
            },
            "tags": ["hsk4", "immersion"]
        }
        
        try:
            note_id = request_anki("addNote", note=note_payload)
            if note_id:
                print(f"Success! Card ID: {note_id}")
                success_words.append(item)
                # Pause to avoid rate limits
                time.sleep(2)
        except Exception as e:
            print(f"Failed to add note: {e}")
            continue

    if success_words:
        print(f"\nUpdating new_words.md with {len(success_words)} successfully added cards...")
        # Reload new_words.md
        with open(new_words_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        header = content.split('## 🟢 Incluido en Anki')[0].rstrip()
        incluido_part = content.split('## 🟢 Incluido en Anki')[1].split('## 🟡 Pendiente de incluir')[0].strip()
        
        success_set = {x['word'] for x in success_words}
        
        # We can construct the new incluido_part
        new_incluido_part = incluido_part
        if new_incluido_part:
            new_incluido_part += "\n"
        for item in success_words:
            # Reconstruct the line neatly, preserving tags
            tags_part = ""
            if '#' in item['orig_line']:
                tags = re.findall(r'#\w+', item['orig_line'])
                if tags:
                    tags_part = " " + " ".join(tags)
            new_incluido_part += f"- **{item['word']}** ({item['pinyin']}) — {item['translation']}{tags_part}\n"
            
        # Rebuild the pending section by keeping only the ones that were NOT successful
        pendiente_section = "\n\n## 🟡 Pendiente de incluir\n*Aquí van las palabras en transición antes de añadirlas a Anki. Cada una debe incluir traducción y una frase memorable:*\n"
        
        # Let's get the original pending items and filter them
        all_pending_original = parse_new_words(new_words_path)
        remaining_pending = [x for x in all_pending_original if x['word'] not in success_set]
        
        for item in remaining_pending:
            w = item['word']
            p = item['pinyin']
            t = item['translation']
            f = item['frase']
            tr = item['traduccion']
            d = item['desc']
            pr = item['prompt']
            
            pendiente_section += f"- **{w}** ({p})"
            if t:
                pendiente_section += f" — {t}"
            pendiente_section += "\n"
            if f:
                pendiente_section += f"    - **Frase:** {f}\n"
            if tr:
                pendiente_section += f"    - _Traducción Español:_ {tr}\n"
            if d:
                pendiente_section += f"    - **Descripción:** {d}\n"
            if pr:
                pendiente_section += f"    - **Prompt:** {pr}\n"
                
        suelto_part = content.split('## 🔴 Suelto')[1].strip()
        
        final_content = (
            header + 
            "\n\n## 🟢 Incluido en Anki\n" + new_incluido_part.strip() + "\n" +
            pendiente_section +
            "\n## 🔴 Suelto\n*Palabras en caracteres chinos listas para estudio, con su pronunciación, significado y etiquetas de Obsidian:\n" +
            suelto_part
        )
        
        with open(new_words_path, 'w', encoding='utf-8') as f:
            f.write(final_content)
        print("new_words.md updated successfully!")
        
    print(f"\nBatch job complete! Added {len(success_words)} cards to Anki.")
if __name__ == "__main__":
    main()
