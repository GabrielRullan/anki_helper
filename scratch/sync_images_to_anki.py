import os
import sys
import json
import shutil
import urllib.request

# Reconfigure stdout to UTF-8
sys.stdout.reconfigure(encoding='utf-8')

ANKICONNECT_URL = 'http://127.0.0.1:8765'
ARTIFACT_DIR = r"C:\Users\gabri\.gemini\antigravity-ide\brain\2fd0281b-38c2-4e09-a3ab-92ccd2e80b48"
WORKSPACE_DIR = r"c:\Users\gabri\Documents\anki_helper"
OUTPUT_DIR = os.path.join(WORKSPACE_DIR, "imagenes_vocabulario")

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

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    if not os.path.exists(ARTIFACT_DIR):
        print(f"[ERROR] Artifact directory does not exist: {ARTIFACT_DIR}")
        return
        
    print(f"Scanning artifact directory: {ARTIFACT_DIR} for new sentence images...")
    
    files = [f for f in os.listdir(ARTIFACT_DIR) if f.startswith("sent_") and f.endswith(".png")]
    print(f"Found {len(files)} sentence images in artifact directory.")
    
    if not files:
        print("No images to sync.")
        return
        
    success_count = 0
    for file in files:
        src_path = os.path.join(ARTIFACT_DIR, file)
        
        # Parse note_id
        # file format: sent_{note_id}.png
        try:
            note_id = int(file.split("_")[1].split(".")[0])
        except Exception as e:
            print(f"Skipping file {file} (unable to parse note_id): {e}")
            continue
            
        dest_path = os.path.join(OUTPUT_DIR, file)
        
        print(f"Syncing card ID {note_id} using {file}...")
        
        # 1. Copy file to workspace's imagenes_vocabulario directory
        try:
            shutil.copy2(src_path, dest_path)
            print(f"  - Copied to {dest_path}")
        except Exception as e:
            print(f"  - [ERROR] Failed to copy to workspace: {e}")
            continue
            
        # 2. Upload to Anki media library
        print("  - Storing in Anki media... ", end="", flush=True)
        try:
            res = request_anki("storeMediaFile", filename=file, path=os.path.abspath(dest_path))
            if res:
                print("Done.")
            else:
                print("Failed (empty result).")
                continue
        except Exception as e:
            print(f"Failed: {e}")
            continue
            
        # 3. Update note fields in Anki
        image_html = f'<img src="{file}">'
        print("  - Updating note in Anki... ", end="", flush=True)
        try:
            res = request_anki("updateNoteFields", note={"id": note_id, "fields": {"Images": image_html}})
            print("Success!")
            success_count += 1
            
            # Remove from artifact directory to mark as processed
            os.remove(src_path)
        except Exception as e:
            print(f"Failed: {e}")
            
    print(f"\nSuccessfully synced {success_count} images to Anki.")
    
    if success_count > 0:
        print("\nRebuilding data extraction and dashboard...")
        scripts_dir = os.path.join(WORKSPACE_DIR, "scripts")
        extract_path = os.path.join(scripts_dir, "extract_anki_data.py")
        dashboard_path = os.path.join(scripts_dir, "generate_dashboard.py")
        
        print("Running extract_anki_data.py...")
        os.system(f'python "{extract_path}"')
        print("Running generate_dashboard.py...")
        os.system(f'python "{dashboard_path}"')
        print("\nDashboard rebuild complete!")

if __name__ == "__main__":
    main()
