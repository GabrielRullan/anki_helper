import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('scratch/annotated_anki_68_88.json', 'r', encoding='utf-8') as f:
    annotated_data = json.load(f)

artifact_dir = r"C:\Users\gabri\.gemini\antigravity-ide\brain\f25e8e96-88ab-4901-8e66-09d0ed992355"
out_filepath = os.path.join(artifact_dir, "traverse_lessons_68_88.md")

md_lines = []
md_lines.append("# Mandarin Blueprint (Traverse) - Lessons 68 to 88 (Anki Sync Analysis)\n")
md_lines.append("> [!NOTE]")
md_lines.append("> Data extracted from Traverse (`https://traverse.link/Mandarin_Blueprint/word-progress/?level=<lesson>`) and compared against your local Anki database (`Chinese::Words` and `Chinese::Char`).")
md_lines.append("> ")
md_lines.append("> - **✅ In Anki**: The item already exists in your Anki collection.")
md_lines.append("> - **❌ NOT in Anki**: Missing from Anki (needs to be added).\n")

md_lines.append("## Overall Summary per Lesson\n")
md_lines.append("| Lesson | Total Hanzi | Hanzi in Anki | Hanzi Missing | Total Words | Words in Anki | Words Missing |")
md_lines.append("|---|:---:|:---:|:---:|:---:|:---:|:---:|")

total_h_all = 0
total_h_in = 0
total_h_missing = 0
total_w_all = 0
total_w_in = 0
total_w_missing = 0

for lvl in range(68, 89):
    lvl_str = str(lvl)
    lvl_data = annotated_data.get(lvl_str, {})
    h_list = lvl_data.get('hanzi', [])
    w_list = lvl_data.get('words', [])

    h_in = sum(1 for h in h_list if h['in_anki'])
    h_miss = sum(1 for h in h_list if not h['in_anki'])
    w_in = sum(1 for w in w_list if w['in_anki'])
    w_miss = sum(1 for w in w_list if not w['in_anki'])

    total_h_all += len(h_list)
    total_h_in += h_in
    total_h_missing += h_miss
    total_w_all += len(w_list)
    total_w_in += w_in
    total_w_missing += w_miss

    md_lines.append(f"| Lesson {lvl} | {len(h_list)} | {h_in} | **{h_miss}** | {len(w_list)} | {w_in} | **{w_miss}** |")

md_lines.append(f"| **TOTAL (68-88)** | **{total_h_all}** | **{total_h_in}** | **{total_h_missing}** | **{total_w_all}** | **{total_w_in}** | **{total_w_missing}** |\n")
md_lines.append("---\n")

for lvl in range(68, 89):
    lvl_str = str(lvl)
    lvl_data = annotated_data.get(lvl_str, {})
    h_list = lvl_data.get('hanzi', [])
    w_list = lvl_data.get('words', [])

    h_missing_items = [h['hanzi'] for h in h_list if not h['in_anki']]
    w_missing_items = [w['word'] for w in w_list if not w['in_anki']]

    md_lines.append(f"## Lesson {lvl}\n")

    md_lines.append(f"> [!IMPORTANT]")
    md_lines.append(f"> **Missing Summary**: {len(h_missing_items)} / {len(h_list)} Hanzi missing | {len(w_missing_items)} / {len(w_list)} Words missing\n")

    # Hanzi Table
    md_lines.append(f"### Lesson {lvl} - New Hanzi ({len(h_list)} items)\n")
    if h_list:
        md_lines.append("| # | Hanzi | Status | # | Hanzi | Status |")
        md_lines.append("|---|---|:---:|---|---|:---:|")
        for i in range(0, len(h_list), 2):
            item1 = h_list[i]
            st1 = "✅ In Anki" if item1['in_anki'] else "❌ **NOT in Anki**"
            row_str = f"| {i+1} | **{item1['hanzi']}** | {st1} "
            if i + 1 < len(h_list):
                item2 = h_list[i+1]
                st2 = "✅ In Anki" if item2['in_anki'] else "❌ **NOT in Anki**"
                row_str += f"| {i+2} | **{item2['hanzi']}** | {st2} |"
            else:
                row_str += "| | | |"
            md_lines.append(row_str)
    else:
        md_lines.append("*No new Hanzi in this lesson.*")
    md_lines.append("\n")

    # Words Table
    md_lines.append(f"### Lesson {lvl} - New Words ({len(w_list)} items)\n")
    if w_list:
        md_lines.append("| # | Word | Status | # | Word | Status |")
        md_lines.append("|---|---|:---:|---|---|:---:|")
        for i in range(0, len(w_list), 2):
            item1 = w_list[i]
            st1 = "✅ In Anki" if item1['in_anki'] else "❌ **NOT in Anki**"
            row_str = f"| {i+1} | **{item1['word']}** | {st1} "
            if i + 1 < len(w_list):
                item2 = w_list[i+1]
                st2 = "✅ In Anki" if item2['in_anki'] else "❌ **NOT in Anki**"
                row_str += f"| {i+2} | **{item2['word']}** | {st2} |"
            else:
                row_str += "| | | |"
            md_lines.append(row_str)
    else:
        md_lines.append("*No new Words in this lesson.*")
    md_lines.append("\n---\n")

with open(out_filepath, 'w', encoding='utf-8') as f:
    f.write("\n".join(md_lines))

print(f"Successfully updated {out_filepath} with Anki status.")
