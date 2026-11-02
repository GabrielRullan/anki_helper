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
    # check keys in p
    comp = p.get('component') or p.get('hanzi') or p.get('fields', {}).get('Component')
    nid = p.get('note_id') or p.get('id')
    if comp and nid:
        prop_to_nid[comp] = nid
print(f"Loaded {len(prop_to_nid)} props from anki_extract.json")

with AnkiConnection(profile_name="Main") as anki:
    char_deck = anki.best_match_deck(["Chinese::Char", "Chinese\x1fChar", "Characters"])
    word_deck = anki.best_match_deck(["Chinese::Words", "Chinese\x1fWords", "Migaku"])
    
    char_notes = anki.get_notes_in_deck(char_deck)
    word_notes = anki.get_notes_in_deck(word_deck)
    
    print(f"Loaded {len(char_notes)} chars, {len(word_notes)} words")
    
    char_to_nid = {}
    char_nid_to_note = {}
    for note in char_notes:
        nid = note['id']
        hanzi = note['fields'].get('Hanzi', '').strip()
        simp = note['fields'].get('Simplified', '').strip()
        if hanzi:
            char_to_nid[hanzi] = nid
            char_nid_to_note[nid] = note
        if simp and simp != hanzi:
            char_to_nid[simp] = nid
            
    word_to_nid = {}
    for note in word_notes:
        nid = note['id']
        word = note['fields'].get('Word', '').strip()
        if word:
            word_to_nid[word] = nid
            
    # Check word updates
    word_updates = []
    for note in word_notes:
        nid = note['id']
        word = note['fields'].get('Word', '').strip()
        fields_to_update = {}
        
        if 'Characters' in note['fields']:
            current_chars = note['fields'].get('Characters', '').strip()
            new_chars = link_text_characters(word, char_to_nid)
            if new_chars != current_chars:
                fields_to_update['Characters'] = (current_chars, new_chars)
                
        if 'Notes' in note['fields']:
            notes_field = note['fields'].get('Notes', '').strip()
            linked_chars = []
            for char in word:
                if '\u4e00' <= char <= '\u9fff' and char in char_to_nid:
                    linked_chars.append(f"[{char}|nid{char_to_nid[char]}]")
            if linked_chars:
                section_html = f"<div style='margin-top:10px;font-size:0.85em;color:#9CA3AF;'><b>Characters in word:</b> {' '.join(linked_chars)}</div>"
                new_notes = update_marked_section(notes_field, section_html)
                if new_notes != notes_field:
                    fields_to_update['Notes'] = (notes_field[:50], new_notes[:50])
                    
        if fields_to_update:
            word_updates.append((nid, word, fields_to_update))
            
    print(f"Word updates needed: {len(word_updates)}")
    for nid, word, f in word_updates[:10]:
        print(f"  Word {word} ({nid}): {list(f.keys())}")
        
    # Check char updates
    char_to_derived = {nid: [] for nid in char_nid_to_note.keys()}
    char_to_words = {nid: [] for nid in char_nid_to_note.keys()}
    
    for nid, note in char_nid_to_note.items():
        comp_raw = note['fields'].get('Components', '').strip()
        components = clean_components(comp_raw)
        cleaned_comps = []
        for comp in components:
            match = re.match(r'^\[?([^|\]]+)', comp)
            if match:
                cleaned_comps.append(match.group(1).strip())
        parent_hanzi = note['fields'].get('Hanzi', '').strip()
        for comp in cleaned_comps:
            if comp in char_to_nid:
                child_nid = char_to_nid[comp]
                if child_nid in char_to_derived:
                    char_to_derived[child_nid].append(f"[{parent_hanzi}|nid{nid}]")
                    
    for word, w_nid in word_to_nid.items():
        for char in word:
            if char in char_to_nid:
                c_nid = char_to_nid[char]
                if c_nid in char_to_words:
                    char_to_words[c_nid].append(f"[{word}|nid{w_nid}]")
                    
    char_updates = []
    for nid, note in char_nid_to_note.items():
        hanzi = note['fields'].get('Hanzi', '').strip()
        comp_raw = note['fields'].get('Components', '').strip()
        notes_field = note['fields'].get('Notes', '').strip()
        
        components = clean_components(comp_raw)
        linked_comps = [resolve_component(comp, char_to_nid, prop_to_nid) for comp in components]
        new_comps_val = ", ".join(linked_comps)
        
        backlinks_parts = []
        derived = sorted(list(set(char_to_derived.get(nid, []))))
        if derived:
            backlinks_parts.append(f"<b>Derived characters:</b> {', '.join(derived)}")
            
        words = sorted(list(set(char_to_words.get(nid, []))))
        if words:
            backlinks_parts.append(f"<b>Words containing {hanzi}:</b> {', '.join(words)}")
            
        fields_to_update = {}
        if new_comps_val and new_comps_val != comp_raw and 'Components' in note['fields']:
            fields_to_update['Components'] = (comp_raw, new_comps_val)
            
        if backlinks_parts and 'Notes' in note['fields']:
            section_html = "<div style='margin-top:15px;padding-top:10px;border-top:1px dashed #374151;font-size:0.85em;color:#9CA3AF;line-height:1.5;'>"
            section_html += "<br/>".join(backlinks_parts)
            section_html += "</div>"
            new_notes = update_marked_section(notes_field, section_html)
            if new_notes != notes_field:
                fields_to_update['Notes'] = (notes_field[:50], new_notes[:50])
                
        if fields_to_update:
            char_updates.append((nid, hanzi, fields_to_update))
            
    print(f"\nChar updates needed: {len(char_updates)}")
    for nid, hanzi, f in char_updates[:10]:
        print(f"  Char {hanzi} ({nid}): {list(f.keys())}")
