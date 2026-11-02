import sys
import os
import json

sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from anki_db import AnkiConnection

with AnkiConnection('Main') as anki:
    c = anki.conn.cursor()
    
    # 1. Check notes where the first field (ID) is '28'
    c.execute("SELECT id, mid, flds, tags FROM notes")
    notes = c.fetchall()
    
    notetypes = anki.get_notetypes()
    
    print(f"Total notes: {len(notes)}")
    
    for nid, mid, flds_str, tags in notes:
        flds = flds_str.split('\x1f')
        nt_name = notetypes.get(mid, {}).get('name', 'Unknown')
        
        # Check if ID field is 28 or note ID is 28 or card ID is 28
        if len(flds) > 0 and flds[0] == '28':
            print(f"Found Note with ID field == '28':")
            print(f"  Note ID: {nid}, Notetype: {nt_name} ({mid})")
            print(f"  Fields count: {len(flds)}")
            field_names = [notetypes.get(mid, {}).get('fields', {}).get(i, f"f_{i}") for i in range(len(flds))]
            for fname, val in zip(field_names, flds):
                if val:
                    print(f"    {fname}: {val[:80]}")
            
            # Check cards for this note
            c.execute("SELECT id, ord, did, queue, type FROM cards WHERE nid = ?", (nid,))
            cards = c.fetchall()
            print(f"  Cards ({len(cards)}):")
            for cid, cord, did, queue, ctype in cards:
                print(f"    Card ID: {cid}, ord: {cord}, did: {did}, queue: {queue}, type: {ctype}")
            print("-" * 50)
            
        elif nid == 28:
            print(f"Found Note with internal ID == 28: mid={mid}")
