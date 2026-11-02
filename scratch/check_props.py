import json

with open('data/anki_extract.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

props = data.get('props', [])
print(f"Props in anki_extract.json: {len(props)}")
if props:
    print("Sample prop:", props[0])
