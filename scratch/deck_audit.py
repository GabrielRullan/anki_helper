import sys
import os
import json

# Add scripts directory to path to import anki_db
sys.path.append(os.path.abspath("scripts"))
from anki_db import AnkiConnection

def audit():
    with AnkiConnection() as conn:
        print("=== ANKI DECK AUDIT ===")
        
        decks = conn.get_decks()
        print("Available Decks:", list(decks.values()))
        
        # 1. Chinese::Words (Migaku Word)
        try:
            words = conn.get_notes_in_deck("Chinese::Words")
            print(f"\n--- Chinese::Words --- Total Notes: {len(words)}")
            missing_characters_field = 0
            missing_notes = 0
            missing_images = 0
            missing_word_audio = 0
            missing_sentence_audio = 0
            
            for n in words:
                f = n['fields']
                if not f.get('Characters', '').strip():
                    missing_characters_field += 1
                if not f.get('Notes', '').strip():
                    missing_notes += 1
                if not f.get('Images', '').strip():
                    missing_images += 1
                if not f.get('Word Audio', '').strip():
                    missing_word_audio += 1
                if not f.get('Sentence Audio', '').strip():
                    missing_sentence_audio += 1
                    
            print(f"  Missing 'Characters' field (unlinked): {missing_characters_field}")
            print(f"  Missing 'Notes' field (Peanuts prompt): {missing_notes}")
            print(f"  Missing 'Images' field: {missing_images}")
            print(f"  Missing 'Word Audio': {missing_word_audio}")
            print(f"  Missing 'Sentence Audio': {missing_sentence_audio}")
        except Exception as e:
            print("Error inspecting Chinese::Words:", e)

        # 2. Chinese::Char (MBP Characters)
        try:
            chars = conn.get_notes_in_deck("Chinese::Char")
            print(f"\n--- Chinese::Char --- Total Notes: {len(chars)}")
            missing_char_scene = 0
            missing_char_image = 0
            missing_char_audio = 0
            missing_pinyin = 0
            
            for n in chars:
                f = n['fields']
                if not f.get('Scene', '').strip():
                    missing_char_scene += 1
                if not f.get('Image', '').strip():
                    missing_char_image += 1
                if not f.get('Audio', '').strip() and not f.get('Sound', '').strip():
                    missing_char_audio += 1
                if not f.get('Pinyin', '').strip():
                    missing_pinyin += 1
                    
            print(f"  Missing 'Scene' (Mnemonic): {missing_char_scene}")
            print(f"  Missing 'Image': {missing_char_image}")
            print(f"  Missing Audio/Sound: {missing_char_audio}")
            print(f"  Missing Pinyin: {missing_pinyin}")
        except Exception as e:
            print("Error inspecting Chinese::Char:", e)

        # 3. Chinese::Sent
        try:
            sents = conn.get_notes_in_deck("Chinese::Sent")
            print(f"\n--- Chinese::Sent --- Total Notes: {len(sents)}")
            missing_sent_audio = 0
            for n in sents:
                f = n['fields']
                if not f.get('Sentence_Audio', '').strip():
                    missing_sent_audio += 1
            print(f"  Missing Sentence_Audio: {missing_sent_audio}")
        except Exception as e:
            print("Error inspecting Chinese::Sent:", e)

        # 4. Japanese::Migaku
        try:
            jp_notes = conn.get_notes_in_deck("Japanese::Migaku")
            print(f"\n--- Japanese::Migaku --- Total Notes: {len(jp_notes)}")
            missing_reading = 0
            missing_translated = 0
            missing_notes_jp = 0
            for n in jp_notes:
                f = n['fields']
                if not f.get('Reading', '').strip():
                    missing_reading += 1
                if not f.get('Translated Sentence', '').strip():
                    missing_translated += 1
                if not f.get('Notes', '').strip():
                    missing_notes_jp += 1
            print(f"  Missing 'Reading' (Furigana): {missing_reading}")
            print(f"  Missing 'Translated Sentence': {missing_translated}")
            print(f"  Missing 'Notes': {missing_notes_jp}")
        except Exception as e:
            print("Error inspecting Japanese::Migaku:", e)

if __name__ == '__main__':
    audit()
