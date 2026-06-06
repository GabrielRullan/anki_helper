import os
import json
import time
import sys
import io
import re
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Fix for terminal encoding issues
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 1. Load configuration
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY or API_KEY == "YOUR_API_KEY_HERE":
    print("Error: GOOGLE_API_KEY not found in .env file.")
    exit(1)

# 2. Initialize Client
client = genai.Client(api_key=API_KEY)

# List of models to try in order of preference
MODELS_TO_TRY = [
    'imagen-4.0-generate-001',
    'imagen-4.0-fast-generate-001',
    'imagen-4.0-ultra-generate-001',
    'imagen-3.0-generate-002'
]

ERROR_LOG_PATH = "data/image_generation_errors.log"

def log_error(word, prompt, error_msg):
    os.makedirs("data", exist_ok=True)
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(ERROR_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] Word: {word}\n")
        f.write(f"Prompt: {prompt}\n")
        f.write(f"Error: {error_msg}\n")
        f.write("-" * 50 + "\n")

def generate_and_save(word, prompt_text, output_dir):
    filename = os.path.join(output_dir, f"{word}.png")
    
    if os.path.exists(filename):
        print(f"Skipping {word}, image already exists.")
        return True

    for model_id in MODELS_TO_TRY:
        print(f"Using {model_id}...", end=" ", flush=True)
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
                    return True
            else:
                msg = f"Warning: {model_id} returned no images (Safety filter?)"
                print(msg, flush=True)
                log_error(word, prompt_text, msg)
                continue
                
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                print(f"Quota exceeded for {model_id}...", flush=True)
                continue
            else:
                msg = f"Error with {model_id}: {error_msg}"
                print(msg, flush=True)
                log_error(word, prompt_text, msg)
                return False
                
    return False

def parse_new_words(file_path):
    """
    Parses new_words.md and extracts all pending words that have prompts.
    Returns list of dicts: {'word': ..., 'prompt': ...}
    """
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return []

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Get only the content under '## 🟡 Pendiente de incluir' up to '## 🔴 Suelto'
    try:
        pendiente_section = content.split('## 🟡 Pendiente de incluir')[1].split('## 🔴 Suelto')[0]
    except IndexError:
        print("Error: Could not find '## 🟡 Pendiente de incluir' or '## 🔴 Suelto' sections in markdown.")
        return []

    # Split into blocks of: * **word**
    blocks = re.split(r'^\s*[*]\s*\*\*', pendiente_section, flags=re.MULTILINE)
    items = []
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        
        # Match the word character name
        match_word = re.match(r'^([^*]+)\*\*', block)
        if match_word:
            word = match_word.group(1).strip()
            
            # Find the prompt line
            prompt_match = re.search(r'^\s*[*]\s*\*Prompt:\*\s*([^\n]+)', block, re.MULTILINE)
            if prompt_match:
                prompt = prompt_match.group(1).strip()
                items.append({
                    'word': word,
                    'prompt': prompt
                })
    return items

def main():
    workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    new_words_path = os.path.join(workspace_dir, "new_words.md")
    output_dir = os.path.join(workspace_dir, "imagenes_vocabulario")
    os.makedirs(output_dir, exist_ok=True)
    
    print("Parsing new_words.md...")
    pending_items = parse_new_words(new_words_path)
    
    if not pending_items:
        print("No pending words with prompts found.")
        return
        
    print(f"Found {len(pending_items)} words to process.")
    
    # Filter out already existing images
    existing_images = {os.path.splitext(f)[0] for f in os.listdir(output_dir) if f.endswith('.png')}
    queue = [p for p in pending_items if p['word'] not in existing_images]
    
    total_total = len(pending_items)
    total_queue = len(queue)
    
    print(f"Total Pending Words: {total_total}")
    print(f"Already Generated: {len(existing_images)}")
    print(f"Remaining Queue: {total_queue}")
    print("-" * 30)

    if total_queue == 0:
        print("All images generated! Nothing to do.")
        return

    success_count = 0
    for index, item in enumerate(queue, 1):
        word = item['word']
        prompt = item['prompt']
        
        print(f"[{index}/{total_queue}] Generating image for: {word}... ", end="", flush=True)
        if generate_and_save(word, prompt, output_dir):
            print("Done.", flush=True)
            success_count += 1
            time.sleep(1)
        else:
            print("Failed.", flush=True)

    print(f"\nSession complete! Successfully generated {success_count} new images.")

if __name__ == "__main__":
    main()
