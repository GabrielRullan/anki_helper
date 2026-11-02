import sys
import os

sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from anki_db import AnkiConnection

with AnkiConnection('Main') as anki:
    c = anki.conn.cursor()
    c.execute("""
        SELECT n.id, n.flds, c.id
        FROM cards c
        JOIN notes n ON c.nid = n.id
        WHERE c.id > 1793570000000 AND c.ord = 1
    """)
    rows = c.fetchall()
    
    radicals = []
    regular = []
    
    for nid, flds_str, cid in rows:
        f = flds_str.split('\x1f')
        f_id = f[0] if len(f) > 0 else ''
        f_hanzi = f[1] if len(f) > 1 else ''
        f_pinyin = f[2] if len(f) > 2 else ''
        f_eng = f[3] if len(f) > 3 else ''
        
        char_code = ord(f_hanzi[0]) if f_hanzi else 0
        # CJK Radicals Supplement: 0x2E80 - 0x2EFF
        # Kangxi Radicals: 0x2F00 - 0x2FDF
        is_radical_block = (0x2E80 <= char_code <= 0x2EFF) or (0x2F00 <= char_code <= 0x2FDF)
        
        if is_radical_block:
            radicals.append((f_id, f_hanzi, hex(char_code), f_eng))
        else:
            regular.append((f_id, f_hanzi, hex(char_code), f_eng, f_pinyin))
            
    print(f"Total cards: {len(rows)}")
    print(f"Radicals supplement block count: {len(radicals)}")
    print(f"Regular characters count: {len(regular)}")
    print("\nRadicals sample:")
    for r in radicals[:15]:
        print(f"  ID={r[0]}: {r[1]} ({r[2]}) - {r[3]}")
    print("\nRegular characters sample:")
    for r in regular[:15]:
        print(f"  ID={r[0]}: {r[1]} ({r[2]}) - {r[3]} ({r[4]})")
