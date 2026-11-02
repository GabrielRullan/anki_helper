import sys
import os
import datetime

sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from anki_db import AnkiConnection

with AnkiConnection('Main') as anki:
    c = anki.conn.cursor()
    # Find all cards created after 2026-11-01 23:00:00 (ts > 1793570000000)
    c.execute('SELECT c.id, c.nid, c.ord, c.did, n.mid, n.flds FROM cards c JOIN notes n ON c.nid = n.id WHERE c.id > 1793570000000')
    rows = c.fetchall()
    print(f'Total cards created recently: {len(rows)}')
    notetypes = anki.get_notetypes()
    for cid, nid, cord, did, mid, flds in rows:
        nt_name = notetypes.get(mid, {}).get('name')
        flds_list = flds.split('\x1f')
        id_field = flds_list[0] if flds_list else ""
        hanzi = flds_list[1] if len(flds_list) > 1 else ""
        print(f'cid={cid}, nid={nid}, ord={cord}, nt={nt_name}, ID={id_field}, Hanzi={hanzi}')
