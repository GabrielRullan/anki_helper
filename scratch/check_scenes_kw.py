import json
import re

with open('data/anki_extract.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

chars = data.get('characters', [])
with_paren = [c for c in chars if '(' in c.get('english', '') or '（' in c.get('english', '')]

print(f"Total matching: {len(with_paren)}")

scenes_check = []
for c in with_paren:
    hanzi = c.get('hanzi')
    pinyin = c.get('pinyin')
    eng = c.get('english')
    scene = c.get('scene', '')
    
    # check if english or parts of it appear in scene
    # clean scene of html
    clean_s = re.sub(r'<[^>]+>', '', scene)
    
    scenes_check.append({
        'hanzi': hanzi,
        'pinyin': pinyin,
        'english': eng,
        'scene_snippet': clean_s[:150]
    })

with open('scratch/scenes_check.json', 'w', encoding='utf-8') as f:
    json.dump(scenes_check, f, ensure_ascii=False, indent=2)

print("Saved scenes check")
