import os
import shutil
import sqlite3
import subprocess
import json
import time
from datetime import datetime

print("Step 1: Closing Anki process if running...")
try:
    subprocess.run(["taskkill", "/F", "/IM", "anki.exe"], capture_output=True)
    time.sleep(1.5)
    print("Anki closed successfully.")
except Exception as e:
    print("Taskkill note:", e)

live_db_path = os.path.expanduser(r"~\AppData\Roaming\Anki2\Gabriel\collection.anki2")
safety_backup_path = r"c:\Users\gabri\Documents\anki_helper\anki_data\collection_backup_before_restoration.anki2"
plan_path = r"c:\Users\gabri\Documents\anki_helper\scratch\full_restoration_plan.json"

print(f"\nStep 2: Creating safety backup at: {safety_backup_path}...")
shutil.copyfile(live_db_path, safety_backup_path)
print("Safety backup created successfully!")

with open(plan_path, 'r', encoding='utf-8') as f:
    restoration_items = json.load(f)

print(f"\nStep 3: Restoring {len(restoration_items)} cards in live collection...")
conn = sqlite3.connect(live_db_path)
cursor = conn.cursor()

updated_count = 0
now_ts = int(datetime.now().timestamp())

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
    """, (new_type, new_queue, new_due, new_ivl, new_factor, new_reps, new_lapses, now_ts, cid))
    
    if cursor.rowcount > 0:
        updated_count += 1

conn.commit()
conn.close()

print(f"\nSuccessfully restored {updated_count} cards in live database!")

print("\nStep 4: Restarting Anki...")
try:
    subprocess.Popen(["cmd.exe", "/c", "start", "", "anki"], shell=True)
    print("Anki restarted successfully!")
except Exception as e:
    print("Error starting Anki:", e)
