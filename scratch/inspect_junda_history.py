import sqlite3
import os
import shutil
import json
from datetime import datetime

# Path to live collection in AppData
anki_db_path = os.path.expanduser(r"~\AppData\Roaming\Anki2\Gabriel\collection.anki2")
if not os.path.exists(anki_db_path):
    anki_db_path = r"c:\Users\gabri\Documents\anki_helper\anki_data\collection.anki2"

temp_db = r"c:\Users\gabri\Documents\anki_helper\scratch\temp_inspect_revlog.anki2"
shutil.copyfile(anki_db_path, temp_db)

conn = sqlite3.connect(temp_db)
cursor = conn.cursor()

# Find note for '耶' or 'junda_1174_32822'
cursor.execute("SELECT id, mid, mod, tags, flds, sfld FROM notes WHERE flds LIKE '%junda_1174_32822%' OR flds LIKE '%耶%'")
note_rows = cursor.fetchall()
print(f"Found {len(note_rows)} notes matching '耶' or 'junda_1174_32822':")

for row in note_rows:
    nid, mid, mod, tags, flds, sfld = row
    print(f"\nNote NID: {nid}")
    print(f"Created/NID Date: {datetime.fromtimestamp(nid/1000.0)}")
    print(f"Mod Date: {datetime.fromtimestamp(mod)}")
    print(f"Tags: {tags}")
    fld_list = flds.split("\x1f")
    print(f"ID Field: {fld_list[0] if len(fld_list)>0 else ''}")
    print(f"Hanzi: {fld_list[1] if len(fld_list)>1 else ''}")
    
    # Get cards for this note
    cursor.execute("SELECT id, nid, ord, mod, usn, type, queue, due, ivl, factor, reps, lapses FROM cards WHERE nid = ?", (nid,))
    cards = cursor.fetchall()
    for c in cards:
        cid, c_nid, c_ord, c_mod, c_usn, c_type, c_queue, c_due, c_ivl, c_factor, c_reps, c_lapses = c
        print(f"  Card CID: {cid} (ord={c_ord}): type={c_type}, queue={c_queue}, reps={c_reps}, lapses={c_lapses}, due={c_due}, ivl={c_ivl}")
        
        # Check revlog for this CID
        cursor.execute("SELECT id, cid, usn, ease, ivl, lastIvl, factor, time, type FROM revlog WHERE cid = ? ORDER BY id ASC", (cid,))
        revs = cursor.fetchall()
        print(f"    Review count in revlog for CID {cid}: {len(revs)}")
        if revs:
            first_rev = datetime.fromtimestamp(revs[0][0]/1000.0)
            last_rev = datetime.fromtimestamp(revs[-1][0]/1000.0)
            print(f"    First review: {first_rev}, Last review: {last_rev}")

# Check all notes with tag junda_auto_import to see how many have ord=1 suspended / new with ord=0 reviewed
cursor.execute("SELECT id, flds FROM notes WHERE tags LIKE '%junda_auto_import%'")
junda_notes = cursor.fetchall()
print(f"\nTotal notes with tag 'junda_auto_import': {len(junda_notes)}")

mismatched_card_history = []
for nid, flds in junda_notes:
    cursor.execute("SELECT id, ord, type, queue, reps FROM cards WHERE nid = ?", (nid,))
    cards = cursor.fetchall()
    card_dict = {c[1]: c for c in cards}
    if 0 in card_dict and 1 in card_dict:
        c0_reps = card_dict[0][4]
        c1_reps = card_dict[1][4]
        c1_queue = card_dict[1][3]
        if c0_reps > 0 and c1_reps == 0:
            mismatched_card_history.append((nid, flds.split("\x1f")[1] if len(flds.split("\x1f"))>1 else "", c0_reps, c1_queue))

print(f"Total Junda notes where Card 0 has reviews (reps > 0) but Card 1 has 0 reviews (reps = 0): {len(mismatched_card_history)}")
if mismatched_card_history:
    print("Sample mismatched notes (first 10):")
    for nid, hanzi, c0_reps, c1_queue in mismatched_card_history[:10]:
        print(f"  NID: {nid} | Hanzi: '{hanzi}' | Card 0 reps: {c0_reps} | Card 1 queue: {c1_queue}")

# Check revlog for any cards associated with 'Chinese Character - Double' model across the collection
conn.close()
