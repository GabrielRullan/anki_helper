import sys
import os
import json
import re

sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from anki_db import AnkiConnection
from link_notes import clean_components, update_marked_section, link_text_characters

with AnkiConnection(profile_name="Main") as anki:
    char_deck = anki.best_match_deck(["Chinese::Char", "Chinese\x1fChar", "Characters"])
    word_deck = anki.best_match_deck(["Chinese::Words", "Chinese\x1fWords", "Migaku"])
    
    char_notes = anki.get_notes_in_deck(char_deck)
    word_notes = anki.get_notes_in_deck(word_deck)
    
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
            
    # Map each character to words containing it
    char_to_words = {nid: [] for nid in char_nid_to_note.keys()}
    for word, w_nid in word_to_nid.items():
        for char in word:
            if char in char_to_nid:
                c_nid = char_to_nid[char]
                if c_nid in char_to_words:
                    char_to_words[c_nid].append(f"[{word}|nid{w_nid}]")
                    
    # 1. Word updates
    word_updates = []
    for note in word_notes:
        nid = note['id']
        word = note['fields'].get('Word', '').strip()
        fields_to_update = {}
        
        # Characters field: if empty or unlinked, copy and link word
        current_chars = note['fields'].get('Characters', '').strip()
        new_chars = link_text_characters(word, char_to_nid)
        # If current_chars is empty or doesn't have links, or differs from newly linked word
        if not current_chars and new_chars:
            fields_to_update['Characters'] = new_chars
        elif current_chars:
            # If current_chars already has links, make sure any plain unlinked hanzi are also linked
            updated_existing_chars = link_text_characters(current_chars, char_to_nid)
            if updated_existing_chars != current_chars:
                fields_to_update['Characters'] = updated_existing_chars
                
        # Notes field: Characters in word
        notes_field = note['fields'].get('Notes', '').strip()
        linked_chars = []
        for char in word:
            if '\u4e00' <= char <= '\u9fff' and char in char_to_nid:
                linked_chars.append(f"[{char}|nid{char_to_nid[char]}]")
                
        if linked_chars:
            section_html = f"<div style='margin-top:10px;font-size:0.85em;color:#9CA3AF;'><b>Characters in word:</b> {' '.join(linked_chars)}</div>"
            new_notes = update_marked_section(notes_field, section_html)
            if new_notes != notes_field:
                fields_to_update['Notes'] = new_notes
                
        if fields_to_update:
            word_updates.append((nid, word, fields_to_update))
            
    # 2. Character updates
    char_updates = []
    start_tag = "<!-- ANKI_LINKER_START -->"
    end_tag = "<!-- ANKI_LINKER_END -->"
    
    for nid, note in char_nid_to_note.items():
        hanzi = note['fields'].get('Hanzi', '').strip()
        notes_field = note['fields'].get('Notes', '').strip()
        comp_raw = note['fields'].get('Components', '').strip()
        
        fields_to_update = {}
        
        # Check if Components has any obsolete |nid links to remove
        if '|nid' in comp_raw:
            cleaned_comp = re.sub(r'\[([^|\]]+)\|nid\d+\]', r'\1', comp_raw)
            if cleaned_comp != comp_raw:
                fields_to_update['Components'] = cleaned_comp
                
        # Backlinks to words containing this character (NO derived characters, NO props!)
        words = sorted(list(set(char_to_words.get(nid, []))))
        
        if words:
            section_html = f"<div style='margin-top:15px;padding-top:10px;border-top:1px dashed #374151;font-size:0.85em;color:#9CA3AF;line-height:1.5;'><b>Words containing {hanzi}:</b> {', '.join(words)}</div>"
            new_notes = update_marked_section(notes_field, section_html)
            if new_notes != notes_field:
                fields_to_update['Notes'] = new_notes
        else:
            # If there are NO words containing this character, but there is an ANKI_LINKER block (e.g. from old derived characters), remove it!
            if start_tag in notes_field and end_tag in notes_field:
                pattern = re.compile(rf"\s*{re.escape(start_tag)}.*?{re.escape(end_tag)}\s*", re.DOTALL)
                new_notes = pattern.sub("", notes_field).strip()
                if new_notes != notes_field:
                    fields_to_update['Notes'] = new_notes
                    
        if fields_to_update:
            char_updates.append((nid, hanzi, fields_to_update))
            
    print(f"Total word notes: {len(word_notes)}, needing update: {len(word_updates)}")
    print(f"Total char notes: {len(char_notes)}, needing update: {len(char_updates)}")
