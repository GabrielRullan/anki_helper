import csv, json, urllib.request, sys, os
sys.stdout.reconfigure(encoding='utf-8')

print("--- Checking data/junda_freq.csv ---")
junda_csv = 'data/junda_freq.csv'
with open(junda_csv, 'r', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        c = row.get('character', '')
        if '黄' in c or '黃' in c:
            print(f"Char: {c} ({hex(ord(c))}) | Rank: {row.get('frequency_rank')} | Pinyin: {row.get('pinyin')} | Def: {row.get('definition')}")

print("\n--- Checking data/character_frequency_audit.csv ---")
audit_csv = 'data/character_frequency_audit.csv'
if os.path.exists(audit_csv):
    with open(audit_csv, 'r', encoding='utf-8') as f:
        for line in f:
            if '黄' in line or '黃' in line:
                print(line.strip())

print("\n--- Checking Anki Notes in Chinese::Char ---")
def req(action, **params):
    payload = {'action': action, 'version': 6}
    if params: payload['params'] = params
    r = urllib.request.Request('http://127.0.0.1:8765', data=json.dumps(payload).encode('utf-8'), headers={'Content-Type':'application/json'})
    return json.loads(urllib.request.urlopen(r).read().decode('utf-8')).get('result')

nids = req('findNotes', query='deck:Chinese::Char 黄')
if nids:
    notes_info = req('notesInfo', notes=nids)
    for n in notes_info:
        hz = n['fields'].get('Hanzi', {}).get('value', '')
        fr = n['fields'].get('Frequency', {}).get('value', '')
        dnr = n['fields'].get('Do_Not_Recall', {}).get('value', '')
        eng = n['fields'].get('English', {}).get('value', '')
        tags = n.get('tags', [])
        print(f"Note ID: {n['noteId']} | Hanzi: {hz} ({hex(ord(hz[0])) if hz else ''}) | Freq: {fr} | DNR: {dnr} | English: {eng} | Tags: {tags}")
