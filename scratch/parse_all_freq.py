import csv, json, urllib.request, sys, os, re
from collections import Counter
sys.stdout.reconfigure(encoding='utf-8')

# Load Jun Da map: character -> rank
junda_map = {}
junda_csv = 'data/junda_freq.csv'
if os.path.exists(junda_csv):
    with open(junda_csv, 'r', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            char = row.get('character', '').strip()
            rank_str = row.get('frequency_rank', '').strip()
            if char and rank_str and rank_str.isdigit():
                junda_map[char] = int(rank_str)

print(f"Loaded Jun Da frequency dataset ({len(junda_map):,} characters).")

def req(action, **params):
    payload = {'action': action, 'version': 6}
    if params: payload['params'] = params
    r = urllib.request.Request('http://127.0.0.1:8765', data=json.dumps(payload).encode('utf-8'), headers={'Content-Type':'application/json'})
    return json.loads(urllib.request.urlopen(r).read().decode('utf-8')).get('result')

nids = req('findNotes', query='deck:Chinese::Char')
notes = []
for i in range(0, len(nids), 500):
    notes.extend(req('notesInfo', notes=nids[i:i+500]))

print(f"Retrieved {len(notes)} notes from Chinese::Char.")

parsed_records = []
unparsed_count = 0

for note in notes:
    nid = note['noteId']
    fields = note['fields']
    hanzi = fields.get('Hanzi', {}).get('value', '').strip()
    simplified = fields.get('Simplified', {}).get('value', '').strip()
    char = hanzi or simplified

    ft_raw = fields.get('FrequencyTier', {}).get('value', '').strip()
    fr_raw = fields.get('FrequencyRank', {}).get('value', '').strip()

    # Determine rank
    rank = None

    # 1. Check Jun Da map first
    if char in junda_map:
        rank = junda_map[char]

    # 2. Extract from ft_raw (e.g. "Tier 1 (#2)", "Tier (Rank #4547)", "Tier 2 (#1004)", etc.)
    if rank is None and ft_raw:
        m = re.search(r'#(\d+)', ft_raw) or re.search(r'Rank (\d+)', ft_raw) or re.search(r'(\d+)', ft_raw)
        if m:
            rank = int(m.group(1))

    # Determine tier
    if rank is not None:
        if rank <= 1000:
            tier = "Tier 1"
        elif rank <= 2500:
            tier = "Tier 2"
        elif rank <= 3500:
            tier = "Tier 3"
        else:
            tier = "Tier 4"
        rank_str = str(rank)
    else:
        tier = "Tier 4"
        rank_str = "Unranked"

    parsed_records.append({
        'note_id': nid,
        'hanzi': char,
        'old_ft': ft_raw,
        'new_tier': tier,
        'new_rank': rank_str
    })

print("\n--- Sample 20 parsed records ---")
for r in parsed_records[:20]:
    print(f"Hanzi: {r['hanzi']:3s} | Old FT: {r['old_ft']:25s} -> Tier: {r['new_tier']:7s} | Rank: {r['new_rank']}")

# Check tier distribution
tier_counts = Counter(r['new_tier'] for r in parsed_records)
print("\nTier Distribution:")
for t, cnt in sorted(tier_counts.items()):
    print(f"  {t}: {cnt} notes")
