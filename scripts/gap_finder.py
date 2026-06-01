import os
import re
import json
import urllib.request
import ssl
import sys
import csv
from collections import Counter
from anki_db import AnkiConnection

# Reconfigure stdout to use UTF-8 on Windows console
sys.stdout.reconfigure(encoding='utf-8')

def clean_sentence_hanzi(text):
    """Filters only Chinese characters (Hanzi) from a string."""
    if not text:
        return []
    # Clean HTML first
    text = re.sub(r'<[^>]+>', '', text)
    # Match standard CJK ideographs
    return [char for char in text if '\u4e00' <= char <= '\u9fff']

def download_hsk_list():
    """Loads HSK 4 wordlist from local hsk4_vocab.csv, falling back to cached JSON or online download."""
    csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "hsk4_vocab.csv"))
    if os.path.exists(csv_path):
        print("Loading HSK 4 wordlist from local hsk4_vocab.csv...")
        try:
            hsk_words = []
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader, None) # skip header
                for row in reader:
                    if not row:
                        continue
                    word = row[0].strip()
                    pinyin = row[1].strip() if len(row) > 1 else ""
                    meaning = row[2].strip() if len(row) > 2 else ""
                    if word:
                        # Map into the dict structure used throughout the codebase:
                        # {'s': word, 'f': [{'i': {'y': pinyin}, 'm': [meaning]}]}
                        hsk_words.append({
                            's': word,
                            'f': [{
                                'i': {'y': pinyin},
                                'm': [meaning]
                            }]
                        })
            return hsk_words
        except Exception as e:
            print(f"Warning: Could not read hsk4_vocab.csv ({e}). Falling back to cached JSON...")

    cache_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "hsk4_cache.json"))
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass # download again if corrupt
            
    url = "https://raw.githubusercontent.com/drkameleon/complete-hsk-vocabulary/main/wordlists/inclusive/old/4.min.json"
    print(f"Downloading HSK 4 wordlist from repository...")
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ctx) as response:
            data = json.loads(response.read().decode('utf-8'))
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return data
    except Exception as e:
        print(f"Warning: Could not download HSK 4 wordlist ({e}). HSK analysis will be skipped.")
        return []

def load_data_from_live_db():
    """Tries to read data live from Anki SQLite database."""
    try:
        with AnkiConnection(profile_name="Main") as anki:
            print("Connecting to live Anki database...")
            char_notes = anki.get_notes_in_deck("Characters")
            migaku_notes = anki.get_notes_in_deck("Migaku")
            return char_notes, migaku_notes
    except Exception as e:
        print(f"Could not connect to live Anki DB: {e}")
        return None, None

