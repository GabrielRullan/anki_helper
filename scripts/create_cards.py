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
ANKICONNECT_URL = 'http://localhost:8765'

# List of models to try in order of preference
MODELS_TO_TRY = [
    'imagen-4.0-generate-001',
    'imagen-4.0-fast-generate-001',
    'imagen-4.0-ultra-generate-001',
    'imagen-3.0-generate-002'
]

ERROR_LOG_PATH = "data/image_generation_errors.log"

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
                continue
                
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                print(f"Quota exceeded for {model_id}...", end=" ", flush=True)
                continue
            else:
                msg = f"Error with {model_id}: {error_msg}"
                log_error(word, prompt_text, msg)
                print(f"{msg}", end=" ", flush=True)
                return None
                
    return None

def parse_new_words(file_path):
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return []

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    try:
        pendiente_section = content.split('## 🟡 Pendiente de incluir')[1].split('## 🔴 Suelto')[0]
    except IndexError:
        print("Error: Sections missing in markdown.")
        return []

    blocks = re.split(r'^\s*[*]\s*\*\*', pendiente_section, flags=re.MULTILINE)
    items = []
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        
        match_word = re.match(r'^([^*]+)\*\*\s*\(([^)]+)\)\s*—\s*([^\n]+)', block)
        if match_word:
            word = match_word.group(1).strip()
            pinyin = match_word.group(2).strip()
            translation = match_word.group(3).strip()
            
            frase_match = re.search(r'^\s*[*]\s*\*Frase:\*\s*([^\n]+)', block, re.MULTILINE)
            traduccion_match = re.search(r'^\s*[*]\s*\*Traducción:\*\s*([^\n]+)', block, re.MULTILINE)
            desc_match = re.search(r'^\s*[*]\s*\*Descripción:\*\s*([^\n]+)', block, re.MULTILINE)
            prompt_match = re.search(r'^\s*[*]\s*\*Prompt:\*\s*([^\n]+)', block, re.MULTILINE)
            
            items.append({
                'word': word,
                'pinyin': pinyin,
                'translation': translation,
                'frase': frase_match.group(1).strip() if frase_match else "",
                'traduccion': traduccion_match.group(1).strip() if traduccion_match else "",
                'desc': desc_match.group(1).strip() if desc_match else "",
                'prompt': prompt_match.group(1).strip() if prompt_match else "",
                'orig_line': f"- **{word}** ({pinyin}) — {translation}" + (f" #{block.split('#')[-1]}" if '#' in block else "")
            })
    return items

def main():
    workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    new_words_path = os.path.join(workspace_dir, "new_words.md")
    output_dir = os.path.join(workspace_dir, "imagenes_vocabulario")
    os.makedirs(output_dir, exist_ok=True)
    
    print("Reading new_words.md...")
    pending_items = parse_new_words(new_words_path)
    
    if not pending_items:
        print("No pending words with prompts found.")
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
        
        # 1. Generate the image
        print(" -> Generating image... ", end="", flush=True)
        img_path = generate_image_file(word, prompt, output_dir)
        if not img_path:
            print("Failed (Image generation error). Skipping.")
            continue
        print(f"Done. Saved to {img_path}")
        
        # 2. Add image to Anki Media collection
        filename = f"{word}.png"
        print(" -> Storing image in Anki... ", end="", flush=True)
        try:
            request_anki("storeMediaFile", filename=filename, path=os.path.abspath(img_path))
            print("Done.")
        except Exception as e:
            print(f"Failed to store media in Anki: {e}. Skipping.")
            continue
            
        # 3. Create the Anki card payload
        print(" -> Adding card to Anki... ", end="", flush=True)
        definitions_html = f"<p>{word} ({pinyin})</p><p>∙ {translation}</p>"
        # Clean phrase and translation of any '*', '-' or '_'
        frase_clean = frase.replace('*', '').replace('-', '').replace('_', '')
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
                "Images": f'<img src="{filename}">',
                "Sentence Audio": "",
                "Word Audio": ""
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
        
        # Parse the remaining pending section
        # We want to remove the successful words from the pending section
        # And add them to the included section
        success_set = {x['word'] for x in success_words}
        
        # We can construct the new incluido_part
        new_incluido_part = incluido_part
        if new_incluido_part:
            new_incluido_part += "\n"
        for item in success_words:
            # We match Obsidian tags from their original suelto lines (e.g. #trabajo)
            # Default tags can be reconstructed
            # Let's see: we saved the original line as it would look in Suelto/Incluido
            new_incluido_part += f"{item['orig_line']}\n"
            
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
            
            pendiente_section += f"* **{w}** ({p}) — {t}\n"
            if f:
                pendiente_section += f"  * *Frase:* {f}\n"
            if tr:
                pendiente_section += f"  * *Traducción:* {tr}\n"
            if d:
                pendiente_section += f"  * *Descripción:* {d}\n"
            if pr:
                pendiente_section += f"  * *Prompt:* {pr}\n"
                
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
