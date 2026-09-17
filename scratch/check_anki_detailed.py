import sqlite3
import os
import shutil
import json
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

appdata = os.getenv('APPDATA')
appdata_db = os.path.join(appdata, "Anki2", "Gabriel", "collection.anki2") if appdata else None

if appdata_db and os.path.exists(appdata_db):
    db_path = appdata_db
    print(f"Using AppData Anki DB: {db_path}")
else:
    db_path = os.path.abspath("anki_data/collection.anki2")
    print(f"Using Workspace Anki DB: {db_path}")

temp_db = os.path.abspath("scratch/temp_anki_detailed.anki2")
shutil.copy2(db_path, temp_db)
if os.path.exists(db_path + "-wal"):
    try:
        shutil.copy2(db_path + "-wal", temp_db + "-wal")
    except OSError:
        pass

conn = sqlite3.connect(temp_db)
cursor = conn.cursor()

# Get deck mapping
cursor.execute("SELECT id, name FROM decks")
decks = {row[0]: row[1] for row in cursor.fetchall()}

# Find target deck IDs
chinese_word_dids = [did for did, name in decks.items() if 'Word' in name or 'Chinese' in name]
chinese_char_dids = [did for did, name in decks.items() if 'Char' in name or 'Chinese' in name]

# Extract notes from cards in Chinese decks
cursor.execute("""
    SELECT c.did, n.flds 
    FROM cards c 
    JOIN notes n ON c.nid = n.id
""")
all_cards = cursor.fetchall()

existing_words_exact = set()
existing_words_fields = set()
existing_chars_exact = set()
all_chinese_chars_in_anki = set()

def clean_text(text):
    text = re.sub(r'<[^>]+>', '', text)  # remove HTML
    return text.strip()

for did, flds in all_cards:
    deck_name = decks.get(did, '')
    fields = [clean_text(f) for f in flds.split('\x1f')]
    
    # Check if in Chinese deck
    if 'Chinese' in deck_name or 'Word' in deck_name or 'Char' in deck_name:
        for f in fields:
            if f:
                existing_words_fields.add(f)
                # First field is usually the target word / hanzi
                existing_words_exact.add(fields[0])
                for char in f:
                    if '\u4e00' <= char <= '\u9fff':
                        all_chinese_chars_in_anki.add(char)
                        if 'Char' in deck_name:
                            existing_chars_exact.add(char)

# Also check all notes in general
cursor.execute("SELECT flds FROM notes")
for (flds,) in cursor.fetchall():
    fields = [clean_text(f) for f in flds.split('\x1f')]
    for f in fields:
        if f:
            existing_words_fields.add(f)
            for char in f:
                if '\u4e00' <= char <= '\u9fff':
                    all_chinese_chars_in_anki.add(char)

print(f"Total Chinese characters in Anki: {len(all_chinese_chars_in_anki)}")
print(f"Total exact words in Anki decks: {len(existing_words_exact)}")

conn.close()
if os.path.exists(temp_db):
    os.remove(temp_db)
if os.path.exists(temp_db + "-wal"):
    os.remove(temp_db + "-wal")

# Save processed results to JSON
with open('scratch/levels_68_88.json', 'r', encoding='utf-8') as f:
    levels_data = json.load(f)

annotated_data = {}

for lvl in range(68, 89):
    lvl_str = str(lvl)
    data = levels_data.get(lvl_str, {})
    words = data.get('All Words', {}).get('new', [])
    hanzi = data.get('All Characters', {}).get('new', [])

    annotated_words = []
    for w in words:
        # Check exact word match or field match
        in_anki = (w in existing_words_fields) or (w in existing_words_exact)
        annotated_words.append({
            'word': w,
            'in_anki': in_anki
        })

    annotated_hanzi = []
    for h in hanzi:
        # Check character presence in character deck or overall anki chars
        in_anki = (h in all_chinese_chars_in_anki)
        annotated_hanzi.append({
            'hanzi': h,
            'in_anki': in_anki
        })

    annotated_data[lvl_str] = {
        'hanzi': annotated_hanzi,
        'words': annotated_words
    }

with open('scratch/annotated_anki_68_88.json', 'w', encoding='utf-8') as f:
    json.dump(annotated_data, f, ensure_ascii=False, indent=2)

print("Saved annotated results to scratch/annotated_anki_68_88.json")
