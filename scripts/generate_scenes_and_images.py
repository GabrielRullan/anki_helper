import os
import sys
import json
import time
import urllib.request
import re
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel

# Reconfigure stdout to use UTF-8 on Windows console
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
        with urllib.request.urlopen(req, timeout=15) as response:
            res = json.loads(response.read().decode('utf-8'))
            if res.get('error'):
                print(f"AnkiConnect Error: {res.get('error')}")
                return None
            return res.get('result')
    except Exception as e:
        print(f"AnkiConnect Request Failed: {e}")
        return None

class SceneItem(BaseModel):
    hanzi: str
    scene: str

class SceneList(BaseModel):
    scenes: list[SceneItem]

def fetch_scenes_from_gemini(batch_chars, client):
    prompt = f"""
Create a memorable, single-sentence mnemonic story (Scene) for each of the following Chinese characters.
Each scene must naturally integrate:
- The Actor (who performs the action)
- The Set (the visual backdrop or set element)
- The Tone-Location (where the action takes place)
- The Props (visual elements representing the components of the character)
- The English Meaning of the character

Format the story in English. Keep it concise, dramatic, funny, or vivid.

Input character details:
{json.dumps(batch_chars, ensure_ascii=False, indent=2)}
"""
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=SceneList
            )
        )
        data = json.loads(response.text.strip())
        return data.get('scenes', [])
    except Exception as e:
        print(f"Error fetching scenes: {e}")
        return None

def generate_image_file(hanzi, scene_text, client, output_dir):
    filename = os.path.join(output_dir, f"{hanzi}.png")
    if os.path.exists(filename):
        return filename

    # Build illustration prompt
    prompt_text = f"Minimalist Peanuts cartoon style illustration of: {scene_text}. On a plain white background, simple lines, flat colors, centered, no text, no letters."

    for model_id in MODELS_TO_TRY:
        print(f"  Trying model {model_id}...", end=" ", flush=True)
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

def main():
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("[ERROR] GOOGLE_API_KEY not found in .env.")
        sys.exit(1)
        
    client = genai.Client(api_key=api_key)
    
    # 1. Load details of characters to process
    details_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "n1_chars_for_scenes.json")
    if not os.path.exists(details_path):
        print(f"[ERROR] Characters for scenes file not found at {details_path}.")
        sys.exit(1)
        
    with open(details_path, 'r', encoding='utf-8') as f:
        chars_data = json.load(f)
        
    print(f"Loaded {len(chars_data)} characters for scene and image generation.")
    
    # 2. Check Anki connection
    version = request_anki("version")
    if not version:
        print("[ERROR] Anki must be open and running with AnkiConnect enabled.")
        sys.exit(1)
    print(f"Connected to Anki (version {version}).")
    
    # 3. Generate Scene descriptions in batches of 35
    batch_size = 35
    generated_scenes_map = {}
    print("\nGenerating scene stories using Gemini...")
    for i in range(0, len(chars_data), batch_size):
        batch = chars_data[i:i+batch_size]
        # Clean data for prompt to save tokens and focus prompt
        batch_prompt_data = []
        for c in batch:
            batch_prompt_data.append({
                'character': c['hanzi'],
                'meaning': c['english'],
                'actor': c['actor'],
                'set': c['set'],
                'tone_location': c['tone_location'],
                'props': c['components']
            })
            
        scenes = fetch_scenes_from_gemini(batch_prompt_data, client)
        if scenes:
            for s in scenes:
                generated_scenes_map[s['hanzi']] = s['scene']
            print(f"Processed batch {i // batch_size + 1} ({len(generated_scenes_map)}/{len(chars_data)} characters).")
        time.sleep(2)
        
    # 4. Update Scene fields in Anki
    print("\nUpdating Scene fields in Anki...")
    notes_to_update = []
    for item in chars_data:
        hz = item['hanzi']
        nid = item['note_id']
        scene_text = generated_scenes_map.get(hz, "")
        if scene_text:
            notes_to_update.append({
                "id": nid,
                "fields": {
                    "Scene": scene_text
                }
            })
            
    # Apply scene updates in batches of 20
    for i in range(0, len(notes_to_update), 20):
        sub_batch = notes_to_update[i:i+20]
        for note_update in sub_batch:
            request_anki("updateNoteFields", note=note_update)
        print(f"Applied scene updates: {min(i+20, len(notes_to_update))}/{len(notes_to_update)}")
        
    # 5. Generate Images, upload to Anki, and update Image field
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "imagenes_vocabulario")
    os.makedirs(output_dir, exist_ok=True)
    
    print("\nGenerating card illustrations and uploading to Anki...")
    success_images = 0
    for idx, item in enumerate(chars_data, 1):
        hz = item['hanzi']
        nid = item['note_id']
        english = item['english']
        scene_text = generated_scenes_map.get(hz, "")
        
        if not scene_text:
            print(f"[{idx}/{len(chars_data)}] Skipping {hz} (no scene description available).")
            continue
            
        print(f"[{idx}/{len(chars_data)}] Illustrating {hz} (Scene: {scene_text[:50]}...):")
        
        # Clean english meaning to a single word keyword for the media filename
        meaning_keyword = re.sub(r'[^a-zA-Z]', '', english.split(',')[0].split(';')[0].strip()).lower()
        if not meaning_keyword:
            meaning_keyword = "char"
            
        media_filename = f"mbp_{hz}_{meaning_keyword}.png"
        
        # Generate image file
        img_path = generate_image_file(hz, scene_text, client, output_dir)
        if not img_path:
            print(f"  [ERROR] Image generation failed for {hz}.")
            continue
            
        # Store media file in Anki
        print("  Storing in Anki media... ", end="", flush=True)
        try:
            request_anki("storeMediaFile", filename=media_filename, path=os.path.abspath(img_path))
            print("Done.")
        except Exception as e:
            print(f"Failed to store media: {e}")
            continue
            
        # Update Image field in note
        image_html = f'<img src="{media_filename}">'
        print("  Updating Image field... ", end="", flush=True)
        try:
            request_anki("updateNoteFields", note={"id": nid, "fields": {"Image": image_html}})
            print("Success!")
            success_images += 1
        except Exception as e:
            print(f"Failed to update note field: {e}")
            
        # Wait between images to avoid rate limits
        time.sleep(3)
        
    print(f"\nCompleted! Generated scenes for {len(notes_to_update)} cards, and images for {success_images} cards.")
    
    # 6. Rebuild extraction and dashboard
    print("\nRebuilding data extraction and dashboard...")
    scripts_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Run extract_anki_data.py
    os.system(f'python "{os.path.join(scripts_dir, "extract_anki_data.py")}"')
    
    # Run generate_dashboard.py
    os.system(f'python "{os.path.join(scripts_dir, "generate_dashboard.py")}"')
    
    print("\nDashboard sync complete!")

if __name__ == "__main__":
    main()
