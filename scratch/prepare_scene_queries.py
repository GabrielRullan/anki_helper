import sys
import os
import json
import re

sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(r"c:\Users\gabri\Documents\antigravity\anki\scripts")

from anki_db import AnkiConnection

def get_field_val(note, field_name):
    fields = note.get('fields', {})
    for k, v in fields.items():
        if k.lower() == field_name.lower():
            if isinstance(v, dict):
                return v.get('value', '').strip()
            return str(v).strip()
    return ''

def main():
    try:
        with AnkiConnection(profile_name="Main") as anki:
            char_deck = anki.best_match_deck(["Chinese::Char", "Chinese\x1fChar", "Characters"])
            prop_deck = anki.best_match_deck(["Chinese::Props", "Chinese\x1fProps"])
            
            char_notes = anki.get_notes_in_deck(char_deck)
            prop_notes = anki.get_notes_in_deck(prop_deck)
            
            # Build prop lookup: component -> prop_meaning
            prop_lookup = {}
            for note in prop_notes:
                comp = get_field_val(note, 'Component')
                prop = get_field_val(note, 'Prop')
                if comp and prop:
                    prop_lookup[comp] = prop
            
            # Find n1_added characters
            n1_added = []
            for note in char_notes:
                tags = note.get('tags', [])
                if 'n1_added' in tags:
                    n1_added.append(note)
                    
            print(f"Found {len(n1_added)} characters with tag 'n1_added'.")
            
            # Extract details
            extracted_chars_info = []
            for note in n1_added:
                hanzi = get_field_val(note, 'Hanzi')
                pinyin = get_field_val(note, 'Pinyin')
                english = get_field_val(note, 'English')
                actor = get_field_val(note, 'Actor')
                c_set = get_field_val(note, 'Set')
                tone_loc = get_field_val(note, 'Tone-Location')
                
                # Parse components out of link format or list
                comp_raw = get_field_val(note, 'Components')
                # Links are of the form [Comp|nid...]
                components = re.findall(r'\[([^|\]]+)(?:\|nid\d+)?\]', comp_raw)
                if not components:
                    # Fallback if plain text
                    components = [c.strip() for c in comp_raw.split(',') if c.strip()]
                    
                # Look up props
                props_with_meanings = []
                for c in components:
                    meaning = prop_lookup.get(c, c)
                    props_with_meanings.append(f"{c} ({meaning})")
                    
                extracted_chars_info.append({
                    'note_id': note['id'],
                    'hanzi': hanzi,
                    'pinyin': pinyin,
                    'english': english,
                    'actor': actor,
                    'set': c_set,
                    'tone_location': tone_loc,
                    'components': props_with_meanings
                })
                
            # Print a few samples
            print("\nSamples:")
            for item in extracted_chars_info[:5]:
                print(f"Hanzi: {item['hanzi']} ({item['pinyin']})")
                print(f"  Meaning: {item['english']}")
                print(f"  Actor: {item['actor']}")
                print(f"  Set: {item['set']}")
                print(f"  Tone-Location: {item['tone_location']}")
                print(f"  Components/Props: {', '.join(item['components'])}")
                print()
                
            # Save to temp JSON
            out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "n1_chars_for_scenes.json")
            with open(out_path, 'w', encoding='utf-8') as f:
                json.dump(extracted_chars_info, f, ensure_ascii=False, indent=2)
            print(f"Details saved to {out_path}")
            
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
