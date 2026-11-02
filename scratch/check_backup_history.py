import zipfile, sqlite3, json, tempfile

def check_bp(bp):
    with zipfile.ZipFile(bp, 'r') as zf:
        data = zf.read('collection.anki2')
    with tempfile.NamedTemporaryFile(delete=False) as tf:
        tf.write(data)
        tname = tf.name
    conn = sqlite3.connect(tname)
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in c.fetchall()]
    print(bp.split('\\')[-1])
    if 'notetypes' in tables:
        c.execute("SELECT id, name FROM notetypes")
        for nid, name in c.fetchall():
            c.execute("SELECT name FROM fields WHERE ntid = ?", (nid,))
            fnames = [r[0] for r in c.fetchall()]
            c.execute("SELECT name FROM templates WHERE ntid = ?", (nid,))
            tmpls = [r[0] for r in c.fetchall()]
            if 'Character' in name or 'Do_Not_Recall' in fnames:
                print(f"  {name} (id={nid}): tmpls={tmpls}, dnr={'Do_Not_Recall' in fnames}")
    elif 'models' in [r[0] for r in c.execute("PRAGMA table_info(col)").fetchall()]:
        c.execute('SELECT models FROM col')
        row = c.fetchone()
        if row and row[0]:
            models = json.loads(row[0])
            for mid, m in models.items():
                fnames = [f['name'] for f in m.get('flds', [])]
                tmpls = [t['name'] for t in m.get('tmpls', [])]
                print(f"  {m['name']} (mid={mid}): tmpls={tmpls}, dnr={'Do_Not_Recall' in fnames}")
    conn.close()

for bp in [
    r'C:\Users\gabri\AppData\Roaming\Anki2\Main\backups\backup-2026-01-08-12.54.59.colpkg',
    r'C:\Users\gabri\AppData\Roaming\Anki2\Main\backups\backup-2026-05-23-21.56.01.colpkg',
    r'C:\Users\gabri\AppData\Roaming\Anki2\Main\backups\backup-2026-10-03-08.43.17.colpkg',
]:
    check_bp(bp)
