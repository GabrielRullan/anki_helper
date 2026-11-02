import json
import urllib.request
import re
import sys
import os
import time
import math
import argparse

# Reconfigure stdout to use UTF-8 on Windows console
sys.stdout.reconfigure(encoding='utf-8')

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
        with urllib.request.urlopen(req, timeout=30) as response:
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
            if isinstance(v, dict):
                return v.get('value', '').strip()
            return str(v).strip()
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

def strip_component_links(comp_str):
    if not comp_str:
        return ""
    # Strip any [X|nid...] links back to plain text
    return re.sub(r'\[([^|\]]+)\|nid\d+\]', r'\1', comp_str)

def link_text_characters(text, char_to_nid):
    if not text:
        return ""
    # Match existing [X|nidYYYY] links or individual characters
    tokens = re.findall(r'\[[^|\]]+\|nid\d+\]|.', text, re.DOTALL)
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

def update_marked_section(field_content, section_html):
    start_tag = "<!-- ANKI_LINKER_START -->"
    end_tag = "<!-- ANKI_LINKER_END -->"
    new_section = f"{start_tag}\n{section_html}\n{end_tag}"
    
    if start_tag in field_content and end_tag in field_content:
        pattern = re.compile(rf"{re.escape(start_tag)}.*?{re.escape(end_tag)}", re.DOTALL)
        return pattern.sub(new_section, field_content)
    else:
        if field_content:
            return f"{field_content}\n\n{new_section}"
        else:
            return new_section

def remove_marked_section(field_content):
    start_tag = "<!-- ANKI_LINKER_START -->"
    end_tag = "<!-- ANKI_LINKER_END -->"
    if start_tag in field_content and end_tag in field_content:
        pattern = re.compile(rf"\s*{re.escape(start_tag)}.*?{re.escape(end_tag)}\s*", re.DOTALL)
        return pattern.sub("", field_content).strip()
    return field_content

def build_links_plan(char_notes, word_notes):
    """
    Computes all link updates:
    - Words: link characters in 'Characters' and 'Notes'
    - Characters: link words in 'Notes' (no props, no derived characters)
    - Clean components: remove obsolete |nid links from 'Components'
    """
    char_to_nid = {}
    char_nid_to_note = {}
    for note in char_notes:
        nid = note.get('noteId') or note.get('id')
        hanzi = get_field_val(note, 'Hanzi')
        simp = get_field_val(note, 'Simplified')
        if hanzi:
            char_to_nid[hanzi] = nid
            char_nid_to_note[nid] = note
        if simp and simp != hanzi:
            char_to_nid[simp] = nid
            
    word_to_nid = {}
    for note in word_notes:
        nid = note.get('noteId') or note.get('id')
        word = get_field_val(note, 'Word')
        if word:
            word_to_nid[word] = nid

    # 1. Process Word cards
    word_updates = []
    nids_to_tag = []
    for note in word_notes:
        nid = note.get('noteId') or note.get('id')
        word = get_field_val(note, 'Word')
        
        # Tag notes with comma in Word field
        if ',' in word or '，' in word:
            word_tags = note.get('tags', [])
            if 'has_comma' not in word_tags:
                nids_to_tag.append(nid)
                
        fields_to_update = {}
        
        # Characters field
        if has_field(note, 'Characters'):
            current_chars = get_field_val(note, 'Characters')
            if not current_chars:
                new_chars = link_text_characters(word, char_to_nid)
            else:
                new_chars = link_text_characters(current_chars, char_to_nid)
            if new_chars and new_chars != current_chars:
                fields_to_update["Characters"] = new_chars
                
        # Notes field
        if has_field(note, 'Notes'):
            notes_field = get_field_val(note, 'Notes')
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

    # 2. Process Character cards (mapping words containing character)
    char_to_words = {nid: [] for nid in char_nid_to_note.keys()}
    for word, w_nid in word_to_nid.items():
        for char in word:
            if char in char_to_nid:
                c_nid = char_to_nid[char]
                if c_nid in char_to_words:
                    char_to_words[c_nid].append(f"[{word}|nid{w_nid}]")

    char_updates = []
    for nid, note in char_nid_to_note.items():
        hanzi = get_field_val(note, 'Hanzi')
        comp_raw = get_field_val(note, 'Components')
        notes_field = get_field_val(note, 'Notes')
        fields_to_update = {}
        
        # Clean components field if it has obsolete |nid links
        if '|nid' in comp_raw and has_field(note, 'Components'):
            cleaned_comp = strip_component_links(comp_raw)
            if cleaned_comp != comp_raw:
                fields_to_update["Components"] = cleaned_comp
                
        # Notes field: Words containing {hanzi}
        words = sorted(list(set(char_to_words.get(nid, []))))
        if words and has_field(note, 'Notes'):
            section_html = f"<div style='margin-top:15px;padding-top:10px;border-top:1px dashed #374151;font-size:0.85em;color:#9CA3AF;line-height:1.5;'><b>Words containing {hanzi}:</b> {', '.join(words)}</div>"
            new_notes = update_marked_section(notes_field, section_html)
            if new_notes != notes_field:
                fields_to_update["Notes"] = new_notes
        elif not words and has_field(note, 'Notes'):
            # If no words contain this character, remove any obsolete linker section
            new_notes = remove_marked_section(notes_field)
            if new_notes != notes_field:
                fields_to_update["Notes"] = new_notes
                
        if fields_to_update:
            char_updates.append({
                "id": nid,
                "fields": fields_to_update
            })

    return char_updates, word_updates, nids_to_tag

