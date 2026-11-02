import sys
import os
import re
import json

sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from anki_db import AnkiConnection
from link_notes import clean_components, update_marked_section, link_text_characters, resolve_component

with open('data/anki_extract.json', 'r', encoding='utf-8') as f:
    extract_data = json.load(f)

props = extract_data.get('props', [])
prop_to_nid = {}
for p in props:
    comp = p.get('component') or p.get('hanzi') or p.get('fields', {}).get('Component')
    nid = p.get('note_id') or p.get('id')
    if comp and nid:
        prop_to_nid[comp] = nid

with AnkiConnection(profile_name="Main") as anki:
    char_deck = anki.best_match_deck(["Chinese::Char", "Chinese\x1fChar", "Characters"])
    char_notes = anki.get_notes_in_deck(char_deck)
    char_to_nid = {n['fields'].get('Hanzi', '').strip(): n['id'] for n in char_notes}
    
    for note in char_notes[:10]:
        hz = note['fields'].get('Hanzi', '').strip()
        comp_raw = note['fields'].get('Components', '').strip()
        comps = clean_components(comp_raw)
        linked_comps = [resolve_component(c, char_to_nid, prop_to_nid) for c in comps]
        new_comps = ", ".join(linked_comps)
        print(f"Char {hz}:")
        print(f"  Old comps: {repr(comp_raw)}")
        print(f"  New comps: {repr(new_comps)}")
        print(f"  Old notes: {repr(note['fields'].get('Notes', '')[:60])}")
