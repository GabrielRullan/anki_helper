import os
import sys
import csv
import json
import argparse
import urllib.request
import urllib.parse
from collections import defaultdict

# Reconfigure stdout for UTF-8 on Windows
sys.stdout.reconfigure(encoding='utf-8')

ANKICONNECT_URL = 'http://127.0.0.1:8765'

def load_junda_freq(csv_path):
    """Loads Jun Da character frequency data into a lookup dict."""
    freq_map = {}
    if not os.path.exists(csv_path):
        print(f"Error: Jun Da frequency file not found at {csv_path}")
        return freq_map

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            char = row.get('character', '').strip()
            if char:
                try:
                    rank = int(row.get('frequency_rank', 99999))
                except ValueError:
                    rank = 99999
                freq_map[char] = {
                    'rank': rank,
                    'pinyin': row.get('pinyin', ''),
                    'definition': row.get('definition', ''),
                    'hsk': row.get('hsk_level', '')
                }
    return freq_map

def fetch_anki_characters():
    """Fetches notes from deck Chinese::Char via AnkiConnect."""
    payload = {
        "action": "findNotes",
        "version": 6,
        "params": {"query": '"deck:Chinese::Char"'}
    }
    try:
        req = urllib.request.Request(
            ANKICONNECT_URL,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            res = json.loads(response.read().decode('utf-8'))
            note_ids = res.get('result', [])
            if not note_ids:
                return None
            
            # Fetch note info
            info_payload = {
                "action": "notesInfo",
                "version": 6,
                "params": {"notes": note_ids}
            }
            req_info = urllib.request.Request(
                ANKICONNECT_URL,
                data=json.dumps(info_payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )
            with urllib.request.urlopen(req_info, timeout=10) as resp_info:
                info_res = json.loads(resp_info.read().decode('utf-8'))
                return info_res.get('result', [])
    except Exception:
        return None

def fetch_fallback_csv(csv_path):
    """Loads characters from data/new_characters.csv if AnkiConnect is not reachable."""
    notes = []
    if not os.path.exists(csv_path):
        return notes
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            char = row.get('Hanzi', row.get('Simplified', '')).strip()
            if char:
                notes.append({
                    'noteId': row.get('Note_ID', row.get('ID', '')),
                    'tags': row.get('Tags', '').split(),
                    'fields': {
                        'Hanzi': {'value': char},
                        'Pinyin': {'value': row.get('Pinyin', '')},
                        'English': {'value': row.get('English', '')}
                    }
                })
    return notes

def is_surname_definition(def_str):
    """Checks if definition explicitly references a surname or family name."""
    if not def_str:
        return False
    d = def_str.lower()
    keywords = ['surname', 'family name', 'used in names', 'patronymic']
    return any(k in d for k in keywords)

def tag_notes_in_anki(note_ids, tag="recognition_only"):
    """Adds tag to specified notes via AnkiConnect."""
    payload = {
        "action": "addTags",
        "version": 6,
        "params": {
            "notes": note_ids,
            "tags": tag
        }
    }
    try:
        req = urllib.request.Request(
            ANKICONNECT_URL,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            res = json.loads(response.read().decode('utf-8'))
            return res.get('error') is None
    except Exception as e:
        print(f"Failed to tag notes via AnkiConnect: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Audit Chinese character frequencies against Jun Da dataset.")
    parser.add_argument("--cutoff", type=int, default=3000, help="Frequency rank cutoff above which characters are considered rare (default: 3000).")
    parser.add_argument("--export-csv", type=str, help="Export detailed audit results to a CSV file.")
    parser.add_argument("--tag-rare", action="store_true", help="Add 'recognition_only' tag to rare characters in Anki via AnkiConnect.")
    args = parser.parse_args()

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    junda_csv = os.path.join(base_dir, "data", "junda_freq.csv")
    fallback_csv = os.path.join(base_dir, "data", "new_characters.csv")

    print(f"Loading Jun Da frequency dataset from {junda_csv}...")
    freq_map = load_junda_freq(junda_csv)
    print(f"Loaded frequency data for {len(freq_map):,} characters.")

    print("\nFetching character notes...")
    anki_notes = fetch_anki_characters()
    source = "AnkiConnect (Chinese::Char deck)"
    if not anki_notes:
        print("AnkiConnect unreachable or deck empty. Falling back to local data/new_characters.csv...")
        anki_notes = fetch_fallback_csv(fallback_csv)
        source = "Local data/new_characters.csv"
    
    print(f"Source: {source} ({len(anki_notes)} notes found)")

    # Analysis data structures
    results = []
    tiers = {
        'Tier 1: Core (Rank 1-1000)': [],
        'Tier 2: Intermediate (Rank 1001-2500)': [],
        'Tier 3: Lower-Freq (Rank 2501-3500)': [],
        'Tier 4: Rare / Surname (>3500 or Unranked)': []
    }
    rare_note_ids = []

    for note in anki_notes:
        fields = note.get('fields', {})
        char = fields.get('Hanzi', {}).get('value', '').strip()
        if not char:
            char = fields.get('Simplified', {}).get('value', '').strip()
        if not char or len(char) > 1:
            continue  # Skip multi-character entries or blank notes

        pinyin = fields.get('Pinyin', {}).get('value', '').strip()
        english = fields.get('English', {}).get('value', '').strip()
        tags = note.get('tags', [])
        note_id = note.get('noteId', '')

        junda_info = freq_map.get(char, {})
        rank = junda_info.get('rank', 99999)
        junda_pinyin = junda_info.get('pinyin', '')
        junda_def = junda_info.get('definition', '')
        hsk = junda_info.get('hsk', '')

        is_surname = is_surname_definition(english) or is_surname_definition(junda_def)

        # Tier assignment
        if rank <= 1000:
            tier_name = 'Tier 1: Core (Rank 1-1000)'
            recommendation = '2 Cards (Recognition + Recall)'
        elif rank <= 2500:
            tier_name = 'Tier 2: Intermediate (Rank 1001-2500)'
            recommendation = '2 Cards (Recognition + Recall)'
        elif rank <= args.cutoff:
            tier_name = 'Tier 3: Lower-Freq (Rank 2501-3500)'
            recommendation = '2 Cards or 1 Card'
        else:
            tier_name = 'Tier 4: Rare / Surname (>3500 or Unranked)'
            recommendation = '1 Card (Recognition Only)'

        if rank > args.cutoff or is_surname:
            if note_id:
                rare_note_ids.append(note_id)

        item = {
            'note_id': note_id,
            'char': char,
            'pinyin': pinyin or junda_pinyin,
            'english': english or junda_def,
            'rank': rank if rank != 99999 else 'Unranked',
            'hsk': hsk or 'N/A',
            'is_surname': 'Yes' if is_surname else 'No',
            'tier': tier_name,
            'recommendation': recommendation,
            'tags': ', '.join(tags)
        }
        results.append(item)
        tiers[tier_name].append(item)

    # Print Summary Report
    print("\n" + "="*70)
    print("         CHINESE CHARACTER FREQUENCY AUDIT REPORT (JUN DA)")
    print("="*70)
    print(f"Total Characters Evaluated: {len(results)}")
    print(f"Rare Cutoff Threshold: Rank > {args.cutoff}")
    print("-"*70)

    for tier_name, items in tiers.items():
        pct = (len(items) / len(results) * 100) if results else 0
        print(f"  • {tier_name:<42} : {len(items):>4} chars ({pct:>5.1f}%)")

    rare_count = len(tiers['Tier 4: Rare / Surname (>3500 or Unranked)'])
    print("-"*70)
    print(f"Total Candidates for Recognition-Only (1 Card): {rare_count} characters")
    print("="*70)

    # Highlight sample rare / surname characters
    print("\n[SAMPLE RARE / SURNAME CHARACTERS (RECOMMEND 1 CARD)]")
    print(f"{'Char':<6} {'Rank':<10} {'Pinyin':<12} {'Surname?':<10} {'English / Definition':<30}")
    print("-" * 72)
    rare_items = tiers['Tier 4: Rare / Surname (>3500 or Unranked)']
    for item in rare_items[:15]:
        def_short = item['english'][:28] + ('..' if len(item['english']) > 28 else '')
        print(f"{item['char']:<6} {str(item['rank']):<10} {item['pinyin']:<12} {item['is_surname']:<10} {def_short:<30}")

    if len(rare_items) > 15:
        print(f"... and {len(rare_items) - 15} more rare characters.")

    # Export CSV if requested
    if args.export_csv:
        export_path = os.path.abspath(args.export_csv)
        print(f"\nExporting audit report to {export_path}...")
        fieldnames = ['note_id', 'char', 'pinyin', 'english', 'rank', 'hsk', 'is_surname', 'tier', 'recommendation', 'tags']
        with open(export_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        print("Export completed successfully.")

    # Tag in Anki if requested
    if args.tag_rare and rare_note_ids:
        print(f"\nApplying 'recognition_only' tag to {len(rare_note_ids)} notes in Anki...")
        success = tag_notes_in_anki(rare_note_ids, "recognition_only")
        if success:
            print("Successfully tagged rare notes in Anki!")
        else:
            print("Failed to tag notes. Ensure Anki is running with AnkiConnect enabled.")

if __name__ == "__main__":
    main()
