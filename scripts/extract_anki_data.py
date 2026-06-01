import json
import re
import sys
import os
from anki_db import AnkiConnection

# Reconfigure stdout to UTF-8
sys.stdout.reconfigure(encoding='utf-8')

def clean_html(text):
    """Helper to clean up HTML tags from Anki fields."""
    if not text:
        return ""
    # Replace breaks with newlines
    text = re.sub(r'<br\s*/?>', '\n', text)
    # Remove all other HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Replace HTML entities
    text = text.replace('&nbsp;', ' ').replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
    return text.strip()

def main():
    try:
        with AnkiConnection(profile_name="Main") as anki:
            print("Connecting to Anki database...")
            
            # Extract Characters deck
            print("Extracting 'Characters' deck...")
            char_notes = anki.get_notes_in_deck("Characters")
            print(f"Retrieved {len(char_notes)} character notes.")
            
            extracted_chars = []
            for note in char_notes:
                f = note['fields']
                
                # Extract and clean key fields
                char_data = {
                    'note_id': note['id'],
                    'hanzi': f.get('Hanzi', '').strip(),
                    'simplified': f.get('Simplified', '').strip(),
                    'pinyin': f.get('Pinyin', '').strip(),
                    'english': f.get('English', '').strip(),
                    'tone': f.get('Tone', '').strip(),
                    'tone_location': f.get('Tone-Location', '').strip(),
                    'actor': f.get('Actor', '').strip(),
                    'set': f.get('Set', '').strip(),
                    'components': clean_html(f.get('Components', '')),
                    'scene': clean_html(f.get('Scene', '')),
                    'hsk_level': f.get('HSK_2', '').strip(), # This field indicates HSK levels
                    'common_words': clean_html(f.get('Common Words', '')),
                    'translation_of_words': clean_html(f.get('Translation of Words', '')),
                    'notes': clean_html(f.get('Notes', '')),
                    'lapses': note.get('lapses', 0),
                    'ease': note.get('ease', 2500),
                    'reps': note.get('reps', 0),
                    'suspended': note.get('suspended', False),
                    'tags': note.get('tags', [])
                }
                
                # Only append if we have actual Hanzi content
                if char_data['hanzi']:
                    extracted_chars.append(char_data)
            
            # Extract Migaku deck
            print("Extracting 'Migaku' deck...")
            migaku_notes = anki.get_notes_in_deck("Migaku")
            print(f"Retrieved {len(migaku_notes)} immersion notes.")
            
            extracted_immersion = []
            for note in migaku_notes:
                f = note['fields']
                
                imm_data = {
                    'note_id': note['id'],
                    'word': clean_html(f.get('Word', '')),
                    'sentence': clean_html(f.get('Sentence', '')),
                    'translation': clean_html(f.get('Translated Sentence', '')),
                    'definitions': clean_html(f.get('Definitions', '')),
                    'example_sentences': clean_html(f.get('Example Sentences', '')),
                    'notes': clean_html(f.get('Notes', '')),
                    'lapses': note.get('lapses', 0),
                    'ease': note.get('ease', 2500),
                    'reps': note.get('reps', 0),
                    'suspended': note.get('suspended', False),
                    'tags': note.get('tags', [])
                }
                
                # Check that we have a sentence or a word
                if imm_data['sentence'] or imm_data['word']:
                    extracted_immersion.append(imm_data)
            
            # Compile results
            output_data = {
                'characters': extracted_chars,
                'immersion': extracted_immersion
            }
            
            output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "anki_extract.json"))
            with open(output_path, 'w', encoding='utf-8') as outfile:
                json.dump(output_data, outfile, ensure_ascii=False, indent=2)
                
            print(f"Extraction complete! Saved data to: {output_path}")
            print(f"Successfully extracted {len(extracted_chars)} characters and {len(extracted_immersion)} immersion cards.")
            
    except Exception as e:
        print(f"An error occurred during extraction: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
