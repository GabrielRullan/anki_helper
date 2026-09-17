import json

with open(r"c:\Users\gabri\Documents\anki_helper\scratch\full_restoration_plan.json", 'r', encoding='utf-8') as f:
    items = json.load(f)

ye_items = [it for it in items if '耶' in it['target']]
print("Items for 耶 in full_restoration_plan.json:", ye_items)
