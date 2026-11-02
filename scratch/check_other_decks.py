import json
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from anki_db import AnkiConnection

with AnkiConnection(profile_name="Main") as anki:
    decks = anki.get_decks()
    print("Decks:", decks)
    for did, dname in decks.items():
        notes = anki.get_notes_in_deck(dname)
        print(f"Deck '{dname}': {len(notes)} notes")
        sample_with_paren = 0
        for n in notes:
            for fname, fval in n['fields'].items():
                if any(w in fname.lower() for w in ['english', 'meaning', 'def', 'trans']):
                    if '(' in fval or '（' in fval:
                        sample_with_paren += 1
                        break
        print(f"  Notes with '(' in trans/meaning/def/english: {sample_with_paren}")
