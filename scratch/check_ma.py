import sys
import os
import json

sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from anki_db import AnkiConnection

with AnkiConnection('Main') as anki:
    c = anki.conn.cursor()
    # Find all notes where Hanzi is '马' or '⻢' or ID is '28' or similar
    c.execute("SELECT id, mid, flds, tags FROM notes WHERE flds LIKE '%⻢%' OR flds LIKE '%马%' OR flds LIKE '28\x1f%'")
    rows = c.fetchall()
    print(f"Found {len(rows)} matching notes:")
    notetypes = anki.get_notetypes()
    for nid, mid, flds_str, tags in rows:
        flds = flds_str.split('\x1f')
        nt = notetypes.get(mid, {})
        id_val = flds[0] if len(flds) > 0 else ''
        hanzi_val = flds[1] if len(flds) > 1 else ''
        pinyin_val = flds[2] if len(flds) > 2 else ''
        eng_val = flds[3] if len(flds) > 3 else ''
        print(f"nid={nid}, mid={mid} ({nt.get('name')}), ID={id_val}, Hanzi={hanzi_val}, Pinyin={pinyin_val}, English={eng_val}")
