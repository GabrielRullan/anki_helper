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

# Extract colpkg
with zipfile.ZipFile(backup_colpkg, 'r') as zf:
    zf.extractall(scratch_dir)

backup_21b = os.path.join(scratch_dir, "collection.anki21b")
backup_decompressed_db = os.path.join(scratch_dir, "collection_aug09.anki2")

dctx = zstandard.ZstdDecompressor()
with open(backup_21b, 'rb') as ifh, open(backup_decompressed_db, 'wb') as ofh:
    dctx.copy_stream(ifh, ofh)

print(f"Decompressed August 09 backup database to {backup_decompressed_db}")

# 2. Extract function for Anki 2.1.50+ DB schema
def get_cards_from_db(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get crt
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
        
        # Extract Hanzi character
        hanzi = ""
        for fld in fld_list[:3]:
            clean = fld.replace('<b>', '').replace('</b>', '').strip()
            if len(clean) == 1 and '\u4e00' <= clean <= '\u9fff':
                hanzi = clean
                break
        if not hanzi and len(fld_list) > 1:
            cjk = [ch for ch in fld_list[1] if '\u4e00' <= ch <= '\u9fff']
            if cjk:
                hanzi = cjk[0]
                
        if hanzi:
            key = (hanzi, c_ord)
            cards_map[key] = {
                'nid': nid,
                'cid': cid,
                'ord': c_ord,
                'hanzi': hanzi,
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
b_crt, b_cards = get_cards_from_db(backup_decompressed_db)
print(f"Loaded {len(b_cards)} character cards from August 09 backup database.")

# Make live copy
live_temp = os.path.join(scratch_dir, "live_copy.anki2")
shutil.copyfile(live_db_path, live_temp)

print("Loading live cards...")
l_crt, l_cards = get_cards_from_db(live_temp)
print(f"Loaded {len(l_cards)} character cards from live database.")

# 3. Compare Cards
mismatched = []

for key, b_card in b_cards.items():
    hanzi, c_ord = key
    
    # Check if this card in backup was NOT new (reps > 0 or type > 0 or ivl > 0)
    if b_card['reps'] > 0 or b_card['type'] > 0 or b_card['ivl'] > 0:
        if key in l_cards:
            l_card = l_cards[key]
            
            # Check if live card is currently new (type=0 / reps=0 / queue=-1)
            if l_card['type'] == 0 or l_card['reps'] == 0 or l_card['queue'] == -1:
                mismatched.append({
                    'hanzi': hanzi,
                    'ord': c_ord,
                    'card_type_name': 'Recognition (ord=0)' if c_ord == 0 else 'Recall (ord=1)',
                    'live_cid': l_card['cid'],
                    'live_nid': l_card['nid'],
                    'live_type': l_card['type'],
                    'live_queue': l_card['queue'],
                    'live_reps': l_card['reps'],
                    'live_ivl': l_card['ivl'],
                    
                    'backup_cid': b_card['cid'],
                    'backup_nid': b_card['nid'],
                    'backup_type': b_card['type'],
                    'backup_queue': b_card['queue'],
                    'backup_reps': b_card['reps'],
                    'backup_lapses': b_card['lapses'],
                    'backup_ivl': b_card['ivl'],
                    'backup_factor': b_card['factor'],
                    'backup_due': b_card['due']
                })

print(f"\n=======================================================")
print(f"TOTAL CARDS NEEDING RESTORATION: {len(mismatched)}")
print(f"=======================================================")

ord0_m = [m for m in mismatched if m['ord'] == 0]
ord1_m = [m for m in mismatched if m['ord'] == 1]

print(f"  - Recognition cards (ord=0): {len(ord0_m)}")
print(f"  - Recall cards (ord=1): {len(ord1_m)}")

print("\n--- SAMPLE MISMATCHED CARDS (First 20) ---")
for m in mismatched[:20]:
    print(f"Hanzi: '{m['hanzi']}' ({m['card_type_name']})")
    print(f"  Live State  : CID={m['live_cid']} | type={m['live_type']} | queue={m['live_queue']} | reps={m['live_reps']} | ivl={m['live_ivl']}")
    print(f"  Backup State: CID={m['backup_cid']} | type={m['backup_type']} | queue={m['backup_queue']} | reps={m['backup_reps']} | ivl={m['backup_ivl']} | factor={m['backup_factor']}")

# Save json
with open(r"c:\Users\gabri\Documents\anki_helper\scratch\restoration_plan.json", 'w', encoding='utf-8') as f:
    json.dump(mismatched, f, indent=2, ensure_ascii=False)

