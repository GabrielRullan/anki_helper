import sys
import os

sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from anki_db import AnkiConnection

with AnkiConnection('Main') as anki:
    c = anki.conn.cursor()
    # Find all cards with flags = 2
    c.execute("""
        SELECT c.id, c.nid, c.ord, c.flags, c.did, n.mid, n.flds, n.tags
        FROM cards c
        JOIN notes n ON c.nid = n.id
        WHERE c.flags = 2
    """)
    rows = c.fetchall()
    print(f"Total cards with orange flag (flags=2): {len(rows)}")
    notetypes = anki.get_notetypes()
    
    notes_map = {}
    for cid, nid, cord, flags, did, mid, flds, tags in rows:
        if nid not in notes_map:
            notes_map[nid] = {'mid': mid, 'cards': [], 'flds': flds, 'tags': tags}
        notes_map[nid]['cards'].append((cid, cord))
        
    print(f"Total unique notes with orange flag: {len(notes_map)}")
    
    # Let's inspect each note
    print("\n--- Listing Notes with Flag=2 ---")
    for nid, data in notes_map.items():
        nt_name = notetypes.get(data['mid'], {}).get('name', 'Unknown')
        f = data['flds'].split('\x1f')
        f_id = f[0] if len(f) > 0 else ''
        f_hanzi = f[1] if len(f) > 1 else ''
        f_pinyin = f[2] if len(f) > 2 else ''
        f_eng = f[3] if len(f) > 3 else ''
        f_phase = f[11] if len(f) > 11 else ''
        f_comp = f[9] if len(f) > 9 else ''
        char_code = ord(f_hanzi[0]) if f_hanzi else 0
        is_radical = (0x2E80 <= char_code <= 0x2EFF) or (0x2F00 <= char_code <= 0x2FDF)
        
        cards_info = [f"ord={cord} (cid={cid})" for cid, cord in data['cards']]
        print(f"nid={nid} | Notetype={nt_name} | ID={f_id:6} | Hanzi={f_hanzi} (U+{char_code:04X}{', Radical' if is_radical else ''}) | Pinyin='{f_pinyin}' | English='{f_eng}' | Cards: {cards_info}")
