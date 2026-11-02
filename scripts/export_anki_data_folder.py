import os
import sys
import json
import shutil
import sqlite3
from datetime import datetime

# Add scripts directory to path to import anki_db
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from anki_db import AnkiConnection

def format_date(timestamp):
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

def main():
    workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    anki_data_dir = os.path.join(workspace_dir, "anki_data")
    os.makedirs(anki_data_dir, exist_ok=True)
    
    print("Connecting to Anki and locating database...")
    try:
        # We instantiate AnkiConnection, which auto-detects Gabriel or active profiles
        conn_manager = AnkiConnection()
        db_path = conn_manager.db_path
        print(f"Located active Anki database at: {db_path}")
        
        # Copy the collection.anki2 database to anki_data
        target_db_path = os.path.join(anki_data_dir, "collection.anki2")
        print(f"Copying database to local copy: {target_db_path}...")
        shutil.copy2(db_path, target_db_path)
        
        # Also copy WAL file if it exists to keep SQLite file consistent
        if os.path.exists(db_path + "-wal"):
            shutil.copy2(db_path + "-wal", target_db_path + "-wal")
        if os.path.exists(db_path + "-shm"):
            shutil.copy2(db_path + "-shm", target_db_path + "-shm")
            
        print("Database copy complete. Connecting to local copy to query stats...")
        conn = sqlite3.connect(target_db_path)
        cursor = conn.cursor()
        
        # Query Decks and Counts
        # cards in Anki are linked to did (deck id)
        # notes are linked to cards via card.nid
        cursor.execute("SELECT id, name FROM decks")
        decks = {row[0]: row[1] for row in cursor.fetchall()}
        
        deck_stats = {}
        for did, name in decks.items():
            # count cards
            cursor.execute("SELECT COUNT(*) FROM cards WHERE did = ? OR odid = ?", (did, did))
            card_count = cursor.fetchone()[0]
            
            # count unique notes
            cursor.execute("SELECT COUNT(DISTINCT nid) FROM cards WHERE did = ? OR odid = ?", (did, did))
            note_count = cursor.fetchone()[0]
            
            # count suspended cards (queue < 0)
            cursor.execute("SELECT COUNT(*) FROM cards WHERE (did = ? OR odid = ?) AND queue < 0", (did, did))
            suspended_count = cursor.fetchone()[0]
            
            # average ease
            cursor.execute("SELECT AVG(factor) FROM cards WHERE (did = ? OR odid = ?) AND factor > 0", (did, did))
            avg_ease = cursor.fetchone()[0]
            avg_ease = round(avg_ease / 10.0, 1) if avg_ease else 250.0  # Anki stores ease in permille
            
            # total lapses
            cursor.execute("SELECT SUM(lapses) FROM cards WHERE did = ? OR odid = ?", (did, did))
            total_lapses = cursor.fetchone()[0] or 0
            
            deck_stats[name] = {
                "deck_id": did,
                "card_count": card_count,
                "note_count": note_count,
                "suspended_count": suspended_count,
                "avg_ease_percent": avg_ease,
                "total_lapses": total_lapses
            }
            
        # Overall Learning Statistics
        stats_summary = {
            "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "total_notes": sum(d['note_count'] for d in deck_stats.values()),
            "total_cards": sum(d['card_count'] for d in deck_stats.values()),
            "decks": deck_stats
        }
        
        # Write json summary
        json_path = os.path.join(anki_data_dir, "deck_statistics.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(stats_summary, f, ensure_ascii=False, indent=2)
            
        # Write readable README.md summary report
        readme_path = os.path.join(anki_data_dir, "README.md")
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write("# Anki Decks & Statistics Copy\n\n")
            f.write(f"This folder contains a local backup of your Anki database and active progress statistics. \n\n")
            f.write(f"- **Last Updated:** {stats_summary['last_updated']}\n")
            f.write(f"- **Total Decks Tracked:** {len(deck_stats)}\n")
            f.write(f"- **Total Notes:** {stats_summary['total_notes']}\n")
            f.write(f"- **Total Cards:** {stats_summary['total_cards']}\n\n")
            
            f.write("## Deck Overview\n\n")
            f.write("| Deck Name | Notes | Cards | Suspended | Avg Ease | Total Lapses |\n")
            f.write("| --- | --- | --- | --- | --- | --- |\n")
            for name, stats in sorted(deck_stats.items()):
                f.write(f"| **{name}** | {stats['note_count']} | {stats['card_count']} | {stats['suspended_count']} | {stats['avg_ease_percent']}% | {stats['total_lapses']} |\n")
                
            f.write("\n## Database Copy Details\n")
            f.write("- **Database File:** [collection.anki2](file:///c:/Users/gabri/Documents/anki_helper/anki_data/collection.anki2)\n")
            f.write("- **Statistics JSON:** [deck_statistics.json](file:///c:/Users/gabri/Documents/anki_helper/anki_data/deck_statistics.json)\n")
            f.write("\n*Note: Do not modify the local sqlite database copy directly. It is read-only for reporting and backup purposes.* \n")
            
        print("Local backup and statistics summary written to 'anki_data' folder successfully.")
        conn.close()
        
    except Exception as e:
        print(f"Error copying database and extracting stats: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
