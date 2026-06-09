import os
import re
import json
import sys
import io
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Fix for terminal encoding issues
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=API_KEY)

def parse_new_words(file_path):
    if not os.path.exists(file_path):
        return []
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    try:
        parts = content.split('## 🟡 Pendiente de incluir')
        pendiente_section = parts[-1].split('## 🔴 Suelto')[0]
    except IndexError:
        return []

    items = []
    current_item = None
    
    for line in pendiente_section.splitlines():
        line_stripped = line.strip()
        if not line_stripped:
            continue
            
        root_match = re.match(r'^[-*]\s+(?:\*\*)?([^*()]+?)(?:\*\*)?\s*\(([^)]+)\)(?:\s*(?:—|-)\s*(.+))?', line)
        if root_match:
            if current_item:
                items.append(current_item)
            word = root_match.group(1).strip()
            pinyin = root_match.group(2).strip().replace('_', '').replace('*', '').strip()
            translation = root_match.group(3).strip() if root_match.group(3) else ""
            current_item = {
                'word': word,
                'pinyin': pinyin,
                'translation': translation,
                'frase': "",
                'traduccion': "",
                'desc': "",
                'prompt': "",
                'orig_line': line.strip()
            }
            continue
            
        if current_item:
            frase_match = re.match(r'^\s*[-*]\s*(?:\*\*|\*|_|__)Frase:(?:\*\*|\*|_|__)\s*(.+)', line)
            if frase_match:
                current_item['frase'] = frase_match.group(1).strip()
                continue
                
            traduccion_es_match = re.match(r'^\s*[-*]\s*(?:\*\*|\*|_|__)Traducción Español:(?:\*\*|\*|_|__)\s*(.+)', line)
            if traduccion_es_match:
                current_item['traduccion'] = traduccion_es_match.group(1).strip()
                continue
                
            traduccion_generic_match = re.match(r'^\s*[-*]\s*(?:\*\*|\*|_|__)Traducción:(?:\*\*|\*|_|__)\s*(.+)', line)
            if traduccion_generic_match and not current_item['traduccion']:
                current_item['traduccion'] = traduccion_generic_match.group(1).strip()
                continue

            desc_match = re.match(r'^\s*[-*]\s*(?:\*\*|\*|_|__)Descripción:(?:\*\*|\*|_|__)\s*(.+)', line)
            if desc_match:
                current_item['desc'] = desc_match.group(1).strip()
                continue
                
            prompt_match = re.match(r'^\s*[-*]\s*(?:\*\*|\*|_|__)Prompt:(?:\*\*|\*|_|__)\s*(.+)', line)
            if prompt_match:
                current_item['prompt'] = prompt_match.group(1).strip()
                continue

    if current_item:
        items.append(current_item)
        
    return items

def generate_missing_fields(word, translation, frase, frase_translation):
    needed_fields = []
    if not translation:
        needed_fields.append("translation (translate the Chinese word to Spanish and English, format as 'Spanish / English')")
    needed_fields.append("visual_description (a simple, visual scene in English representing the sentence, suitable for a Peanuts/Charlie Brown cartoon style illustration, focusing on a single character/action, no abstract concepts)")

    prompt = f"""
Analyze this Chinese vocabulary word and sentence:
Word: {word}
Current Translation: {translation if translation else "Unknown"}
Sentence: {frase}
Sentence Translation: {frase_translation}

We need to generate the following missing fields:
{chr(10).join(f"- {f}" for f in needed_fields)}

Format your response as a JSON object with these keys (if needed):
- "translation": (string, only if missing)
- "visual_description": (string, single visual sentence describing the scene in English, e.g., "A child looking under a couch with a magnifying glass.")

Return ONLY the raw JSON block, no markdown formatting.
"""
    try:
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
        print(f"Error generating fields for {word}: {e}")
        return {}

def main():
    new_words_path = r"c:\Users\gabri\Documents\antigravity\anki\new_words.md"
    print("Testing parser...")
    items = parse_new_words(new_words_path)
    print(f"Parsed {len(items)} items.")
    if items:
        # Show first 3 items
        for i, item in enumerate(items[:3]):
            print(f"\nItem {i+1}:")
            print(f"  Word: {item['word']}")
            print(f"  Pinyin: {item['pinyin']}")
            print(f"  Translation: {item['translation']}")
            print(f"  Frase: {item['frase']}")
            print(f"  Traducción: {item['traduccion']}")
            
            print("  Calling Gemini to generate missing fields...")
            generated = generate_missing_fields(item['word'], item['translation'], item['frase'], item['traduccion'])
            print(f"  Gemini output: {generated}")
            
            final_translation = item['translation'] or generated.get('translation', '')
            desc = item['desc'] or generated.get('visual_description', '')
            prompt = (
                f"Minimalist Peanuts cartoon style illustration for a language learning flashcard. "
                f"The image must be extremely simple, focusing only on {desc}. "
                f"Strict requirements: "
                f"- Absolutely no text, no letters, no words, no speech bubbles, and no characters from any alphabet (Latin, Chinese, etc.). "
                f"- Plain, solid, completely white background. "
                f"- Clean line art with minimal, flat colors. "
                f"- Plenty of empty white space around the centered characters."
            )
            print(f"  Final Translation: {final_translation}")
            print(f"  Final Prompt: {prompt}")

if __name__ == "__main__":
    main()
