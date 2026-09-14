import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('scratch/levels_68_88.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

artifact_dir = r"C:\Users\gabri\.gemini\antigravity-ide\brain\f25e8e96-88ab-4901-8e66-09d0ed992355"
out_filepath = os.path.join(artifact_dir, "traverse_lessons_68_88.md")

md_lines = []
md_lines.append("# Mandarin Blueprint (Traverse) - New Hanzi and Words for Lessons 68 to 88\n")
md_lines.append("> [!NOTE]")
md_lines.append("> Data extracted directly from `https://traverse.link/Mandarin_Blueprint/word-progress/?level=<lesson>`.")
md_lines.append("> For each lesson, items shown in **red** on Traverse correspond to the new characters and new words introduced in that specific lesson.\n")

md_lines.append("## Summary Overview\n")
md_lines.append("| Lesson | New Hanzi (Characters) Count | New Words Count |")
md_lines.append("|---|---|---|")

total_hanzi = 0
total_words = 0

for lvl in range(68, 89):
    lvl_str = str(lvl)
    lvl_data = data.get(lvl_str, {})
    new_words = lvl_data.get('All Words', {}).get('new', [])
    new_hanzi = lvl_data.get('All Characters', {}).get('new', [])
    md_lines.append(f"| Lesson {lvl} | {len(new_hanzi)} | {len(new_words)} |")
    total_hanzi += len(new_hanzi)
    total_words += len(new_words)

md_lines.append(f"| **Total (68-88)** | **{total_hanzi}** | **{total_words}** |\n")
md_lines.append("---\n")

def chunk_list(lst, n=10):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

for lvl in range(68, 89):
    lvl_str = str(lvl)
    lvl_data = data.get(lvl_str, {})
    new_words = lvl_data.get('All Words', {}).get('new', [])
    new_hanzi = lvl_data.get('All Characters', {}).get('new', [])

    md_lines.append(f"## Lesson {lvl}\n")

    # Hanzi Table
    md_lines.append(f"### Lesson {lvl} - New Hanzi ({len(new_hanzi)} items)\n")
    if new_hanzi:
        md_lines.append("| # | Hanzi | # | Hanzi | # | Hanzi | # | Hanzi | # | Hanzi |")
        md_lines.append("|---|---|---|---|---|---|---|---|---|---|")
        for i in range(0, len(new_hanzi), 5):
            row_items = new_hanzi[i:i+5]
            row_str = ""
            for idx, h in enumerate(row_items):
                item_num = i + idx + 1
                row_str += f"| {item_num} | **{h}** "
            # fill missing cells if any
            for idx in range(len(row_items), 5):
                row_str += "| | "
            row_str += "|"
            md_lines.append(row_str)
    else:
        md_lines.append("*No new Hanzi in this lesson.*")
    md_lines.append("\n")

    # Words Table
    md_lines.append(f"### Lesson {lvl} - New Words ({len(new_words)} items)\n")
    if new_words:
        md_lines.append("| # | Word | # | Word | # | Word | # | Word | # | Word |")
        md_lines.append("|---|---|---|---|---|---|---|---|---|---|")
        for i in range(0, len(new_words), 5):
            row_items = new_words[i:i+5]
            row_str = ""
            for idx, w in enumerate(row_items):
                item_num = i + idx + 1
                row_str += f"| {item_num} | **{w}** "
            for idx in range(len(row_items), 5):
                row_str += "| | "
            row_str += "|"
            md_lines.append(row_str)
    else:
        md_lines.append("*No new Words in this lesson.*")
    md_lines.append("\n---\n")

with open(out_filepath, 'w', encoding='utf-8') as f:
    f.write("\n".join(md_lines))

print(f"Generated {out_filepath} with {len(md_lines)} lines.")
