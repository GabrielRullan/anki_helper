import sys
import os
import re
sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scripts.anki_db import AnkiConnection

def main():
    with AnkiConnection(profile_name="Main") as anki:
        decks = anki.get_decks()
        print("Available decks:", list(decks.values()))
        
        # We search in all decks
        notes_found = 0
        for deck_id, deck_name in decks.items():
            notes = anki.get_notes_in_deck(deck_name)
            for note in notes:
                for f_name, f_val in note['fields'].items():
                    # Search for any brackets [ ... | nid... ] that contain HTML or images
                    matches = re.findall(r'\[([^|\]]*\|nid\d+)\]', f_val)
                    for match in matches:
                        link_text = match.split('|')[0]
                        if '<' in link_text or 'img' in link_text.lower():
                            notes_found += 1
                            print(f"Deck: {deck_name}, Note ID: {note['id']}")
                            print(f"  Field: {f_name}")
                            print(f"  Value: {repr(f_val)}")
                            print("-" * 50)
                            
        print(f"Total matching notes found: {notes_found}")

if __name__ == '__main__':
    main()
