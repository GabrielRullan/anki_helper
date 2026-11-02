import sys
import os
import json

sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from anki_db import AnkiConnection

with AnkiConnection(profile_name="Main") as anki:
    word_deck = anki.best_match_deck(["Chinese::Words", "Chinese\x1fWords", "Migaku"])
    notes = anki.get_notes_in_deck(word_deck)
    
    missing_linker = 0
    has_linker = 0
    for n in notes:
        notes_val = n['fields'].get('Notes', '')
        if '<!-- ANKI_LINKER_START -->' not in notes_val:
            missing_linker += 1
        else:
            has_linker += 1
            
    print(f"Total word notes: {len(notes)}")
    print(f"Notes with ANKI_LINKER block: {has_linker}")
    print(f"Notes WITHOUT ANKI_LINKER block: {missing_linker}")