def load_data_from_backup_json():
    """Reads data from the static anki_extract.json backup file."""
    backup_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "anki_extract.json"))
    if not os.path.exists(backup_path):
        print(f"Backup file {backup_path} not found.")
        return None, None
        
    print(f"Reading from static backup file: {backup_path}...")
    try:
        with open(backup_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Reconstruct field dictionary style to match get_notes_in_deck return format
            char_notes = [{'id': n['note_id'], 'fields': {'Hanzi': n['hanzi'], 'Simplified': n.get('simplified', '')}} for n in data['characters']]
            migaku_notes = [{'id': n['note_id'], 'fields': {'Sentence': n['sentence'], 'Word': n['word']}} for n in data['immersion']]
            return char_notes, migaku_notes
    except Exception as e:
        print(f"Error reading backup file: {e}")
        return None, None

def analyze_gap_and_synergy(char_notes, migaku_notes, hsk_words):
    # 1. Compile learned characters
    learned_chars = set()
    for note in char_notes:
        hz = note['fields'].get('Hanzi', '').strip()
        if hz:
            learned_chars.add(hz)
        # Also include Simplified form if it differs/exists (handles radical variants like ⻚ vs 页)
        simp = note['fields'].get('Simplified', '').strip()
        if simp:
            learned_chars.add(simp)
            
    # Load manually marked known characters from known_characters.csv
    known_chars_csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "known_characters.csv"))
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
            
    # Also compile learned words from Migaku word fields
    learned_words = set()
    for note in migaku_notes:
        w = note['fields'].get('Word', '').strip()
        # Clean HTML out of words if any
        w_cleaned = re.sub(r'<[^>]+>', '', w).strip()
        if w_cleaned:
            learned_words.add(w_cleaned)
            
    # Load manually marked known words from known_words.csv
    known_words_csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "known_words.csv"))
    if os.path.exists(known_words_csv_path):
        try:
            with open(known_words_csv_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader, None) # skip header
                for row in reader:
                    if not row:
                        continue
                    word = row[0].strip()
                    if word:
                        learned_words.add(word)
        except Exception as e:
            print(f"Warning: Could not read known_words.csv ({e})")
            
    print(f"Learned characters: {len(learned_chars)}")
    print(f"Studied immersion cards: {len(migaku_notes)}")
    print(f"Known immersion words (including manually marked): {len(learned_words)}")
    
    # 2. Extract and count all characters seen in immersion sentences and words
    all_immersion_chars = []
    for note in migaku_notes:
        sent = note['fields'].get('Sentence', '')
        all_immersion_chars.extend(clean_sentence_hanzi(sent))
        w = note['fields'].get('Word', '')
        all_immersion_chars.extend(clean_sentence_hanzi(w))
        
    char_counts = Counter(all_immersion_chars)
    seen_chars = set(char_counts.keys())
    
    # 3. Calculate gaps
    gaps = seen_chars - learned_chars
    sorted_gaps = sorted([(char, char_counts[char]) for char in gaps], key=lambda x: x[1], reverse=True)
    
    # 4. HSK characters gap analysis
    hsk_chars = set()
    hsk_words_set = set()
    for hsk_item in hsk_words:
        word = hsk_item.get('s', '')
        if word:
            hsk_words_set.add(word)
            hsk_chars.update(clean_sentence_hanzi(word))
            
    missing_chars_hsk = hsk_chars - learned_chars
    
    # 5. Words in Migaku deck missing that are in HSK
    missing_hsk_words_in_migaku = []
    for hsk_item in hsk_words:
        word = hsk_item.get('s', '')
        if word and word not in learned_words:
            # Parse definition
            meanings = []
            for f_item in hsk_item.get('f', []):
                meanings.extend(f_item.get('m', []))
            meanings_str = "; ".join(meanings)
            
            # Pinyin
            pinyin = ""
            if hsk_item.get('f'):
                pinyin = hsk_item['f'][0].get('i', {}).get('y', '')
                
            missing_hsk_words_in_migaku.append({
                'word': word,
                'pinyin': pinyin,
                'meaning': meanings_str
            })
    
    # 6. HSK 4 Synergy analysis
    synergy_words = []
    one_char_away_words = {} # character -> list of HSK words that need it
    
    for hsk_item in hsk_words:
        word = hsk_item.get('s', '')
        if not word or word in learned_words:
            continue
            
        # Parse definition
        meanings = []
        for f_item in hsk_item.get('f', []):
            meanings.extend(f_item.get('m', []))
        meanings_str = "; ".join(meanings)
        
        # Pinyin
        pinyin = ""
        if hsk_item.get('f'):
            pinyin = hsk_item['f'][0].get('i', {}).get('y', '')
            
        word_chars = set(word)
        missing_chars = word_chars - learned_chars
        
        if len(missing_chars) == 0:
            # Word is composed entirely of learned characters!
            synergy_words.append({
                'word': word,
                'pinyin': pinyin,
                'meanings': meanings_str
            })
        elif len(missing_chars) == 1:
            # Word is exactly 1 character away
            missing_char = list(missing_chars)[0]
            if missing_char not in one_char_away_words:
                one_char_away_words[missing_char] = []
            one_char_away_words[missing_char].append({
                'word': word,
                'pinyin': pinyin,
                'meanings': meanings_str
            })

    # Sort one character away by how many HSK words it unlocks
    sorted_unlocks = []
    for char, words in one_char_away_words.items():
        sorted_unlocks.append({
            'character': char,
            'unlocked_words': words,
            'unlock_count': len(words),
            'immersion_occurrences': char_counts.get(char, 0)
        })
    # Sort primarily by unlock count, secondarily by immersion frequency
    sorted_unlocks.sort(key=lambda x: (x['unlock_count'], x['immersion_occurrences']), reverse=True)
    
    return {
        'learned_chars_count': len(learned_chars),
        'total_immersion_cards': len(migaku_notes),
        'total_gaps_count': len(gaps),
        'top_gaps': sorted_gaps[:50], # Top 50 gaps
        'synergy_words': synergy_words,
        'unlocked_chars': sorted_unlocks[:30], # Top 30 characters to unlock most words
        'missing_chars_migaku': sorted(list(gaps)),
        'missing_chars_hsk': sorted(list(missing_chars_hsk)),
        'missing_hsk_words_in_migaku': missing_hsk_words_in_migaku
    }

