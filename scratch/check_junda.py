import csv
import sys

sys.stdout.reconfigure(encoding='utf-8')

missing_63_list = ['漾', '抠', '竣', '夌', '舛', '飙', '飓', '缤', '雚', '孛', '捎', '溉', '秤', '蔗', '巅', '臊', '拌', '涝', '秧', '惋', '窿', '椰', '攒', '汛', '涮', '沏', '潦', '鳄', '刁', '叼', '蘸', '惦', '绯', '撬', '拄', '抡', '媲', '炖', '灸', '煲', '诽', '讹', '酣', '酥', '酗', '酵', '孪', '弈', '盹', '赡', '刨', '馁', '馋', '冗', '粽', '掰', '屹', '卤', '阂', '踊', '跤', '囱', '殃']

junda_map = {}
with open('data/junda_freq.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        c = row['character']
        if c:
            junda_map[c] = row

found = 0
for h in missing_63_list:
    if h in junda_map:
        found += 1
        info = junda_map[h]
        print(f"Match '{h}': Pinyin={info['pinyin']}, Def={info['definition']}, HSK={info['hsk_level']}, Rank={info['frequency_rank']}")
    else:
        print(f"Not in Junda: '{h}'")

print(f"\nFound {found} / {len(missing_63_list)} in Junda database!")
