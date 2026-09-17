import os
import json
import sqlite3
import zipfile
import re
import urllib.request
import jieba
import csv
from collections import Counter

# 1. Unpack APKG if not already done
apkg_path = r"c:\Users\gabri\Documents\anki_helper\data\SpoonfedChineseSimplified.apkg"
extract_dir = r"c:\Users\gabri\Documents\anki_helper\scratch\spoonfed_extracted"

os.makedirs(extract_dir, exist_ok=True)

with zipfile.ZipFile(apkg_path, 'r') as zip_ref:
    zip_ref.extractall(extract_dir)

db_path = os.path.join(extract_dir, "collection.anki2")
if not os.path.exists(db_path):
    db_path = os.path.join(extract_dir, "collection.anki21")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT id, flds FROM notes")
rows = cursor.fetchall()
conn.close()

spoonfed_notes = []
for row_id, flds_str in rows:
    flds = flds_str.split("\x1f")
    # Fields: ['English', 'Pinyin', 'Hanzi', 'Audio']
    english = flds[0] if len(flds) > 0 else ""
    pinyin = flds[1] if len(flds) > 1 else ""
    hanzi = flds[2] if len(flds) > 2 else ""
    audio = flds[3] if len(flds) > 3 else ""
    
    spoonfed_notes.append({
        'id': row_id,
        'hanzi': hanzi.strip(),
        'pinyin': pinyin.strip(),
        'english': english.strip(),
        'audio': audio.strip()
    })

print(f"Total extracted Spoonfed notes: {len(spoonfed_notes)}")

# 2. Get User's Known Words & Characters from AnkiConnect
def get_user_anki_data():
    req_data_words = json.dumps({'action': 'findNotes', 'version': 6, 'params': {'query': 'deck:"Chinese::Words"'}}).encode('utf-8')
    req = urllib.request.Request('http://localhost:8765', req_data_words)
    with urllib.request.urlopen(req) as resp:
        word_ids = json.loads(resp.read().decode('utf-8'))['result']
    
    req_data_info = json.dumps({'action': 'notesInfo', 'version': 6, 'params': {'notes': word_ids}}).encode('utf-8')
    req = urllib.request.Request('http://localhost:8765', req_data_info)
    with urllib.request.urlopen(req) as resp:
        word_notes = json.loads(resp.read().decode('utf-8'))['result']
        
    known_words = set()
    for n in word_notes:
        w = n['fields']['Word']['value'].strip()
        # Clean HTML or tags
        w_clean = re.sub(r'<[^>]+>', '', w)
        if w_clean:
            known_words.add(w_clean)
            
    # Also fetch Chinese::Char
    req_data_chars = json.dumps({'action': 'findNotes', 'version': 6, 'params': {'query': 'deck:"Chinese::Char"'}}).encode('utf-8')
    req = urllib.request.Request('http://localhost:8765', req_data_chars)
    with urllib.request.urlopen(req) as resp:
        char_ids = json.loads(resp.read().decode('utf-8'))['result']
        
    req_data_cinfo = json.dumps({'action': 'notesInfo', 'version': 6, 'params': {'notes': char_ids}}).encode('utf-8')
    req = urllib.request.Request('http://localhost:8765', req_data_cinfo)
    with urllib.request.urlopen(req) as resp:
        char_notes = json.loads(resp.read().decode('utf-8'))['result']
        
    known_chars = set()
    for n in char_notes:
        c = n['fields']['Hanzi']['value'].strip() if 'Hanzi' in n['fields'] else ""
        if not c and 'Word' in n['fields']:
            c = n['fields']['Word']['value'].strip()
        c_clean = re.sub(r'<[^>]+>', '', c)
        if c_clean:
            known_chars.add(c_clean)
            
    return known_words, known_chars

known_words, known_chars = get_user_anki_data()
print(f"Loaded {len(known_words)} target words from Chinese::Words")
print(f"Loaded {len(known_chars)} target characters from Chinese::Char")

# 3. Quality & Audio Analysis
has_audio_count = 0
audio_tag_format_count = 0
pinyin_has_tone_marks = 0
empty_hanzi = 0
empty_english = 0
html_tag_count = 0

all_spoonfed_words = Counter()
all_spoonfed_chars = Counter()

processed_sentences = []

