import json
import urllib.request
import re
import sys

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
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            res = json.loads(response.read().decode('utf-8'))
            if res.get('error'):
                return None
            return res.get('result')
    except Exception as e:
        return None

def main():
    print("Finding all notes in collection...")
    note_ids = request_anki("findNotes", query="")
    if not note_ids:
        print("No notes found.")
        return
        
    print(f"Total notes: {len(note_ids)}. Fetching info...")
    chunk_size = 500
    notes_info = []
    for i in range(0, len(note_ids), chunk_size):
        chunk = note_ids[i:i+chunk_size]
        res = request_anki("notesInfo", notes=chunk)
        if res:
            notes_info.extend(res)
            
    link_pattern = re.compile(r'\[([^|\]]*)\|nid(\d+)\]')
    
    suspicious_links = []
    
    for note in notes_info:
        note_id = note['noteId']
        fields = note['fields']
        
        for field_name, field_data in fields.items():
            val = field_data['value']
            matches = link_pattern.findall(val)
            for title, nid in matches:
                title_stripped = title.strip()
                # Check for:
                # 1. empty title
                # 2. contains img/src
                # 3. contains image extension (.png, .jpg, .gif)
                # 4. contains web link or html tags
                is_empty = not title_stripped
                has_image_tag = '<img' in title_stripped or 'src=' in title_stripped
                has_image_ext = any(ext in title_stripped.lower() for ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg'])
                has_html = '<' in title_stripped or '>' in title_stripped
                
                if is_empty or has_image_tag or has_image_ext or has_html:
                    suspicious_links.append({
                        'note_id': note_id,
                        'field': field_name,
                        'title': title,
                        'nid': nid,
                        'type': 'empty' if is_empty else 'image_tag' if has_image_tag else 'image_ext' if has_image_ext else 'html'
                    })
                    
    print(f"\nFound {len(suspicious_links)} suspicious links:")
    for idx, item in enumerate(suspicious_links):
        print(f"{idx+1}. Note ID: {item['note_id']} | Field: {item['field']} | Type: {item['type']} | Title: {repr(item['title'])} | Linked NID: {item['nid']}")
        
if __name__ == '__main__':
    main()
