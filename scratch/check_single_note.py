import sys
import os
import json

sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from anki_db import AnkiConnection

with AnkiConnection(profile_name="Main") as anki:
    word_deck = anki.best_match_deck(["Chinese::Words", "Chinese\x1fWords", "Migaku"])
    notes = anki.get_notes_in_deck(word_deck)
    for n in notes:
        if n['id'] == 1747256613563:
            for k, v in n['fields'].items():
                print(f"{k}: {repr(v)}")
            break
