import sys
import os

sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from anki_db import AnkiConnection

with AnkiConnection('Main') as anki:
    c = anki.conn.cursor()
    for target_id in ['326', '368', '369', '395']:
        c.execute("""
            SELECT c.id, c.ord, c.queue, c.type, c.reps, c.lapses, c.flags
            FROM cards c
            JOIN notes n ON c.nid = n.id
            WHERE n.flds LIKE ? || '\x1f%'
        """, (target_id,))
        print(f"Cards for ID={target_id}:")
        for r in c.fetchall():
            print(f"  cid={r[0]}, ord={r[1]}, queue={r[2]}, type={r[3]}, reps={r[4]}, lapses={r[5]}, flags={r[6]}")
