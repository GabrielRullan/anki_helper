import os
import sys
import json
import urllib.request
import urllib.parse
import base64
import time
import hashlib
from concurrent.futures import ThreadPoolExecutor

sys.stdout.reconfigure(encoding='utf-8')

ANKICONNECT_URL = 'http://127.0.0.1:8765'

def request_anki(action, retries=5, delay=2, **params):
    payload = {"action": action, "version": 6}
    if params:
        payload["params"] = params
    
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                ANKICONNECT_URL,
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                res = json.loads(response.read().decode('utf-8'))
                if res.get('error'):
                    print(f"AnkiConnect Error [{action}]: {res.get('error')}", flush=True)
                    return None
                return res.get('result')
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                print(f"AnkiConnect Request Failed [{action}]: {e}", flush=True)
                return None

def fetch_tts_audio(text, lang='zh-CN'):
    url = f"https://translate.google.com/translate_tts?ie=UTF-8&tl={lang}&client=tw-ob&q={urllib.parse.quote(text)}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.read()
    except Exception as e:
        print(f"TTS fetch failed for '{text}': {e}", flush=True)
        return None

def process_note_audio(note):
    f = note.get('fields', {})
    nid = note['noteId']
    c = f.get('Hanzi', {}).get('value', '').strip() or f.get('Simplified', {}).get('value', '').strip()
    if not c:
        return False

    current_sound = f.get('Sound', {}).get('value', '').strip()
    if current_sound:
        return False

    audio_bytes = fetch_tts_audio(c, lang='zh-CN')
    if not audio_bytes:
        return False

    # Unique filename based on character hash
    char_hash = hashlib.md5(c.encode('utf-8')).hexdigest()[:10]
    filename = f"zh_char_{char_hash}.mp3"
    b64_data = base64.b64encode(audio_bytes).decode('ascii')

    stored = request_anki("storeMediaFile", filename=filename, data=b64_data)
    if stored:
        sound_tag = f"[sound:{filename}]"
        request_anki("updateNoteFields", note={"id": nid, "fields": {"Sound": sound_tag}})
        return True
    return False

def main():
    print("=" * 70, flush=True)
    print("   GENERATING MANDARIN TTS AUDIO FOR CHARACTER DECK")
    print("=" * 70, flush=True)

    note_ids = request_anki("findNotes", query='deck:Chinese::Char')
    if not note_ids:
        print("Error: No notes found in Chinese::Char deck", flush=True)
        return

    notes_info = request_anki("notesInfo", notes=note_ids)
    missing_audio_notes = [n for n in notes_info if not n['fields'].get('Sound', {}).get('value', '').strip()]

    print(f"Total Character Notes: {len(notes_info):,}")
    print(f"Notes Missing Audio: {len(missing_audio_notes):,}", flush=True)

    if not missing_audio_notes:
        print("All character notes already have audio populated!", flush=True)
        return

    print("\nGenerating native TTS audio files and updating notes...", flush=True)

    chunk_size = 50
    success_count = 0

    for i in range(0, len(missing_audio_notes), chunk_size):
        chunk = missing_audio_notes[i:i + chunk_size]
        with ThreadPoolExecutor(max_workers=5) as executor:
            results = list(executor.map(process_note_audio, chunk))
            success_count += sum(1 for r in results if r)
        print(f"  Progress: {min(i + chunk_size, len(missing_audio_notes))}/{len(missing_audio_notes)} processed ({success_count} audio files created).", flush=True)
        time.sleep(0.5)

    print(f"\nSuccessfully generated and attached TTS audio for {success_count:,} notes!", flush=True)
    print("=" * 70, flush=True)

if __name__ == "__main__":
    main()
