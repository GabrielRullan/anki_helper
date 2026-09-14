import csv
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

missing_63_list = ['漾', '抠', '竣', '夌', '舛', '飙', '飓', '缤', '雚', '孛', '捎', '溉', '秤', '蔗', '巅', '臊', '拌', '涝', '秧', '惋', '窿', '椰', '攒', '汛', '涮', '沏', '潦', '鳄', '刁', '叼', '蘸', '惦', '绯', '撬', '拄', '抡', '媲', '炖', '灸', '煲', '诽', '讹', '酣', '酥', '酗', '酵', '孪', '弈', '盹', '赡', '刨', '馁', '馋', '冗', '粽', '掰', '屹', '卤', '阂', '踊', '跤', '囱', '殃']

print(f"Searching for {len(missing_63_list)} missing Hanzi across workspace data files...")

# Search new_characters.csv
nc_found = {}
with open('data/new_characters.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        h = row.get('Hanzi') or row.get('Simplified')
        if h in missing_63_list:
            nc_found[h] = row

print(f"Found in data/new_characters.csv: {len(nc_found)} / {len(missing_63_list)}")

# Search junda_freq.csv
junda_found = {}
if os.path.exists('data/junda_freq.csv'):
    with open('data/junda_freq.csv', 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            h = row.get('Character') or row.get('Hanzi') or row.get('Simplified') or row.get('char')
            if h in missing_63_list:
                junda_found[h] = row

print(f"Found in data/junda_freq.csv: {len(junda_found)} / {len(missing_63_list)}")

for h in missing_63_list[:10]:
    if h in junda_found:
        print(f"  Junda '{h}': {junda_found[h]}")
