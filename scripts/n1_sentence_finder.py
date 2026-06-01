import os
import re
import json
import sys
import csv
from collections import Counter
from anki_db import AnkiConnection
from gap_finder import clean_sentence_hanzi, load_data_from_live_db, load_data_from_backup_json

# Reconfigure stdout to use UTF-8 on Windows console
sys.stdout.reconfigure(encoding='utf-8')

def check_descriptive_context(sentence, translation):
    """
    Checks if an immersion sentence provides poor context for learning.
    Returns (is_low_context, reason).
    """
    # Clean text to just Chinese characters
    clean_sent = "".join(clean_sentence_hanzi(sentence))
    if not clean_sent or len(clean_sent) < 5:
        return True, "Too short (< 5 characters)"
    if not translation or len(translation.strip()) < 3:
        return True, "Missing or very short translation"
    return False, ""

def find_n1_sentences(char_notes, migaku_notes):
    """
    Categorizes immersion cards into:
      - N+0: All characters are already learned in Palace.
      - N+1: Exactly one character in the sentence is missing from Palace.
      - N+2+: Multiple characters are missing from Palace.
    
    Returns lists of:
      - n0_sentences: list of dicts {sentence, word, translation, note_id}
      - n1_sentences: list of dicts {sentence, word, translation, note_id, missing_char, char_freq, low_context, low_context_reason}
      - n2_sentences: list of dicts {sentence, word, translation, note_id, missing_chars}
    """
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
            
    # 2. First pass: Count frequencies of all character gaps across all immersion sentences
    # This helps us rank N+1 sentences by how important the missing character is.
    all_gaps = []
    for note in migaku_notes:
        sent = note['fields'].get('Sentence', '')
        sent_chars = clean_sentence_hanzi(sent)
        gaps = [c for c in sent_chars if c not in learned_chars]
        all_gaps.extend(gaps)
        
    gap_frequencies = Counter(all_gaps)
    
    n0_sentences = []
    n1_sentences = []
    n2_sentences = []
    
    # 3. Second pass: Categorize sentences
    for note in migaku_notes:
        f = note['fields']
        sent = f.get('Sentence', '')
        word = f.get('Word', '')
        translation = f.get('Translated Sentence', f.get('Translation', ''))
        note_id = note.get('id', note.get('note_id', 0))
        
        sent_chars = clean_sentence_hanzi(sent)
        if not sent_chars:
            continue
            
        # Unique characters in this sentence that are not learned
        unique_gaps = sorted(list(set(c for c in sent_chars if c not in learned_chars)))
        
        # Check context quality
        is_low, low_reason = check_descriptive_context(sent, translation)
        
        sent_data = {
            'note_id': note_id,
            'sentence': sent,
            'word': word,
            'translation': translation,
            'lapses': note.get('lapses', 0),
            'ease': note.get('ease', 2500),
            'reps': note.get('reps', 0),
            'low_context': is_low,
            'low_context_reason': low_reason
        }
        
        if len(unique_gaps) == 0:
            n0_sentences.append(sent_data)
        elif len(unique_gaps) == 1:
            missing_char = unique_gaps[0]
            # Add specific info for N+1 sorting
            sent_data.update({
                'missing_char': missing_char,
                'char_freq': gap_frequencies.get(missing_char, 0)
            })
            n1_sentences.append(sent_data)
        else:
            sent_data.update({
                'missing_chars': unique_gaps,
                'missing_count': len(unique_gaps)
            })
            n2_sentences.append(sent_data)
            
    # Sort N+1 sentences:
    # 1. By character frequency descending (most high-yield characters first)
    # 2. By character name to group sentences with the same missing character together
    n1_sentences.sort(key=lambda x: (x['char_freq'], x['missing_char']), reverse=True)
    
    return n0_sentences, n1_sentences, n2_sentences

def main():
    # 1. Load data
    char_notes, migaku_notes = load_data_from_live_db()
    if char_notes is None:
        char_notes, migaku_notes = load_data_from_backup_json()
        
    if not char_notes:
        print("Error: Could not retrieve notes.")
        return
        
    print(f"Loaded {len(char_notes)} characters and {len(migaku_notes)} immersion cards.")
    
    # 2. Analyze
    n0, n1, n2 = find_n1_sentences(char_notes, migaku_notes)
    
    print("\n=== N+1 READABILITY ANALYSIS ===")
    print(f"N+0 (Fully Readable Sentences): {len(n0)}")
    print(f"N+1 (One Character Away):       {len(n1)}")
    print(f"N+2+ (Harder):                  {len(n2)}")
    
    print("\nTop 10 N+1 Sentences (Sorted by Missing Character Frequency):")
    for i, sent in enumerate(n1[:10]):
        print(f"\n{i+1}. Sentence: {sent['sentence']}")
        print(f"   Translation: {sent['translation']}")
        print(f"   Missing Character: {sent['missing_char']} (seen {sent['char_freq']} times in immersion)")

if __name__ == "__main__":
    main()