def generate_report(results):
    report_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "gap_report.md"))
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# HSK 4 Chinese Learning Gap & Synergy Report\n\n")
        f.write(f"This report highlights the gaps between your **Characters** memory palace and your **Migaku** immersion sentences, and schedules high-yield HSK 4 vocabulary.\n\n")
        
        f.write("## Summary Statistics\n")
        f.write(f"- **Characters learned in Palace**: {results['learned_chars_count']}\n")
        f.write(f"- **Immersion cards processed**: {results['total_immersion_cards']}\n")
        f.write(f"- **Unique character gaps in immersion**: {results['total_gaps_count']}\n")
        f.write(f"- **HSK 1-4 words ready for study (zero new characters)**: {len(results['synergy_words'])}\n")
        f.write(f"- **HSK characters missing from Palace**: {len(results['missing_chars_hsk'])}\n")
        f.write(f"- **HSK words missing from Migaku deck**: {len(results['missing_hsk_words_in_migaku'])}\n\n")
        
        f.write("## 1. Top Character Gaps (from Immersion)\n")
        f.write("These characters appear frequently in your immersion sentences but have not yet been added to your Characters deck. Adding these to your memory palace will make those immersion sentences significantly easier to read!\n\n")
        f.write("| Character | Occurrences in Immersion | Actions |\n")
        f.write("| --- | --- | --- |\n")
        for char, count in results['top_gaps'][:30]:
            f.write(f"| **{char}** | {count} | [Create MBP Card] |\n")
            
        f.write("\n## 2. HSK 4 Synergy Words (Ready to Study!)\n")
        f.write("You already know all the characters making up these HSK 1-4 vocabulary words. You can add these words to your study rotation with **zero character overhead**:\n\n")
        f.write("| Word | Pinyin | Meaning |\n")
        f.write("| --- | --- | --- |\n")
        # Show top 50 synergy words
        for item in results['synergy_words'][:50]:
            f.write(f"| **{item['word']}** | {item['pinyin']} | {item['meanings']} |\n")
        if len(results['synergy_words']) > 50:
            f.write(f"\n*...and {len(results['synergy_words']) - 50} more synergy words listed in the database.*\n")
            
        f.write("\n## 3. High-Yield Character Unlocks (1 Character Away)\n")
        f.write("Learning just **one** of these characters will unlock multiple HSK 1-4 vocabulary words that you can immediately study:\n\n")
        for item in results['unlocked_chars'][:15]:
            f.write(f"### Character: **{item['character']}** (seen {item['immersion_occurrences']} times in immersion)\n")
            f.write(f"Learning this character unlocks **{item['unlock_count']}** vocabulary words:\n\n")
            f.write("| Word | Pinyin | Meaning |\n")
            f.write("| --- | --- | --- |\n")
            for w in item['unlocked_words']:
                f.write(f"| **{w['word']}** | {w['pinyin']} | {w['meanings']} |\n")
            f.write("\n")
            
        # Add the new section specifically for the user's questions
        f.write("## 4. HSK & Migaku Gap Analysis\n\n")
        
        f.write("### Characters missing from Characters deck that are in Migaku deck\n")
        f.write(f"Total: {len(results['missing_chars_migaku'])}\n\n")
        f.write(" ".join([f"**{c}**" for c in results['missing_chars_migaku']]) + "\n\n")
        
        f.write("### Characters missing from Characters deck that are in HSK\n")
        f.write(f"Total: {len(results['missing_chars_hsk'])}\n\n")
        if results['missing_chars_hsk']:
            f.write(" ".join([f"**{c}**" for c in results['missing_chars_hsk']]) + "\n\n")
        else:
            f.write("None! You have added all HSK 4 characters to your Characters deck.\n\n")
            
        f.write("### HSK words missing from Migaku deck\n")
        f.write(f"Total: {len(results['missing_hsk_words_in_migaku'])}\n\n")
        f.write(", ".join([f"**{item['word']}**" for item in results['missing_hsk_words_in_migaku']]) + "\n\n")
            
    print(f"\nReport successfully generated and saved to: {os.path.abspath(report_path)}")

