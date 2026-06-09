import os
import re
import sys
import io
import time
import argparse
import json
from dotenv import load_dotenv

# Fix terminal encoding issues
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Load environment configuration
load_dotenv()

# Predefined models to try in Developer API mode
MODELS_TO_TRY = [
    'imagen-4.0-fast-generate-001',
    'imagen-4.0-generate-001',
    'imagen-4.0-ultra-generate-001'
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

def parse_new_words(file_path):
    """
    Parses new_words.md using a robust line-by-line approach to extract
    pending words and their visual prompts.
    """
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return []

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    try:
        parts = content.split('## 🟡 Pendiente de incluir')
        pendiente_section = parts[-1].split('## 🔴 Suelto')[0]
    except IndexError:
        print("Error: Could not find '## 🟡 Pendiente de incluir' or '## 🔴 Suelto' sections in markdown.")
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
            current_item = {
                'word': word,
                'prompt': ""
            }
            continue
            
        if current_item:
            prompt_match = re.match(r'^\s*[-*]\s*(?:\*\*|\*|_|__)Prompt:(?:\*\*|\*|_|__)\s*(.+)', line)
            if prompt_match:
                current_item['prompt'] = prompt_match.group(1).strip()
                continue

    if current_item:
        items.append(current_item)
        
    # Filter only those that have prompts
    return [item for item in items if item['prompt']]

def generate_image_developer_api(word, prompt_text, filename, client):
    for model_id in MODELS_TO_TRY:
        print(f"Using model {model_id}...", end=" ", flush=True)
        attempts = 3
        for attempt in range(attempts):
            try:
                response = client.models.generate_images(
                    model=model_id,
                    prompt=prompt_text,
                    config={'number_of_images': 1, 'output_mime_type': 'image/png', 'aspect_ratio': '1:1'}
                )
                
                if response and response.generated_images:
                    image_bytes = response.generated_images[0].image.image_bytes
                    with open(filename, "wb") as f:
                        f.write(image_bytes)
                    return True
                else:
                    msg = f"Warning: {model_id} returned no images (safety filter?)"
                    log_error(word, prompt_text, msg)
                    break # Try next model
                    
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
                    break # Try next model
    return False

def generate_image_vertex_ai(word, prompt_text, filename):
    try:
        import vertexai
        from vertexai.preview.vision_models import ImageGenerationModel
    except ImportError:
        print("\n[ERROR] vertexai SDK not installed. Run 'pip install google-cloud-aiplatform'")
        return False

    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    if not project_id:
        print("\n[ERROR] GOOGLE_CLOUD_PROJECT env var not set.")
        return False

    print(f"Using Vertex AI project '{project_id}'...", end=" ", flush=True)
    try:
        vertexai.init(project=project_id, location=location)
        model = ImageGenerationModel.from_pretrained("imagen-3.0-generate-002")
        response = model.generate_images(
            prompt=prompt_text,
            number_of_images=1,
            aspect_ratio="1:1",
            add_watermark=False
        )
        if response and response.images:
            response.images[0].save(location=filename, include_generation_parameters=False)
            return True
        else:
            print("No images returned.", end=" ", flush=True)
            return False
    except Exception as e:
        print(f"Vertex AI Error: {e}", end=" ", flush=True)
        log_error(word, prompt_text, str(e))
        return False

def main():
    parser = argparse.ArgumentParser(description="Generate vocabulary illustration images standalone.")
    parser.add_argument("--vertex", action="store_true", help="Use Google Cloud Vertex AI instead of Gemini Developer API")
    args = parser.parse_args()

    workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    new_words_path = os.path.join(workspace_dir, "new_words.md")
    output_dir = os.path.join(workspace_dir, "imagenes_vocabulario")
    os.makedirs(output_dir, exist_ok=True)

    print("Parsing new_words.md...")
    pending_items = parse_new_words(new_words_path)
    
    if not pending_items:
        print("No pending words with prompts found.")
        return
        
    print(f"Found {len(pending_items)} pending words with prompts.")
    
    # Filter out already existing images
    existing_images = {os.path.splitext(f)[0] for f in os.listdir(output_dir) if f.endswith('.png')}
    queue = [p for p in pending_items if p['word'] not in existing_images]
    
    print(f"Total Pending Words: {len(pending_items)}")
    print(f"Already Generated: {len(existing_images)}")
    print(f"Remaining Queue: {len(queue)}")
    print("-" * 30)

    if not queue:
        print("All images generated! Nothing to do.")
        return

    # Initialize client if in Developer API mode
    client = None
    if not args.vertex:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key or api_key == "YOUR_API_KEY_HERE":
            print("[ERROR] GOOGLE_API_KEY not found in .env file.")
            sys.exit(1)
        from google import genai
        client = genai.Client(api_key=api_key)

    success_count = 0
    for index, item in enumerate(queue, 1):
        word = item['word']
        prompt = item['prompt']
        filename = os.path.join(output_dir, f"{word}.png")
        
        print(f"[{index}/{len(queue)}] Illustrating: {word}... ", end="", flush=True)
        
        if args.vertex:
            success = generate_image_vertex_ai(word, prompt, filename)
        else:
            success = generate_image_developer_api(word, prompt, filename, client)
            
        if success:
            print("Success!")
            success_count += 1
            time.sleep(1)
        else:
            print("Failed.")

    print(f"\nDone! Successfully generated {success_count} images.")

if __name__ == "__main__":
    main()
