import sqlite3
import os
import shutil
import zipfile
import json
from datetime import datetime

# 1. Paths
live_db_path = os.path.expanduser(r"~\AppData\Roaming\Anki2\Gabriel\collection.anki2")
backup_colpkg = r"C:\Users\gabri\AppData\Roaming\Anki2\Gabriel\backups\backup-2026-08-09-22.34.28.colpkg"

scratch_backup_dir = r"c:\Users\gabri\Documents\anki_helper\scratch\aug09_backup_extracted"
os.makedirs(scratch_backup_dir, exist_ok=True)

print(f"Extracting backup package: {backup_colpkg}...")
with zipfile.ZipFile(backup_colpkg, 'r') as zf:
    zf.extractall(scratch_backup_dir)

backup_db_path = os.path.join(scratch_backup_dir, "collection.anki2")

# 2. Extract Character Cards from Backup Database
def load_char_cards_from_db(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get crt
    cursor.execute("SELECT crt FROM col")
    crt = cursor.fetchone()[0]
    
    # Query all character cards (notes containing Hanzi or tagged junda / Chinese Character)
    cursor.execute("""
        SELECT n.id, n.flds, n.tags, c.id, c.ord, c.type, c.queue, c.due, c.ivl, c.factor, c.reps, c.lapses
        FROM notes n
        JOIN cards c ON n.id = c.nid
    """)
    rows = cursor.fetchall()
    
    char_map = {} # key: (hanzi, ord) -> dict of card details
    
    for row in rows:
        nid, flds, tags, cid, c_ord, c_type, c_queue, c_due, c_ivl, c_factor, c_reps, c_lapses = row
        fld_list = flds.split("\x1f")
        
        # Extract Hanzi (usually field 1 or field 0)
        hanzi = ""
        for fld in fld_list[:3]:
            # Clean HTML
            fld_clean = fld.replace('<b>', '').replace('</b>', '').strip()
            if len(fld_clean) == 1 and '\u4e00' <= fld_clean <= '\u9fff':
                hanzi = fld_clean
                break
        if not hanzi and len(fld_list) > 1:
            # Fallback check
            cjk = [ch for ch in fld_list[1] if '\u4e00' <= ch <= '\u9fff']
            if cjk:
                hanzi = cjk[0]
                
        if hanzi:
            key = (hanzi, c_ord)
            char_map[key] = {
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
    return crt, char_map

print("Loading card data from backup DB...")
backup_crt, backup_cards = load_char_cards_from_db(backup_db_path)
print(f"Loaded {len(backup_cards)} character cards from backup database.")

print("Loading card data from live DB...")
# Make temporary copy of live DB to inspect
live_temp = r"c:\Users\gabri\Documents\anki_helper\scratch\live_temp.anki2"
shutil.copyfile(live_db_path, live_temp)

live_crt, live_cards = load_char_cards_from_db(live_temp)
print(f"Loaded {len(live_cards)} character cards from live database.")

# 3. Compare and Identify Restorable Cards
restoration_targets = []

for key, b_card in backup_cards.items():
    hanzi, c_ord = key
    
    # Check if this card was reviewed / active in backup (reps > 0 or type > 0 or ivl > 0)
    if b_card['reps'] > 0 or b_card['type'] > 0 or b_card['ivl'] > 0:
        if key in live_cards:
            l_card = live_cards[key]
            
            # Check if live card is considered new or suspended with reps=0
            if l_card['type'] == 0 or l_card['reps'] == 0 or l_card['queue'] == -1:
                # Calculate adjusted due date for live database
                # Difference in collection days between backup and live
                # We retain the interval, factor, reps, lapses, and set type=2 (review), queue=2 (review) or queue=0 (un-suspended)
                
                restoration_targets.append({
                    'hanzi': hanzi,
                    'ord': c_ord,
                    'card_name': 'Recognition (ord=0)' if c_ord == 0 else 'Recall (ord=1)',
                    'live_cid': l_card['cid'],
                    'live_nid': l_card['nid'],
                    'live_type': l_card['type'],
                    'live_queue': l_card['queue'],
                    'live_reps': l_card['reps'],
                    'live_ivl': l_card['ivl'],
                    
                    'backup_nid': b_card['nid'],
                    'backup_cid': b_card['cid'],
                    'backup_type': b_card['type'],
                    'backup_queue': b_card['queue'],
                    'backup_reps': b_card['reps'],
                    'backup_lapses': b_card['lapses'],
                    'backup_ivl': b_card['ivl'],
                    'backup_factor': b_card['factor'],
                    'backup_due': b_card['due']
                })

print(f"\n=== COMPARISON RESULTS ===")
print(f"Total cards identified needing restoration: {len(restoration_targets)}")

ord0_targets = [t for t in restoration_targets if t['ord'] == 0]
ord1_targets = [t for t in restoration_targets if t['ord'] == 1]

print(f"  - Recognition cards (ord=0): {len(ord0_targets)}")
print(f"  - Recall cards (ord=1): {len(ord1_targets)}")

print("\n--- SAMPLE RESTORATION TARGETS (First 15) ---")
for t in restoration_targets[:15]:
    print(f"Hanzi: '{t['hanzi']}' ({t['card_name']}) | Live CID: {t['live_cid']} | Backup CID: {t['backup_cid']}")
    print(f"  LIVE state  : type={t['live_type']}, queue={t['live_queue']}, reps={t['live_reps']}, ivl={t['live_ivl']}")
    print(f"  BACKUP state: type={t['backup_type']}, queue={t['backup_queue']}, reps={t['backup_reps']}, ivl={t['backup_ivl']}, factor={t['backup_factor']}, lapses={t['backup_lapses']}")

# Save full comparison targets to JSON
with open(r"c:\Users\gabri\Documents\anki_helper\scratch\restoration_targets.json", 'w', encoding='utf-8') as f:
    json.dump(restoration_targets, f, indent=2, ensure_ascii=False)

