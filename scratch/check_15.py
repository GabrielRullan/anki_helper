import sys, json, urllib.request
sys.stdout.reconfigure(encoding='utf-8')

targets = ['安排', '导游', '对于', '开玩笑', '民族', '难道', '难受', '千万', '填空', '同情', '压力', '真正', '正常', '正好', '正式']

for t in targets:
    p = {'action': 'findNotes', 'version': 6, 'params': {'query': f'Word:"{t}"'}}
    r = json.loads(urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8765', json.dumps(p).encode('utf-8'))).read().decode('utf-8'))['result']
    if not r:
        p = {'action': 'findNotes', 'version': 6, 'params': {'query': f'"{t}"'}}
        r = json.loads(urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8765', json.dumps(p).encode('utf-8'))).read().decode('utf-8'))['result']
    print(f"{t}: {len(r)} notes found")
