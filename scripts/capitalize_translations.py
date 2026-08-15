import os
import sys
import json
import urllib.request
import time
from concurrent.futures import ThreadPoolExecutor

sys.stdout.reconfigure(encoding='utf-8')

ANKICONNECT_URL = 'http://127.0.0.1:8765'

def request_anki(action, retries=5, delay=2, **params):
    payload = {"action": action, "version": 6}
    if params:
        payload["params"] = params
    
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                ANKICONNECT_URL,
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                res = json.loads(response.read().decode('utf-8'))
                if res.get('error'):
                    print(f"AnkiConnect Error [{action}]: {res.get('error')}", flush=True)
                    return None
                return res.get('result')
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                print(f"AnkiConnect Request Failed [{action}]: {e}", flush=True)
                return None

def capitalize_word_or_phrase(s):
    s = s.strip()
    if not s:
        return ''
    if ' / ' in s:
        subparts = s.split(' / ')
        return ' / '.join([capitalize_word_or_phrase(sp) for sp in subparts])
    
    for idx, ch in enumerate(s):
        if ch.isalpha():
            return s[:idx] + ch.upper() + s[idx+1:]
    return s

def capitalize_english_field(def_str):
    if not def_str:
        return ''
    # Split by semicolon
    parts = def_str.split(';')
    capitalized_parts = [capitalize_word_or_phrase(p) for p in parts]
    return '; '.join(capitalized_parts)

def capitalize_translation_of_words(tow_str):
    if not tow_str:
        return ''
    # Split by comma or semicolon
    parts = tow_str.split(',')
    capitalized_parts = [capitalize_word_or_phrase(p) for p in parts]
    return ', '.join(capitalized_parts)

def main():
    print("=" * 70, flush=True)
    print("   CAPITALIZING TRANSLATIONS FOR ALL CHINESE CHARACTER NOTES")
    print("=" * 70, flush=True)

    note_ids = request_anki("findNotes", query='deck:Chinese::Char')
    if not note_ids:
        print("Error: No notes found in deck 'Chinese::Char'", flush=True)
        return

    print(f"Fetching {len(note_ids):,} notes from Chinese::Char deck...", flush=True)
    notes_info = request_anki("notesInfo", notes=note_ids)

    update_payloads = []
    for note in notes_info:
        f = note.get('fields', {})
        nid = note['noteId']
        
        eng_orig = f.get('English', {}).get('value', '').strip()
        tow_orig = f.get('Translation of Words', {}).get('value', '').strip()

        eng_new = capitalize_english_field(eng_orig)
        tow_new = capitalize_translation_of_words(tow_orig)

        fields_to_update = {}
        if eng_orig != eng_new:
            fields_to_update['English'] = eng_new
        if tow_orig != tow_new:
            fields_to_update['Translation of Words'] = tow_new

        if fields_to_update:
            update_payloads.append({
                'id': nid,
                'fields': fields_to_update
            })

    print(f"\nFound {len(update_payloads):,} notes requiring translation capitalization updates.", flush=True)

    def update_single(p):
        return request_anki("updateNoteFields", note=p)

    if update_payloads:
        chunk_size = 100
        for i in range(0, len(update_payloads), chunk_size):
            chunk = update_payloads[i:i + chunk_size]
            with ThreadPoolExecutor(max_workers=5) as executor:
                list(executor.map(update_single, chunk))
            print(f"  Progress: {min(i + chunk_size, len(update_payloads))}/{len(update_payloads)} notes updated.", flush=True)

        print(f"\nSuccessfully capitalized translations on {len(update_payloads):,} notes!", flush=True)
    else:
        print("\nAll translations are already properly capitalized.", flush=True)

    print("=" * 70, flush=True)

if __name__ == "__main__":
    main()
