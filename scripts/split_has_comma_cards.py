import json
import urllib.request
import sys
import re
import time

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
        with urllib.request.urlopen(req, timeout=20) as response:
            res = json.loads(response.read().decode('utf-8'))
            if res.get('error'):
                raise Exception(res.get('error'))
            return res.get('result')
    except Exception as e:
        print(f"AnkiConnect Request Failed: {e}")
        return None

def main():
    print("Finding cards/notes with tag 'has_comma'...")
    note_ids = request_anki("findNotes", query="tag:has_comma")
    if not note_ids:
        print("No notes found with tag 'has_comma'.")
        return
        
    print(f"Found {len(note_ids)} notes to process.")
    notes_info = request_anki("notesInfo", notes=note_ids)
    
    split_count = 0
    cleaned_count = 0
    
    for idx, note in enumerate(notes_info, 1):
        note_id = note['noteId']
        fields = note['fields']
        word_val = fields.get('Word', {}).get('value', '').strip()
        
        # Clean HTML out of the word field just in case
        word_clean = re.sub(r'<[^>]+>', '', word_val).strip()
        
        print(f"\n[{idx}/{len(notes_info)}] Checking Note ID: {note_id} | Word: '{word_clean}'")
        
        # Check if there is a comma in the Word field (accepting both English ',' and Chinese '，')
        if ',' not in word_clean and '，' not in word_clean:
            print(f" -> No comma found in Word. Removing 'has_comma' tag...")
            request_anki("removeTags", notes=[note_id], tags="has_comma")
            cleaned_count += 1
            continue
            
        # Split on both English and Chinese commas
        parts = [p.strip() for p in re.split(r'[,，]+', word_clean) if p.strip()]
        if len(parts) <= 1:
            print(f" -> Word splits to <= 1 parts. Removing 'has_comma' tag...")
            request_anki("removeTags", notes=[note_id], tags="has_comma")
            cleaned_count += 1
            continue
            
        print(f" -> Detected {len(parts)} parts to separate: {parts}")
        
        # Get scheduling of the original card
        card_ids = note.get('cards', [])
        if not card_ids:
            print(" -> Error: Original note has no cards.")
            continue
            
        orig_card_id = card_ids[0]
        orig_card_info = request_anki("cardsInfo", cards=[orig_card_id])
        if not orig_card_info:
            print(" -> Error: Could not fetch original card info.")
            continue
            
        orig_info = orig_card_info[0]
        orig_queue = orig_info['queue']
        orig_due = orig_info['due']
        deck_name = orig_info['deckName']
        model_name = note['modelName']
        
        # Copy fields
        original_fields = {}
        for f_name, f_data in fields.items():
            original_fields[f_name] = f_data['value']
            
        # Prepare tags (remove 'has_comma' for single parts)
        new_tags = [t for t in note.get('tags', []) if t != 'has_comma']
        
        # Create duplicate cards for parts[1:]
        for part in parts[1:]:
            print(f"   -> Creating duplicate note for: '{part}'...")
            new_fields = original_fields.copy()
            new_fields['Word'] = part
            
            note_payload = {
                "deckName": deck_name,
                "modelName": model_name,
                "fields": new_fields,
                "options": {
                    "allowDuplicate": True
                },
                "tags": new_tags
            }
            
            new_note_id = request_anki("addNote", note=note_payload)
            if not new_note_id:
                print(f"      [ERROR] Failed to add note for '{part}'")
                continue
                
            print(f"      Success! New Note ID: {new_note_id}")
            
            # Match scheduling to original card
            new_note_info = request_anki("notesInfo", notes=[new_note_id])
            if new_note_info and new_note_info[0].get('cards'):
                new_card_id = new_note_info[0]['cards'][0]
                
                # If original was a review card (queue=2), sync the due date
                if orig_queue == 2:
                    # Set due to today first to retrieve today's absolute day number
                    request_anki("setDueDate", cards=[new_card_id], days="0")
                    new_card_info = request_anki("cardsInfo", cards=[new_card_id])
                    if new_card_info:
                        today = new_card_info[0]['due']
                        days_needed = orig_due - today
                        request_anki("setDueDate", cards=[new_card_id], days=str(days_needed))
                        print(f"      Scheduled new card as review due on absolute day {orig_due} (offset from today: {days_needed})")
                else:
                    print("      Original card is new/learning; new card remains in default new queue.")
            time.sleep(0.5)
            
        # Update original note to have the first part only and remove the 'has_comma' tag
        print(f"   -> Updating original note {note_id} to '{parts[0]}' and removing 'has_comma' tag...")
        request_anki("updateNoteFields", note={
            "id": note_id,
            "fields": {
                "Word": parts[0]
            }
        })
        request_anki("removeTags", notes=[note_id], tags="has_comma")
        split_count += 1
        
    print(f"\nProcessing Complete!")
    print(f" -> Successfully split {split_count} notes containing commas.")
    print(f" -> Removed 'has_comma' tag from {cleaned_count} notes with no commas.")

if __name__ == '__main__':
    main()
