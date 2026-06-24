import os
import sys
import json
import time
import urllib.request
import re
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Reconfigure stdout to use UTF-8 on Windows console
sys.stdout.reconfigure(encoding='utf-8')

ANKICONNECT_URL = 'http://127.0.0.1:8765'
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
                print(f"AnkiConnect Error: {res.get('error')}")
                return None
            return res.get('result')
    except Exception as e:
        print(f"AnkiConnect Request Failed: {e}")
        return None

def clean_html(text):
    """Helper to clean up HTML tags from Anki fields."""
    if not text:
        return ""
    # Replace breaks with space/newlines
    text = re.sub(r'<br\s*/?>', ' ', text)
    # Remove all other HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Replace HTML entities
    text = text.replace('&nbsp;', ' ').replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
    return text.strip()

def generate_visual_description(sentence, translation, client):
    """Ask Gemini to generate a simple visual description of the sentence."""
    prompt = f"""
Analyze this Chinese sentence and its translation:
Sentence: {sentence}
Translation: {translation}

We need a simple, concrete visual scene description in English representing the sentence.
It should be suitable for a Peanuts/Charlie Brown cartoon style illustration, focusing on a single character/action, with NO abstract concepts and NO text.
For example:
- For " Frog Kermit also wants to cultivate immortality", a good description would be "Frog Kermit wearing a monk robe sitting cross-legged in meditation on a small cloud."
- For "Time is money", a good description would be "A cartoon character running while holding a big clock and a bag with a dollar sign."

Provide ONLY a single, clean English sentence describing the visual scene. Do not include any other text, quotes, or explanation.
"""
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        desc = response.text.strip()
        # Clean any wrapping quotes
        if (desc.startswith('"') and desc.endswith('"')) or (desc.startswith("'") and desc.endswith("'")):
            desc = desc[1:-1].strip()
        return desc
    except Exception as e:
        print(f"Error generating visual description: {e}")
        return None

def generate_image_file(note_id, visual_description, client, output_dir):
    """Generate image using Imagen models and save locally."""
    filename = os.path.join(output_dir, f"sent_{note_id}.png")
    if os.path.exists(filename):
        return filename

    # Build illustration prompt
    prompt_text = (
        f"Minimalist Peanuts cartoon style illustration of: {visual_description}. "
        f"On a plain white background, simple lines, flat colors, centered, "
        f"no text, no letters, no words, no speech bubbles."
    )

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
                    time.sleep(15)
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
    
    # 1. Check Anki connection
    version = request_anki("version")
    if not version:
        print("[ERROR] Anki must be open and running with AnkiConnect enabled.")
        sys.exit(1)
    print(f"Connected to Anki (version {version}).")
    
    # 2. Query all notes in Chinese::Sent
    print("Searching for notes in 'Chinese::Sent' deck...")
    note_ids = request_anki("findNotes", query='deck:"Chinese::Sent"')
    if not note_ids:
        print("No notes found in deck 'Chinese::Sent'.")
        return
        
    notes_info = request_anki("notesInfo", notes=note_ids)
    
    # 3. Filter notes missing images
    missing_notes = []
    for note in notes_info:
        fields = note.get('fields', {})
        sentence = fields.get('Sentence', {}).get('value', '').strip()
        translation = fields.get('Translated_Sentence', {}).get('value', '').strip()
        images_val = fields.get('Images', {}).get('value', '').strip()
        nid = note.get('noteId')
        
        # Check if Images is empty or doesn't contain an <img> tag
        if not images_val or '<img' not in images_val.lower():
            missing_notes.append({
                'note_id': nid,
                'sentence': clean_html(sentence),
                'translation': clean_html(translation)
            })
            
    print(f"Total notes: {len(notes_info)}")
    print(f"Notes missing images: {len(missing_notes)}")
    
    if not missing_notes:
        print("All sentence cards already have images!")
        return
        
    scripts_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(os.path.dirname(scripts_dir), "imagenes_vocabulario")
    os.makedirs(output_dir, exist_ok=True)
    
    # 4. Generate images and update notes
    success_count = 0
    for idx, item in enumerate(missing_notes, 1):
        nid = item['note_id']
        sentence = item['sentence']
        translation = item['translation']
        
        print(f"\n[{idx}/{len(missing_notes)}] Sentence: {sentence}")
        print(f"    Translation: {translation}")
        
        # Step A: Generate description via Gemini
        print("    Generating visual description...", end=" ", flush=True)
        visual_desc = generate_visual_description(sentence, translation, client)
        if not visual_desc:
            print("Failed.")
            continue
        print(f"Done.\n    Description: {visual_desc}")
        
        # Step B: Generate image via Imagen
        media_filename = f"sent_{nid}.png"
        img_path = generate_image_file(nid, visual_desc, client, output_dir)
        if not img_path:
            print("    [ERROR] Image generation failed.")
            continue
            
        # Step C: Store media file in Anki
        print("    Storing in Anki media... ", end="", flush=True)
        try:
            res = request_anki("storeMediaFile", filename=media_filename, path=os.path.abspath(img_path))
            if res:
                print("Done.")
            else:
                print("Failed (returned empty).")
                continue
        except Exception as e:
            print(f"Failed: {e}")
            continue
            
        # Step D: Update Images field in note
        image_html = f'<img src="{media_filename}">'
        print("    Updating Images field... ", end="", flush=True)
        try:
            request_anki("updateNoteFields", note={"id": nid, "fields": {"Images": image_html}})
            print("Success!")
            success_count += 1
        except Exception as e:
            print(f"Failed: {e}")
            
        # Wait to avoid rate limits
        print("    Waiting 10 seconds before next card...")
        time.sleep(10)
        
    print(f"\nCompleted! Generated and updated {success_count}/{len(missing_notes)} images.")
    
    # 5. Rebuild extraction and dashboard
    print("\nRebuilding data extraction and dashboard...")
    try:
        extract_path = os.path.join(scripts_dir, "extract_anki_data.py")
        dashboard_path = os.path.join(scripts_dir, "generate_dashboard.py")
        
        print("Running extract_anki_data.py...")
        os.system(f'python "{extract_path}"')
        print("Running generate_dashboard.py...")
        os.system(f'python "{dashboard_path}"')
        print("\nDashboard sync complete!")
    except Exception as e:
        print(f"Error rebuilding dashboard: {e}")

if __name__ == "__main__":
    main()
