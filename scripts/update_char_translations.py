import os
import sys
import json
import urllib.request
import argparse

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
    with urllib.request.urlopen(req, timeout=25) as response:
        res = json.loads(response.read().decode('utf-8'))
        if res.get('error'):
            raise RuntimeError(f"AnkiConnect error on {action}: {res['error']}")
        return res.get('result')

def main():
    parser = argparse.ArgumentParser(description="Update character translations in Anki")
    parser.add_argument("--apply", action="store_true", help="Apply updates to Anki via AnkiConnect")
    parser.add_argument("--dry-run", action="store_true", help="Dry run without modifying Anki")
    parser.add_argument("--input", default="data/char_translation_improvements.json", help="Path to improvements dataset")
    args = parser.parse_args()

    if not args.apply and not args.dry_run:
        print("Please specify either --dry-run or --apply.")
        sys.exit(1)

    if not os.path.exists(args.input):
        print(f"Error: input file {args.input} not found.")
        sys.exit(1)

    with open(args.input, 'r', encoding='utf-8') as f:
        dataset = json.load(f)

    updates = dataset.get('updates', [])
    print(f"Loaded {len(updates)} translation improvements from {args.input}")

    if args.dry_run:
        print("\n--- DRY RUN PREVIEW ---")
        for i, u in enumerate(updates, 1):
            print(f"{i:2d}. [{u['hanzi']}] {u['pinyin']} (Note ID: {u['note_id']})")
            print(f"    Category : {u['category']}")
            print(f"    Current  : \"{u['old_english']}\"")
            print(f"    Proposed : \"{u['new_english']}\"")
            print(f"    Reason   : {u['reason']}")
            print()
        print(f"Dry run complete. Total updates to apply: {len(updates)}")
        return

    # Check AnkiConnect connectivity
    try:
        decks = request_anki("deckNames")
        print(f"Connected to Anki. Decks: {decks}")
    except Exception as e:
        print(f"Error connecting to AnkiConnect: {e}")
        sys.exit(1)

    # Save backup of current note fields before applying
    note_ids = [u['note_id'] for u in updates]
    print(f"Fetching current field values for {len(note_ids)} notes for backup...")
    notes_info = request_anki("notesInfo", notes=note_ids)

    backup_data = []
    for info in notes_info:
        backup_data.append({
            "note_id": info['noteId'],
            "fields": {k: v['value'] for k, v in info['fields'].items()}
        })

    backup_path = "data/char_translation_backup.json"
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(backup_data, f, ensure_ascii=False, indent=2)
    print(f"Saved pre-update backup to {backup_path}")

    # Apply updates
    success_count = 0
    fail_count = 0

    for i, u in enumerate(updates, 1):
        nid = u['note_id']
        new_val = u['new_english']
        try:
            request_anki("updateNoteFields", note={"id": nid, "fields": {"English": new_val}})
            success_count += 1
            print(f"[{i}/{len(updates)}] Updated {u['hanzi']} ({nid}) -> \"{new_val}\"")
        except Exception as e:
            fail_count += 1
            print(f"[{i}/{len(updates)}] FAILED to update {u['hanzi']} ({nid}): {e}")

    print(f"\nUpdate finished: {success_count} succeeded, {fail_count} failed.")

    # Re-extract data
    print("\nRunning extract_anki_data.py to refresh local extract...")
    os.system(f"{sys.executable} scripts/extract_anki_data.py")
    print("Anki extraction complete.")

if __name__ == "__main__":
    main()
