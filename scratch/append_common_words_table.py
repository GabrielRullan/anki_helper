import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('scratch/extracted_common_words.json', 'r', encoding='utf-8') as f:
    char_notes = json.load(f)

# Group by lesson
notes_by_lesson = {}
for item in char_notes:
    lvl = item['lesson']
    if lvl not in notes_by_lesson:
        notes_by_lesson[lvl] = []
    notes_by_lesson[lvl].append(item)

artifact_dir = r"C:\Users\gabri\.gemini\antigravity-ide\brain\f25e8e96-88ab-4901-8e66-09d0ed992355"
out_filepath = os.path.join(artifact_dir, "traverse_lessons_68_88.md")

# Read current content of artifact
with open(out_filepath, 'r', encoding='utf-8') as f:
    existing_content = f.read()

# Generate new sections for Common Words in Character Cards
new_md_lines = []
new_md_lines.append("\n\n---\n")
new_md_lines.append("# Common Words Embedded in Character Cards (Lessons 68–88)\n")
new_md_lines.append("> [!NOTE]")
new_md_lines.append("> Below is the complete table of **Common Words** and **Word Translations** associated with each Chinese Character in your Anki deck (`Chinese::Char`) for Lessons 68 through 88.\n")

for lvl in range(68, 89):
    items = notes_by_lesson.get(lvl, [])
    new_md_lines.append(f"## Lesson {lvl} - Character Common Words ({len(items)} characters)\n")
    if items:
        new_md_lines.append("| # | Hanzi | Pinyin | Character Meaning | Common Words in Card | Word Translations |")
        new_md_lines.append("|---|:---:|:---:|---|---|---|")
        for idx, it in enumerate(items, 1):
            h = it['hanzi']
            p = it['pinyin']
            e = it['english'].replace('\n', ' ')
            cw = it['common_words'].replace('\n', ' ') or '-'
            tw = it['translation_words'].replace('\n', ' ') or '-'
            new_md_lines.append(f"| {idx} | **{h}** | `{p}` | {e} | **{cw}** | {tw} |")
    else:
        new_md_lines.append("*No character cards found for this lesson.*")
    new_md_lines.append("\n")

updated_full_content = existing_content + "\n".join(new_md_lines)

with open(out_filepath, 'w', encoding='utf-8') as f:
    f.write(updated_full_content)

print(f"Appended Common Words tables to {out_filepath}")
