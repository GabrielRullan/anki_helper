import sys
import os

sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from anki_db import AnkiConnection

with AnkiConnection('Main') as anki:
    c = anki.conn.cursor()
    c.execute("""
        SELECT c.id, c.nid, n.flds, n.tags
        FROM cards c
        JOIN notes n ON c.nid = n.id
        WHERE c.flags = 2
        ORDER BY c.id
    """)
    rows = c.fetchall()
    
    print(f"Total orange flagged cards: {len(rows)}")
    
    # Check Hanzi, English, Pinyin, MBP_Phase, MBP_Level, Components, Scene, Notes
    # For each, let's see why it's in the MBP deck
    for i, (cid, nid, flds_str, tags) in enumerate(rows):
        f = flds_str.split('\x1f')
        f_id = f[0] if len(f) > 0 else ''
        f_hanzi = f[1] if len(f) > 1 else ''
        f_pinyin = f[2] if len(f) > 2 else ''
        f_eng = f[3] if len(f) > 3 else ''
        f_phase = f[11] if len(f) > 11 else ''
        f_level = f[12] if len(f) > 12 else ''
        f_words = f[14] if len(f) > 14 else ''
        char_code = ord(f_hanzi[0]) if f_hanzi else 0
        is_radical = (0x2E80 <= char_code <= 0x2EFF) or (0x2F00 <= char_code <= 0x2FDF)
        
        print(f"{i+1:2d}. ID={f_id:5} | {f_hanzi} | Pinyin: {f_pinyin:10} | {f_eng:22} | Phase: {f_phase} Lvl: {f_level} | Words: {f_words[:30]}")
