import sqlite3
import os
import glob
import json

print("--- Searching backup databases in anki_data or scratch ---")
backup_files = glob.glob(r"c:\Users\gabri\Documents\anki_helper\**\*.anki2", recursive=True)
print(f"Found {len(backup_files)} database files:")

for bf in backup_files:
    try:
        conn = sqlite3.connect(bf)
        cursor = conn.cursor()
        cursor.execute("SELECT id, flds, tags FROM notes WHERE flds LIKE '%junda_1174_32822%' OR flds LIKE '%耶%'")
        rows = cursor.fetchall()
        if rows:
            print(f"\nIn DB '{bf}':")
            for r in rows:
                print(f"  NID {r[0]}: fields_sample='{r[1][:80]}...' | tags='{r[2]}'")
        conn.close()
    except Exception as e:
        pass
