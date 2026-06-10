import sys
import os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scripts.anki_db import AnkiConnection

def main():
    with AnkiConnection(profile_name="Main") as anki:
        # Resolve decks
        char_deck = anki.best_match_deck(["Chinese::Char", "Chinese\x1fChar", "Characters"])
        prop_deck = anki.best_match_deck(["Chinese::Props", "Chinese\x1fProps"])
        word_deck = anki.best_match_deck(["Chinese::Words", "Chinese\x1fWords", "Migaku"])
        
        print(f"Char deck: {char_deck}")
        print(f"Prop deck: {prop_deck}")
        
        # Find notes matching '玫' or '枚' in any deck
        for deck_name, name in [("Char", char_deck), ("Prop", prop_deck), ("Word", word_deck)]:
            notes = anki.get_notes_in_deck(name)
            print(f"\nSearching in {deck_name} deck ({len(notes)} notes)...")
            
            # Search for '玫'
            for note in notes:
                fields = note['fields']
                for f_name, f_val in fields.items():
                    if '玫' in f_val:
                        print(f"  Note ID: {note['id']}, Notetype: {note['notetype']}")
                        print(f"    Field '{f_name}': {repr(f_val)}")
                        for k, v in fields.items():
                            if k != f_name and v.strip():
                                print(f"    Field '{k}': {repr(v)}")
                        print("-" * 30)

if __name__ == '__main__':
    main()