for idx, note in enumerate(spoonfed_notes):
    hanzi = note['hanzi']
    pinyin = note['pinyin']
    english = note['english']
    audio = note['audio']
    
    # Check HTML tags
    if '<' in hanzi or '<' in pinyin or '<' in english:
        html_tag_count += 1
        
    # Clean text for analysis
    clean_hanzi = re.sub(r'<[^>]+>', '', hanzi)
    clean_pinyin = re.sub(r'<[^>]+>', '', pinyin)
    clean_english = re.sub(r'<[^>]+>', '', english)
    
    if not clean_hanzi:
        empty_hanzi += 1
    if not clean_english:
        empty_english += 1
        
    if audio:
        has_audio_count += 1
        if '[sound:' in audio:
            audio_tag_format_count += 1
            
    # Check pinyin tone marks vs tone numbers
    if re.search(r'[āáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜ]', clean_pinyin):
        pinyin_has_tone_marks += 1
        
    # Extract Hanzi characters (only CJK)
    cjk_chars = [ch for ch in clean_hanzi if '\u4e00' <= ch <= '\u9fff']
    for ch in cjk_chars:
        all_spoonfed_chars[ch] += 1
        
    # Word segmentation
    words = [w for w in jieba.cut(clean_hanzi) if any('\u4e00' <= ch <= '\u9fff' for ch in w)]
    for w in words:
        all_spoonfed_words[w] += 1
        
    # Overlap analysis per sentence
    unknown_words = [w for w in words if w not in known_words]
    known_words_in_sent = [w for w in words if w in known_words]
    
    # Check character overlap
    unknown_chars_in_sent = [ch for ch in cjk_chars if ch not in known_chars]
    
    processed_sentences.append({
        'id': note['id'],
        'hanzi': clean_hanzi,
        'pinyin': clean_pinyin,
        'english': clean_english,
        'audio': audio,
        'char_count': len(cjk_chars),
        'word_count': len(words),
        'words': words,
        'unknown_words': unknown_words,
        'num_unknown_words': len(unknown_words),
        'unknown_chars': unknown_chars_in_sent,
        'num_unknown_chars': len(unknown_chars_in_sent)
    })

# 4. Global Overlap Calculations
unique_spoonfed_words = set(all_spoonfed_words.keys())
unique_spoonfed_chars = set(all_spoonfed_chars.keys())

words_covered = unique_spoonfed_words.intersection(known_words)
words_missing = unique_spoonfed_words - known_words

chars_covered = unique_spoonfed_chars.intersection(known_chars)
chars_missing = unique_spoonfed_chars - known_chars

# Sentence breakdown by unknown word count
sent_0_unknown = [s for s in processed_sentences if s['num_unknown_words'] == 0]
sent_1_unknown = [s for s in processed_sentences if s['num_unknown_words'] == 1]
sent_2_unknown = [s for s in processed_sentences if s['num_unknown_words'] == 2]
sent_3plus_unknown = [s for s in processed_sentences if s['num_unknown_words'] >= 3]

# Write extracted dataset to CSV file
csv_out_path = r"c:\Users\gabri\Documents\anki_helper\data\spoonfed_phrases_extracted.csv"
with open(csv_out_path, 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['ID', 'Hanzi', 'Pinyin', 'English', 'Audio', 'Word Count', 'Char Count', 'Unknown Words Count', 'Unknown Words List'])
    for s in processed_sentences:
        writer.writerow([
            s['id'],
            s['hanzi'],
            s['pinyin'],
            s['english'],
            s['audio'],
            s['word_count'],
            s['char_count'],
            s['num_unknown_words'],
            ", ".join(s['unknown_words'])
        ])

print(f"\n--- Extracted CSV saved to {csv_out_path} ---")

report_stats = {
    'total_sentences': len(spoonfed_notes),
    'quality': {
        'has_audio_pct': (has_audio_count / len(spoonfed_notes)) * 100,
        'pinyin_tone_marks_pct': (pinyin_has_tone_marks / len(spoonfed_notes)) * 100,
        'empty_hanzi': empty_hanzi,
        'empty_english': empty_english,
        'html_tag_count': html_tag_count
    },
    'words_summary': {
        'total_unique_spoonfed_words': len(unique_spoonfed_words),
        'words_covered_count': len(words_covered),
        'words_covered_pct': (len(words_covered) / len(unique_spoonfed_words)) * 100 if unique_spoonfed_words else 0,
        'user_known_words_total': len(known_words),
        'user_known_words_in_spoonfed_pct': (len(words_covered) / len(known_words)) * 100 if known_words else 0
    },
    'chars_summary': {
        'total_unique_spoonfed_chars': len(unique_spoonfed_chars),
        'chars_covered_count': len(chars_covered),
        'chars_covered_pct': (len(chars_covered) / len(unique_spoonfed_chars)) * 100 if unique_spoonfed_chars else 0,
        'user_known_chars_total': len(known_chars)
    },
    'sentence_comprehension': {
        'i_plus_0_count': len(sent_0_unknown),
        'i_plus_0_pct': (len(sent_0_unknown) / len(processed_sentences)) * 100,
        'i_plus_1_count': len(sent_1_unknown),
        'i_plus_1_pct': (len(sent_1_unknown) / len(processed_sentences)) * 100,
        'i_plus_2_count': len(sent_2_unknown),
        'i_plus_2_pct': (len(sent_2_unknown) / len(processed_sentences)) * 100,
        'i_plus_3plus_count': len(sent_3plus_unknown),
        'i_plus_3plus_pct': (len(sent_3plus_unknown) / len(processed_sentences)) * 100
    }
}

with open(r"c:\Users\gabri\Documents\anki_helper\scratch\spoonfed_analysis_result.json", 'w', encoding='utf-8') as f:
    json.dump(report_stats, f, indent=2, ensure_ascii=False)

print("\n--- Summary Report JSON ---")
print(json.dumps(report_stats, indent=2, ensure_ascii=False))
