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

def get_field_val(note, field_name):
    fields = note.get('fields', {})
    for k, v in fields.items():
        if k.lower() == field_name.lower():
            return v.get('value', '').strip()
    return ''

def main():
    print("Checking connection to AnkiConnect...")
    version = request_anki("version")
    if not version:
        print("[ERROR] Could not connect to Anki. Make sure Anki is open and AnkiConnect is active.")
        sys.exit(1)
    print(f"Connected to Anki (version {version}).")

    char_deck = "Chinese::Char"
    word_deck = "Chinese::Words"
    
    print(f"Fetching character notes from deck '{char_deck}'...")
    char_ids = request_anki("findNotes", query=f'deck:"{char_deck}"')
    if not char_ids:
        print(f"No notes found in character deck '{char_deck}'")
        return
    char_notes = request_anki("notesInfo", notes=char_ids)
    
    # Map each Hanzi/Simplified character to its note ID
    char_to_nid = {}
    for note in char_notes:
        nid = note['noteId']
        hanzi = get_field_val(note, 'Hanzi')
        simp = get_field_val(note, 'Simplified')
        if hanzi:
            char_to_nid[hanzi] = nid
        if simp and simp != hanzi:
            char_to_nid[simp] = nid
            
    print(f"Mapped {len(char_to_nid)} unique characters from Chinese::Char.")
    
    print(f"Fetching word notes from deck '{word_deck}'...")
    word_ids = request_anki("findNotes", query=f'deck:"{word_deck}"')
    if not word_ids:
        print(f"No notes found in word deck '{word_deck}'")
        return
    word_notes = request_anki("notesInfo", notes=word_ids)
    
    notes_to_update = []
    
    for note in word_notes:
        nid = note['noteId']
        word = get_field_val(note, 'Word')
        # Strip HTML from word
        word_clean = re.sub(r'<[^>]+>', '', word).strip()
        
        # We only look for notes where the "Characters" field is empty
        chars_val = get_field_val(note, 'Characters')
        if not chars_val:
            # Generate links for characters in the word
            linked_chars = []
            for char in word_clean:
                # Check if it's a Chinese character and in our map
                if '\u4e00' <= char <= '\u9fff':
                    if char in char_to_nid:
                        linked_chars.append(f"[{char}|nid{char_to_nid[char]}]")
                    else:
                        linked_chars.append(char)
                else:
                    linked_chars.append(char)
            new_chars_val = "".join(linked_chars)
            
            if new_chars_val:
                notes_to_update.append({
                    "id": nid,
                    "fields": {
                        "Characters": new_chars_val
                    }
                })
                
    if not notes_to_update:
        print("No notes require updating (all notes already have 'Characters' populated).")
        return
        
    print(f"Found {len(notes_to_update)} notes in Chinese::Words to populate with linked characters.")
    
    # We will update in batches
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
            
        time.sleep(0.1)
        
    print(f"\nProcessing Complete!")
    print(f"Successfully updated {success_count} word notes.")

if __name__ == '__main__':
    main()
