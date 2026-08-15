import os
import sys
import json
import urllib.request
import time
import opencc
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

def main():
    print("=" * 70, flush=True)
    print("   STANDARDIZING TRADITIONAL CHINESE FIELD (OPENCC) & TAGGING VARIANTS")
    print("=" * 70, flush=True)

    converter = opencc.OpenCC('s2t')

    note_ids = request_anki("findNotes", query='deck:Chinese::Char')
    if not note_ids:
        print("Error: No notes found in deck 'Chinese::Char'", flush=True)
        return

    notes_info = request_anki("notesInfo", notes=note_ids)
    print(f"Loaded {len(notes_info):,} character notes from Anki.", flush=True)

    update_payloads = []
    tag_has_variant_nids = []
    tag_remove_variant_nids = []

    for note in notes_info:
        f = note.get('fields', {})
        nid = note['noteId']
        c = f.get('Hanzi', {}).get('value', '').strip() or f.get('Simplified', {}).get('value', '').strip()
        if not c:
            continue

        current_trad = f.get('Traditional', {}).get('value', '').strip()
        clean_trad = converter.convert(c)

        if current_trad != clean_trad:
            update_payloads.append({
                "id": nid,
                "fields": {
                    "Traditional": clean_trad
                }
            })

        current_tags = note.get('tags', [])
        if clean_trad != c:
            if "has_traditional_variant" not in current_tags:
                tag_has_variant_nids.append(nid)
        else:
            if "has_traditional_variant" in current_tags:
                tag_remove_variant_nids.append(nid)

    print(f"\nNotes requiring Traditional field update/cleaning: {len(update_payloads):,}", flush=True)
    print(f"Notes requiring 'has_traditional_variant' tag addition: {len(tag_has_variant_nids):,}", flush=True)

    def update_single(p):
        return request_anki("updateNoteFields", note=p)

    if update_payloads:
        chunk_size = 100
        for i in range(0, len(update_payloads), chunk_size):
            chunk = update_payloads[i:i + chunk_size]
            with ThreadPoolExecutor(max_workers=5) as executor:
                list(executor.map(update_single, chunk))
            print(f"  Progress: {min(i + chunk_size, len(update_payloads))}/{len(update_payloads)} notes updated.", flush=True)

        print(f"\nSuccessfully updated Traditional field on {len(update_payloads):,} notes!", flush=True)
    else:
        print("\nAll Traditional fields are already up to date and standardized.", flush=True)

    if tag_has_variant_nids:
        print(f"\nTagging {len(tag_has_variant_nids):,} notes with 'has_traditional_variant'...", flush=True)
        request_anki("addTags", notes=tag_has_variant_nids, tags="has_traditional_variant")
        print("Tagging completed successfully!", flush=True)

    if tag_remove_variant_nids:
        request_anki("removeTags", notes=tag_remove_variant_nids, tags="has_traditional_variant")

    print("=" * 70, flush=True)

if __name__ == "__main__":
    main()
