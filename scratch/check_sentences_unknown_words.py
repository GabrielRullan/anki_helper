import json
import csv
import jieba
import re
import urllib.request

# 1. Fetch user known words from Chinese::Words via AnkiConnect
req_data_words = json.dumps({'action': 'findNotes', 'version': 6, 'params': {'query': 'deck:"Chinese::Words"'}}).encode('utf-8')
req = urllib.request.Request('http://localhost:8765', req_data_words)
with urllib.request.urlopen(req) as resp:
    word_ids = json.loads(resp.read().decode('utf-8'))['result']

req_data_info = json.dumps({'action': 'notesInfo', 'version': 6, 'params': {'notes': word_ids}}).encode('utf-8')
req = urllib.request.Request('http://localhost:8765', req_data_info)
with urllib.request.urlopen(req) as resp:
    word_notes = json.loads(resp.read().decode('utf-8'))['result']

user_words_strict = set()
for n in word_notes:
    if 'Word' in n['fields']:
        w = re.sub(r'<[^>]+>', '', n['fields']['Word']['value']).strip()
        if w:
            user_words_strict.add(w)

print(f"Loaded {len(user_words_strict)} words from Chinese::Words")

# Base foundational HSK 1-2 words/particles
basic_foundational = {
    '我', '你', '他', '她', '它', '我们', '你们', '他们', '她们', '的', '了', '在', '是', '有', '不', '没',
    '吗', '呢', '吧', '这', '那', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十', '个', '去', '来',
    '好', '说', '想', '要', '做', '看', '听', '写', '读', '很', '太', '多', '少', '大', '小', '上', '下', '中',
    '里', '和', '跟', '把', '被', '给', '就', '也', '都', '还', '又', '只', '能', '会', '可以', '什么', '怎么',
    '谁', '哪', '哪里', '怎么了', '为什么', '多少', '几', '这个', '那个', '因为', '所以', '但是', '如果'
}

user_words_with_base = user_words_strict.union(basic_foundational)

# 2. Read Spoonfed dataset
csv_in_path = r"c:\Users\gabri\Documents\anki_helper\data\spoonfed_phrases_extracted.csv"
rows = []
with open(csv_in_path, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for r in reader:
        rows.append(r)

total_sentences = len(rows)

# Strict check (only Chinese::Words deck)
strict_0_unk = 0
strict_has_unk = 0

# Practical check (Chinese::Words deck + basic foundational pronouns/particles)
base_0_unk = 0
base_1_unk = 0
base_2_unk = 0
base_3plus_unk = 0

for r in rows:
    hanzi = r['Hanzi']
    words = [w for w in jieba.cut(hanzi) if any('\u4e00' <= ch <= '\u9fff' for ch in w)]
    
    # Strict
    strict_unk_words = [w for w in words if w not in user_words_strict]
    if len(strict_unk_words) == 0:
        strict_0_unk += 1
    else:
        strict_has_unk += 1
        
    # With base
    base_unk_words = [w for w in words if w not in user_words_with_base]
    if len(base_unk_words) == 0:
        base_0_unk += 1
    elif len(base_unk_words) == 1:
        base_1_unk += 1
    elif len(base_unk_words) == 2:
        base_2_unk += 1
    else:
        base_3plus_unk += 1

print("\n=== SENTENCE OVERLAP ANALYSIS ===")
print(f"Total Sentences in Spoonfed Chinese: {total_sentences}")

print("\n--- PERSPECTIVE A: Strict Comparison against `Chinese::Words` Deck Only ---")
print(f"- Sentences with 100% words in Chinese::Words: {strict_0_unk} ({strict_0_unk/total_sentences*100:.2f}%)")
print(f"- Sentences containing AT LEAST 1 word NOT in Chinese::Words: {strict_has_unk} ({strict_has_unk/total_sentences*100:.2f}%)")

print("\n--- PERSPECTIVE B: Practical Comparison (`Chinese::Words` + Basic HSK1 Pronouns/Particles) ---")
print(f"- Sentences with 0 unknown words (100% Known): {base_0_unk} ({base_0_unk/total_sentences*100:.2f}%)")
print(f"- Sentences containing AT LEAST 1 unknown word: {total_sentences - base_0_unk} ({(total_sentences - base_0_unk)/total_sentences*100:.2f}%)")
print(f"  ├─ Exactly 1 new word (i+1 optimal target): {base_1_unk} ({base_1_unk/total_sentences*100:.2f}%)")
print(f"  ├─ Exactly 2 new words (i+2 secondary queue): {base_2_unk} ({base_2_unk/total_sentences*100:.2f}%)")
print(f"  └─ 3 or more new words (i+3+ advanced queue): {base_3plus_unk} ({base_3plus_unk/total_sentences*100:.2f}%)")
