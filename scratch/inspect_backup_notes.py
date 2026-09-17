import sqlite3
import os
import json

db_path = r"c:\Users\gabri\Documents\anki_helper\scratch\aug09_backup_extracted\collection.anki2"

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get model details
cursor.execute("SELECT models FROM col")
models_raw = cursor.fetchone()[0]
models = json.loads(models_raw)

print("Models in August 09 Backup DB:")
for mid, mdef in models.items():
    print(f"Model ID {mid}: name='{mdef.get('name')}', fields={[f['name'] for f in mdef.get('flds', [])]}")

# Sample notes
cursor.execute("SELECT id, mid, flds, tags FROM notes LIMIT 10")
for row in cursor.fetchall():
    nid, mid, flds, tags = row
    print(f"\nNote NID: {nid} | Model ID: {mid} | Tags: {tags}")
    print("  Fields:", flds.split("\x1f")[:5])

conn.close()
