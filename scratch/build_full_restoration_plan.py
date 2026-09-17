import sqlite3
import os
import shutil
import zstandard
import zipfile
import json
from datetime import datetime

# 1. Paths
live_db_path = os.path.expanduser(r"~\AppData\Roaming\Anki2\Gabriel\collection.anki2")
backup_colpkg = r"C:\Users\gabri\AppData\Roaming\Anki2\Gabriel\backups\backup-2026-08-09-22.34.28.colpkg"

scratch_dir = r"c:\Users\gabri\Documents\anki_helper\scratch\aug09_extracted"
os.makedirs(scratch_dir, exist_ok=True)

backup_21b = os.path.join(scratch_dir, "collection.anki21b")
backup_decompressed_db = os.path.join(scratch_dir, "collection_aug09.anki2")

if not os.path.exists(backup_decompressed_db):
    with zipfile.ZipFile(backup_colpkg, 'r') as zf:
        zf.extractall(scratch_dir)

    dctx = zstandard.ZstdDecompressor()
    with open(backup_21b, 'rb') as ifh, open(backup_decompressed_db, 'wb') as ofh:
        dctx.copy_stream(ifh, ofh)

# 2. Extract function for Anki 2.1.50+ DB schema
def get_all_notes_cards(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT crt FROM col")
    crt = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT n.id, n.flds, n.tags, c.id, c.ord, c.type, c.queue, c.due, c.ivl, c.factor, c.reps, c.lapses
        FROM notes n
        JOIN cards c ON n.id = c.nid
    """)
    rows = cursor.fetchall()
    
    cards_map = {}
    for row in rows:
        nid, flds, tags, cid, c_ord, c_type, c_queue, c_due, c_ivl, c_factor, c_reps, c_lapses = row
        fld_list = flds.split("\x1f")
        
        # Extract target word / hanzi
        target = ""
        for fld in fld_list[:3]:
            clean = fld.replace('<b>', '').replace('</b>', '').strip()
            if clean:
                target = clean
                break
                
        if target:
            # Map key by (target, ord)
            key = (target.strip(), c_ord)
            # If multiple exist, pick the one with highest reps/ivl
            if key not in cards_map or c_reps > cards_map[key]['reps'] or c_ivl > cards_map[key]['ivl']:
                cards_map[key] = {
                    'nid': nid,
                    'cid': cid,
                    'ord': c_ord,
                    'target': target.strip(),
                    'tags': tags,
                    'type': c_type,
                    'queue': c_queue,
                    'due': c_due,
                    'ivl': c_ivl,
                    'factor': c_factor,
                    'reps': c_reps,
                    'lapses': c_lapses,
                    'flds': flds
                }
            
    conn.close()
    return crt, cards_map

print("Loading August 09 backup cards...")
b_crt, b_cards = get_all_notes_cards(backup_decompressed_db)
print(f"Loaded {len(b_cards)} total cards from August 09 backup database.")

live_temp = os.path.join(scratch_dir, "live_copy.anki2")
shutil.copyfile(live_db_path, live_temp)

print("Loading live cards...")
l_crt, l_cards = get_all_notes_cards(live_temp)
print(f"Loaded {len(l_cards)} total cards from live database.")

# Calculate current day index relative to collection creation time (crt)
# Current timestamp
now_ts = int(datetime.now().timestamp())
current_day_index = int((now_ts - l_crt) / 86400)
print(f"Current Day Index in Anki Scheduler: {current_day_index}")

# 3. Match and Build Restoration Items
restoration_items = []

for key, b_card in b_cards.items():
    target, c_ord = key
    
    # Needs restoration if backup had reviews/interval
    if b_card['reps'] > 0 or b_card['ivl'] > 0 or b_card['type'] in (1, 2, 3):
        if key in l_cards:
            l_card = l_cards[key]
            
            # Check if live card is marked new, suspended, or reps=0
            if l_card['type'] == 0 or l_card['reps'] == 0 or l_card['queue'] == -1 or l_card['ivl'] == 0:
                # Calculate restored due date
                restored_ivl = max(1, b_card['ivl'])
                restored_due = current_day_index + restored_ivl
                restored_factor = b_card['factor'] if b_card['factor'] > 0 else 2500
                restored_reps = max(1, b_card['reps'])
                restored_lapses = b_card['lapses']
                
                restoration_items.append({
                    'target': target,
                    'ord': c_ord,
                    'live_cid': l_card['cid'],
                    'live_nid': l_card['nid'],
                    'backup_cid': b_card['cid'],
                    'backup_nid': b_card['nid'],
                    
                    'old_type': l_card['type'],
                    'old_queue': l_card['queue'],
                    'old_reps': l_card['reps'],
                    'old_ivl': l_card['ivl'],
                    
                    'new_type': 2,       # Review
                    'new_queue': 2,      # Review queue
                    'new_due': restored_due,
                    'new_ivl': restored_ivl,
                    'new_factor': restored_factor,
                    'new_reps': restored_reps,
                    'new_lapses': restored_lapses
                })

print(f"\n=======================================================")
print(f"TOTAL CARDS READY TO RESTORE FROM BACKUP: {len(restoration_items)}")
print(f"=======================================================")

with open(r"c:\Users\gabri\Documents\anki_helper\scratch\full_restoration_plan.json", 'w', encoding='utf-8') as f:
    json.dump(restoration_items, f, indent=2, ensure_ascii=False)

# Sample detailed plan output
for item in restoration_items[:10]:
    print(f"Target: '{item['target']}' (ord={item['ord']}) | Live CID: {item['live_cid']}")
    print(f"  BEFORE: type={item['old_type']}, queue={item['old_queue']}, reps={item['old_reps']}, ivl={item['old_ivl']}")
    print(f"  AFTER : type={item['new_type']}, queue={item['new_queue']}, reps={item['new_reps']}, ivl={item['new_ivl']}d, factor={item['new_factor']}, due={item['new_due']}")
