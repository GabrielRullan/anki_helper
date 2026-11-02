import sys
import os

sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from anki_db import AnkiConnection

with AnkiConnection('Main') as anki:
    c = anki.conn.cursor()
    c.execute("SELECT n.id, n.flds, c.id, c.ord FROM notes n JOIN cards c ON c.nid = n.id")
    for nid, flds, cid, cord in c.fetchall():
        f = flds.split('\x1f')
        if len(f) > 0 and f[0] in [str(i) for i in range(25, 32)]:
            print(f"ID: {f[0]:2} | Hanzi: {f[1]} | Card ord: {cord} | Card id: {cid}")
