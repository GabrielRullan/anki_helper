import sys
import os

sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from anki_db import AnkiConnection

with AnkiConnection('Main') as anki:
    c = anki.conn.cursor()
    # Check notes for 林 (740), 黄 (856), 筷 (1288)
    for target_id in ['740', '856', '1288', '1776', '1909']:
        c.execute("SELECT id, flds, tags FROM notes WHERE flds LIKE ? || '\x1f%'", (target_id,))
        row = c.fetchone()
        if row:
            f = row[1].split('\x1f')
            print(f"=== ID: {f[0]} | Hanzi: {f[1]} | Pinyin: {f[2]} | English: {f[3]} ===")
            print(f"  Phase: {f[11]} | Level: {f[12]}")
            print(f"  Common Words: {f[14]}")
            print(f"  Scene: {f[10][:120]}...")
            print(f"  Tags: {row[2]}")
