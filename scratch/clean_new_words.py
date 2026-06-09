import os
import re
import sys
import io

# Fix for terminal encoding issues
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

new_words_path = r"c:\Users\gabri\Documents\antigravity\anki\new_words.md"
with open(new_words_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Locate the 🟡 Pendiente de incluir section
try:
    header = content.split('## 🟢 Incluido en Anki')[0].rstrip()
    incluido_part = content.split('## 🟢 Incluido en Anki')[1].split('## 🟡 Pendiente de incluir')[0].strip()
    pendiente_part = content.split('## 🟡 Pendiente de incluir')[1].split('## 🔴 Suelto')[0].strip()
    suelto_part = content.split('## 🔴 Suelto')[1].strip()
except IndexError:
    print("Error splitting sections!")
    exit(1)

# Let's parse the entries in the pending section
# It currently contains:
# - **潮湿** (cháoshī) — Húmedo / Humid, damp
#     - **Frase:** ...
# We want to parse these items and move them to the incluido section
lines = pendiente_part.splitlines()
items_to_move = []
current_item = None

for line in lines:
    line_stripped = line.strip()
    if not line_stripped or line_stripped.startswith("*Aquí van las"):
        continue
    
    root_match = re.match(r'^[-*]\s+(?:\*\*)?([^*()]+?)(?:\*\*)?\s*\(([^)]+)\)(?:\s*(?:—|-)\s*(.+))?', line)
    if root_match:
        if current_item:
            items_to_move.append(current_item)
        word = root_match.group(1).strip()
        pinyin = root_match.group(2).strip().replace('_', '').replace('*', '').strip()
        translation = root_match.group(3).strip() if root_match.group(3) else ""
        current_item = {
            'word': word,
            'pinyin': pinyin,
            'translation': translation,
            'orig_line': line.strip()
        }
        continue

if current_item:
    items_to_move.append(current_item)

print(f"Moving {len(items_to_move)} items to Included:")
for item in items_to_move:
    print(f" - {item['word']}")

# 2. Append them to incluido_part
new_incluido_part = incluido_part
if new_incluido_part:
    new_incluido_part += "\n"

for item in items_to_move:
    # Format identically to other included lines
    new_incluido_part += f"- **{item['word']}** ({item['pinyin']}) — {item['translation']}\n"

# 3. Reconstruct the file with an empty pending section
empty_pendiente_section = (
    "\n\n## 🟡 Pendiente de incluir\n"
    "*Aquí van las palabras en transición antes de añadirlas a Anki. Cada una debe incluir traducción y una frase memorable:*\n"
)

final_content = (
    header +
    "\n\n## 🟢 Incluido en Anki\n" + new_incluido_part.strip() + "\n" +
    empty_pendiente_section +
    "\n## 🔴 Suelto\n*Palabras en caracteres chinos listas para estudio, con su pronunciación, significado y etiquetas de Obsidian:\n" +
    suelto_part
)

with open(new_words_path, 'w', encoding='utf-8') as f:
    f.write(final_content)

print("new_words.md cleaned successfully!")
