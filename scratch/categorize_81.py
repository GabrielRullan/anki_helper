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
    
    radicals = []
    kangxi_props = []
    bound_morphemes = []
    others = []
    
    for cid, nid, flds_str, tags in rows:
        f = flds_str.split('\x1f')
        f_id = f[0] if len(f) > 0 else ''
        f_hanzi = f[1] if len(f) > 1 else ''
        f_pinyin = f[2] if len(f) > 2 else ''
        f_eng = f[3] if len(f) > 3 else ''
        f_words = f[14] if len(f) > 14 else ''
        char_code = ord(f_hanzi[0]) if f_hanzi else 0
        is_radical_block = (0x2E80 <= char_code <= 0x2EFF) or (0x2F00 <= char_code <= 0x2FDF)
        
        entry = (f_id, f_hanzi, f_pinyin, f_eng, f_words)
        
        if is_radical_block:
            radicals.append(entry)
        elif '(部首)' in f_words or '(部件)' in f_words or f_words.strip() == '':
            kangxi_props.append(entry)
        elif any(s in f_words for s in ['子', '儿', '色', '头', '老']):
            bound_morphemes.append(entry)
        else:
            others.append(entry)
            
    print(f"1. Radicals Supplement Block ({len(radicals)}):")
    for r in radicals:
        print(f"   ID={r[0]:4} {r[1]} [{r[2]}]: {r[3]}")
        
    print(f"\n2. Kangxi / Pure Components (marked 部首/部件) ({len(kangxi_props)}):")
    for r in kangxi_props:
        print(f"   ID={r[0]:4} {r[1]} [{r[2]}]: {r[3]}")
        
    print(f"\n3. Bound Morphemes (almost exclusively used with 子/儿/色/头/老, etc.) ({len(bound_morphemes)}):")
    for r in bound_morphemes:
        print(f"   ID={r[0]:4} {r[1]} [{r[2]}]: {r[3]} (Words: {r[4]})")
        
    print(f"\n4. Other Characters ({len(others)}):")
    for r in others:
        print(f"   ID={r[0]:4} {r[1]} [{r[2]}]: {r[3]} (Words: {r[4]})")
