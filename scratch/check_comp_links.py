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
    
    with_links = 0
    without_links = 0
    for note in char_notes:
        comp = note['fields'].get('Components', '')
        if '|nid' in comp:
            with_links += 1
        else:
            without_links += 1
            
    print(f"Total char notes: {len(char_notes)}")
    print(f"Components WITH |nid links: {with_links}")
    print(f"Components WITHOUT |nid links: {without_links}")
    
    # Sample with links
    samples = [n['fields'].get('Components', '') for n in char_notes if '|nid' in n['fields'].get('Components', '')][:5]
    print("\nSample components with links:")
    for s in samples:
        print(" ", s)
        
    # Sample without links
    samples_no = [n['fields'].get('Components', '') for n in char_notes if '|nid' not in n['fields'].get('Components', '') and n['fields'].get('Components', '')][:5]
    print("\nSample components without links:")
    for s in samples_no:
        print(" ", s)
