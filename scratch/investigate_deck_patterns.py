import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('data/anki_extract.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

chars = data.get('characters', [])

print(f"Total characters: {len(chars)}")

no_parens = [c for c in chars if '(' not in c.get('english', '') and '（' not in c.get('english', '')]
print(f"Sample of characters WITHOUT parens in english ({len(no_parens)} total):")
for c in no_parens[:30]:
    print(f"  {c.get('hanzi')} [{c.get('pinyin')}]: '{c.get('english')}'")

# Look at measure words conventions
mws = [c for c in chars if 'm.w.' in c.get('english', '').lower() or 'measure word' in c.get('english', '').lower() or 'classifier' in c.get('english', '').lower()]
print(f"\nMeasure words ({len(mws)} total):")
for c in mws[:20]:
    print(f"  {c.get('hanzi')} [{c.get('pinyin')}]: '{c.get('english')}'")

# Look at surnames conventions
surnames = [c for c in chars if 'surname' in c.get('english', '').lower()]
print(f"\nSurnames ({len(surnames)} total):")
for c in surnames[:20]:
    print(f"  {c.get('hanzi')} [{c.get('pinyin')}]: '{c.get('english')}'")

# Look at particles conventions
particles = [c for c in chars if 'particle' in c.get('english', '').lower()]
print(f"\nParticles ({len(particles)} total):")
for c in particles[:20]:
    print(f"  {c.get('hanzi')} [{c.get('pinyin')}]: '{c.get('english')}'")
