import json
import urllib.request
import re
import csv
from collections import Counter, defaultdict

# 1. Fetch all notes and suspended state from AnkiConnect for Chinese::Char
def get_char_deck_info():
    # Find all notes in Chinese::Char
    req_notes = json.dumps({'action': 'findNotes', 'version': 6, 'params': {'query': 'deck:"Chinese::Char"'}}).encode('utf-8')
    with urllib.request.urlopen(urllib.request.Request('http://localhost:8765', req_notes)) as resp:
        all_char_note_ids = json.loads(resp.read().decode('utf-8'))['result']
        
    req_info = json.dumps({'action': 'notesInfo', 'version': 6, 'params': {'notes': all_char_note_ids}}).encode('utf-8')
    with urllib.request.urlopen(urllib.request.Request('http://localhost:8765', req_info)) as resp:
        char_notes = json.loads(resp.read().decode('utf-8'))['result']

    # Find suspended cards in Chinese::Char
    req_suspended = json.dumps({'action': 'findCards', 'version': 6, 'params': {'query': 'deck:"Chinese::Char" is:suspended'}}).encode('utf-8')
    with urllib.request.urlopen(urllib.request.Request('http://localhost:8765', req_suspended)) as resp:
        suspended_card_ids = set(json.loads(resp.read().decode('utf-8'))['result'])

    active_chars = set()
    suspended_chars = set()
    all_deck_chars = set()

    char_to_note_info = {}

    for note in char_notes:
        fields = note['fields']
        # Try Hanzi field, then Word field, then simplified
        c = fields.get('Hanzi', {}).get('value', '').strip()
        if not c:
            c = fields.get('Word', {}).get('value', '').strip()
        if not c:
            c = fields.get('Simplified', {}).get('value', '').strip()
            
        c_clean = re.sub(r'<[^>]+>', '', c).strip()
        
        # Extract CJK char
        cjk = [ch for ch in c_clean if '\u4e00' <= ch <= '\u9fff']
        for ch in cjk:
            all_deck_chars.add(ch)
            # Check if any card of this note is suspended
            is_suspended = any(card_id in suspended_card_ids for card_id in note.get('cards', []))
            if is_suspended:
                suspended_chars.add(ch)
            else:
                active_chars.add(ch)
            
            char_to_note_info[ch] = {
                'note_id': note['noteId'],
                'suspended': is_suspended,
                'pinyin': fields.get('Pinyin', {}).get('value', ''),
                'english': fields.get('English', {}).get('value', '')
            }

    return all_deck_chars, active_chars, suspended_chars, char_to_note_info

# 2. Read extracted Spoonfed phrases CSV
csv_in_path = r"c:\Users\gabri\Documents\anki_helper\data\spoonfed_phrases_extracted.csv"
spoonfed_rows = []
with open(csv_in_path, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for r in reader:
        spoonfed_rows.append(r)

# Extract every Hanzi from Spoonfed and count occurrences
spoonfed_char_counts = Counter()
char_to_spoonfed_sentences = defaultdict(list)

for row in spoonfed_rows:
    hanzi_text = row['Hanzi']
    for ch in hanzi_text:
        if '\u4e00' <= ch <= '\u9fff':
            spoonfed_char_counts[ch] += 1
            if len(char_to_spoonfed_sentences[ch]) < 5:
                char_to_spoonfed_sentences[ch].append(row)

unique_spoonfed_chars = set(spoonfed_char_counts.keys())

# 3. Perform comparison
all_deck_chars, active_chars, suspended_chars, char_to_note_info = get_char_deck_info()

completely_missing_chars = unique_spoonfed_chars - all_deck_chars
in_deck_active_chars = unique_spoonfed_chars.intersection(active_chars)
in_deck_suspended_only_chars = (unique_spoonfed_chars.intersection(suspended_chars)) - active_chars

print("=== SPOONFED HANZI VS CHINESE::CHAR DECK ANALYSIS ===")
print(f"Total Unique Hanzi in Spoonfed Chinese: {len(unique_spoonfed_chars)}")
print(f"Total Hanzi in Chinese::Char deck: {len(all_deck_chars)} (Active: {len(active_chars)}, Suspended: {len(suspended_chars)})")
print(f"\n1. Hanzi in Chinese::Char (ACTIVE): {len(in_deck_active_chars)} ({len(in_deck_active_chars)/len(unique_spoonfed_chars)*100:.2f}%)")
print(f"2. Hanzi in Chinese::Char (SUSPENDED ONLY): {len(in_deck_suspended_only_chars)} ({len(in_deck_suspended_only_chars)/len(unique_spoonfed_chars)*100:.2f}%)")
print(f"3. Hanzi NOT in Chinese::Char AT ALL (Not even suspended): {len(completely_missing_chars)} ({len(completely_missing_chars)/len(unique_spoonfed_chars)*100:.2f}%)")

# Detailed list of completely missing characters sorted by Spoonfed frequency
missing_list = []
for ch in completely_missing_chars:
    freq = spoonfed_char_counts[ch]
    sents = char_to_spoonfed_sentences[ch]
    missing_list.append({
        'char': ch,
        'spoonfed_frequency': freq,
        'example_sentences': sents
    })

missing_list.sort(key=lambda x: x['spoonfed_frequency'], reverse=True)

print(f"\n--- ALL {len(missing_list)} COMPLETELY MISSING CHARACTERS ---")
for idx, item in enumerate(missing_list, 1):
    c = item['char']
    freq = item['spoonfed_frequency']
    sample_sent = item['example_sentences'][0] if item['example_sentences'] else {}
    print(f"{idx:2d}. Character: '{c}' | Appears {freq} time(s) in Spoonfed | Example: {sample_sent.get('Hanzi', '')} ({sample_sent.get('Pinyin', '')}) -> '{sample_sent.get('English', '')}'")

# Write full missing details to JSON artifact/scratch
with open(r"c:\Users\gabri\Documents\anki_helper\scratch\missing_spoonfed_chars.json", 'w', encoding='utf-8') as f:
    json.dump({
        'total_spoonfed_chars': len(unique_spoonfed_chars),
        'total_deck_chars': len(all_deck_chars),
        'active_chars_count': len(in_deck_active_chars),
        'suspended_only_count': len(in_deck_suspended_only_chars),
        'completely_missing_count': len(completely_missing_chars),
        'missing_characters': missing_list
    }, f, indent=2, ensure_ascii=False)

