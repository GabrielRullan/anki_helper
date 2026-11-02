import json
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from anki_db import AnkiConnection

with AnkiConnection(profile_name="Main") as anki:
    notetypes = anki.get_notetypes()
    for ntid, nt in notetypes.items():
        if "char" in nt['name'].lower() or "mandarin" in nt['name'].lower() or "hanzi" in nt['name'].lower():
            print(f"Notetype {ntid}: {nt['name']}")
            print(f"Fields: {nt['fields']}")
