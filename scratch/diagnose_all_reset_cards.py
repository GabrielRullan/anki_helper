import sqlite3
import os
import shutil
import json
from datetime import datetime

anki_db_path = os.path.expanduser(r"~\AppData\Roaming\Anki2\Gabriel\collection.anki2")
if not os.path.exists(anki_db_path):
    anki_db_path = r"c:\Users\gabri\Documents\anki_helper\anki_data\collection.anki2"

temp_db = r"c:\Users\gabri\Documents\anki_helper\scratch\temp_diagnose_cards.anki2"
shutil.copyfile(anki_db_path, temp_db)

conn = sqlite3.connect(temp_db)
cursor = conn.cursor()

# Query cards that have reps = 0 (or type = 0) but have revlog entries!
cursor.execute("""
    SELECT c.id, c.nid, c.ord, c.type, c.queue, c.due, c.ivl, c.factor, c.reps, c.lapses, n.flds, n.tags, n.mid
    FROM cards c
    JOIN notes n ON c.nid = n.id
    WHERE c.reps = 0 AND EXISTS (SELECT 1 FROM revlog r WHERE r.cid = c.id)
""")

reset_cards = cursor.fetchall()
print(f"Total cards where reps = 0 in cards table BUT revlog has review history: {len(reset_cards)}")

detailed_restorable = []

for card in reset_cards:
    cid, nid, c_ord, c_type, c_queue, c_due, c_ivl, c_factor, c_reps, c_lapses, flds, tags, mid = card
    
    # Get revlog stats
    cursor.execute("""
        SELECT id, ease, ivl, lastIvl, factor, time, type 
        FROM revlog 
        WHERE cid = ? 
        ORDER BY id ASC
    """, (cid,))
    revs = cursor.fetchall()
    
    num_revs = len(revs)
    last_rev = revs[-1]
    last_rev_id, last_ease, last_ivl, last_lastIvl, last_factor, last_time, last_type = last_rev
    last_rev_dt = datetime.fromtimestamp(last_rev_id / 1000.0)
    
    fld_parts = flds.split("\x1f")
    hanzi = fld_parts[1] if len(fld_parts) > 1 else ""
    id_field = fld_parts[0] if len(fld_parts) > 0 else ""
    
    detailed_restorable.append({
        'cid': cid,
        'nid': nid,
        'ord': c_ord,
        'hanzi': hanzi,
        'id_field': id_field,
        'tags': tags,
        'current_type': c_type,
        'current_queue': c_queue,
        'revlog_count': num_revs,
        'last_rev_date': last_rev_dt.strftime('%Y-%m-%d %H:%M:%S'),
        'last_ivl': last_ivl,
        'last_factor': last_factor,
        'last_type': last_type
    })

# Sample restorable cards
print("\n--- SAMPLE RESTORABLE CARDS (First 15) ---")
for r in detailed_restorable[:15]:
    print(f"CID {r['cid']} (NID {r['nid']}, ord={r['ord']}) | Hanzi: '{r['hanzi']}' ({r['id_field']})")
    print(f"  Current in cards table: type={r['current_type']}, queue={r['current_queue']}")
    print(f"  Revlog History: {r['revlog_count']} reviews | Last Rev: {r['last_rev_date']} | Last Interval: {r['last_ivl']} days | Factor: {r['last_factor']}")

# Breakdown by ord and tag
ord0_count = sum(1 for r in detailed_restorable if r['ord'] == 0)
ord1_count = sum(1 for r in detailed_restorable if r['ord'] == 1)
print(f"\nBreakdown by ord: ord=0 (Recognition): {ord0_count}, ord=1 (Recall): {ord1_count}")

# Save diagnosis result
with open(r"c:\Users\gabri\Documents\anki_helper\scratch\reset_cards_diagnosis.json", 'w', encoding='utf-8') as f:
    json.dump(detailed_restorable, f, indent=2, ensure_ascii=False)

conn.close()
