import sqlite3
import os
import shutil
import subprocess
import json
import time
from datetime import datetime

# 1. Close Anki process
print("Closing Anki process...")
try:
    subprocess.run(["taskkill", "/F", "/IM", "anki.exe"], capture_output=True)
    time.sleep(1.5)
    print("Anki process closed.")
except Exception as e:
    print("Taskkill exception:", e)

live_db_path = os.path.expanduser(r"~\AppData\Roaming\Anki2\Gabriel\collection.anki2")
safety_backup_path = r"c:\Users\gabri\Documents\anki_helper\anki_data\collection_backup_junda_sync.anki2"

# Make safety backup
shutil.copyfile(live_db_path, safety_backup_path)
print(f"Safety backup created at {safety_backup_path}")

conn = sqlite3.connect(live_db_path)
cursor = conn.cursor()

# Query all Junda notes where Card 0 has reps > 0 and type = 2, but Card 1 has reps = 0 or queue = -1
cursor.execute("""
    SELECT n.id, n.flds, n.tags,
           c0.id, c0.type, c0.queue, c0.due, c0.ivl, c0.factor, c0.reps, c0.lapses,
           c1.id, c1.type, c1.queue, c1.due, c1.ivl, c1.factor, c1.reps, c1.lapses
    FROM notes n
    JOIN cards c0 ON n.id = c0.nid AND c0.ord = 0
    JOIN cards c1 ON n.id = c1.nid AND c1.ord = 1
    WHERE (n.tags LIKE '%junda%' OR n.flds LIKE '%junda_%')
      AND c0.reps > 0
      AND (c1.reps == 0 OR c1.queue == -1 OR c1.type == 0)
""")

mismatched_junda = cursor.fetchall()
print(f"\nFound {len(mismatched_junda)} Junda notes where Card 0 is reviewed but Card 1 is new/suspended:")

now_ts = int(datetime.now().timestamp())
updated_count = 0

for row in mismatched_junda:
    nid, flds, tags, c0_id, c0_type, c0_queue, c0_due, c0_ivl, c0_factor, c0_reps, c0_lapses, c1_id, c1_type, c1_queue, c1_due, c1_ivl, c1_factor, c1_reps, c1_lapses = row
    hanzi = flds.split("\x1f")[1] if len(flds.split("\x1f")) > 1 else ""
    id_field = flds.split("\x1f")[0] if len(flds.split("\x1f")) > 0 else ""
    
    print(f"  Hanzi: '{hanzi}' ({id_field}) | Syncing Card 1 (CID {c1_id}) to Card 0 (ivl={c0_ivl}d, factor={c0_factor}, reps={c0_reps})")
    
    cursor.execute("""
        UPDATE cards
        SET type = ?, queue = ?, due = ?, ivl = ?, factor = ?, reps = ?, lapses = ?, mod = ?
        WHERE id = ?
    """, (c0_type, c0_queue, c0_due, c0_ivl, c0_factor, c0_reps, c0_lapses, now_ts, c1_id))
    
    if cursor.rowcount > 0:
        updated_count += 1

conn.commit()
conn.close()

print(f"\nSuccessfully synced {updated_count} Junda Recall cards to match Recognition card history!")

print("Restarting Anki...")
try:
    subprocess.Popen([r"C:\Users\gabri\AppData\Local\Programs\Anki\anki.exe"])
    print("Anki restarted!")
except Exception as e:
    print("Error starting Anki:", e)
