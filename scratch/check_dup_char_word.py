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
        w = n['fields'].get('Word', '')
        if len(w) == 2 and w[0] == w[1] and '\u4e00' <= w[0] <= '\u9fff':
            print(f"Word: {w} ({n['id']})")
            print(f"  Characters field: {repr(n['fields'].get('Characters', ''))}")
            print(f"  Notes field: {repr(n['fields'].get('Notes', ''))}")
            break
