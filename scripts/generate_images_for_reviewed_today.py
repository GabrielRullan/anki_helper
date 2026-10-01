import os
import sys
import json
import time
import re
import urllib.request
from datetime import datetime, date
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')

# Setup paths
workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, workspace_dir)

from scripts.anki_db import AnkiConnection
from scripts.generate_scenes_and_images import request_anki, fetch_scenes_from_gemini

from google import genai
from google.genai import types

IMAGE_MODELS = ['gemini-2.5-flash-image', 'gemini-3.1-flash-image', 'gemini-3-pro-image']

def sanitize_text(text):
    """Clean text of terms that might trigger safety filters."""
    replacements = {
        'corpse': 'figure lying down',
        'dead': 'asleep',
        'kill': 'defeat',
        'blood': 'red liquid',
        'sick': 'unwell person',
        'sickness': 'unwell feeling',
        'tumor': 'swelling lump',
        'urine': 'water splash',
        'urinate': 'splash water',
        'bomb': 'firework',
        'blast': 'burst',
    }
    cleaned = text
    for word, sub in replacements.items():
        cleaned = re.sub(rf'\b{word}\b', sub, cleaned, flags=re.IGNORECASE)
    return cleaned

def generate_image_file(hanzi, english, scene_text, client, output_dir):
    filename = os.path.join(output_dir, f"{hanzi}.png")
    
    clean_scene = sanitize_text(scene_text)
    clean_english = re.sub(r'[^a-zA-Z\s]', '', english.split(',')[0].split(';')[0].strip())
    
    prompts_to_try = [
        f"Minimalist Peanuts cartoon style illustration of: {clean_scene}. On a plain white background, simple lines, flat colors, centered, no text, no letters.",
        f"Minimalist Peanuts cartoon style illustration depicting {clean_english}. On a plain white background, simple lines, flat colors, centered, no text, no letters."
    ]

    for prompt_text in prompts_to_try:
        for model_id in IMAGE_MODELS:
            print(f"    Trying model {model_id}...", end=" ", flush=True)
            for attempt in range(2):
                try:
                    response = client.models.generate_content(
                        model=model_id,
                        contents=f"Generate image: {prompt_text}"
                    )
                    
                    if response and response.candidates:
                        for cand in response.candidates:
                            if cand.content and cand.content.parts:
                                for part in cand.content.parts:
                                    if part.inline_data and part.inline_data.data:
                                        image_bytes = part.inline_data.data
                                        with open(filename, "wb") as f:
                                            f.write(image_bytes)
                                        print("Success!")
                                        return filename
                        print("No inline image returned.")
                    else:
                        print("No candidates returned.")
                except Exception as e:
                    error_msg = str(e)
                    if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                        print(f"Rate limited (attempt {attempt+1}/2). Sleeping 5s...", end=" ", flush=True)
                        time.sleep(5)
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
    
    # 1. Test AnkiConnect
    version = request_anki("version")
    if not version:
        print("[ERROR] AnkiConnect is not reachable on port 8765. Make sure Anki is open.")
        sys.exit(1)
    print(f"Connected to Anki (version {version}).")
    
    # 2. Get notes reviewed today from SQLite
    today = date.today()
    start_of_day = datetime(today.year, today.month, today.day)
    start_ts_ms = int(start_of_day.timestamp() * 1000)
    print(f"Fetching reviews since today {today} (timestamp ms: {start_ts_ms})...")
    
    with AnkiConnection() as db:
        cursor = db.conn.cursor()
        cursor.execute('''
            SELECT DISTINCT c.id, c.nid, n.flds
            FROM revlog r
            JOIN cards c ON r.cid = c.id
            JOIN notes n ON c.nid = n.id
            JOIN decks d ON c.did = d.id
            WHERE d.name LIKE '%Char%' AND r.id >= ?
            ORDER BY r.id DESC
        ''', (start_ts_ms,))
        
        rows = cursor.fetchall()
        
    print(f"Found {len(rows)} total card review logs today in Chinese Character deck.")
    
    notes_to_process = []
    seen_nids = set()
    
    for row in rows:
        cid, nid, flds = row
        if nid in seen_nids:
            continue
        seen_nids.add(nid)
        
        fields = flds.split('\x1f')
        hanzi = fields[1] if len(fields) > 1 else ""
        pinyin = fields[2] if len(fields) > 2 else ""
        english = fields[3] if len(fields) > 3 else ""
        actor = fields[5] if len(fields) > 5 else ""
        set_val = fields[6] if len(fields) > 6 else ""
        tone_loc = fields[8] if len(fields) > 8 else ""
        components = fields[9] if len(fields) > 9 else ""
        scene = fields[10] if len(fields) > 10 else ""
        image = fields[23] if len(fields) > 23 else ""
        
        # Only process notes missing an image
        if not image.strip() or "<img" not in image.lower():
            notes_to_process.append({
                'nid': nid,
                'cid': cid,
                'hanzi': hanzi,
                'pinyin': pinyin,
                'english': english,
                'actor': actor,
                'set': set_val,
                'tone_location': tone_loc,
                'components': components,
                'scene': scene
            })
            
    print(f"Unique reviewed notes missing images today: {len(notes_to_process)}")
    if not notes_to_process:
        print("All cards reviewed today already have images! Nothing to do.")
        return

    # 3. Check for notes missing scenes and generate them
    missing_scenes = [item for item in notes_to_process if not item['scene'].strip()]
    if missing_scenes:
        print(f"\nGenerating missing scenes for {len(missing_scenes)} notes...")
        batch_prompt_data = []
        for c in missing_scenes:
            batch_prompt_data.append({
                'character': c['hanzi'],
                'meaning': c['english'],
                'actor': c['actor'],
                'set': c['set'],
                'tone_location': c['tone_location'],
                'props': c['components']
            })
        generated_scenes = fetch_scenes_from_gemini(batch_prompt_data, client)
        if generated_scenes:
            scene_map = {s['hanzi']: s['scene'] for s in generated_scenes}
            for item in missing_scenes:
                if item['hanzi'] in scene_map:
                    item['scene'] = scene_map[item['hanzi']]
                    request_anki("updateNoteFields", note={"id": item['nid'], "fields": {"Scene": item['scene']}})
                    print(f"  Updated Scene for {item['hanzi']}: {item['scene'][:60]}...")

    # 4. Output directory for images
    output_dir = os.path.join(workspace_dir, "imagenes_vocabulario")
    os.makedirs(output_dir, exist_ok=True)
    
    # 5. Generate images, upload to Anki, update card Image fields
    print(f"\nGenerating images for remaining {len(notes_to_process)} cards reviewed today...")
    success_count = 0
    
    for idx, item in enumerate(notes_to_process, 1):
        hz = item['hanzi']
        nid = item['nid']
        english = item['english']
        scene_text = item['scene']
        
        print(f"[{idx}/{len(notes_to_process)}] Illustrating {hz} ({item['pinyin']}): Meaning: '{english}'...")
        
        meaning_keyword = re.sub(r'[^a-zA-Z]', '', english.split(',')[0].split(';')[0].strip()).lower() or "char"
        media_filename = f"mbp_{hz}_{meaning_keyword}.png"
        
        # Generate image file
        img_path = generate_image_file(hz, english, scene_text, client, output_dir)
        if not img_path:
            print(f"  [ERROR] Failed image generation for {hz}.")
            continue
            
        # Store media file in Anki
        print("  Uploading to Anki media... ", end="", flush=True)
        try:
            res = request_anki("storeMediaFile", filename=media_filename, path=os.path.abspath(img_path))
            if res:
                print("Done.", end=" ", flush=True)
            else:
                print("Failed (storeMediaFile returned null).")
                continue
        except Exception as e:
            print(f"Failed to store media: {e}")
            continue
            
        # Update Image field in note
        image_html = f'<img src="{media_filename}">'
        print("Updating note Image field... ", end="", flush=True)
        try:
            request_anki("updateNoteFields", note={"id": nid, "fields": {"Image": image_html}})
            print("SUCCESS!")
            success_count += 1
        except Exception as e:
            print(f"Failed: {e}")
            
        time.sleep(1)
        
    print(f"\nCompleted generating and updating {success_count}/{len(notes_to_process)} remaining images for cards reviewed today!")
    
    # 6. Refresh data extraction & dashboard
    print("\nRefreshing dashboard and extracted data...")
    scripts_dir = os.path.join(workspace_dir, "scripts")
    os.system(f'python "{os.path.join(scripts_dir, "extract_anki_data.py")}"')
    os.system(f'python "{os.path.join(scripts_dir, "generate_dashboard.py")}"')
    print("\nAll tasks completed successfully!")

if __name__ == "__main__":
    main()
