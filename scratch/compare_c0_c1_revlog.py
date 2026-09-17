import sqlite3
import os
import shutil
from datetime import datetime

anki_db_path = os.path.expanduser(r"~\AppData\Roaming\Anki2\Gabriel\collection.anki2")
if not os.path.exists(anki_db_path):
    anki_db_path = r"c:\Users\gabri\Documents\anki_helper\anki_data\collection.anki2"

temp_db = r"c:\Users\gabri\Documents\anki_helper\scratch\temp_inspect_revlog3.anki2"
shutil.copyfile(anki_db_path, temp_db)

conn = sqlite3.connect(temp_db)
cursor = conn.cursor()

c0 = 1786803210923
c1 = 1786803210924

print("=== CARD 0 (Recognition) REVLOG ===")
cursor.execute("SELECT id, ease, ivl, lastIvl, factor, time, type FROM revlog WHERE cid = ? ORDER BY id ASC", (c0,))
for r in cursor.fetchall():
    dt = datetime.fromtimestamp(r[0]/1000.0)
    print(f"[{dt}] ease={r[1]}, ivl={r[2]}, lastIvl={r[3]}, factor={r[4]}, time={r[5]}ms, type={r[6]}")

print("\n=== CARD 1 (Recall) REVLOG ===")
cursor.execute("SELECT id, ease, ivl, lastIvl, factor, time, type FROM revlog WHERE cid = ? ORDER BY id ASC", (c1,))
for r in cursor.fetchall():
    dt = datetime.fromtimestamp(r[0]/1000.0)
    print(f"[{dt}] ease={r[1]}, ivl={r[2]}, lastIvl={r[3]}, factor={r[4]}, time={r[5]}ms, type={r[6]}")

conn.close()
