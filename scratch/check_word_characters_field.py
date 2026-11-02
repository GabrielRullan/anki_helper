import sys
import os
import json

sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from anki_db import AnkiConnection

with AnkiConnection(profile_name="Main") as anki:
    word_deck = anki.best_match_deck(["Chinese::Words", "Chinese\x1fWords", "Migaku"])
    notes = anki.get_notes_in_deck(word_deck)
    
    empty_chars = 0
    unlinked_chars = 0
    linked_chars = 0
    
    for n in notes:
        c = n['fields'].get('Characters', '').strip()
        if not c:
            empty_chars += 1
        elif '|nid' in c:
            linked_chars += 1
        else:
            unlinked_chars += 1
            
    print(f"Total word notes: {len(notes)}")
    print(f"Empty Characters: {empty_chars}")
    print(f"Unlinked Characters: {unlinked_chars}")
    print(f"Linked Characters: {linked_chars}")
