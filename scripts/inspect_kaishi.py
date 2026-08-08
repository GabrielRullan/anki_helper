import sqlite3
import json
import os

extract_dir = "data/kaishi_temp"
db_path = os.path.join(extract_dir, "collection.anki21")

if not os.path.exists(db_path):
    print("collection.anki21 not found, trying collection.anki2")
    db_path = os.path.join(extract_dir, "collection.anki2")

print(f"Opening SQLite database at {db_path}...")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get model names and fields from col table
cursor.execute("SELECT models FROM col")
models_json = cursor.fetchone()[0]
models = json.loads(models_json)

print("\n--- Note Types in APKG ---")
for mid, model in models.items():
    print(f"ID: {mid}, Name: {model['name']}")
    print("Fields:")
    for fld in model['flds']:
        print(f"  - {fld['name']} (index {fld['ord']})")

# Let's count notes
cursor.execute("SELECT count(*) FROM notes")
count = cursor.fetchone()[0]
print(f"\nTotal notes: {count}")

# Print first few notes fields
cursor.execute("SELECT flds, mid FROM notes LIMIT 5")
rows = cursor.fetchall()
for idx, (flds, mid) in enumerate(rows):
    print(f"\nNote {idx+1} (model ID {mid}):")
    print(flds.split('\x1f'))

conn.close()