def main():
    # 1. Fetch character and immersion data
    char_notes, migaku_notes = load_data_from_live_db()
    if char_notes is None:
        char_notes, migaku_notes = load_data_from_backup_json()
        
    if not char_notes:
        print("Error: Could not retrieve notes. Ensure Anki is running or anki_extract.json exists.")
        return
        
    # 2. Download HSK wordlist
    hsk_words = download_hsk_list()
    if not hsk_words:
        return
        
    # 3. Analyze
    print("Analyzing characters and compiling HSK synergies...")
    results = analyze_gap_and_synergy(char_notes, migaku_notes, hsk_words)
    
    # 4. Write reports
    generate_report(results)
    
    # 5. Output small summary to console
    print("\n=== ANALYSIS SUMMARY ===")
    print(f"Characters Learned: {results['learned_chars_count']}")
    print(f"Character Gaps in Immersion: {results['total_gaps_count']}")
    print(f"HSK Synergy Words Ready: {len(results['synergy_words'])}")
    print(f"HSK Characters Missing from Palace: {len(results['missing_chars_hsk'])}")
    print(f"HSK Words Missing from Migaku: {len(results['missing_hsk_words_in_migaku'])}")
    
    print("\n=== ANSWERS TO SPECIFIC GAP QUESTIONS ===")
    print(f"1. Characters missing that are in Migaku deck (Total {len(results['missing_chars_migaku'])}):")
    print("  " + " ".join(results['missing_chars_migaku']))
    
    print(f"\n2. Characters missing that are in HSK (Total {len(results['missing_chars_hsk'])}):")
    if results['missing_chars_hsk']:
        print("  " + " ".join(results['missing_chars_hsk']))
    else:
        print("  None! (You have all HSK characters in your Palace)")
        
    print(f"\n3. Words in Migaku deck missing that are in HSK (Total {len(results['missing_hsk_words_in_migaku'])}):")
    # Show first 50 words to avoid console spam, and tell the user they can view the full list in the report
    words_to_show = [item['word'] for item in results['missing_hsk_words_in_migaku'][:50]]
    print("  " + ", ".join(words_to_show))
    if len(results['missing_hsk_words_in_migaku']) > 50:
        print(f"  ...and {len(results['missing_hsk_words_in_migaku']) - 50} more. See the full list in gap_report.md")
        
    print("\nTop 5 Character Gaps (from Immersion):")
    for char, count in results['top_gaps'][:5]:
        print(f"  - {char}: seen {count} times")
        
    print("\nTop 3 HSK Synergy Words:")
    for w in results['synergy_words'][:3]:
        print(f"  - {w['word']} ({w['pinyin']}): {w['meanings'][:60]}...")
        
if __name__ == "__main__":
    main()

