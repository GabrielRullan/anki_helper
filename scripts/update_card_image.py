import os
import sys
import io
import re
import json
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

MODELS_TO_TRY = [
    'imagen-4.0-generate-001',
    'imagen-4.0-fast-generate-001',
    'imagen-4.0-ultra-generate-001',
    'imagen-3.0-generate-002'
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
        with urllib.request.urlopen(req, timeout=15) as response:
            res = json.loads(response.read().decode('utf-8'))
            if res.get('error'):
                raise Exception(res.get('error'))
            return res.get('result')
    except Exception as e:
        print(f"AnkiConnect Request Failed for action '{action}': {e}")
        return None

def find_prompt_in_md(file_path, target_word):
    if not os.path.exists(file_path):
        return None
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Search for the word block under any bullet list
    pattern = re.compile(rf'^\s*[-*]\s*\*\*{re.escape(target_word)}\*\*(.*?)(?=^\s*[-*]\s*\*\*|##|$)', re.DOTALL | re.MULTILINE)
    match = pattern.search(content)
    if match:
        block = match.group(1)
        prompt_match = re.search(r'^\s*[*]\s*\*Prompt:\*\s*([^\n]+)', block, re.MULTILINE)
        if prompt_match:
            return prompt_match.group(1).strip()
    return None

def generate_image_file(word, prompt_text, output_dir):
    filename = os.path.join(output_dir, f"{word}.png")
    
    # We overwrite the existing file since we are explicitly updating it
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
                print("Warning: no images returned.", end=" ", flush=True)
                continue
                
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                print(f"Quota exceeded for {model_id}...", end=" ", flush=True)
                continue
            else:
                print(f"Error with {model_id}: {error_msg}", end=" ", flush=True)
                return None
                
    return None

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/update_card_image.py <word> [custom_prompt]")
        sys.exit(1)
        
    word = sys.argv[1].strip()
    custom_prompt = " ".join(sys.argv[2:]).strip() if len(sys.argv) > 2 else None
    
    workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    new_words_path = os.path.join(workspace_dir, "new_words.md")
    output_dir = os.path.join(workspace_dir, "imagenes_vocabulario")
    os.makedirs(output_dir, exist_ok=True)
    
    prompt = None
    if custom_prompt:
        prompt = custom_prompt
        print(f"Using custom prompt provided via command line.")
    else:
        print(f"Searching for word '{word}' in new_words.md...")
        prompt = find_prompt_in_md(new_words_path, word)
        
    if not prompt:
        if not custom_prompt:
            print(f"Error: Word '{word}' or its Prompt was not found in new_words.md.")
            print("Please specify a custom prompt as the second argument:")
            print(f"  python scripts/update_card_image.py {word} \"Your custom image prompt here...\"")
            sys.exit(1)
            
    print(f"Word: {word}")
    print(f"Prompt: {prompt}")
    print("-" * 50)
    
    # 1. Generate image
    print("Generating new image...", flush=True)
    img_path = generate_image_file(word, prompt, output_dir)
    if not img_path:
        print("\nError: Failed to generate image.")
        sys.exit(1)
    print(f"\nImage successfully saved to: {img_path}")
    
    # 2. Upload to Anki media
    filename = f"{word}.png"
    print("Uploading image to Anki media library...", end=" ", flush=True)
    media_res = request_anki("storeMediaFile", filename=filename, path=os.path.abspath(img_path))
    if media_res is None:
        print("Failed to store media file in Anki.")
    else:
        print("Done.")
        
    # 3. Find Note ID in Anki
    print(f"Searching for card '{word}' in Anki...", end=" ", flush=True)
    note_ids = request_anki("findNotes", query=f'deck:"Chinese::Words" "Word:{word}"')
    if not note_ids:
        # try case-insensitive or loose check
        note_ids = request_anki("findNotes", query=f'deck:"Chinese::Words" "{word}"')
        
    if note_ids:
        note_id = note_ids[0]
        print(f"Found Note ID: {note_id}")
        
        # Update Note field
        print("Updating note fields to refresh image...", end=" ", flush=True)
        update_payload = {
            "note": {
                "id": note_id,
                "fields": {
                    "Images": f'<img src="{filename}">'
                }
            }
        }
        update_res = request_anki("updateNoteFields", **update_payload)
        print("Done. Card updated successfully!")
    else:
        print("\nWarning: Note was not found in Anki deck 'Chinese::Words'.")
        print("The image was saved locally and stored in Anki media, but no card field was updated.")
        
if __name__ == "__main__":
    main()
