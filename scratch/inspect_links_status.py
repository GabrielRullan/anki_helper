import sys
import os
import json

sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from anki_db import AnkiConnection

with AnkiConnection(profile_name="Main") as anki:
    char_deck = anki.best_match_deck(["Chinese::Char", "Chinese\x1fChar", "Characters"])
    word_deck = anki.best_match_deck(["Chinese::Words", "Chinese\x1fWords", "Migaku"])
    prop_deck = anki.best_match_deck(["Chinese::Props", "Chinese\x1fProps"])
    
    char_notes = anki.get_notes_in_deck(char_deck)
    word_notes = anki.get_notes_in_deck(word_deck)
    
    print(f"Char notes: {len(char_notes)}")
    print(f"Word notes: {len(word_notes)}")
    
    if char_notes:
        print("\n--- SAMPLE CHAR NOTE FIELDS ---")
        sample_c = char_notes[0]
        for k, v in sample_c['fields'].items():
            print(f"  {k}: {repr(v[:80]) if len(v) > 80 else repr(v)}")
            
    if word_notes:
        print("\n--- SAMPLE WORD NOTE FIELDS ---")
        sample_w = word_notes[0]
        for k, v in sample_w['fields'].items():
            print(f"  {k}: {repr(v[:80]) if len(v) > 80 else repr(v)}")
