import zstandard
import sqlite3
import os

compressed_path = r"c:\Users\gabri\Documents\anki_helper\scratch\aug09_backup_extracted\collection.anki21b"
decompressed_db = r"c:\Users\gabri\Documents\anki_helper\scratch\aug09_backup_extracted\collection_decompressed.anki2"

dctx = zstandard.ZstdDecompressor()
with open(compressed_path, 'rb') as ifh, open(decompressed_db, 'wb') as ofh:
    dctx.copy_stream(ifh, ofh)

print(f"Decompressed collection.anki21b to {decompressed_db}! Size: {os.path.getsize(decompressed_db)} bytes.")

conn = sqlite3.connect(decompressed_db)
cursor = conn.cursor()

# Get table names
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
print("Tables:", cursor.fetchall())

# Get model details
cursor.execute("SELECT models FROM col")
import json
models = json.loads(cursor.fetchone()[0])
print("Models in backup DB:")
for mid, mdef in models.items():
    print(f"  Model {mid}: {mdef.get('name')}")

# Sample notes
cursor.execute("SELECT count(*) FROM notes")
print("Total notes in backup DB:", cursor.fetchone()[0])

cursor.execute("SELECT count(*) FROM cards")
print("Total cards in backup DB:", cursor.fetchone()[0])

conn.close()
