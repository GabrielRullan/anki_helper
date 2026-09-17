import zipfile
import sqlite3
import json
import os
import shutil

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

# Get table names
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("Tables:", tables)

# Get count of notes
cursor.execute("SELECT count(*) FROM notes")
print("Notes count:", cursor.fetchone()[0])

# Get model details from col table
cursor.execute("SELECT models FROM col")
models_raw = cursor.fetchone()[0]
models = json.loads(models_raw)
print("Models keys:", list(models.keys()))
for mid, mdef in models.items():
    print(f"Model {mid}: name={mdef.get('name')}, fields={[f['name'] for f in mdef.get('flds', [])]}")

# Sample notes
cursor.execute("SELECT id, mid, flds FROM notes LIMIT 10")
for row in cursor.fetchall():
    fields = row[2].split("\x1f")
    print("--- Note Sample ---")
    print(fields)

conn.close()
