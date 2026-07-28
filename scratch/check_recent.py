import os
import sys
import re
import csv
from datetime import datetime

# Adjust path to find anki_db module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts')))
from anki_db import AnkiConnection

sys.stdout.reconfigure(encoding='utf-8')

def clean_hanzi(text):
    if not text:
        return []
    text = re.sub(r'<[^>]+>', '', text)
    return [char for char in text if '\u4e00' <= char <= '\u9fff']

def main():
    try:
        with AnkiConnection(profile_name="Gabriel") as anki:
            print("Successfully connected to Anki DB.")
            
            # Decks
            char_deck_name = anki.best_match_deck(["Chinese::Char", "Chinese\x1fChar", "Characters"])
            word_deck_name = anki.best_match_deck(["Chinese::Words", "Chinese\x1fWords", "Migaku"])
            
            print(f"Reading Character deck: {char_deck_name}")
            char_notes = anki.get_notes_in_deck(char_deck_name)
            
            print(f"Reading Word deck: {word_deck_name}")
            word_notes = anki.get_notes_in_deck(word_deck_name)
            
            # Collect all characters in Characters deck (Hanzi and Simplified)
            learned_chars = set()
            for note in char_notes:
                hz = note['fields'].get('Hanzi', '').strip()
                if hz:
                    learned_chars.add(hz)
                simp = note['fields'].get('Simplified', '').strip()
                if simp:
                    learned_chars.add(simp)
            
            # Load manually marked known characters from known_characters.csv
            known_chars_csv_path = os.path.join(os.path.dirname(__file__), "..", "data", "known_characters.csv")
            if os.path.exists(known_chars_csv_path):
                try:
                    with open(known_chars_csv_path, 'r', encoding='utf-8') as f:
                        reader = csv.reader(f)
                        next(reader, None) # skip header
                        for row in reader:
                            if not row:
                                continue
                            char = row[0].strip()
                            if char:
                                learned_chars.add(char)
                except Exception as e:
                    print(f"Warning: Could not read known_characters.csv ({e})")
            
            print(f"Total unique characters in Characters deck (plus known_characters): {len(learned_chars)}")
            
            # Sort word notes by note ID (creation timestamp) descending to find recent ones
            word_notes_sorted = sorted(word_notes, key=lambda x: x['id'], reverse=True)
            
            print(f"Total words in Chinese::Words deck: {len(word_notes)}")
            print("\nAnalyzing recent words...")
            
            # Let's check the most recent 50 words added
            recent_count = min(50, len(word_notes_sorted))
            print(f"Checking the {recent_count} most recently added words:")
            print(f"{'Word':<15} | {'Date Added':<20} | {'Status':<15} | {'Missing Characters':<20}")
            print("-" * 80)
            
            missing_count = 0
            recent_gaps = []
            for note in word_notes_sorted[:recent_count]:
                word = note['fields'].get('Word', '').strip()
                word_clean = re.sub(r'<[^>]+>', '', word).strip()
                
                timestamp_s = note['id'] / 1000.0
                date_str = datetime.fromtimestamp(timestamp_s).strftime('%Y-%m-%d %H:%M:%S')
                
                chars_in_word = clean_hanzi(word_clean)
                missing = [c for c in chars_in_word if c not in learned_chars]
                
                if missing:
                    status = "GAP DETECTED"
                    missing_str = ", ".join(missing)
                    missing_count += 1
                    recent_gaps.append((word_clean, date_str, missing))
                else:
                    status = "ALL CHARS OK"
                    missing_str = "-"
                
                print(f"{word_clean:<15} | {date_str:<20} | {status:<15} | {missing_str:<20}")
            
            print("-" * 80)
            print(f"Analysis complete. Found {missing_count} words with missing characters out of the {recent_count} most recent.")
            
            # Write a detailed report to a markdown file
            report_path = os.path.join(os.path.dirname(__file__), "..", "recent_word_character_gaps.md")
            with open(report_path, 'w', encoding='utf-8') as rf:
                rf.write("# Recent Word Character Gaps Report\n\n")
                rf.write(f"Analyzed the **{recent_count}** most recently added words in `Chinese::Words`.\n")
                rf.write(f"Found **{missing_count}** words that contain characters not in `Chinese::Char` (including `known_characters.csv`).\n\n")
                if recent_gaps:
                    rf.write("## Words with Missing Characters\n\n")
                    rf.write("| Word | Date Added | Missing Characters |\n")
                    rf.write("| --- | --- | --- |\n")
                    for w, d, m in recent_gaps:
                        m_str = ", ".join(f"**{c}**" for c in m)
                        rf.write(f"| {w} | {d} | {m_str} |\n")
                else:
                    rf.write("All characters in the recent words are present in `Chinese::Char`!\n")
            print(f"\nDetailed report saved to: {report_path}")
            
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
