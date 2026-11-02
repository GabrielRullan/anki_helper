import sys
import os

sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from anki_db import AnkiConnection

with AnkiConnection('Main') as anki:
    c = anki.conn.cursor()
    c.execute("SELECT id, mid, flds FROM notes")
    notetypes = anki.get_notetypes()
    for nid, mid, flds in c.fetchall():
        f = flds.split('\x1f')
        if len(f) > 0 and f[0] in [str(i) for i in range(20, 35)]:
            print(f"ID: {f[0]:3} | Hanzi: {f[1]:2} | Pinyin: {f[2]:6} | English: {f[3]:15} | Notetype: {notetypes.get(mid, {}).get('name')}")
