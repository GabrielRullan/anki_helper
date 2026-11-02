import sys
import os
import json
import sqlite3

sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from anki_db import AnkiConnection

with AnkiConnection('Main') as anki:
    c = anki.conn.cursor()
    
    # 1. Let's inspect templates from `notetypes` table
    # In Anki 2.1 schemas, let's check `col` table or `notetypes` config
    c.execute("SELECT id, name, config FROM notetypes")
    for nid, name, config in c.fetchall():
        print(f"Notetype {nid}: {name}")
    
    # Let's inspect templates table
    c.execute("SELECT ntid, ord, name, config FROM templates")
    for ntid, ord_v, name, config in c.fetchall():
        print(f"Template ntid={ntid}, ord={ord_v}, name={name}, config_len={len(config) if config else 0}")
        # Let's see if config contains text/strings
        if config:
            try:
                # print any readable ascii/utf-8 strings in blob
                import re
                strings = re.findall(b'[\x20-\x7e\xc0-\xff]{4,}', config)
                print("   Config strings sample:", [s.decode('utf-8', errors='ignore') for s in strings[:10]])
            except Exception as e:
                print("   Error parsing config:", e)

    # Let's check notetype 1789676260669 ("Chinese Character - Single") vs 1768218202442 ("Chinese Character - Double")
    # How many notes have each notetype?
    c.execute("SELECT mid, count(*) FROM notes GROUP BY mid")
    for mid, count in c.fetchall():
        print(f"Notes count for mid={mid}: {count}")

