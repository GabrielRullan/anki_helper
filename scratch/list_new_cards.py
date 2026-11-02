import sys
import os

sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from anki_db import AnkiConnection

with AnkiConnection('Main') as anki:
    c = anki.conn.cursor()
    c.execute('SELECT c.id, c.nid, c.ord, n.mid, n.flds FROM cards c JOIN notes n ON c.nid = n.id WHERE c.id > 1793570000000 ORDER BY c.id ASC')
    rows = c.fetchall()
    print(f"Total newly created cards: {len(rows)}")
    notetypes = anki.get_notetypes()
    for cid, nid, cord, mid, flds in rows:
        f = flds.split('\x1f')
        # f[0]: ID, f[1]: Hanzi, f[2]: Pinyin, f[3]: English, f[11]: Phase, f[12]: Level
        f_id = f[0] if len(f) > 0 else ''
        f_hanzi = f[1] if len(f) > 1 else ''
        f_pinyin = f[2] if len(f) > 2 else ''
        f_eng = f[3] if len(f) > 3 else ''
        f_comp = f[9] if len(f) > 9 else ''
        print(f"ID={f_id:6} | Hanzi={f_hanzi:2} | Pinyin={f_pinyin:10} | English={f_eng:20} | Comps={f_comp:10}")
