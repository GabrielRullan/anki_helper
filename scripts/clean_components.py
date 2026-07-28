import json
import urllib.request
import re
import sys
import time
import math

sys.stdout.reconfigure(encoding='utf-8')
ANKICONNECT_URL = 'http://127.0.0.1:8765'

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
        with urllib.request.urlopen(req, timeout=30) as response:
            res = json.loads(response.read().decode('utf-8'))
            if res.get('error'):
                print(f"Error in {action}: {res.get('error')}")
                return None
            return res.get('result')
    except Exception as e:
        print(f"Request failed in {action}: {e}")
        return None

def clean_value(val):
    if not val:
        return val
    # Replace [X|nidYYYY] with X
    return re.sub(r'\[([^|\]]+)\|nid\d+\]', r'\1', val)

def main():
    print("Checking connection to AnkiConnect...")
    version = request_anki("version")
    if not version:
        print("[ERROR] Could not connect to Anki. Please make sure Anki is open and AnkiConnect is installed.")
        sys.exit(1)
    print(f"Connected to Anki (version {version}).")

    deck_name = "Chinese::Char"
    print(f"Finding all notes in deck: '{deck_name}'...")
    note_ids = request_anki("findNotes", query=f'deck:"{deck_name}"')
    if not note_ids:
        print(f"No notes found in deck '{deck_name}'.")
        return
        
    print(f"Found {len(note_ids)} notes. Fetching fields...")
    notes_info = request_anki("notesInfo", notes=note_ids)
    
    notes_to_update = []
    for note in notes_info:
        note_id = note['noteId']
        fields = note['fields']
        if 'Components' not in fields:
            continue
            
        comp_val = fields['Components']['value']
        cleaned_val = clean_value(comp_val)
        
        if comp_val != cleaned_val:
            notes_to_update.append({
                "id": note_id,
                "fields": {
                    "Components": cleaned_val
                }
            })
            
    if not notes_to_update:
        print("No notes require updating in the Components field.")
        return
        
    print(f"Found {len(notes_to_update)} notes to update out of {len(note_ids)} total notes.")
    
    # We will update in batches to prevent UI freeze and large payloads
    batch_size = 50
    success_count = 0
    total_batches = math.ceil(len(notes_to_update) / batch_size)
    
    print("Starting updates...")
    for i in range(0, len(notes_to_update), batch_size):
        batch = notes_to_update[i:i+batch_size]
        actions = [
            {
                "action": "updateNoteFields",
                "params": {
                    "note": note
                }
            }
            for note in batch
        ]
        
        batch_num = (i // batch_size) + 1
        print(f"Applying batch {batch_num}/{total_batches}...", end=" ", flush=True)
        
        res = request_anki("multi", actions=actions)
        if res:
            success_count += len(batch)
            print("Success.")
        else:
            print("Failed batch update. Retrying individually for this batch...")
            batch_success = 0
            for note in batch:
                res_ind = request_anki("updateNoteFields", note=note)
                if res_ind is not None:
                    batch_success += 1
                    success_count += 1
            print(f"Batch {batch_num} individual success: {batch_success}/{len(batch)}")
            
        # Optional small sleep to avoid overwhelming Anki
        time.sleep(0.1)
        
    print(f"\nProcessing Complete!")
    print(f"Successfully updated {success_count} notes.")

if __name__ == '__main__':
    main()
