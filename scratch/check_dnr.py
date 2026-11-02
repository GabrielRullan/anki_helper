import sys
import os

sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from anki_db import AnkiConnection

with AnkiConnection('Main') as anki:
    c = anki.conn.cursor()
    # Notetype 1789676260669 is Chinese Character - Single
    c.execute("SELECT id, flds FROM notes WHERE mid = 1789676260669")
    rows = c.fetchall()
    print(f"Total notes in Chinese Character - Single: {len(rows)}")
    
    dnr_values = {}
    for nid, flds_str in rows:
        flds = flds_str.split('\x1f')
        # What is the last field (Do_Not_Recall)?
        # Let's check ord 25
        dnr = flds[25] if len(flds) > 25 else '<missing>'
        dnr_values[dnr] = dnr_values.get(dnr, 0) + 1
        
    print("Do_Not_Recall value counts in Single:", dnr_values)