def main():
    parser = argparse.ArgumentParser(description="Update bidirectional links between Words and Characters in Anki")
    parser.add_argument("--apply", action="store_true", help="Apply updates to Anki via AnkiConnect")
    parser.add_argument("--dry-run", action="store_true", help="Preview updates without modifying Anki")
    parser.add_argument("--batch-size", type=int, default=50, help="Batch size for AnkiConnect multi calls")
    args = parser.parse_args()

    # Default to dry-run if neither is specified
    if not args.apply and not args.dry_run:
        args.dry_run = True

    print("Connecting to AnkiConnect...")
    version = request_anki("version")
    if not version:
        print("\n[ERROR] Could not connect to Anki. Please make sure Anki is open.")
        sys.exit(1)
        
    print(f"Connected to Anki (version {version}).")
    
    char_deck = resolve_anki_deck(["Chinese::Char", "Chinese\x1fChar", "Characters"])
    word_deck = resolve_anki_deck(["Chinese::Words", "Chinese\x1fWords", "Migaku"])
    
    print(f"Using Character deck: '{char_deck}'")
    print(f"Using Word/Immersion deck: '{word_deck}'")
    
    print("Fetching character notes...")
    char_ids = request_anki("findNotes", query=f'deck:"{char_deck}"')
    if not char_ids:
        print(f"No cards found in Character deck '{char_deck}'.")
        sys.exit(1)
    char_notes = request_anki("notesInfo", notes=char_ids)
    
    print("Fetching word notes...")
    word_ids = request_anki("findNotes", query=f'deck:"{word_deck}"')
    word_notes = request_anki("notesInfo", notes=word_ids) if word_ids else []
    
    print(f"Loaded {len(char_notes)} character notes and {len(word_notes)} word notes.")
    
    char_updates, word_updates, nids_to_tag = build_links_plan(char_notes, word_notes)
    
    print(f"\n--- LINK UPDATES SUMMARY ---")
    print(f"Character notes needing update : {len(char_updates)}")
    print(f"Word notes needing update      : {len(word_updates)}")
    print(f"Word notes needing 'has_comma' : {len(nids_to_tag)}")
    print(f"Total notes to update          : {len(char_updates) + len(word_updates)}")

    if args.dry_run:
        print("\n[DRY RUN] Showing sample character updates:")
        for u in char_updates[:5]:
            print(f"  Note {u['id']} fields: {list(u['fields'].keys())}")
            if 'Notes' in u['fields']:
                print(f"    New Notes preview: {repr(u['fields']['Notes'][:120])}...")
        print("\n[DRY RUN] Showing sample word updates:")
        for u in word_updates[:5]:
            print(f"  Note {u['id']} fields: {list(u['fields'].keys())}")
            if 'Characters' in u['fields']:
                print(f"    New Characters: {u['fields']['Characters']}")
            if 'Notes' in u['fields']:
                print(f"    New Notes preview: {repr(u['fields']['Notes'][:120])}...")
        print(f"\nDry run complete. Use --apply to execute {len(char_updates) + len(word_updates)} updates.")
        return

    # Apply tagging
    if nids_to_tag:
        print(f"\nAdding 'has_comma' tag to {len(nids_to_tag)} word notes...")
        request_anki("addTags", notes=nids_to_tag, tags="has_comma")

    total_updates = char_updates + word_updates
    if not total_updates:
        print("All cards are already fully linked! Nothing to update.")
        return

    # Save backup before applying
    backup_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "link_notes_backup.json")
    print(f"\nSaving pre-update backup of {len(total_updates)} notes to {backup_file}...")
    backup_data = []
    # Fetch current values for all notes being updated
    update_ids = [u['id'] for u in total_updates]
    for b_idx in range(0, len(update_ids), 500):
        b_ids = update_ids[b_idx:b_idx+500]
        infos = request_anki("notesInfo", notes=b_ids) or []
        for info in infos:
            backup_data.append({
                "note_id": info['noteId'],
                "fields": {k: v['value'] for k, v in info['fields'].items()}
            })
    with open(backup_file, 'w', encoding='utf-8') as f_bak:
        json.dump(backup_data, f_bak, ensure_ascii=False, indent=2)
    print(f"Successfully saved backup of {len(backup_data)} notes.")

    batch_size = args.batch_size
    success_count = 0
    total_batches = math.ceil(len(total_updates) / batch_size)
    print(f"\nApplying {len(total_updates)} updates in {total_batches} batches (batch size {batch_size})...")

    start_time = time.time()
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
        res = request_anki("multi", actions=actions)
        if res is not None:
            # In AnkiConnect, successful updateNoteFields returns None/null.
            # Errors return a dict with an 'error' key.
            batch_success = sum(1 for r in res if not (isinstance(r, dict) and 'error' in r and r['error']))
            success_count += batch_success
            print(f"Batch {batch_num}/{total_batches}: {batch_success}/{len(batch)} updated.")
        else:
            print(f"Batch {batch_num} multi call failed. Trying individual updates...")
            batch_success = 0
            for note in batch:
                res_ind = request_anki("updateNoteFields", note=note)
                if res_ind is None or res_ind is True or not (isinstance(res_ind, dict) and 'error' in res_ind and res_ind['error']):
                    batch_success += 1
                    success_count += 1
            print(f"Batch {batch_num}/{total_batches} individual: {batch_success}/{len(batch)} updated.")
            
        time.sleep(0.05)

    elapsed = time.time() - start_time
    print(f"\nFinished! Successfully updated {success_count}/{len(total_updates)} notes in {elapsed:.1f}s.")

    # Refresh extraction
    print("\nRefreshing local cache via extract_anki_data.py...")
    extract_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "extract_anki_data.py")
    os.system(f'python "{extract_script}"')
    print("Done!")

if __name__ == "__main__":
    main()
