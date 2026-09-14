import sqlite3
import os
import shutil
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Try APPDATA database first, fallback to workspace anki_data/collection.anki2
appdata = os.getenv('APPDATA')
appdata_db = os.path.join(appdata, "Anki2", "Gabriel", "collection.anki2") if appdata else None

if appdata_db and os.path.exists(appdata_db):
    db_path = appdata_db
    print(f"Using AppData Anki DB: {db_path}")
else:
    db_path = os.path.abspath("anki_data/collection.anki2")
    print(f"Using Workspace Anki DB: {db_path}")

# Copy to temp file to avoid locks
temp_db = os.path.abspath("scratch/temp_anki.anki2")
shutil.copy2(db_path, temp_db)
if os.path.exists(db_path + "-wal"):
    try:
        shutil.copy2(db_path + "-wal", temp_db + "-wal")
    except OSError:
        pass

conn = sqlite3.connect(temp_db)
cursor = conn.cursor()

# Get all decks
cursor.execute("SELECT id, name FROM decks")
decks = {row[0]: row[1] for row in cursor.fetchall()}
print("Decks found in Anki:")
for did, name in decks.items():
    print(f"  [{did}] {name}")

# Get all notes
cursor.execute("SELECT id, mid, flds FROM notes")
notes_raw = cursor.fetchall()
print(f"Total notes in collection: {len(notes_raw)}")

# Extract all field strings from all notes across all decks
anki_words = set()
anki_chars = set()

for n_id, mid, flds in notes_raw:
    fields = flds.split('\x1f')
    for f in fields:
        # Clean HTML tags if any
        clean_f = f.strip()
        if clean_f:
            anki_words.add(clean_f)
            for char in clean_f:
                if '\u4e00' <= char <= '\u9fff':
                    anki_chars.add(char)

print(f"Total unique field values indexed: {len(anki_words)}")
print(f"Total unique Hanzi characters in Anki: {len(anki_chars)}")

# Clean up temp db
conn.close()
if os.path.exists(temp_db):
    os.remove(temp_db)
if os.path.exists(temp_db + "-wal"):
    os.remove(temp_db + "-wal")

# Now check against levels 68 to 88
with open('scratch/levels_68_88.json', 'r', encoding='utf-8') as f:
    levels_data = json.load(f)

missing_words_total = 0
missing_hanzi_total = 0
total_words_check = 0
total_hanzi_check = 0

for lvl in range(68, 89):
    lvl_str = str(lvl)
    data = levels_data.get(lvl_str, {})
    words = data.get('All Words', {}).get('new', [])
    hanzi = data.get('All Characters', {}).get('new', [])

    missing_words = [w for w in words if w not in anki_words]
    missing_hanzi = [h for h in hanzi if h not in anki_chars]

    total_words_check += len(words)
    total_hanzi_check += len(hanzi)
    missing_words_total += len(missing_words)
    missing_hanzi_total += len(missing_hanzi)

    print(f"Level {lvl}: Hanzi missing={len(missing_hanzi)}/{len(hanzi)}, Words missing={len(missing_words)}/{len(words)}")

print(f"\nOVERALL: Missing Hanzi={missing_hanzi_total}/{total_hanzi_check}, Missing Words={missing_words_total}/{total_words_check}")
