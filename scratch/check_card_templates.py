import sys
import os
import json

sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from anki_db import AnkiConnection

with AnkiConnection(profile_name="Main") as anki:
    cursor = anki.conn.cursor()
    cursor.execute("SELECT id, name, tmpls FROM notetypes")
    for ntid, name, tmpls in cursor.fetchall():
        if "char" in name.lower() or "migaku" in name.lower():
            print(f"=== Notetype: {name} ({ntid}) ===")
            parsed_tmpls = json.loads(tmpls) if isinstance(tmpls, str) else tmpls
            for t in parsed_tmpls:
                print(f"  Template: {t.get('name')}")
                print(f"  Front: {t.get('qfmt', '')[:100]}...")
                print(f"  Back: {t.get('afmt', '')[:200]}...")
                print()
