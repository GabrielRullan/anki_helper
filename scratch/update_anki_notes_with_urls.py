import urllib.request
import json
import re
import os
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

# Load scraped URL mapping
url_file = 'data/mbp_urls_68_88.json'
if not os.path.exists(url_file):
    print("URL file missing!")
    sys.exit(1)

with open(url_file, 'r', encoding='utf-8') as f:
    url_map = json.load(f)

print(f"Loaded {len(url_map)} character URLs from {url_file}")

# Query notes tagged lesson_68 to lesson_88
all_note_ids = set()
for lvl in range(68, 89):
    ids = invoke('findNotes', query=f'tag:lesson_{lvl}')
    all_note_ids.update(ids)

print(f"Found {len(all_note_ids)} character notes across tags lesson_68..lesson_88")

notes_info = invoke('notesInfo', notes=list(all_note_ids))

updated_count = 0
skipped_count = 0
missing_url_count = 0

for info in notes_info:
    n_id = info['noteId']
    fields = info['fields']
    h = fields.get('Hanzi', {}).get('value', '').strip() or fields.get('Simplified', {}).get('value', '').strip()
    
    if not h or h not in url_map:
        missing_url_count += 1
        continue
    
    url = url_map[h]
    current_notes_html = fields.get('Notes', {}).get('value', '').strip()
    
    # Check if URL is already in Notes
    if url in current_notes_html:
        skipped_count += 1
        continue
    
    # Clean out any old MBP link if re-updating
    clean_html = re.sub(r'<div class="mbp-link"[^>]*>.*?</div>', '', current_notes_html, flags=re.DOTALL).strip()
    
    link_html = f'<div class="mbp-link" style="margin-top:8px;font-size:0.85em;"><a href="{url}" target="_blank" style="color:#60A5FA;text-decoration:underline;">Mandarin Blueprint Lesson ({h})</a></div>'
    
    if clean_html:
        new_notes_html = f"{clean_html}\n{link_html}"
    else:
        new_notes_html = link_html
        
    invoke('updateNoteFields', note={
        'id': n_id,
        'fields': {
            'Notes': new_notes_html
        }
    })
    
    updated_count += 1
    if updated_count <= 15 or updated_count % 100 == 0:
        print(f"Updated Note {n_id} ({h}): added {url}")

print("\n==========================================")
print(f"FINISHED! Updated {updated_count} notes with Mandarin Blueprint URLs.")
print(f"Skipped (URL already present): {skipped_count}")
print(f"No online URL found (e.g. beyond course level 80): {missing_url_count}")
print("==========================================")
