import os
import json
import urllib.request
import sys

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
                raise Exception(res.get('error'))
            return res.get('result')
    except Exception as e:
        print(f"API Request Failed for action '{action}': {e}")
        return None

def main():
    decks = request_anki("deckNames")
    if "Chinese::Sent" not in decks:
        print("Chinese::Sent deck not found.")
        return

    note_ids = request_anki("findNotes", query='deck:"Chinese::Sent"')
    print(f"Total notes in Chinese::Sent: {len(note_ids)}")

    notes_info = request_anki("notesInfo", notes=note_ids)
    no_image_notes = []
    has_image_notes = []
    
    for note in notes_info:
        fields = note.get('fields', {})
        # Find which field holds the image. In Chinese Sentence - Double/Single, it is "Images".
        img_val = fields.get('Images', {}).get('value', '').strip()
        sentence_val = fields.get('Sentence', {}).get('value', '').strip()
        translation_val = fields.get('Translated_Sentence', {}).get('value', '').strip()
        
        # Check if img_val contains an <img> tag or is empty
        if not img_val or '<img' not in img_val.lower():
            no_image_notes.append({
                'id': note.get('noteId'),
                'model': note.get('modelName'),
                'sentence': sentence_val,
                'translation': translation_val,
                'images_field_value': img_val
            })
        else:
            has_image_notes.append({
                'id': note.get('noteId'),
                'sentence': sentence_val,
                'images_field_value': img_val
            })

    print(f"Notes with images: {len(has_image_notes)}")
    print(f"Notes without images: {len(no_image_notes)}")
    
    if no_image_notes:
        print("\nFirst 10 notes without images:")
        for idx, item in enumerate(no_image_notes[:10], 1):
            print(f"{idx}. ID: {item['id']} ({item['model']})")
            print(f"   Sentence: {repr(item['sentence'])}")
            print(f"   Translation: {repr(item['translation'])}")
            print(f"   Image Field: {repr(item['images_field_value'])}")

if __name__ == "__main__":
    main()
