import os
import json
import time
import re
from dotenv import load_dotenv
import vertexai
from vertexai.preview.vision_models import ImageGenerationModel

# 1. Load configuration
load_dotenv()
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

if not PROJECT_ID or PROJECT_ID == "your-project-id":
    print("Error: GOOGLE_CLOUD_PROJECT not set in .env file.")
    exit(1)

# 2. Initialize Vertex AI (Uses ADC from gcloud auth application-default login)
vertexai.init(project=PROJECT_ID, location=LOCATION)
MODEL_ID = "imagen-3.0-generate-002"
model = ImageGenerationModel.from_pretrained(MODEL_ID)

def generate_and_save(word, prompt_text, output_dir):
    filename = os.path.join(output_dir, f"{word}.png")
    
    if os.path.exists(filename):
        print(f"Skipping {word}, image already exists.")
        return True

    print(f"Generating image for {word} via Vertex AI...")
    
    try:
        response = model.generate_images(
            prompt=prompt_text,
            number_of_images=1,
            aspect_ratio="1:1",
            add_watermark=False # Optional
        )
        
        for image in response.images:
            image.save(location=filename, include_generation_parameters=False)
            print(f"Successfully saved {filename}")
            return True
            
    except Exception as e:
        print(f"Error generating {word}: {e}")
        if "429" in str(e):
            print("Rate limit hit. Waiting 60 seconds...")
            time.sleep(60)
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
    for item in queue:
        word = item['word']
        prompt = item['prompt']
        
        if generate_and_save(word, prompt, output_dir):
            success_count += 1
            # Pause to avoid aggressive rate limiting
            time.sleep(1)

    print(f"\nDone! Successfully processed {success_count} images.")

if __name__ == "__main__":
    main()
