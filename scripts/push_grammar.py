import csv
import os
import json
import urllib.request
import sys

# Reconfigure stdout to UTF-8
sys.stdout.reconfigure(encoding='utf-8')

ANKICONNECT_URL = 'http://localhost:8765'

def request(action, **params):
    payload = {"action": action, "version": 6}
    if params:
        payload["params"] = params
    
    req = urllib.request.Request(
        ANKICONNECT_URL, 
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            res = json.loads(response.read().decode('utf-8'))
            if res.get('error'):
                raise Exception(res.get('error'))
            return res.get('result')
    except Exception as e:
        print(f"API Request Failed for action '{action}': {e}")
        raise

def normalize_sentence(sentence):
    if not sentence:
        return ""
    # Strip common markdown bold markers, spaces, and punctuation to match sentences reliably
    clean = sentence.replace("**", "").replace("强", "").strip()
    return clean

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(base_dir, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "grammar_import.csv"))
    
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} does not exist. Please run 'python import_grammar.py' first.")
        sys.exit(1)
        
    print("Connecting to Anki via AnkiConnect...")
    try:
        # Check if target deck exists (supporting both 'Migaku' and 'Word_Sentence')
        decks = request("deckNames")
        deck_name = "Migaku"
        if "Migaku" not in decks:
            if "Word_Sentence" in decks:
                deck_name = "Word_Sentence"
            else:
                print(f"Error: Target deck ('Migaku' or 'Word_Sentence') not found in Anki. Available decks: {decks}")
                sys.exit(1)
            
        # Check if Migaku Sentence note type exists
        models = request("modelNames")
        if "Migaku Sentence" not in models:
            print("Error: 'Migaku Sentence' note type not found in Anki.")
            sys.exit(1)
            
        # Fetch existing notes in target deck to build duplicate check set
        print(f"Fetching existing notes from Anki deck '{deck_name}' for duplicate checking...")
        note_ids = request("findNotes", query=f'deck:"{deck_name}" "note:Migaku Sentence"')
        notes_info = request("notesInfo", notes=note_ids)
        
        existing_sentences = {}
        for note in notes_info:
            fields = note.get('fields', {})
            sentence_field = fields.get('Sentence', {}).get('value', '').strip()
            if sentence_field:
                existing_sentences[normalize_sentence(sentence_field)] = note.get('noteId')
                
        print(f"Found {len(existing_sentences)} existing sentences in the '{deck_name}' deck.")
        
        # Read the CSV and categorize notes into additions and updates
        notes_to_add = []
        notes_to_update = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                sentence = row.get('Sentence', '').strip()
                normalized = normalize_sentence(sentence)
                
                if normalized in existing_sentences:
                    note_id = existing_sentences[normalized]
                    notes_to_update.append((note_id, row))
                else:
                    notes_to_add.append(row)
                    
        # Add new notes
        added_count = 0
        if notes_to_add:
            print(f"Pushing {len(notes_to_add)} new grammar phrases to Anki...")
            for row in notes_to_add:
                note_payload = {
                    "deckName": deck_name,
                    "modelName": "Migaku Sentence",
                    "fields": {
                        "Word": row.get('Word', '').strip() or "\u200b",
                        "Sentence": row.get('Sentence', ''),
                        "Translated Sentence": row.get('Translated Sentence', ''),
                        "Definitions": row.get('Definitions', ''),
                        "Notes": row.get('Notes', ''),
                        "Grammar Point": row.get('Grammar Point', '')
                    },
                    "options": {
                        "allowDuplicate": True
                    },
                    "tags": ["grammar", "hsk4"]
                }
                try:
                    note_id = request("addNote", note=note_payload)
                    if note_id:
                        added_count += 1
                        print(f"Added note: {row.get('Sentence', '')[:30]}... (ID: {note_id})")
                except Exception as e:
                    print(f"Failed to add note '{row.get('Sentence', '')[:20]}...': {e}")
        else:
            print("No new grammar phrases to add.")
            
        # Update existing notes to ensure Word is empty and Spanish is removed from Notes
        updated_count = 0
        if notes_to_update:
            print(f"Updating {len(notes_to_update)} existing grammar phrases to clear 'Word' and sync all fields...")
            for note_id, row in notes_to_update:
                update_payload = {
                    "note": {
                        "id": note_id,
                        "fields": {
                            "Word": "\u200b",  # Zero-width space to bypass empty first field constraint
                            "Sentence": row.get('Sentence', ''),
                            "Translated Sentence": row.get('Translated Sentence', ''),
                            "Definitions": row.get('Definitions', ''),
                            "Notes": row.get('Notes', ''),
                            "Grammar Point": row.get('Grammar Point', '')
                        }
                    }
                }
                try:
                    request("updateNoteFields", **update_payload)
                    updated_count += 1
                except Exception as e:
                    print(f"Failed to update note ID {note_id}: {e}")
        else:
            print("No existing notes to update.")
                
        print(f"\nPush complete! Successfully added {added_count} and updated {updated_count} notes in your Migaku deck.")
        
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
