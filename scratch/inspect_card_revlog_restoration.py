import sqlite3
import os
import shutil
import json
from datetime import datetime

anki_db_path = os.path.expanduser(r"~\AppData\Roaming\Anki2\Gabriel\collection.anki2")
if not os.path.exists(anki_db_path):
    anki_db_path = r"c:\Users\gabri\Documents\anki_helper\anki_data\collection.anki2"

temp_db = r"c:\Users\gabri\Documents\anki_helper\scratch\temp_inspect_revlog2.anki2"
shutil.copyfile(anki_db_path, temp_db)

conn = sqlite3.connect(temp_db)
cursor = conn.cursor()

# Get crt (collection creation time) from col table to compute due day numbers accurately
cursor.execute("SELECT crt FROM col")
crt = cursor.fetchone()[0]
print(f"Collection creation timestamp (crt): {crt} ({datetime.fromtimestamp(crt)})")

# Inspect CID 1786803210924 (Recall card for 耶 junda_1174_32822)
cid = 1786803210924
cursor.execute("SELECT id, nid, ord, type, queue, due, ivl, factor, reps, lapses FROM cards WHERE id = ?", (cid,))
card_row = cursor.fetchone()
print("\nCurrent card row in database:")
print(card_row)

cursor.execute("SELECT id, ease, ivl, lastIvl, factor, time, type FROM revlog WHERE cid = ? ORDER BY id ASC", (cid,))
revs = cursor.fetchall()
print(f"\nRevlog entries for CID {cid}:")
for r in revs:
    rev_id, ease, ivl, lastIvl, factor, rtime, rtype = r
    rev_dt = datetime.fromtimestamp(rev_id / 1000.0)
    print(f"  [{rev_dt}] ease={ease}, ivl={ivl}, lastIvl={lastIvl}, factor={factor}, rtype={rtype}")

# Calculate restored values
reps = len(revs)
lapses = sum(1 for r in revs if r[1] == 1 and r[6] in (1, 2))
last_r = revs[-1]
last_rev_timestamp = last_r[0] / 1000.0
last_ivl = last_r[2]
last_factor = last_r[4]

# In Anki 2.1 scheduler, due date for review cards (type=2) is the number of days since collection creation
last_rev_day = int((last_rev_timestamp - crt) / 86400)
restored_due = last_rev_day + max(1, last_ivl) if last_ivl > 0 else last_rev_day + 1
restored_type = 2 if last_ivl > 0 else 1
restored_queue = 2 if restored_type == 2 else 1

print("\n--- PROPOSED RESTORED VALUES FOR CARD 1786803210924 ---")
print(f"Reps: {reps}")
print(f"Lapses: {lapses}")
print(f"Interval (ivl): {last_ivl}")
print(f"Factor: {last_factor}")
print(f"Type: {restored_type} (Review)")
print(f"Queue: {restored_queue} (Review)")
print(f"Due day index: {restored_due}")

conn.close()
