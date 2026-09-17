import json
import urllib.request
import sys

sys.stdout.reconfigure(encoding='utf-8')
ANKICONNECT_URL = 'http://127.0.0.1:8765'

def invoke(action, **params):
    req = urllib.request.Request(
        ANKICONNECT_URL,
        data=json.dumps({'action': action, 'version': 6, 'params': params}).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        if res.get('error'):
            raise Exception(res['error'])
        return res.get('result')

fix_map = {
    1787514324361: ('弹药, 弹吉他', 'Ammunition, Play guitar'),
    1787581231369: ('女娲, 女娲补天', 'Nüwa goddess, Nüwa mends the sky'),
    1787581231618: ('焊接, 电焊', 'Weld, Electric welding'),
    1787581231881: ('繇役, 歌繇', 'Corvée labor, Folk song')
}

for n_id, (cw, tw) in fix_map.items():
    invoke('updateNoteFields', note={
        'id': n_id,
        'fields': {
            'Common Words': cw,
            'Translation of Words': tw
        }
    })
    print(f"Updated note {n_id}")

print("Done updating all remaining notes!")
