import sys
import os

sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from anki_db import AnkiConnection

with AnkiConnection('Main') as anki:
    c = anki.conn.cursor()
    c.execute("""
        SELECT c.id, c.nid, c.flags, n.flds, n.tags
        FROM cards c
        JOIN notes n ON c.nid = n.id
        WHERE c.id > 1793570000000 AND c.ord = 1
        ORDER BY c.id
    """)
    rows = c.fetchall()
    
    flagged = [r for r in rows if r[2] == 2]
    unflagged = [r for r in rows if r[2] == 0]
    
    print(f"Flagged (81):")
    f_ids = [r[3].split('\x1f')[0] for r in flagged]
    print("  ID field range:", f_ids[0], "to", f_ids[-1])
    # check note id range
    print("  Note ID range:", flagged[0][1], "to", flagged[-1][1])
    
    print(f"\nUnflagged (84):")
    u_ids = [r[3].split('\x1f')[0] for r in unflagged]
    print("  ID field range:", u_ids[0], "to", u_ids[-1])
    print("  Note ID range:", unflagged[0][1], "to", unflagged[-1][1])
    
    # Check what kind of characters are in flagged vs unflagged
    print("\nSample flagged characters:")
    for r in flagged[:10]:
        f = r[3].split('\x1f')
        print(f"  ID={f[0]:6} Hanzi={f[1]:2} Pinyin={f[2]:10} English={f[3]}")
        
    print("\nSample unflagged characters:")
    for r in unflagged[:10]:
        f = r[3].split('\x1f')
        print(f"  ID={f[0]:6} Hanzi={f[1]:2} Pinyin={f[2]:10} English={f[3]}")
