import os
import sys
import time
import re
from dotenv import load_dotenv
from google import genai

# Reconfigure stdout to use UTF-8 on Windows console
sys.stdout.reconfigure(encoding='utf-8')

# Add scripts directory to path to allow imports from generate_scenes_and_images
scripts_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(scripts_dir)

try:
    from generate_scenes_and_images import request_anki, generate_image_file
except ImportError:
    sys.path.append(os.path.dirname(scripts_dir))
    from scripts.generate_scenes_and_images import request_anki, generate_image_file

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
    
    # 2. Query all notes with tag 'n1_added' in Chinese::Char
    print("Searching for notes with tag 'n1_added' in Chinese::Char deck...")
    query = 'deck:"Chinese::Char" tag:n1_added'
    note_ids = request_anki("findNotes", query=query)
    
    if not note_ids:
        print("No notes found with tag 'n1_added' in Chinese::Char.")
        return
        
    notes_info = request_anki("notesInfo", notes=note_ids)
    
    # 3. Filter notes missing images
    missing_notes = []
    for note in notes_info:
        fields = note.get('fields', {})
        hz = fields.get('Hanzi', {}).get('value', '').strip()
        img = fields.get('Image', {}).get('value', '').strip()
        scene = fields.get('Scene', {}).get('value', '').strip()
        english = fields.get('English', {}).get('value', '').strip()
        nid = note.get('noteId')
        
        if not img or '<img' not in img.lower():
            missing_notes.append({
                'note_id': nid,
                'hanzi': hz,
                'english': english,
                'scene_text': scene
            })
            
    print(f"Found {len(missing_notes)} notes missing images.")
    if not missing_notes:
        print("All cards already have images! Nothing to generate.")
        return
        
    output_dir = os.path.join(workspace_dir := os.path.dirname(scripts_dir), "imagenes_vocabulario")
    os.makedirs(output_dir, exist_ok=True)
    
    # 4. Generate images and update notes
    success_count = 0
    for idx, item in enumerate(missing_notes, 1):
        hz = item['hanzi']
        nid = item['note_id']
        english = item['english']
        scene_text = item['scene_text']
        
        if not scene_text:
            print(f"[{idx}/{len(missing_notes)}] Skipping {hz} (no scene description available in note!).")
            continue
            
        print(f"[{idx}/{len(missing_notes)}] Illustrating {hz} (Scene: {scene_text[:60]}...):")
        
        # Clean english meaning to a single word keyword for the media filename
        meaning_keyword = re.sub(r'[^a-zA-Z]', '', english.split(',')[0].split(';')[0].strip()).lower()
        if not meaning_keyword:
            meaning_keyword = "char"
            
        media_filename = f"mbp_{hz}_{meaning_keyword}.png"
        
        # Generate image file (reuses generate_scenes_and_images.py logic)
        img_path = generate_image_file(hz, scene_text, client, output_dir)
        if not img_path:
            print(f"  [ERROR] Image generation failed for {hz}.")
            continue
            
        # Store media file in Anki
        print("  Storing in Anki media... ", end="", flush=True)
        try:
            res = request_anki("storeMediaFile", filename=media_filename, path=os.path.abspath(img_path))
            if res:
                print("Done.")
            else:
                print("Failed (returned empty).")
                continue
        except Exception as e:
            print(f"Failed to store media: {e}")
            continue
            
        # Update Image field in note
        image_html = f'<img src="{media_filename}">'
        print("  Updating Image field in note... ", end="", flush=True)
        try:
            request_anki("updateNoteFields", note={"id": nid, "fields": {"Image": image_html}})
            print("Success!")
            success_count += 1
        except Exception as e:
            print(f"Failed to update note field: {e}")
            
        # Wait a bit between calls to avoid rate limits
        time.sleep(15)
        
    print(f"\nCompleted! Generated and updated {success_count}/{len(missing_notes)} images.")
    
    # 5. Rebuild extraction and dashboard
    print("\nRebuilding data extraction and dashboard...")
    print("Running extract_anki_data.py...")
    os.system(f'python "{os.path.join(scripts_dir, "extract_anki_data.py")}"')
    print("Running generate_dashboard.py...")
    os.system(f'python "{os.path.join(scripts_dir, "generate_dashboard.py")}"')
    print("\nDashboard sync complete!")

if __name__ == "__main__":
    main()
