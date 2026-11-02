import sys
import os

sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from anki_db import AnkiConnection

with AnkiConnection('Main') as anki:
    c = anki.conn.cursor()
    # Find all notes whose card 1 was created recently (id > 1793570000000)
    c.execute("""
        SELECT n.id, n.flds, n.tags, c.id
        FROM cards c
        JOIN notes n ON c.nid = n.id
        WHERE c.id > 1793570000000 AND c.ord = 1
    """)
    rows = c.fetchall()
    print(f"Total notes with newly generated ord=1: {len(rows)}")
    
    # Let's inspect fields of these notes:
    # Field indices for Chinese Character - Double:
    # 0: ID
    # 1: Hanzi
    # 2: Pinyin
    # 3: English
    # 4: Initial
    # 5: Actor
    # 6: Set
    # 7: Tone
    # 8: Tone-Location
    # 9: Components
    # 10: Scene
    # 11: MBP_Phase
    # 12: MBP_Level
    # 13: HSK_2
    # 14: Common Words
    # 15: Translation of Words
    # 16: Simplified
    # 17: Traditional
    # 18: FrequencyTier
    # 19: FrequencyRank
    # 20: Sound
    # 21: Words_Sound
    # 22: Words_English_Sound
    # 23: Image
    # 24: Notes
    
    empty_pinyin = 0
    phase_counts = {}
    tags_counts = {}
    hsk_counts = {}
    
    for nid, flds_str, tags, cid in rows:
        f = flds_str.split('\x1f')
        f_id = f[0] if len(f) > 0 else ''
        f_hanzi = f[1] if len(f) > 1 else ''
        f_pinyin = f[2] if len(f) > 2 else ''
        f_phase = f[11] if len(f) > 11 else ''
        f_hsk = f[13] if len(f) > 13 else ''
        
        if not f_pinyin.strip():
            empty_pinyin += 1
            
        phase_counts[f_phase] = phase_counts.get(f_phase, 0) + 1
        hsk_counts[f_hsk] = hsk_counts.get(f_hsk, 0) + 1
        for t in tags.split():
            tags_counts[t] = tags_counts.get(t, 0) + 1
            
    print(f"Empty pinyin count among new cards: {empty_pinyin} / {len(rows)}")
    print(f"Phase counts: {phase_counts}")
    print(f"HSK counts: {hsk_counts}")
    print(f"Tags sample: {dict(list(tags_counts.items())[:10])}")
