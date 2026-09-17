import json
import csv
import jieba
import re
from collections import Counter

# Load HSK 1-6 vocabulary if available or standard basic words
basic_hsk1_2 = {
    '我', '你', '他', '她', '它', '我们', '你们', '他们', '她们', '的', '了', '在', '是', '有', '不', '没',
    '吗', '呢', '吧', '这', '那', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十', '个', '去', '来',
    '好', '说', '想', '要', '做', '看', '听', '写', '读', '很', '太', '多', '少', '大', '小', '上', '下', '中',
    '里', '和', '跟', '把', '被', '给', '就', '也', '都', '还', '又', '只', '能', '会', '可以', '什么', '怎么',
    '谁', '哪', '哪里', '怎么了', '为什么', '多少', '几', '这个', '那个', '因为', '所以', '但是', '如果'
}

csv_in_path = r"c:\Users\gabri\Documents\anki_helper\data\spoonfed_phrases_extracted.csv"
rows = []
with open(csv_in_path, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for r in reader:
        rows.append(r)

# Load user words from JSON/Anki
with open(r"c:\Users\gabri\Documents\anki_helper\scratch\spoonfed_analysis_result.json", 'r', encoding='utf-8') as f:
    stats = json.load(f)

# Re-evaluating with basic_hsk1_2 + user_words
import urllib.request
req_data_words = json.dumps({'action': 'findNotes', 'version': 6, 'params': {'query': 'deck:"Chinese::Words"'}}).encode('utf-8')
req = urllib.request.Request('http://localhost:8765', req_data_words)
with urllib.request.urlopen(req) as resp:
    word_ids = json.loads(resp.read().decode('utf-8'))['result']

req_data_info = json.dumps({'action': 'notesInfo', 'version': 6, 'params': {'notes': word_ids}}).encode('utf-8')
req = urllib.request.Request('http://localhost:8765', req_data_info)
with urllib.request.urlopen(req) as resp:
    word_notes = json.loads(resp.read().decode('utf-8'))['result']

user_words = set(re.sub(r'<[^>]+>', '', n['fields']['Word']['value']).strip() for n in word_notes if 'Word' in n['fields'])
user_words.discard('')

combined_known_words = user_words.union(basic_hsk1_2)

# Also check character coverage
req_data_chars = json.dumps({'action': 'findNotes', 'version': 6, 'params': {'query': 'deck:"Chinese::Char"'}}).encode('utf-8')
req = urllib.request.Request('http://localhost:8765', req_data_chars)
with urllib.request.urlopen(req) as resp:
    char_ids = json.loads(resp.read().decode('utf-8'))['result']

req_data_cinfo = json.dumps({'action': 'notesInfo', 'version': 6, 'params': {'notes': char_ids}}).encode('utf-8')
req = urllib.request.Request('http://localhost:8765', req_data_cinfo)
with urllib.request.urlopen(req) as resp:
    char_notes = json.loads(resp.read().decode('utf-8'))['result']

known_chars = set()
for n in char_notes:
    c = n['fields']['Hanzi']['value'].strip() if 'Hanzi' in n['fields'] else ""
    if not c and 'Word' in n['fields']:
        c = n['fields']['Word']['value'].strip()
    c_clean = re.sub(r'<[^>]+>', '', c)
    if c_clean:
        known_chars.add(c_clean)

# Evaluate sentence levels with combined words
i0 = 0
i1 = 0
i2 = 0
i3plus = 0

sample_i0 = []
sample_i1 = []

for r in rows:
    hanzi = r['Hanzi']
    words = [w for w in jieba.cut(hanzi) if any('\u4e00' <= ch <= '\u9fff' for ch in w)]
    unknowns = [w for w in words if w not in combined_known_words]
    num_unk = len(unknowns)
    if num_unk == 0:
        i0 += 1
        if len(sample_i0) < 10:
            sample_i0.append(r)
    elif num_unk == 1:
        i1 += 1
        if len(sample_i1) < 10:
            sample_i1.append((r, unknowns[0]))
    elif num_unk == 2:
        i2 += 1
    else:
        i3plus += 1

print("--- OVERLAP RE-ANALYSIS WITH BASIC GRAMMAR/PRONOUNS + IMMERSION WORDS ---")
print(f"User Immersion Words: {len(user_words)}")
print(f"User Characters: {len(known_chars)}")
print(f"Total Sentences in Spoonfed: {len(rows)}")
print(f"i+0 (100% words known): {i0} ({i0/len(rows)*100:.2f}%)")
print(f"i+1 (Exactly 1 new word): {i1} ({i1/len(rows)*100:.2f}%)")
print(f"i+2 (2 new words): {i2} ({i2/len(rows)*100:.2f}%)")
print(f"i+3+ (3+ new words): {i3plus} ({i3plus/len(rows)*100:.2f}%)")

print("\n--- SAMPLE i+0 SENTENCES (Fully Known Words) ---")
for s in sample_i0:
    print(f"- {s['Hanzi']} ({s['Pinyin']}) : {s['English']}")

print("\n--- SAMPLE i+1 SENTENCES (Ideal Target Sentences - 1 New Word) ---")
for s, target_w in sample_i1:
    print(f"- {s['Hanzi']} (Target Word: '{target_w}') | {s['Pinyin']} | {s['English']}")
