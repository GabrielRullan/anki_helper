import sys
import os

sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from anki_db import AnkiConnection

with AnkiConnection('Main') as anki:
    c = anki.conn.cursor()
    # Check all 165 newly generated cards
    c.execute("""
        SELECT c.id, c.nid, c.ord, c.flags, n.flds
        FROM cards c
        JOIN notes n ON c.nid = n.id
        WHERE c.id > 1793570000000 AND c.ord = 1
        ORDER BY c.id
    """)
    rows = c.fetchall()
    print(f"Total newly created ord=1 cards: {len(rows)}")
    flag_counts = {}
    for cid, nid, cord, flags, flds in rows:
        flag_counts[flags] = flag_counts.get(flags, 0) + 1
    print("Flag distribution among the 165 new cards:", flag_counts)
    
    # Are there any other cards with flags=2 that were NOT created recently?
    c.execute("SELECT count(*) FROM cards WHERE flags = 2 AND id <= 1793570000000")
    print("Older cards with flag=2:", c.fetchone()[0])
