import re
import csv
import os
import sys

def parse_semana_md(filepath):
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
        
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Split content by markdown headers "### "
    sections = re.split(r'\n### ', content)
    grammar_items = []
    
    for section in sections[1:]:
        lines = section.strip().split('\n')
        if not lines:
            continue
            
        # Parse the header line
        # e.g., "1. 不仅……而且/还/也 (No solo... sino también / Not only... but also)"
        header_line = lines[0].strip()
        header_match = re.match(r'^(\d+)\.\s*(.*)', header_line)
        if header_match:
            gid = header_match.group(1)
            rest = header_match.group(2).strip()
            if rest.endswith(')'):
                last_open = rest.rfind('(')
                if last_open != -1:
                    gtitle = rest[:last_open].strip()
                    gmeaning_raw = rest[last_open+1:-1].strip()
                    if '/' in gmeaning_raw:
                        gmeaning = gmeaning_raw.split('/')[-1].strip()
                    else:
                        gmeaning = gmeaning_raw
                else:
                    gtitle = rest
                    gmeaning = ""
            else:
                gtitle = rest
                gmeaning = ""
        else:
            gid = ""
            gtitle = header_line
            gmeaning = ""
            
        es_list = []
        en_list = []
        zh_list = []
        notes = []
        
        # Regex to match list items
        for line in lines[1:]:
            line = line.strip()
            if not line:
                continue
                
            es_match = re.match(r'^\*\s*\*\*ES(?:\s*\((.*?)\))?:\*\*\s*(.*)', line)
            en_match = re.match(r'^\*\s*\*\*EN(?:\s*\((.*?)\))?:\*\*\s*(.*)', line)
            zh_match = re.match(r'^\*\s*\*\*ZH(?:\s*\((.*?)\))?:\*\*\s*(.*)', line)
            note_match = re.match(r'^\*\s*\*Note:\s*(.*?)\*', line)
            
            if es_match:
                sub_label = es_match.group(1) or ""
                text = es_match.group(2).strip()
                es_list.append((sub_label, text))
            elif en_match:
                sub_label = en_match.group(1) or ""
                text = en_match.group(2).strip()
                en_list.append((sub_label, text))
            elif zh_match:
                sub_label = zh_match.group(1) or ""
                text = zh_match.group(2).strip()
                zh_list.append((sub_label, text))
            elif note_match:
                notes.append(note_match.group(1).strip())
            elif line.startswith('*') and ('Note:' in line or 'note:' in line):
                notes.append(line.replace('*', '').strip())
                
        n_examples = min(len(es_list), len(en_list), len(zh_list))
        
        if len(es_list) != len(en_list) or len(en_list) != len(zh_list):
            print(f"Warning in Lesson {gid}: count mismatch (ES:{len(es_list)}, EN:{len(en_list)}, ZH:{len(zh_list)})")
            
        common_notes = "; ".join(notes)
        
        for i in range(n_examples):
            es_sub, es_text = es_list[i]
            en_sub, en_text = en_list[i]
            zh_sub, zh_text = zh_list[i]
            
            sub_label = en_sub or zh_sub or es_sub
            
            grammar_items.append({
                'id': gid,
                'grammar_pattern': gtitle,
                'grammar_meaning': gmeaning,
                'sub_label': sub_label,
                'spanish': es_text,
                'english': en_text,
                'chinese': zh_text,
                'notes': common_notes
            })
            
    return grammar_items

def generate_csv(items, output_path):
    # CSV headers matching the grammar recall fields, with Word set to empty
    headers = ['Word', 'Grammar Point', 'Sentence', 'Translated Sentence', 'Definitions', 'Notes']
    
    with open(output_path, 'w', encoding='utf-8', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()
        for item in items:
            # Combine only sub-labels and parsed notes into the Notes field (excluding Spanish translation)
            notes_parts = []
            if item['sub_label']:
                notes_parts.append(f"Grammar usage: {item['sub_label']}")
            if item['notes']:
                notes_parts.append(f"Explanation: {item['notes']}")
            combined_notes = "\n\n".join(notes_parts)

            writer.writerow({
                'Word': '',
                'Grammar Point': item['grammar_pattern'],
                'Sentence': item['chinese'],
                'Translated Sentence': item['english'],
                'Definitions': item['grammar_meaning'],
                'Notes': combined_notes
            })
    print(f"Successfully generated {output_path} with {len(items)} grammar rows matching Migaku fields.")

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(base_dir, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lessons", "semana.md"))
    output_path = os.path.join(base_dir, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "grammar_import.csv"))
    
    try:
        items = parse_semana_md(input_path)
        generate_csv(items, output_path)
    except Exception as e:
        print(f"Error parsing grammar: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
