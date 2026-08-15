import os
import sys
import csv
import json
import urllib.request
import time
from collections import defaultdict
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

def capitalize_phrase(s):
    s = s.strip()
    if not s:
        return ''
    for idx, ch in enumerate(s):
        if ch.isalpha():
            return s[:idx] + ch.upper() + s[idx+1:]
    return s

def capitalize_words_translation(tow_str):
    if not tow_str:
        return ''
    parts = tow_str.split(',')
    return ', '.join([capitalize_phrase(p) for p in parts])

def main():
    print("=" * 70, flush=True)
    print("   POPULATING COMMON WORDS & TRANSLATIONS FOR CHARACTER DECK")
    print("=" * 70, flush=True)

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 1. Build offline word dictionary mapping: char -> [(word, translation)]
    char_words_map = defaultdict(list)

    # Load from junda_freq.csv words & definitions if present
    junda_csv = os.path.join(base_dir, "data", "junda_freq.csv")
    if os.path.exists(junda_csv):
        with open(junda_csv, 'r', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                c = row.get('character', '').strip()
                def_str = row.get('definition', '').strip()
                if c and def_str:
                    char_words_map[c].append((c, capitalize_phrase(def_str)))

    # Load from data/new_characters.csv
    new_chars_csv = os.path.join(base_dir, "data", "new_characters.csv")
    if os.path.exists(new_chars_csv):
        with open(new_chars_csv, 'r', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                c = row.get('Hanzi', row.get('Simplified', '')).strip()
                cw = row.get('Common Words', '').strip()
                tw = row.get('Translation of Words', '').strip()
                if c and cw and tw:
                    cwords = [w.strip() for w in cw.split(',')]
                    ctrans = [t.strip() for t in tw.split(',')]
                    for w, t in zip(cwords, ctrans):
                        if w and t and (w, capitalize_phrase(t)) not in char_words_map[c]:
                            char_words_map[c].append((w, capitalize_phrase(t)))

    # Load from data/kaishi_cards.json
    kaishi_json = os.path.join(base_dir, "data", "kaishi_cards.json")
    if os.path.exists(kaishi_json):
        try:
            with open(kaishi_json, 'r', encoding='utf-8') as f:
                kaishi_data = json.load(f)
                for item in kaishi_data:
                    word = item.get('word', '').strip()
                    trans = item.get('translation', item.get('english', '')).strip()
                    if word and trans:
                        for char in word:
                            if '\u4e00' <= char <= '\u9fff':
                                if len(char_words_map[char]) < 5:
                                    pair = (word, capitalize_phrase(trans))
                                    if pair not in char_words_map[char]:
                                        char_words_map[char].append(pair)
        except Exception as e:
            print(f"Notice: kaishi_cards.json read note ({e})", flush=True)

    print(f"Built offline vocabulary database for {len(char_words_map):,} Chinese characters.", flush=True)

    # 2. Query Anki notes missing Common Words
    note_ids = request_anki("findNotes", query='deck:Chinese::Char')
    if not note_ids:
        print("Error: No notes found in Chinese::Char deck", flush=True)
        return

    notes_info = request_anki("notesInfo", notes=note_ids)
    print(f"Found {len(notes_info):,} total character notes in Anki.", flush=True)

    update_payloads = []
    for note in notes_info:
        f = note.get('fields', {})
        nid = note['noteId']
        c = f.get('Hanzi', {}).get('value', '').strip() or f.get('Simplified', {}).get('value', '').strip()
        if not c:
            continue

        cw_current = f.get('Common Words', {}).get('value', '').strip()
        tw_current = f.get('Translation of Words', {}).get('value', '').strip()

        if not cw_current or not tw_current:
            pairs = char_words_map.get(c, [])
            if pairs:
                cw_new = ", ".join([p[0] for p in pairs[:3]])
                tw_new = ", ".join([p[1] for p in pairs[:3]])

                update_payloads.append({
                    "id": nid,
                    "fields": {
                        "Common Words": cw_new,
                        "Translation of Words": tw_new
                    }
                })

    print(f"Found {len(update_payloads):,} character notes missing Common Words that can be populated.", flush=True)

    def update_single(p):
        return request_anki("updateNoteFields", note=p)

    if update_payloads:
        chunk_size = 100
        for i in range(0, len(update_payloads), chunk_size):
            chunk = update_payloads[i:i + chunk_size]
            with ThreadPoolExecutor(max_workers=5) as executor:
                list(executor.map(update_single, chunk))
            print(f"  Progress: {min(i + chunk_size, len(update_payloads))}/{len(update_payloads)} notes updated.", flush=True)

        print(f"\nSuccessfully populated Common Words on {len(update_payloads):,} notes!", flush=True)
    else:
        print("\nAll character notes already have Common Words populated.", flush=True)

    print("=" * 70, flush=True)

if __name__ == "__main__":
    main()
