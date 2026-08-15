import os
import sys
import csv
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

def is_surname_definition(def_str):
    if not def_str:
        return False
    d = def_str.lower()
    keywords = ['surname', 'family name', 'used in names', 'patronymic']
    return any(k in d for k in keywords)

def format_frequency(rank, is_surname):
    if rank <= 1000:
        return f"Tier 1 (#{rank})"
    elif rank <= 2500:
        return f"Tier 2 (#{rank})"
    elif rank <= 3500 and not is_surname:
        return f"Tier 3 (#{rank})"
    else:
        rank_str = f"#{rank}" if rank != 99999 else "Unranked"
        return f"Tier 4 - Rare ({rank_str})"

def main():
    print("=" * 70, flush=True)
    print("   UPDATING 'FREQUENCY' FIELD FOR ALL CHINESE CHARACTER NOTES")
    print("=" * 70, flush=True)

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    junda_csv = os.path.join(base_dir, "data", "junda_freq.csv")
    junda_map = {}

    with open(junda_csv, 'r', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            try:
                rank = int(row.get('frequency_rank', 99999))
            except ValueError:
                rank = 99999
            char = row.get('character', '').strip()
            if char:
                junda_map[char] = {
                    'rank': rank,
                    'definition': row.get('definition', '')
                }

    print(f"Loaded Jun Da frequency dataset ({len(junda_map):,} characters).", flush=True)

    note_ids = request_anki("findNotes", query='deck:Chinese::Char')
    if not note_ids:
        print("Error: No notes found in deck 'Chinese::Char'", flush=True)
        return

    notes_info = request_anki("notesInfo", notes=note_ids)
    print(f"Found {len(notes_info):,} notes in Chinese::Char deck.", flush=True)

    update_payloads = []
    for note in notes_info:
        f = note.get('fields', {})
        char = f.get('Hanzi', {}).get('value', '').strip() or f.get('Simplified', {}).get('value', '').strip()
        if not char:
            continue

        eng = f.get('English', {}).get('value', '')
        jinfo = junda_map.get(char, {})
        rank = jinfo.get('rank', 99999)
        jdef = jinfo.get('definition', '')

        is_surname = is_surname_definition(eng) or is_surname_definition(jdef)
        freq_str = format_frequency(rank, is_surname)

        current_freq = f.get('Frequency', {}).get('value', '').strip()
        if current_freq != freq_str:
            update_payloads.append({
                "id": note['noteId'],
                "fields": {
                    "Frequency": freq_str
                }
            })

    print(f"\nUpdating Frequency field for {len(update_payloads):,} notes...", flush=True)

    def update_single_note(p):
        return request_anki("updateNoteFields", note=p)

    if update_payloads:
        chunk_size = 100
        for i in range(0, len(update_payloads), chunk_size):
            chunk = update_payloads[i:i + chunk_size]
            with ThreadPoolExecutor(max_workers=5) as executor:
                list(executor.map(update_single_note, chunk))
            print(f"  Progress: {min(i + chunk_size, len(update_payloads))}/{len(update_payloads)} notes updated.", flush=True)

        print(f"Successfully updated Frequency field on {len(update_payloads):,} notes!", flush=True)
    else:
        print("All notes are already up to date.", flush=True)

    print("\n" + "=" * 70, flush=True)
    print("   FREQUENCY FIELD UPDATE COMPLETED SUCCESSFULLY!", flush=True)
    print("=" * 70, flush=True)

if __name__ == "__main__":
    main()
