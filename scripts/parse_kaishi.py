import sqlite3
import json
import os
import shutil
import re

extract_dir = "data/kaishi_temp"
db_path = os.path.join(extract_dir, "collection.anki21")
media_map_path = os.path.join(extract_dir, "media")
output_json_path = "data/kaishi_cards.json"

if not os.path.exists(db_path):
    db_path = os.path.join(extract_dir, "collection.anki2")

if not os.path.exists(db_path) or not os.path.exists(media_map_path):
    print("Error: Extract files missing in data/kaishi_temp")
    exit(1)

print("Loading media map...")
with open(media_map_path, 'r', encoding='utf-8') as f:
    media_map = json.load(f)

# Invert media map: maps real filename to index string
media_filename_to_idx = {v: k for k, v in media_map.items()}

print("Connecting to Anki SQLite DB...")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Fetch notes
cursor.execute("SELECT flds FROM notes")
notes_rows = cursor.fetchall()

cards = []

def clean_media_ref(field_val):
    # Extracts filename from [sound:filename.mp3] or <img src="filename.jpg">
    if not field_val:
        return ""
    # Check sound
    sound_match = re.search(r'\[sound:([^\]]+)\]', field_val)
    if sound_match:
        return sound_match.group(1).strip()
    # Check image
    img_match = re.search(r'<img src="([^"]+)"', field_val)
    if img_match:
        return img_match.group(1).strip()
    return field_val.strip()

print("Parsing notes...")
for row in notes_rows:
    fields = row[0].split('\x1f')
    if len(fields) < 14:
        continue
    
    word = fields[0].strip()
    word_reading = fields[1].strip()
    word_meaning = fields[2].strip()
    word_furigana = fields[3].strip()
    word_audio_ref = fields[4].strip()
    sentence = fields[5].strip()
    sentence_meaning = fields[6].strip()
    sentence_furigana = fields[7].strip()
    sentence_audio_ref = fields[8].strip()
    notes = fields[9].strip()
    pitch_accent = fields[10].strip()
    pitch_accent_notes = fields[11].strip()
    frequency = fields[12].strip()
    picture_ref = fields[13].strip()
    
    word_audio_file = clean_media_ref(word_audio_ref)
    sentence_audio_file = clean_media_ref(sentence_audio_ref)
    picture_file = clean_media_ref(picture_ref)
    
    media_mappings = {}
    if word_audio_file and word_audio_file in media_filename_to_idx:
        media_mappings['word_audio'] = os.path.join(extract_dir, media_filename_to_idx[word_audio_file])
    if sentence_audio_file and sentence_audio_file in media_filename_to_idx:
        media_mappings['sentence_audio'] = os.path.join(extract_dir, media_filename_to_idx[sentence_audio_file])
    if picture_file and picture_file in media_filename_to_idx:
        media_mappings['picture'] = os.path.join(extract_dir, media_filename_to_idx[picture_file])

    cards.append({
        'word': word,
        'word_reading': word_reading,
        'word_meaning': word_meaning,
        'word_furigana': word_furigana,
        'word_audio': word_audio_file,
        'sentence': sentence,
        'sentence_meaning': sentence_meaning,
        'sentence_furigana': word_reading if not sentence_furigana else sentence_furigana, # Fallback reading
        'sentence_audio': sentence_audio_file,
        'notes': notes,
        'pitch_accent': pitch_accent,
        'pitch_accent_notes': pitch_accent_notes,
        'frequency': frequency,
        'picture': picture_file,
        'media_mappings': media_mappings
    })

conn.close()

print(f"Saving {len(cards)} parsed cards to {output_json_path}...")
with open(output_json_path, 'w', encoding='utf-8') as f:
    json.dump(cards, f, ensure_ascii=False, indent=2)

print("Parse complete!")
