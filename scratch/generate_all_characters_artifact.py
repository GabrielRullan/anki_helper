import json
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('scratch/all_anki_characters_raw.json', 'r', encoding='utf-8') as f:
    notes = json.load(f)

artifact_dir = r"C:\Users\gabri\.gemini\antigravity-ide\brain\f25e8e96-88ab-4901-8e66-09d0ed992355"
out_filepath = os.path.join(artifact_dir, "all_anki_character_common_words.md")

# Group by MBP Tag / Level if present, or general category
mbp_lesson_notes = {}
other_notes = []

for n in notes:
    tags = n.get('tags', [])
    mbp_tag = None
    for t in tags:
        if re.match(r'^MBP-\d+$', t):
            mbp_tag = t
            break

    if mbp_tag:
        lvl_num = int(mbp_tag.replace('MBP-', ''))
        if lvl_num not in mbp_lesson_notes:
            mbp_lesson_notes[lvl_num] = []
        mbp_lesson_notes[lvl_num].append(n)
    else:
        other_notes.append(n)

md_lines = []
md_lines.append("# All Chinese Character Common Words in Anki\n")
md_lines.append("> [!NOTE]")
md_lines.append(f"> Complete repository of **{len(notes)} Chinese Character cards** extracted directly from your live Anki collection (`Chinese::Char`).")
md_lines.append("> Includes character pinyin, English meaning, embedded common words, and word translations.\n")

md_lines.append("## Summary Overview\n")
md_lines.append(f"- **Total Character Cards**: **{len(notes)}**")
md_lines.append(f"- **MBP Lesson Tagged Cards (MBP-1 to MBP-88)**: **{sum(len(v) for v in mbp_lesson_notes.values())}**")
md_lines.append(f"- **Other Collection Characters**: **{len(other_notes)}**\n")
md_lines.append("---\n")

# Section 1: MBP Lessons (Sorted 1..88)
md_lines.append("# Part 1: MBP Lessons Characters\n")

for lvl in sorted(mbp_lesson_notes.keys()):
    items = mbp_lesson_notes[lvl]
    md_lines.append(f"## Lesson {lvl} (`MBP-{lvl}`) - {len(items)} Characters\n")
    md_lines.append("| # | Hanzi | Pinyin | Character Meaning | Common Words | Word Translations |")
    md_lines.append("|---|:---:|:---:|---|---|---|")
    for idx, it in enumerate(items, 1):
        h = it['hanzi']
        p = it['pinyin']
        e = it['english'].replace('\n', ' ')
        cw = it['common_words'].replace('\n', ' ') or '-'
        tw = it['translation_words'].replace('\n', ' ') or '-'
        md_lines.append(f"| {idx} | **{h}** | `{p}` | {e} | **{cw}** | {tw} |")
    md_lines.append("\n")

# Section 2: Other Characters in Collection
if other_notes:
    md_lines.append("---\n")
    md_lines.append(f"# Part 2: Additional Characters in Collection ({len(other_notes)} Characters)\n")
    md_lines.append("| # | Hanzi | Pinyin | Character Meaning | Common Words | Word Translations |")
    md_lines.append("|---|:---:|:---:|---|---|---|")
    for idx, it in enumerate(other_notes, 1):
        h = it['hanzi']
        p = it['pinyin']
        e = it['english'].replace('\n', ' ')
        cw = it['common_words'].replace('\n', ' ') or '-'
        tw = it['translation_words'].replace('\n', ' ') or '-'
        md_lines.append(f"| {idx} | **{h}** | `{p}` | {e} | **{cw}** | {tw} |")
    md_lines.append("\n")

with open(out_filepath, 'w', encoding='utf-8') as f:
    f.write("\n".join(md_lines))

print(f"Generated complete artifact: {out_filepath} with {len(md_lines)} lines.")
