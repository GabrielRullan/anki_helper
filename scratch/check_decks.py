import sys
import os

sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from anki_db import AnkiConnection

with AnkiConnection('Main') as anki:
    decks = anki.get_decks()
    c = anki.conn.cursor()
    c.execute("SELECT did, count(*) FROM cards WHERE flags = 2 GROUP BY did")
    print("Flagged cards decks:")
    for did, count in c.fetchall():
        print(f"  Deck: {decks.get(did, 'Unknown')} ({did}) -> {count} cards")
        
    c.execute("SELECT did, count(*) FROM cards WHERE id > 1793570000000 AND ord = 1 AND flags = 0 GROUP BY did")
    print("\nUnflagged newly generated cards decks:")
    for did, count in c.fetchall():
        print(f"  Deck: {decks.get(did, 'Unknown')} ({did}) -> {count} cards")
