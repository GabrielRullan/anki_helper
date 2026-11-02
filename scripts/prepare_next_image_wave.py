import json
import os
import sys
import glob
import shutil

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath('scripts'))
from apply_generated_scenes_and_images import get_media_filename

ARTIFACT_DIR = r'C:\Users\gabri\.gemini\antigravity\brain\20ac4fc3-656b-4a42-b283-4a8aef7a6354'
REGEN_DIR = os.path.abspath(os.path.join('imagenes_vocabulario', 'mbp_regenerated'))
os.makedirs(REGEN_DIR, exist_ok=True)

def collect_from_artifact_dir():
    merged = json.load(open('data/active_scenes_merged.json', encoding='utf-8'))
    copied = 0
    for item in merged:
        nid = item['note_id']
        fname = get_media_filename(item['hanzi'], item['english'])
        dst = os.path.join(REGEN_DIR, fname)
        if os.path.exists(dst):
            continue
        pattern = os.path.join(ARTIFACT_DIR, f"nid_{nid}_*.*")
        matches = glob.glob(pattern)
        if matches:
            # Take newest match
            matches.sort(key=os.path.getmtime, reverse=True)
            shutil.copy2(matches[0], dst)
            copied += 1
    return copied

def get_remaining_items():
    collect_from_artifact_dir()
    merged = json.load(open('data/active_scenes_merged.json', encoding='utf-8'))
    remaining = []
    for item in merged:
        fname = get_media_filename(item['hanzi'], item['english'])
        dst = os.path.join(REGEN_DIR, fname)
        if not os.path.exists(dst):
            item['target_filename'] = fname
            remaining.append(item)
    return remaining

def build_batch_prompt(batch):
    lines = [
        f"Generate {len(batch)} minimalist Peanuts cartoon style flashcard illustrations (plain solid white background, simple clean line art, flat colors, centered, no text or letters of any alphabet).",
        "IMPORTANT: For each image, you MUST set the image name / filename prefix to the exact `nid_<note_id>` identifier shown below so our script can match it automatically:\n"
    ]
    for i, it in enumerate(batch, 1):
        clean_scene = it['scene'].replace('**', '')
        lines.append(f"{i}. ImageName MUST start with: `nid_{it['note_id']}` (for character {it['hanzi']})")
        lines.append(f"   Brief: Minimalist Peanuts cartoon style illustration of: {clean_scene} Plain solid white background, simple clean line art, flat colors, centered, no text or letters.\n")
    lines.append("Reply briefly once all images in this batch have been generated.")
    return "\n".join(lines)

if __name__ == "__main__":
    merged_total = len(json.load(open('data/active_scenes_merged.json', encoding='utf-8')))
    rem = get_remaining_items()
    print(f"Remaining images to generate: {len(rem)} / {merged_total}")
    # Write next 10 batches of 8 images each
    batch_size = 8
    num_batches = min(10, (len(rem) + batch_size - 1) // batch_size)
    batches_out = []
    for b in range(num_batches):
        sub = rem[b*batch_size : (b+1)*batch_size]
        batches_out.append({
            'batch_index': b + 1,
            'count': len(sub),
            'hanzi_list': [x['hanzi'] for x in sub],
            'prompt': build_batch_prompt(sub)
        })
    with open('data/next_image_batches.json', 'w', encoding='utf-8') as f:
        json.dump(batches_out, f, ensure_ascii=False, indent=2)
    print(f"Prepared {len(batches_out)} batches in data/next_image_batches.json")
