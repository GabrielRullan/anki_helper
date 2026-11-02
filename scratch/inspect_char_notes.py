import sys
import os
import json
import re

sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from anki_db import AnkiConnection

with AnkiConnection(profile_name="Main") as anki:
    char_deck = anki.best_match_deck(["Chinese::Char", "Chinese\x1fChar", "Characters"])
    char_notes = anki.get_notes_in_deck(char_deck)
    
    has_linker = 0
    has_derived = 0
    has_words = 0
    empty_notes = 0
    
    sample_derived = []
    
    for note in char_notes:
        notes_val = note['fields'].get('Notes', '')
        if not notes_val:
            empty_notes += 1
            continue
        if '<!-- ANKI_LINKER_START -->' in notes_val:
            has_linker += 1
            if 'Derived characters:' in notes_val:
                has_derived += 1
                if len(sample_derived) < 5:
                    sample_derived.append((note['fields'].get('Hanzi', ''), notes_val))
            if 'Words containing' in notes_val:
                has_words += 1
                
    print(f"Total char notes: {len(char_notes)}")
    print(f"Empty Notes field: {empty_notes}")
    print(f"Notes with ANKI_LINKER block: {has_linker}")
    print(f"Notes with 'Derived characters:': {has_derived}")
    print(f"Notes with 'Words containing': {has_words}")
    
    print("\n--- SAMPLE NOTES WITH DERIVED CHARACTERS ---")
    for hz, n in sample_derived:
        print(f"Hanzi: {hz}")
        print(n)
        print("-" * 40)
