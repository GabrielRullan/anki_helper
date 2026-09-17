import sqlite3
import os
import json

live_db_path = os.path.expanduser(r"~\AppData\Roaming\Anki2\Gabriel\collection.anki2")

temp_db = r"c:\Users\gabri\Documents\anki_helper\scratch\temp_verify.anki2"
import shutil
shutil.copyfile(live_db_path, temp_db)

conn = sqlite3.connect(temp_db)
cursor = conn.cursor()

# Check card status for '耶' (junda_1174_32822)
cursor.execute("""
    SELECT c.id, c.ord, c.type, c.queue, c.due, c.ivl, c.factor, c.reps, c.lapses, n.flds
    FROM cards c
    JOIN notes n ON c.nid = n.id
    WHERE n.flds LIKE '%junda_1174_32822%'
""")
rows = cursor.fetchall()
print("=== VERIFICATION FOR '耶' (junda_1174_32822) ===")
for r in rows:
    cid, c_ord, c_type, c_queue, c_due, c_ivl, c_factor, c_reps, c_lapses, flds = r
    print(f"CID: {cid} (ord={c_ord}): type={c_type} (2=Review), queue={c_queue} (2=Review), reps={c_reps}, ivl={c_ivl}d, factor={c_factor}, due={c_due}")

# Also verify how many total cards in the collection now have type=2 and queue=2
cursor.execute("SELECT count(*) FROM cards WHERE type=2 AND queue=2")
print(f"\nTotal active Review cards (type=2, queue=2) in collection: {cursor.fetchone()[0]}")

conn.close()
