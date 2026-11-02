import os
import sys
import json
import time
import math
import urllib.request

sys.stdout.reconfigure(encoding='utf-8')

ANKICONNECT_URL = 'http://127.0.0.1:8765'

def request_anki(action, **params):
    payload = {"action": action, "version": 6}
    if params:
        payload["params"] = params
    req = urllib.request.Request(
        ANKICONNECT_URL,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req, timeout=20) as response:
        res = json.loads(response.read().decode('utf-8'))
        if res.get('error'):
            raise RuntimeError(f"AnkiConnect error on {action}: {res['error']}")
        return res.get('result')

def main():
    merged = []
    for idx in range(1, 7):
        path = os.path.join('data', f'missing_scenes_output_{idx}.json')
        if not os.path.exists(path):
            print(f"[ERROR] Missing {path}")
            sys.exit(1)
        with open(path, 'r', encoding='utf-8') as f:
            chunk = json.load(f)
            merged.extend(chunk)

    merged_path = os.path.join('data', 'all_missing_scenes_merged.json')
    with open(merged_path, 'w', encoding='utf-8') as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)

    print(f"Merged {len(merged)} items into {merged_path}.")

    if "--merge-only" in sys.argv:
        return

    updates = []
    nids_updated = []
    for item in merged:
        nid = item['note_id']
        scene = item.get('scene', '').strip()
        if not scene:
            print(f"[WARN] Empty scene for {item.get('hanzi')}")
            continue
        updates.append({
            'id': nid,
            'fields': {'Scene': scene}
        })
        nids_updated.append(nid)

    batch_size = 50
    total_batches = math.ceil(len(updates) / batch_size)
    for i in range(0, len(updates), batch_size):
        batch = updates[i:i+batch_size]
        actions = [
            {"action": "updateNoteFields", "params": {"note": u}}
            for u in batch
        ]
        b_num = i // batch_size + 1
        print(f"Updating Anki batch {b_num}/{total_batches} ({len(batch)} notes)...", end=" ", flush=True)
        request_anki("multi", actions=actions)
        print("OK")
        time.sleep(0.1)

    if nids_updated:
        print(f"Removing 'needs_scene_update' tag from {len(nids_updated)} notes...")
        request_anki("removeTags", notes=nids_updated, tags="needs_scene_update")

    print(f"Successfully synced {len(updates)} missing scenes to Anki!")

if __name__ == "__main__":
    main()
