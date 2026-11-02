import sys
import os
import json
import re

sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from anki_db import AnkiConnection

with AnkiConnection(profile_name="Main") as anki:
    word_deck = anki.best_match_deck(["Chinese::Words", "Chinese\x1fWords", "Migaku"])
    notes = anki.get_notes_in_deck(word_deck)
    for n in notes:
        for fname, fval in n['fields'].items():
            if 'prop' in fval.lower():
                print(f"Word note {n['id']} ({n['fields'].get('Word')}) - Field '{fname}':")
                print(f"  {repr(fval)}")
                print("-" * 50)
