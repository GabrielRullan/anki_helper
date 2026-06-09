import re
import os
import sys
import json
import urllib.request
import csv

# Reconfigure stdout to UTF-8
sys.stdout.reconfigure(encoding='utf-8')

ANKICONNECT_URL = 'http://127.0.0.1:8765'

def generate_csv(items, output_path):
    headers = ['Word', 'Grammar Point', 'Sentence', 'Translated Sentence', 'Definitions', 'Notes']
    with open(output_path, 'w', encoding='utf-8', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()
        for item in items:
            notes_parts = []
            if item['sub_label']:
                notes_parts.append(f"Grammar usage: {item['sub_label']}")
            if item['notes']:
                notes_parts.append(f"Explanation: {item['notes']}")
            combined_notes = "\n\n".join(notes_parts)
            writer.writerow({
                'Word': '',
                'Grammar Point': item['grammar_pattern'],
                'Sentence': item['chinese'],
                'Translated Sentence': item['english'],
                'Definitions': item['grammar_meaning'],
                'Notes': combined_notes
            })
    print(f"Successfully generated {output_path} with {len(items)} grammar rows matching Migaku fields.")

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
                raise Exception(res.get('error'))
            return res.get('result')
    except Exception as e:
        print(f"API Request Failed for action '{action}': {e}")
        raise

def parse_semana_md(filepath):
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
        
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Split content by markdown headers "### "
    sections = re.split(r'\n### ', content)
    grammar_items = []
    
    for section in sections[1:]:
        lines = section.strip().split('\n')
        if not lines:
            continue
            
        header_line = lines[0].strip()
        header_match = re.match(r'^(\d+)\.\s*(.*)', header_line)
        if header_match:
            gid = header_match.group(1)
            rest = header_match.group(2).strip()
            if rest.endswith(')'):
                last_open = rest.rfind('(')
                if last_open != -1:
                    gtitle = rest[:last_open].strip()
                    gmeaning_raw = rest[last_open+1:-1].strip()
                    if '/' in gmeaning_raw:
                        gmeaning = gmeaning_raw.split('/')[-1].strip()
                    else:
                        gmeaning = gmeaning_raw
                else:
                    gtitle = rest
                    gmeaning = ""
            else:
                gtitle = rest
                gmeaning = ""
        else:
            gid = ""
            gtitle = header_line
            gmeaning = ""
            
        es_list = []
        en_list = []
        zh_list = []
        notes = []
        
        for line in lines[1:]:
            line = line.strip()
            if not line:
                continue
                
            es_match = re.match(r'^\*\s*\*\*ES(?:\s*\((.*?)\))?:\*\*\s*(.*)', line)
            en_match = re.match(r'^\*\s*\*\*EN(?:\s*\((.*?)\))?:\*\*\s*(.*)', line)
            zh_match = re.match(r'^\*\s*\*\*ZH(?:\s*\((.*?)\))?:\*\*\s*(.*)', line)
            note_match = re.match(r'^\*\s*\*Note:\s*(.*?)\*', line)
            
            if es_match:
                sub_label = es_match.group(1) or ""
                text = es_match.group(2).strip()
                es_list.append((sub_label, text))
            elif en_match:
                sub_label = en_match.group(1) or ""
                text = en_match.group(2).strip()
                en_list.append((sub_label, text))
            elif zh_match:
                sub_label = zh_match.group(1) or ""
                text = zh_match.group(2).strip()
                zh_list.append((sub_label, text))
            elif note_match:
                notes.append(note_match.group(1).strip())
            elif line.startswith('*') and ('Note:' in line or 'note:' in line):
                notes.append(line.replace('*', '').strip())
                
        n_examples = min(len(es_list), len(en_list), len(zh_list))
        
        if len(es_list) != len(en_list) or len(en_list) != len(zh_list):
            print(f"Warning in Lesson {gid}: count mismatch (ES:{len(es_list)}, EN:{len(en_list)}, ZH:{len(zh_list)})")
            
        common_notes = "; ".join(notes)
        
        for i in range(n_examples):
            es_sub, es_text = es_list[i]
            en_sub, en_text = en_list[i]
            zh_sub, zh_text = zh_list[i]
            
            sub_label = en_sub or zh_sub or es_sub
            
            grammar_items.append({
                'id': gid,
                'grammar_pattern': gtitle,
                'grammar_meaning': gmeaning,
                'sub_label': sub_label,
                'spanish': es_text,
                'english': en_text,
                'chinese': zh_text,
                'notes': common_notes
            })
            
    return grammar_items

def normalize_sentence(sentence):
    if not sentence:
        return ""
    # Strip common markdown bold markers, spaces, and punctuation to match sentences reliably
    clean = sentence.replace("**", "").replace("强", "").strip()
    return clean

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(base_dir, "..", "lessons", "semana.md")
    
    if not os.path.exists(input_path):
        print(f"Error: {input_path} does not exist.")
        sys.exit(1)
        
    print(f"Parsing grammar from {input_path}...")
    try:
        items = parse_semana_md(input_path)
    except Exception as e:
        print(f"Failed to parse grammar markdown: {e}")
        sys.exit(1)
        
    print(f"Parsed {len(items)} grammar examples.")
    
    print("Connecting to Anki via AnkiConnect...")
    try:
        # Check if target deck exists (supporting both 'Migaku' and 'Word_Sentence')
        decks = request_anki("deckNames")
        deck_name = "Migaku"
        if "Migaku" not in decks:
            if "Word_Sentence" in decks:
                deck_name = "Word_Sentence"
            else:
                print(f"Error: Target deck ('Migaku' or 'Word_Sentence') not found in Anki. Available decks: {decks}")
                sys.exit(1)
            
        # Check if Migaku Sentence note type exists
        models = request_anki("modelNames")
        if "Migaku Sentence" not in models:
            print("Error: 'Migaku Sentence' note type not found in Anki.")
            sys.exit(1)
            
        # Fetch existing notes in target deck to build duplicate check set
        print(f"Fetching existing notes from Anki deck '{deck_name}' for duplicate checking...")
        note_ids = request_anki("findNotes", query=f'deck:"{deck_name}" "note:Migaku Sentence"')
        notes_info = request_anki("notesInfo", notes=note_ids)
        
        existing_sentences = {}
        for note in notes_info:
            fields = note.get('fields', {})
            sentence_field = fields.get('Sentence', {}).get('value', '').strip()
            if sentence_field:
                existing_sentences[normalize_sentence(sentence_field)] = note.get('noteId')
                
        print(f"Found {len(existing_sentences)} existing sentences in the '{deck_name}' deck.")
        
        # Categorize notes into additions and updates
        notes_to_add = []
        notes_to_update = []
        
        for item in items:
            chinese_sentence = item['chinese']
            normalized = normalize_sentence(chinese_sentence)
            
            notes_parts = []
            if item['sub_label']:
                notes_parts.append(f"Grammar usage: {item['sub_label']}")
            if item['notes']:
                notes_parts.append(f"Explanation: {item['notes']}")
            combined_notes = "\n\n".join(notes_parts)
            
            row_data = {
                'Word': "\u200b", # Zero-width space to bypass empty first field constraint
                'Sentence': chinese_sentence,
                'Translated Sentence': item['english'],
                'Definitions': item['grammar_meaning'],
                'Notes': combined_notes,
                'Grammar Point': item['grammar_pattern']
            }
            
            if normalized in existing_sentences:
                note_id = existing_sentences[normalized]
                notes_to_update.append((note_id, row_data))
            else:
                notes_to_add.append(row_data)
                
        # Add new notes
        added_count = 0
        if notes_to_add:
            print(f"Pushing {len(notes_to_add)} new grammar phrases to Anki...")
            for row in notes_to_add:
                note_payload = {
                    "deckName": deck_name,
                    "modelName": "Migaku Sentence",
                    "fields": row,
                    "options": {
                        "allowDuplicate": True
                    },
                    "tags": ["grammar", "hsk4"]
                }
                try:
                    note_id = request_anki("addNote", note=note_payload)
                    if note_id:
                        added_count += 1
                        print(f"Added note: {row['Sentence'][:30]}... (ID: {note_id})")
                except Exception as e:
                    print(f"Failed to add note '{row['Sentence'][:20]}...': {e}")
        else:
            print("No new grammar phrases to add.")
            
        # Update existing notes
        updated_count = 0
        if notes_to_update:
            print(f"Updating {len(notes_to_update)} existing grammar phrases to clear 'Word' and sync all fields...")
            for note_id, row in notes_to_update:
                update_payload = {
                    "note": {
                        "id": note_id,
                        "fields": row
                    }
                }
                try:
                    request_anki("updateNoteFields", **update_payload)
                    updated_count += 1
                except Exception as e:
                    print(f"Failed to update note ID {note_id}: {e}")
        else:
            print("No existing notes to update.")
                
        print(f"\nSync complete! Successfully added {added_count} and updated {updated_count} notes in your Migaku deck.")
        
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
