import sqlite3
import os
import shutil
import json
from datetime import datetime

# 1. Paths
live_db_path = os.path.expanduser(r"~\AppData\Roaming\Anki2\Gabriel\collection.anki2")
safety_backup_path = r"c:\Users\gabri\Documents\anki_helper\anki_data\collection_backup_before_restoration.anki2"
plan_path = r"c:\Users\gabri\Documents\anki_helper\scratch\full_restoration_plan.json"

# Make safety backup
print(f"Creating safety backup at: {safety_backup_path}...")
shutil.copyfile(live_db_path, safety_backup_path)
print("Safety backup created successfully!")

with open(plan_path, 'r', encoding='utf-8') as f:
    restoration_items = json.load(f)

print(f"Loaded {len(restoration_items)} cards to restore.")

conn = sqlite3.connect(live_db_path)
cursor = conn.cursor()

updated_count = 0

for item in restoration_items:
    cid = item['live_cid']
    new_type = item['new_type']
    new_queue = item['new_queue']
    new_due = item['new_due']
    new_ivl = item['new_ivl']
    new_factor = item['new_factor']
    new_reps = item['new_reps']
    new_lapses = item['new_lapses']
    
    cursor.execute("""
        UPDATE cards
        SET type = ?, queue = ?, due = ?, ivl = ?, factor = ?, reps = ?, lapses = ?, mod = ?
        WHERE id = ?
    """, (new_type, new_queue, new_due, new_ivl, new_factor, new_reps, new_lapses, int(datetime.now().timestamp()), cid))
    
    if cursor.rowcount > 0:
        updated_count += 1

conn.commit()
conn.close()

print(f"\n=======================================================")
print(f"SUCCESSFULLY RESTORED {updated_count} CARDS IN LIVE ANKI DATABASE!")
print(f"=======================================================")
