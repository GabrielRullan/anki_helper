import os
import re
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

def get_media_filename(hanzi, english):
    meaning_keyword = re.sub(r'[^a-zA-Z]', '', english.split(',')[0].split(';')[0].split('/')[0].strip()).lower()
    if not meaning_keyword:
        meaning_keyword = "char"
    return f"mbp_{hanzi}_{meaning_keyword}.png"

def main():
    merged_path = os.path.join('data', 'active_scenes_merged.json')
    if os.path.exists(merged_path) and "--remerge" not in sys.argv:
        with open(merged_path, 'r', encoding='utf-8') as f:
            merged = json.load(f)
        print(f"Loaded {len(merged)} items from {merged_path}.")
    else:
        merged = []
        for idx in range(1, 5):
            path = os.path.join('data', f'active_scenes_output_{idx}.json')
            if not os.path.exists(path):
                print(f"[ERROR] Missing {path}")
                sys.exit(1)
            with open(path, 'r', encoding='utf-8') as f:
                chunk = json.load(f)
                merged.extend(chunk)
        with open(merged_path, 'w', encoding='utf-8') as f:
            json.dump(merged, f, ensure_ascii=False, indent=2)
        print(f"Merged {len(merged)} items into {merged_path}.")

    if "--merge-only" in sys.argv:
        return

    updates = []
    nids_scene_updated = []
    nids_image_updated = []
    nids_still_need_image = []
    img_dir = os.path.abspath(os.path.join('imagenes_vocabulario', 'mbp_regenerated'))
    os.makedirs(img_dir, exist_ok=True)

    for item in merged:
        nid = item['note_id']
        scene = item.get('scene', '').strip()
        hz = item['hanzi']
        eng = item.get('english', '')
        if not scene:
            continue

        fields_to_set = {'Scene': scene}

        # Check if a newly generated image exists in imagenes_vocabulario/mbp_regenerated
        media_filename = get_media_filename(hz, eng)
        local_img_path = os.path.join(img_dir, media_filename)
        if os.path.exists(local_img_path):
            request_anki("storeMediaFile", filename=media_filename, path=local_img_path)
            fields_to_set['Image'] = f'<img src="{media_filename}">'
            nids_image_updated.append(nid)
        else:
            nids_still_need_image.append(nid)

        updates.append({
            'id': nid,
            'fields': fields_to_set
        })
        nids_scene_updated.append(nid)

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

    if nids_scene_updated:
        print(f"Removing 'needs_scene_update' tag from {len(nids_scene_updated)} updated active notes...")
        request_anki("removeTags", notes=nids_scene_updated, tags="needs_scene_update")

    if nids_image_updated:
        request_anki("removeTags", notes=nids_image_updated, tags="needs_image_update")
        print(f"Uploaded and linked {len(nids_image_updated)} regenerated images.")

    if nids_still_need_image:
        request_anki("addTags", notes=nids_still_need_image, tags="needs_image_update")
        print(f"Tagged {len(nids_still_need_image)} notes with 'needs_image_update'.")

    print(f"Successfully updated {len(updates)} active notes in Anki!")

if __name__ == "__main__":
    main()
