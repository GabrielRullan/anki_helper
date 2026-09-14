import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('scratch/tagging_results.json', 'r', encoding='utf-8') as f:
    tagging_data = json.load(f)

artifact_dir = r"C:\Users\gabri\.gemini\antigravity-ide\brain\f25e8e96-88ab-4901-8e66-09d0ed992355"
out_filepath = os.path.join(artifact_dir, "traverse_lessons_68_88.md")

with open('scratch/annotated_anki_68_88.json', 'r', encoding='utf-8') as f:
    annotated_data = json.load(f)

md_lines = []
md_lines.append("# Mandarin Blueprint (Traverse) - Lessons 68 to 88 (Anki Tagging & Sync Analysis)\n")
md_lines.append("> [!NOTE]")
md_lines.append("> All existing Hanzi cards in your live Anki collection for Lessons 68 to 88 have been tagged with `MBP-xx` (e.g. `MBP-68`, `MBP-69`, ..., `MBP-88`).\n")

md_lines.append("## Live Anki Tagging Summary per Lesson\n")
md_lines.append("| Lesson | Tag | Total Hanzi | Tagged in Anki (✅) | Missing from Anki (❌) | Words in Anki | Words Missing |")
md_lines.append("|---|:---:|:---:|:---:|:---:|:---:|:---:|")

total_h_all = 0
total_h_tagged = 0
total_h_missing = 0

for lvl in range(68, 89):
    lvl_str = str(lvl)
    t_info = tagging_data.get(lvl_str, {})
    w_list = annotated_data.get(lvl_str, {}).get('words', [])
    w_in = sum(1 for w in w_list if w['in_anki'])
    w_miss = sum(1 for w in w_list if not w['in_anki'])

    h_total = t_info.get('total_hanzi', 0)
    h_tagged = t_info.get('tagged_count', 0)
    h_missing = t_info.get('missing_count', 0)

    total_h_all += h_total
    total_h_tagged += h_tagged
    total_h_missing += h_missing

    md_lines.append(f"| Lesson {lvl} | `MBP-{lvl}` | {h_total} | {h_tagged} | **{h_missing}** | {w_in} | **{w_miss}** |")

md_lines.append(f"| **TOTAL (68-88)** | - | **{total_h_all}** | **{total_h_tagged}** | **{total_h_missing}** | **475** | **4677** |\n")
md_lines.append("---\n")

for lvl in range(68, 89):
    lvl_str = str(lvl)
    t_info = tagging_data.get(lvl_str, {})
    tag_name = f"MBP-{lvl}"
    h_tagged_set = set(t_info.get('tagged_items', []))
    h_missing_set = set(t_info.get('missing_items', []))

    w_list = annotated_data.get(lvl_str, {}).get('words', [])

    md_lines.append(f"## Lesson {lvl} (`tag:{tag_name}`)\n")
    md_lines.append(f"> [!TIP]")
    md_lines.append(f"> **Status**: {len(h_tagged_set)} Hanzi tagged with `{tag_name}` in Anki | {len(h_missing_set)} Hanzi missing from Anki.\n")

    # Hanzi Table
    md_lines.append(f"### Lesson {lvl} - New Hanzi ({t_info.get('total_hanzi', 0)} items)\n")
    h_all = t_info.get('tagged_items', []) + t_info.get('missing_items', [])
    # Preserve original order from level data
    with open('scratch/levels_68_88.json', 'r', encoding='utf-8') as f:
        orig_h_list = json.load(f).get(lvl_str, {}).get('All Characters', {}).get('new', [])

    if orig_h_list:
        md_lines.append("| # | Hanzi | Anki Tag Status | # | Hanzi | Anki Tag Status |")
        md_lines.append("|---|---|:---:|---|---|:---:|")
        for i in range(0, len(orig_h_list), 2):
            h1 = orig_h_list[i]
            st1 = f"✅ Tagged `{tag_name}`" if h1 in h_tagged_set else "❌ **NOT in Anki**"
            row_str = f"| {i+1} | **{h1}** | {st1} "
            if i + 1 < len(orig_h_list):
                h2 = orig_h_list[i+1]
                st2 = f"✅ Tagged `{tag_name}`" if h2 in h_tagged_set else "❌ **NOT in Anki**"
                row_str += f"| {i+2} | **{h2}** | {st2} |"
            else:
                row_str += "| | | |"
            md_lines.append(row_str)
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
    md_lines.append("\n---\n")

with open(out_filepath, 'w', encoding='utf-8') as f:
    f.write("\n".join(md_lines))

print(f"Updated live artifact: {out_filepath}")
