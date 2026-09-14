import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

def invoke(action, **params):
    req = urllib.request.Request(
        'http://127.0.0.1:8765',
        data=json.dumps({'action': action, 'version': 6, 'params': params}).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        if res.get('error'):
            raise Exception(res['error'])
        return res.get('result')

# Sample hanzi from lesson 68 that are in Anki: 萨, 锦, 链, 轰, 桑, 纽, 纹, 缴, 迹, 迪...
test_hanzi = ['萨', '锦', '链', '轰', '桑', '纽', '纹', '缴', '迹', '迪']

for h in test_hanzi:
    notes1 = invoke('findNotes', query=f'deck:"Chinese Char" Hanzi:"{h}"')
    notes2 = invoke('findNotes', query=f'deck:"*Char*" "{h}"')
    print(f"Hanzi '{h}': query 'deck:\"Chinese Char\" Hanzi:\"{h}\"' => {notes1}, general query => {notes2[:3]}")
