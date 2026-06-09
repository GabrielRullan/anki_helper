import sys
import os

sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(r"c:\Users\gabri\Documents\antigravity\anki\scripts")

from anki_db import AnkiConnection
from n1_sentence_finder import find_n1_sentences
from gap_finder import load_data_from_live_db, load_data_from_backup_json

def main():
    char_notes, migaku_notes = load_data_from_live_db()
    if char_notes is None:
        char_notes, migaku_notes = load_data_from_backup_json()
        
    if not char_notes:
        print("Error: Could not retrieve notes.")
        return
        
    print(f"Loaded {len(char_notes)} characters and {len(migaku_notes)} immersion cards.")
    
    n0, n1, n2 = find_n1_sentences(char_notes, migaku_notes)
    
    # Extract unique missing characters and count their occurrences in n1 sentences
    missing_char_counts = {}
    for item in n1:
        c = item['missing_char']
        missing_char_counts[c] = missing_char_counts.get(c, 0) + 1
        
    sorted_missing = sorted(missing_char_counts.items(), key=lambda x: x[1], reverse=True)
    print(f"\nFound {len(sorted_missing)} unique missing characters in N+1 sentences:")
    for char, count in sorted_missing[:30]:
        print(f"  Character: {char} (occurs in {count} N+1 sentences)")

if __name__ == "__main__":
    main()
