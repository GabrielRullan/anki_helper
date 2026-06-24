import os
import json
import urllib.request
import sys
import re

# Reconfigure stdout to UTF-8
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
        with urllib.request.urlopen(req, timeout=15) as response:
            res = json.loads(response.read().decode('utf-8'))
            if res.get('error'):
                print(f"AnkiConnect Error: {res.get('error')}")
                return None
            return res.get('result')
    except Exception as e:
        print(f"AnkiConnect Request Failed: {e}")
        return None

def clean_html(text):
    if not text:
        return ""
    text = re.sub(r'<br\s*/?>', ' ', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('&nbsp;', ' ').replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
    return text.strip()

def main():
    note_ids = request_anki("findNotes", query='deck:"Chinese::Sent"')
    if not note_ids:
        print("No notes found in deck 'Chinese::Sent'.")
        return
        
    notes_info = request_anki("notesInfo", notes=note_ids)
    missing_notes = []
    
    for note in notes_info:
        fields = note.get('fields', {})
        sentence = fields.get('Sentence', {}).get('value', '').strip()
        translation = fields.get('Translated_Sentence', {}).get('value', '').strip()
        images_val = fields.get('Images', {}).get('value', '').strip()
        nid = note.get('noteId')
        
        if not images_val or '<img' not in images_val.lower():
            missing_notes.append({
                'note_id': nid,
                'sentence': clean_html(sentence),
                'translation': clean_html(translation)
            })
            
    output_path = "data/missing_sentences.json"
    os.makedirs("data", exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(missing_notes, f, ensure_ascii=False, indent=2)
        
    print(f"Successfully exported {len(missing_notes)} missing sentence notes to {output_path}")

if __name__ == "__main__":
    main()
