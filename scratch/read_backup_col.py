import sys
import os
import zipfile
import sqlite3
import json

sys.stdout.reconfigure(encoding='utf-8')

backup_path = r"C:\Users\gabri\AppData\Roaming\Anki2\Main\backups\backup-2026-11-01-23.11.24.colpkg"
target_db = r"c:\Users\gabri\Documents\antigravity\anki\scratch\backup_col.anki2"

with zipfile.ZipFile(backup_path, 'r') as zf:
    with open(target_db, 'wb') as f_out:
        f_out.write(zf.read('collection.anki2'))

conn = sqlite3.connect(target_db)
c = conn.cursor()

# In collection.anki2, models are in `col` table
c.execute("SELECT models FROM col")
row = c.fetchone()
if row and row[0]:
    models = json.loads(row[0])
    for mid, mdata in models.items():
        print(f"Model {mid}: {mdata.get('name')}")
        flds = [f['name'] for f in mdata.get('flds', [])]
        print(f"  Fields: {flds}")
        tmpls = [t['name'] for t in mdata.get('tmpls', [])]
        print(f"  Templates: {tmpls}")
        for t in mdata.get('tmpls', []):
            if 'Recall' in t['name']:
                print(f"    Recall Front: {t.get('qfmt')}")

# Check note 1768474724432
c.execute("SELECT id, mid, flds, tags FROM notes WHERE id = 1768474724432")
n = c.fetchone()
if n:
    print("\nNote 1768474724432 in backup:")
    print("  mid:", n[1])
    flds = n[2].split('\x1f')
    print("  flds count:", len(flds))
    # print all fields with their model field names
    m = models.get(str(n[1]))
    fld_names = [f['name'] for f in m['flds']] if m else []
    for fname, fval in zip(fld_names, flds):
        if fval:
            print(f"    {fname}: {fval[:100]}")
    c.execute("SELECT id, ord, did, queue, type FROM cards WHERE nid = 1768474724432")
    print("  cards:", c.fetchall())

conn.close()
