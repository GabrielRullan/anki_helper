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
        
        print(f"Char deck: {char_deck}")
        print(f"Prop deck: {prop_deck}")
        
        char_notes = anki.get_notes_in_deck(char_deck)
        prop_notes = anki.get_notes_in_deck(prop_deck)
        
        print(f"Loaded {len(char_notes)} char notes, {len(prop_notes)} prop notes.")
        
        print("\nChecking for HTML/images in Hanzi field of Char deck:")
        bad_char_hanzi = []
        for note in char_notes:
            hz = note['fields'].get('Hanzi', '')
            if '<' in hz or 'img' in hz.lower():
                bad_char_hanzi.append((note['id'], hz))
        
        for nid, hz in bad_char_hanzi[:20]:
            print(f"  Note ID: {nid}, Hanzi: {hz}")
            
        print("\nChecking for HTML/images in Components field of Char deck:")
        bad_char_comp = []
        for note in char_notes:
            comp = note['fields'].get('Components', '')
            if '<' in comp or 'img' in comp.lower():
                bad_char_comp.append((note['id'], comp))
                
        for nid, comp in bad_char_comp[:20]:
            print(f"  Note ID: {nid}, Components: {comp}")
            
        print("\nChecking for HTML/images in Component field of Prop deck:")
        bad_prop_comp = []
        for note in prop_notes:
            comp = note['fields'].get('Component', '')
            if '<' in comp or 'img' in comp.lower():
                bad_prop_comp.append((note['id'], comp))
                
        for nid, comp in bad_prop_comp[:20]:
            print(f"  Note ID: {nid}, Component: {comp}")

if __name__ == '__main__':
    main()
