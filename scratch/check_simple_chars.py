import sys
import os

sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from anki_db import AnkiConnection

with AnkiConnection('Main') as anki:
    c = anki.conn.cursor()
    for target_id in ['326', '368', '369', '395']:
        c.execute("SELECT id, flds, tags FROM notes WHERE flds LIKE ? || '\x1f%'", (target_id,))
        row = c.fetchone()
        if row:
            f = row[1].split('\x1f')
            print(f"ID={f[0]} | Hanzi={f[1]} | Pinyin={f[2]} | Eng={f[3]} | Level={f[12]} | Common Words={f[14]} | Tags={row[2]}")
