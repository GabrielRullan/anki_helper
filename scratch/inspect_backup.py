import sys
import os
import zipfile
import sqlite3
import shutil
import tempfile
import json

sys.stdout.reconfigure(encoding='utf-8')

backup_path = r"C:\Users\gabri\AppData\Roaming\Anki2\Main\backups\backup-2026-11-01-23.11.24.colpkg"

with tempfile.TemporaryDirectory() as tmpdir:
    with zipfile.ZipFile(backup_path, 'r') as zf:
        print("Files in colpkg:", zf.namelist())
        # extract collection.anki2 or collection.anki21
        db_name = 'collection.anki21' if 'collection.anki21' in zf.namelist() else 'collection.anki2'
        zf.extract(db_name, tmpdir)
        db_path = os.path.join(tmpdir, db_name)
        
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # 1. Check notetypes
    c.execute("SELECT id, name FROM notetypes")
    nts = c.fetchall()
    print("Notetypes before change:")
    for ntid, name in nts:
        print(f"  {ntid}: {name}")
        c.execute("SELECT ord, name FROM fields WHERE ntid = ? ORDER BY ord", (ntid,))
        f_list = [f"{ord_val}:{fname}" for ord_val, fname in c.fetchall()]
        print(f"    Fields: {f_list}")
        c.execute("SELECT ord, name FROM templates WHERE ntid = ?", (ntid,))
        t_list = [f"{ord_val}:{tname}" for ord_val, tname in c.fetchall()]
        print(f"    Templates: {t_list}")
        
    # 2. Check note 1768474724432 (ID=28)
    c.execute("SELECT id, mid, flds, tags FROM notes WHERE id = 1768474724432")
    n = c.fetchone()
    if n:
        print("\nNote 1768474724432 before change:")
        print("  mid:", n[1])
        flds = n[2].split('\x1f')
        print("  flds count:", len(flds))
        print("  flds values:", flds)
        print("  tags:", n[3])
        
        # Check cards for this note before change
        c.execute("SELECT id, ord, did, queue, type FROM cards WHERE nid = 1768474724432")
        cards = c.fetchall()
        print("  cards count:", len(cards))
        for card in cards:
            print("    card:", card)
            
    conn.close()
