import json
import urllib.request
import re
import sys
import time
import math

ANKICONNECT_URL = 'http://127.0.0.1:8765'

def request_anki(action, **params):
    payload = {"action": action, "version": 6}
    if params:
        payload["params"] = params
    
    req = urllib.request.Request(
        ANKICONNECT_URL, 
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as response:
            res = json.loads(response.read().decode('utf-8'))
            if res.get('error'):
                print(f"\nAnkiConnect error on action '{action}': {res.get('error')}")
                return None
            return res.get('result')
    except Exception as e:
        print(f"\nAnkiConnect request failed on action '{action}': {e}")
        return None

def resolve_anki_deck(candidates):
    existing = request_anki("deckNames")
    if not existing:
        return candidates[-1]
    
    def normalize(name):
        return name.replace('::', '\x1f').replace('/', '\x1f').replace('\\', '\x1f').lower().strip()
        
    normalized_existing = {normalize(e): e for e in existing}
    for cand in candidates:
        if normalize(cand) in normalized_existing:
            return normalized_existing[normalize(cand)]
    return candidates[-1]

def get_field_val(note, field_name):
    fields = note.get('fields', {})
    for k, v in fields.items():
        if k.lower() == field_name.lower():
            return v.get('value', '').strip()
    return ''

def has_field(note, field_name):
    fields = note.get('fields', {})
    return any(k.lower() == field_name.lower() for k in fields.keys())

def clean_components(comp_str):
    if not comp_str:
        return []
    # Strip HTML tags
    comp_str = re.sub(r'<[^>]+>', '', comp_str)
    # Split by comma or space
    parts = re.split(r'[,，\s]+', comp_str)
    return [p.strip() for p in parts if p.strip()]

def link_text_characters(text, char_to_nid):
    if not text:
        return ""
    # Match [X|nidYYYY] links or individual characters
    tokens = re.findall(r'\[[^|\]]+\|nid\d{13}\]|.', text, re.DOTALL)
    linked_tokens = []
    for token in tokens:
        if token.startswith('[') and token.endswith(']'):
            linked_tokens.append(token)
        else:
            if len(token) == 1 and '\u4e00' <= token <= '\u9fff':
                if token in char_to_nid:
                    linked_tokens.append(f"[{token}|nid{char_to_nid[token]}]")
                else:
                    linked_tokens.append(token)
            else:
                linked_tokens.append(token)
    return "".join(linked_tokens)

def resolve_component(comp, char_to_nid, prop_to_nid):
    # Match either '[X|nidYYYY]' or 'X'
    match_link = re.match(r'^\[?([^|\]]+)(?:\|nid\d+)?\]?$', comp)
    comp_hanzi = match_link.group(1).strip() if match_link else comp
    
    if comp_hanzi in prop_to_nid:
        return f"[{comp_hanzi}|nid{prop_to_nid[comp_hanzi]}]"
    elif comp_hanzi in char_to_nid:
        return f"[{comp_hanzi}|nid{char_to_nid[comp_hanzi]}]"
    else:
        return comp_hanzi

def update_marked_section(field_content, section_html):
    start_tag = "<!-- ANKI_LINKER_START -->"
    end_tag = "<!-- ANKI_LINKER_END -->"
    new_section = f"{start_tag}\n{section_html}\n{end_tag}"
    
    if start_tag in field_content and end_tag in field_content:
        # Replace existing section
        pattern = re.compile(rf"{re.escape(start_tag)}.*?{re.escape(end_tag)}", re.DOTALL)
        return pattern.sub(new_section, field_content)
    else:
        # Append to notes
        if field_content:
            return f"{field_content}\n\n{new_section}"
        else:
            return new_section

def main():
    print("Connecting to AnkiConnect...")
    version = request_anki("version")
    if not version:
        print("\n[ERROR] Could not connect to Anki. Please make sure Anki is open.")
        sys.exit(1)
        
    print(f"Connected to Anki (version {version}).")
    
    # 1. Resolve decks
    char_deck = resolve_anki_deck(["Chinese::Char", "Chinese\x1fChar", "Characters"])
    word_deck = resolve_anki_deck(["Chinese::Words", "Chinese\x1fWords", "Migaku"])
    prop_deck = resolve_anki_deck(["Chinese::Props", "Chinese\x1fProps"])
    
    print(f"Using Character deck: '{char_deck}'")
    print(f"Using Word/Immersion deck: '{word_deck}'")
    print(f"Using Prop deck: '{prop_deck}'")
    
    # 2. Fetch all character notes
    print("Fetching character notes...")
    char_ids = request_anki("findNotes", query=f'deck:"{char_deck}"')
    if not char_ids:
        print(f"No cards found in Character deck '{char_deck}'.")
        sys.exit(1)
    char_notes = request_anki("notesInfo", notes=char_ids)
    
    # 3. Fetch all word notes
    print("Fetching word notes...")
    word_ids = request_anki("findNotes", query=f'deck:"{word_deck}"')
    word_notes = request_anki("notesInfo", notes=word_ids) if word_ids else []
    
    # 4. Fetch all prop notes
    print("Fetching prop notes...")
    prop_ids = request_anki("findNotes", query=f'deck:"{prop_deck}"')
    prop_notes = request_anki("notesInfo", notes=prop_ids) if prop_ids else []
    
    print(f"Loaded {len(char_notes)} character notes, {len(word_notes)} word notes, and {len(prop_notes)} prop notes.")
    
    # 5. Map Character Hanzi, Word, and Prop Component to note_ids (nids)
    char_to_nid = {}
    char_nid_to_note = {}
    for note in char_notes:
        nid = note['noteId']
        hanzi = get_field_val(note, 'Hanzi')
        simp = get_field_val(note, 'Simplified')
        
        if hanzi:
            char_to_nid[hanzi] = nid
            char_nid_to_note[nid] = note
        if simp and simp != hanzi:
            char_to_nid[simp] = nid
            
    word_to_nid = {}
    for note in word_notes:
        nid = note['noteId']
        word = get_field_val(note, 'Word')
        if word:
            word_to_nid[word] = nid
            
    prop_to_nid = {}
    for note in prop_notes:
        nid = note['noteId']
        comp = get_field_val(note, 'Component')
        if comp:
            prop_to_nid[comp] = nid

    # 6. Process word cards: tag commas, copy Word to Characters (and link), and add links to character backlinks
    word_updates = []
    nids_to_tag = []
    for note in word_notes:
        nid = note['noteId']
        word = get_field_val(note, 'Word')
        
        # Tag notes with comma in Word field
        if ',' in word or '，' in word:
            word_tags = note.get('tags', [])
            if 'has_comma' not in word_tags:
                nids_to_tag.append(nid)
                
        fields_to_update = {}
        
        # Copy Word to Characters and link
        if has_field(note, 'Characters'):
            current_chars_val = get_field_val(note, 'Characters')
            new_chars_val = link_text_characters(word, char_to_nid)
            if new_chars_val != current_chars_val:
                fields_to_update["Characters"] = new_chars_val
                
        # Link constituent characters in word Notes field
        if has_field(note, 'Notes'):
            notes_field = get_field_val(note, 'Notes')
            
            # Extract character links in word
            linked_chars = []
            for char in word:
                if '\u4e00' <= char <= '\u9fff' and char in char_to_nid:
                    linked_chars.append(f"[{char}|nid{char_to_nid[char]}]")
            
            if linked_chars:
                section_html = f"<div style='margin-top:10px;font-size:0.85em;color:#9CA3AF;'><b>Characters in word:</b> {' '.join(linked_chars)}</div>"
                new_notes = update_marked_section(notes_field, section_html)
                if new_notes != notes_field:
                    fields_to_update["Notes"] = new_notes
                    
        if fields_to_update:
            word_updates.append({
                "id": nid,
                "fields": fields_to_update
            })
            
    # Apply tags in bulk via AnkiConnect
    if nids_to_tag:
        print(f"Adding 'has_comma' tag to {len(nids_to_tag)} word notes...")
        request_anki("addTags", notes=nids_to_tag, tags="has_comma")

    # 7. Process character cards: update components, and link derived characters & words
    char_to_derived = {nid: [] for nid in char_nid_to_note.keys()}
    char_to_words = {nid: [] for nid in char_nid_to_note.keys()}
    
    # Analyze components and build parent links
    for nid, note in char_nid_to_note.items():
        comp_raw = get_field_val(note, 'Components')
        components = clean_components(comp_raw)
        
        cleaned_hanzi_comps = []
        for comp in components:
            match = re.match(r'^\[?([^|\]]+)', comp)
            if match:
                cleaned_hanzi_comps.append(match.group(1).strip())
                
        for comp in cleaned_hanzi_comps:
            parent_hanzi = get_field_val(note, 'Hanzi')
            if comp in char_to_nid:
                child_nid = char_to_nid[comp]
                if child_nid in char_to_derived:
                    char_to_derived[child_nid].append(f"[{parent_hanzi}|nid{nid}]")
                    
    # Analyze word containment for character -> words relationship
    for word, w_nid in word_to_nid.items():
        for char in word:
            if char in char_to_nid:
                c_nid = char_to_nid[char]
                if c_nid in char_to_words:
                    char_to_words[c_nid].append(f"[{word}|nid{w_nid}]")

    # Generate character note updates
    char_updates = []
    for nid, note in char_nid_to_note.items():
        hanzi = get_field_val(note, 'Hanzi')
        comp_raw = get_field_val(note, 'Components')
        notes_field = get_field_val(note, 'Notes')
        
        # Resolve visual components to Note Linker format (Prop deck takes precedence, Character deck next)
        components = clean_components(comp_raw)
        linked_comps = []
        for comp in components:
            linked_comps.append(resolve_component(comp, char_to_nid, prop_to_nid))
                
        new_comps_val = ", ".join(linked_comps)
        
        # Build backlinks details
        backlinks_parts = []
        derived = sorted(list(set(char_to_derived.get(nid, []))))
        if derived:
            backlinks_parts.append(f"<b>Derived characters:</b> {', '.join(derived)}")
            
        words = sorted(list(set(char_to_words.get(nid, []))))
        if words:
            backlinks_parts.append(f"<b>Words containing {hanzi}:</b> {', '.join(words)}")
            
        fields_to_update = {}
        
        if new_comps_val and new_comps_val != comp_raw and has_field(note, 'Components'):
            fields_to_update["Components"] = new_comps_val
            
        if backlinks_parts and has_field(note, 'Notes'):
            section_html = "<div style='margin-top:15px;padding-top:10px;border-top:1px dashed #374151;font-size:0.85em;color:#9CA3AF;line-height:1.5;'>"
            section_html += "<br/>".join(backlinks_parts)
            section_html += "</div>"
            
            new_notes = update_marked_section(notes_field, section_html)
            if new_notes != notes_field:
                fields_to_update["Notes"] = new_notes
                
        if fields_to_update:
            char_updates.append({
                "id": nid,
                "fields": fields_to_update
            })

    # 8. Apply updates
    total_updates = char_updates + word_updates
    if not total_updates:
        print("All cards are already fully linked! Nothing to update.")
        return
        
    print(f"Found {len(total_updates)} notes to update ({len(char_updates)} characters, {len(word_updates)} words).")
    
    # We use a batch size of 20 to avoid locking Anki UI
    batch_size = 20
    success_count = 0
    total_batches = math.ceil(len(total_updates) / batch_size)
    
    for i in range(0, len(total_updates), batch_size):
        batch = total_updates[i:i+batch_size]
        actions = []
        for note in batch:
            actions.append({
                "action": "updateNoteFields",
                "params": {
                    "note": note
                }
            })
            
        batch_num = i // batch_size + 1
        print(f"Applying batch {batch_num} of {total_batches}...", end=" ", flush=True)
        
        res = request_anki("multi", actions=actions)
        if res:
            success_count += len(batch)
            print("Success.")
        else:
            print("Failed. Trying individual updates in this batch...")
            batch_success = 0
            for note in batch:
                res_ind = request_anki("updateNoteFields", note=note)
                if res_ind is not None:
                    batch_success += 1
                    success_count += 1
            print(f"Batch {batch_num} individual success: {batch_success}/{len(batch)}")
            
        time.sleep(0.3)
        
    print(f"\nCompleted! Successfully updated {success_count} notes.")

if __name__ == "__main__":
    main()
