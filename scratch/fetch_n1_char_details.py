import sys
import os
import json
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types

sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(r"c:\Users\gabri\Documents\antigravity\anki\scripts")

from anki_db import AnkiConnection
from n1_sentence_finder import find_n1_sentences
from gap_finder import load_data_from_live_db, load_data_from_backup_json

def fetch_details_from_gemini(characters, api_key):
    client = genai.Client(api_key=api_key)
    
    prompt = f"""
For each of the following Chinese characters, provide its pronunciation and translation details.
You must return a JSON array of objects. Each object must have these exact keys:
- "character": the input character
- "pinyin": the standard pinyin with correct diacritical tone marks (e.g. "diàn" for 殿)
- "english": a concise English definition (e.g. "palace, hall, temple" for 殿)
- "components": a list of visual components/radicals/primitives that make up the character. The components must be individual Chinese characters or common radicals that exist in standard character sets (e.g., for 殿, the components are ["尸", "共", "殳"]; for 谣, ["讠", "缶", " badass" -> wait, use standard: ["讠", "缶", "山", "皿"] or similar standard radicals like ["讠", "缶", "䍃"] or ["讠", "爫", "缶"] etc. Be accurate, clear, and list standard component characters).

Characters to process:
{", ".join(characters)}

Return ONLY the raw JSON block without markdown formatting or other text.
"""
    try:
        print(f"Sending batch request to Gemini for {len(characters)} characters...")
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        data = json.loads(response.text.strip())
        return data
    except Exception as e:
        print(f"Error calling Gemini: {e}")
        return None

def main():
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GOOGLE_API_KEY not found in .env.")
        return
        
    char_notes, migaku_notes = load_data_from_live_db()
    if char_notes is None:
        char_notes, migaku_notes = load_data_from_backup_json()
        
    if not char_notes:
        print("Error: Could not retrieve notes.")
        return
        
    n0, n1, n2 = find_n1_sentences(char_notes, migaku_notes)
    
    # Unique missing characters
    missing_chars = sorted(list(set(item['missing_char'] for item in n1)))
    print(f"Found {len(missing_chars)} missing characters to process.")
    
    # Split into batches of 35 to stay within token/rate limits if any
    batch_size = 35
    all_details = []
    
    for i in range(0, len(missing_chars), batch_size):
        batch = missing_chars[i:i+batch_size]
        details = fetch_details_from_gemini(batch, api_key)
        if details:
            all_details.extend(details)
            print(f"Successfully processed {len(all_details)}/{len(missing_chars)} characters.")
        time.sleep(2)
        
    # Save the resulting JSON data
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "n1_missing_chars_details.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_details, f, ensure_ascii=False, indent=2)
        
    print(f"Details saved to {output_path}")

if __name__ == "__main__":
    main()
