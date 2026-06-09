import os
import re
import sys
import io

# Fix for terminal encoding issues
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

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
            
        # Match root entries starting with - or * at start of line
        # e.g., - **瓢虫** (_piáochóng_) - Mariquita / Ladybug
        # or - 蚜虫 (_piáochóng_)
        # Group 1: word, Group 2: pinyin, Group 3: optional translation
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
            # Match Frase field
            frase_match = re.match(r'^\s*[-*]\s*(?:\*\*|\*|_|__)Frase:(?:\*\*|\*|_|__)\s*(.+)', line)
            if frase_match:
                current_item['frase'] = frase_match.group(1).strip()
                continue
                
            # Match Traducción Español or Traducción
            traduccion_es_match = re.match(r'^\s*[-*]\s*(?:\*\*|\*|_|__)Traducción Español:(?:\*\*|\*|_|__)\s*(.+)', line)
            if traduccion_es_match:
                current_item['traduccion'] = traduccion_es_match.group(1).strip()
                continue
                
            traduccion_generic_match = re.match(r'^\s*[-*]\s*(?:\*\*|\*|_|__)Traducción:(?:\*\*|\*|_|__)\s*(.+)', line)
            if traduccion_generic_match and not current_item['traduccion']:
                current_item['traduccion'] = traduccion_generic_match.group(1).strip()
                continue

            # Match Description
            desc_match = re.match(r'^\s*[-*]\s*(?:\*\*|\*|_|__)Descripción:(?:\*\*|\*|_|__)\s*(.+)', line)
            if desc_match:
                current_item['desc'] = desc_match.group(1).strip()
                continue
                
            # Match Prompt
            prompt_match = re.match(r'^\s*[-*]\s*(?:\*\*|\*|_|__)Prompt:(?:\*\*|\*|_|__)\s*(.+)', line)
            if prompt_match:
                current_item['prompt'] = prompt_match.group(1).strip()
                continue

    if current_item:
        items.append(current_item)
        
    return items

new_words_path = r"c:\Users\gabri\Documents\antigravity\anki\new_words.md"
items = parse_new_words(new_words_path)
print(f"Total parsed: {len(items)}")
if items:
    for i in range(min(5, len(items))):
        print(f"\nItem {i+1}:")
        print(f"  Word: {items[i]['word']}")
        print(f"  Pinyin: {items[i]['pinyin']}")
        print(f"  Translation: {items[i]['translation']}")
        print(f"  Frase: {items[i]['frase']}")
        print(f"  Traducción: {items[i]['traduccion']}")
        print(f"  Desc: {items[i]['desc']}")
        print(f"  Prompt: {items[i]['prompt']}")
