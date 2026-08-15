import os
import sys
import csv
import json
import urllib.request
import time

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
                print(f"AnkiConnect Error [{action}]: {res.get('error')}")
                return None
            return res.get('result')
    except Exception as e:
        print(f"AnkiConnect Request Failed [{action}]: {e}")
        return None

def is_surname_definition(def_str):
    if not def_str:
        return False
    d = def_str.lower()
    keywords = ['surname', 'family name', 'used in names', 'patronymic']
    return any(k in d for k in keywords)

def main():
    print("=" * 70)
    print("   STARTING ANKI CHARACTER DECK OPTIMIZATION ACTIONS (JUN DA)")
    print("=" * 70)

    # 1. Ensure Do_Not_Recall field exists on model
    fields = request_anki("modelFieldNames", modelName="Chinese Character")
    if not fields:
        print("Error: Could not retrieve fields for model 'Chinese Character'")
        return
    if "Do_Not_Recall" not in fields:
        print("Adding 'Do_Not_Recall' field to 'Chinese Character' model...")
        request_anki("addModelField", model={"name": "Chinese Character"}, field={"name": "Do_Not_Recall"}, index=len(fields))
        print("Field added successfully.")

    # 2. Load Jun Da Dataset
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    junda_csv = os.path.join(base_dir, "data", "junda_freq.csv")
    junda_items = []
    junda_map = {}

    with open(junda_csv, 'r', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            try:
                rank = int(row.get('frequency_rank', 99999))
            except ValueError:
                rank = 99999
            char = row.get('character', '').strip()
            if char:
                info = {
                    'rank': rank,
                    'char': char,
                    'pinyin': row.get('pinyin', ''),
                    'definition': row.get('definition', ''),
                    'hsk': row.get('hsk_level', '')
                }
                junda_items.append(info)
                junda_map[char] = info

    print(f"Loaded Jun Da frequency dataset ({len(junda_map):,} characters).")

    # 3. Query existing Anki notes
    note_ids = request_anki("findNotes", query='"deck:Chinese::Char"')
    if not note_ids:
        print("Error: No notes found in deck 'Chinese::Char'")
        return

    notes_info = request_anki("notesInfo", notes=note_ids)
    existing_map = {} # char -> note_info
    for note in notes_info:
        f = note.get('fields', {})
        c = f.get('Hanzi', {}).get('value', '').strip() or f.get('Simplified', {}).get('value', '').strip()
        if c:
            existing_map[c] = note

    print(f"Existing notes in Chinese::Char: {len(existing_map):,}")

    # =========================================================================
    # ACTION 1: Add Do_Not_Recall = 'y' to Tier 4 / Rare / Surname notes
    # =========================================================================
    print("\n--- ACTION 1: Setting Do_Not_Recall = 'y' for Tier 4 / Rare / Surnames ---")
    tier4_updated_count = 0
    for c, note in existing_map.items():
        jinfo = junda_map.get(c, {})
        rank = jinfo.get('rank', 99999)
        eng = note['fields'].get('English', {}).get('value', '')
        jdef = jinfo.get('definition', '')

        is_surname = is_surname_definition(eng) or is_surname_definition(jdef)

        if rank > 3000 or is_surname:
            current_dnr = note['fields'].get('Do_Not_Recall', {}).get('value', '').strip()
            if current_dnr != 'y':
                nid = note['noteId']
                request_anki("updateNoteFields", note={"id": nid, "fields": {"Do_Not_Recall": "y"}})
                tier4_updated_count += 1

    print(f"Action 1 Complete: Set Do_Not_Recall = 'y' on {tier4_updated_count} notes.")

    # Helper function to add missing notes
    def add_missing_tier_chars(start_rank, end_rank, tier_label):
        missing = [item for item in junda_items if start_rank <= item['rank'] <= end_rank and item['char'] not in existing_map]
        print(f"\n--- Adding Missing {tier_label} (Ranks {start_rank}-{end_rank}): {len(missing)} characters missing ---")
        added_notes = []
        for i, item in enumerate(missing, 1):
            c = item['char']
            rank = item['rank']
            dnr = 'y' if rank > 3000 or is_surname_definition(item['definition']) else ''
            note_payload = {
                "deckName": "Chinese::Char",
                "modelName": "Chinese Character",
                "fields": {
                    "Hanzi": c,
                    "Simplified": c,
                    "Pinyin": item['pinyin'],
                    "English": item['definition'],
                    "Frequency": str(rank),
                    "HSK_2": item['hsk'],
                    "Do_Not_Recall": dnr
                },
                "tags": ["junda_auto_import", f"junda_tier_{tier_label.lower().replace(' ', '_')}"]
            }
            new_id = request_anki("addNote", note=note_payload)
            if new_id:
                added_notes.append(new_id)
                existing_map[c] = {"noteId": new_id, "fields": {"Hanzi": {"value": c}}}
            if i % 100 == 0 or i == len(missing):
                print(f"  Progress: {i}/{len(missing)} notes added.")
        return added_notes

    # =========================================================================
    # ACTION 2: Add missing Tier 1 (1-1000) & Reposition at Queue Position 0
    # =========================================================================
    add_missing_tier_chars(1, 1000, "Tier 1")

    # Retrieve all note IDs for Tier 1
    t1_items = [item for item in junda_items if 1 <= item['rank'] <= 1000 and item['char'] in existing_map]
    t1_items.sort(key=lambda x: x['rank'])
    t1_note_ids = [existing_map[item['char']]['noteId'] for item in t1_items]

    # Find card IDs for these notes
    t1_card_ids = []
    if t1_note_ids:
        # Query in chunks of 500
        for chunk in [t1_note_ids[i:i+500] for i in range(0, len(t1_note_ids), 500)]:
            nids_str = ",".join(str(nid) for nid in chunk)
            cids = request_anki("findCards", query=f"nid:{nids_str}")
            if cids:
                t1_card_ids.extend(cids)

    print(f"Repositioning {len(t1_card_ids)} Tier 1 cards starting at queue position 0...")
    if t1_card_ids:
        request_anki("repositionCards", cards=t1_card_ids, start=0, step=1, force=True)
        print("Action 2 Complete: Tier 1 repositioned at 0+.")

    # =========================================================================
    # ACTION 3: Add missing Tier 2 (1001-2500) & Reposition at Queue Position 100
    # =========================================================================
    add_missing_tier_chars(1001, 2500, "Tier 2")

    t2_items = [item for item in junda_items if 1001 <= item['rank'] <= 2500 and item['char'] in existing_map]
    t2_items.sort(key=lambda x: x['rank'])
    t2_note_ids = [existing_map[item['char']]['noteId'] for item in t2_items]

    t2_card_ids = []
    if t2_note_ids:
        for chunk in [t2_note_ids[i:i+500] for i in range(0, len(t2_note_ids), 500)]:
            nids_str = ",".join(str(nid) for nid in chunk)
            cids = request_anki("findCards", query=f"nid:{nids_str}")
            if cids:
                t2_card_ids.extend(cids)

    print(f"Repositioning {len(t2_card_ids)} Tier 2 cards starting at queue position 100...")
    if t2_card_ids:
        request_anki("repositionCards", cards=t2_card_ids, start=100, step=1, force=True)
        print("Action 3 Complete: Tier 2 repositioned at 100+.")

    # =========================================================================
    # ACTION 4: Add missing Tier 3 (2501-3500) & Reposition at Queue Position 3000
    # =========================================================================
    add_missing_tier_chars(2501, 3500, "Tier 3")

    t3_items = [item for item in junda_items if 2501 <= item['rank'] <= 3500 and item['char'] in existing_map]
    t3_items.sort(key=lambda x: x['rank'])
    t3_note_ids = [existing_map[item['char']]['noteId'] for item in t3_items]

    t3_card_ids = []
    if t3_note_ids:
        for chunk in [t3_note_ids[i:i+500] for i in range(0, len(t3_note_ids), 500)]:
            nids_str = ",".join(str(nid) for nid in chunk)
            cids = request_anki("findCards", query=f"nid:{nids_str}")
            if cids:
                t3_card_ids.extend(cids)

    print(f"Repositioning {len(t3_card_ids)} Tier 3 cards starting at queue position 3000...")
    if t3_card_ids:
        request_anki("repositionCards", cards=t3_card_ids, start=3000, step=1, force=True)
        print("Action 4 Complete: Tier 3 repositioned at 3000+.")

    print("\n" + "=" * 70)
    print("   ALL 4 CHARACTER ACTIONS EXECUTED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    main()
