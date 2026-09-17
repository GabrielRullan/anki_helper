import csv
import json
import re
from collections import Counter

csv_in_path = r"c:\Users\gabri\Documents\anki_helper\data\spoonfed_phrases_extracted.csv"

rows = []
with open(csv_in_path, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append(row)

print(f"Loaded {len(rows)} rows from extracted CSV.")

# Sample beginning, middle, end
print("\n--- SAMPLE BEGINNING (Rows 1-5) ---")
for r in rows[:5]:
    print(f"[{r['ID']}] {r['Hanzi']} | {r['Pinyin']} | {r['English']}")

print("\n--- SAMPLE MIDDLE (Rows 4000-4005) ---")
for r in rows[4000:4005]:
    print(f"[{r['ID']}] {r['Hanzi']} | {r['Pinyin']} | {r['English']}")

print("\n--- SAMPLE END (Rows 8000-8005) ---")
for r in rows[8000:8005]:
    print(f"[{r['ID']}] {r['Hanzi']} | {r['Pinyin']} | {r['English']}")

# Length statistics
char_lengths = [int(r['Char Count']) for r in rows]
avg_len = sum(char_lengths) / len(char_lengths)
min_len = min(char_lengths)
max_len = max(char_lengths)

print(f"\n--- SENTENCE LENGTH STATS ---")
print(f"Min: {min_len} chars, Max: {max_len} chars, Avg: {avg_len:.2f} chars")

# Top unknown words in Spoonfed
unknown_words_counter = Counter()
for r in rows:
    unk_str = r['Unknown Words List']
    if unk_str:
        words = [w.strip() for w in unk_str.split(',') if w.strip()]
        for w in words:
            unknown_words_counter[w] += 1

print("\n--- TOP 20 UNKNOWN WORDS IN SPOONFED CHINESE ---")
for w, count in unknown_words_counter.most_common(20):
    print(f"Word: {w} (Appears in {count} sentences)")

# HTML tag analysis
html_tags_found = []
for r in rows:
    if '<' in r['Hanzi'] or '<' in r['Pinyin'] or '<' in r['English']:
        html_tags_found.append(r)

print(f"\nTotal rows with HTML tags: {len(html_tags_found)}")
if html_tags_found:
    print("Sample HTML tag row:", html_tags_found[0])
