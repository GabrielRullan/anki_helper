import os
import sys
import json
import time
import urllib.request
import urllib.parse
import hashlib
import base64
import re

sys.stdout.reconfigure(encoding='utf-8')

ANKICONNECT_URL = 'http://127.0.0.1:8765'

def req(action, retries=5, delay=2, **params):
    payload = {"action": action, "version": 6}
    if params:
        payload["params"] = params
    
    for attempt in range(retries):
        try:
            r = urllib.request.Request(
                ANKICONNECT_URL,
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )
            with urllib.request.urlopen(r, timeout=30) as resp:
                res = json.loads(resp.read().decode('utf-8'))
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

def fetch_tts(text, lang='zh-CN'):
    if not text:
        return None
    clean = re.sub(r'<[^>]+>', '', text).strip()
    if not clean:
        return None
    url = f"https://translate.google.com/translate_tts?ie=UTF-8&tl={lang}&client=tw-ob&q={urllib.parse.quote(clean)}"
    request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    try:
        with urllib.request.urlopen(request, timeout=10) as resp:
            return resp.read()
    except Exception as e:
        print(f"TTS fetch failed for '{clean}': {e}", flush=True)
        return None

def store_audio(audio_bytes, filename):
    b64 = base64.b64encode(audio_bytes).decode('ascii')
    return req("storeMediaFile", filename=filename, data=b64)

CHAR_GAPS = [
    {
        "character": "娲",
        "pinyin": "wā",
        "english": "goddess in Chinese mythology (Nüwa)",
        "initial": "W",
        "actor": "Su Wu kong",
        "final": "-a",
        "set": "-a",
        "tone": "1",
        "location": "In Front [1]",
        "components": ["女", "圉"]
    },
    {
        "character": "焊",
        "pinyin": "hàn",
        "english": "weld, solder",
        "initial": "H",
        "actor": "Indiana Jones (Harrison Ford)",
        "final": "-an",
        "set": "-an",
        "tone": "4",
        "location": "Backyard [4]",
        "components": ["火", "干"]
    },
    {
        "character": "繇",
        "pinyin": "yóu",
        "english": "cause, originate from; folk song",
        "initial": "Y",
        "actor": "Yelena (Black Widow)",
        "final": "-ou",
        "set": "-ou",
        "tone": "2",
        "location": "Hall or Kitchen [2]",
        "components": ["䍃", "糸"]
    }
]

def main():
    print("=" * 70)
    print("   ADDING 3 MISSING IMMERSION CHARACTERS TO Chinese::Char")
    print("=" * 70)

    char_deck = "Chinese::Char"
    model_name = "Chinese Character - Double"
    timestamp_sec = int(time.time())

    added_chars = 0
    for idx, c in enumerate(CHAR_GAPS):
        char = c["character"]
        pinyin = c["pinyin"]
        english = c["english"]
        
        print(f"Processing character: {char} ({pinyin})...", end=" ", flush=True)

        c_hash = hashlib.md5(char.encode('utf-8')).hexdigest()[:10]
        c_fn = f"zh_char_{c_hash}.mp3"

        c_audio = fetch_tts(char, 'zh-CN')
        if c_audio:
            store_audio(c_audio, c_fn)

        field_id = str(timestamp_sec + idx + 2000)

        fields = {
            'ID': field_id,
            'Hanzi': char,
            'Pinyin': pinyin,
            'English': english,
            'Initial': c["initial"],
            'Actor': c["actor"],
            'Set': c["set"],
            'Tone': c["tone"],
            'Tone-Location': c["location"],
            'Components': ", ".join(c["components"]),
            'Scene': f"{c['actor']} at {c['location']} using {', '.join(c['components'])} to represent {english}.",
            'MBP_Phase': 'Immersion Gap',
            'MBP_Level': 'N+1',
            'HSK_2': '',
            'Common Words': '',
            'Translation of Words': '',
            'Simplified': char,
            'Traditional': char,
            'FrequencyTier': 'Immersion',
            'FrequencyRank': '',
            'Sound': f"[sound:{c_fn}]" if c_audio else "",
            'Words_Sound': '',
            'Words_English_Sound': '',
            'Image': '',
            'Notes': 'Added automatically via gap finder immersion scan',
            'Do_Not_Recall': ''
        }

        payload = {
            "deckName": char_deck,
            "modelName": model_name,
            "fields": fields,
            "options": {"allowDuplicate": False},
            "tags": ["immersion_gap", "n1_added"]
        }

        res = req("addNote", note=payload)
        if res:
            print(f"Success! (Note ID: {res})", flush=True)
            added_chars += 1
        else:
            print("Skipped or duplicate.", flush=True)

    print(f"\nAdded {added_chars}/3 character cards to '{char_deck}'!")

    print("\nRunning character linking script to update word character fields...")
    base_dir = r"c:\Users\gabri\Documents\anki_helper"
    scripts_dir = os.path.join(base_dir, "scripts")
    os.system(f'python "{os.path.join(scripts_dir, "link_word_characters.py")}"')

    print("\nRefreshing extract, gap finder, and dashboard...")
    os.system(f'python "{os.path.join(scripts_dir, "extract_anki_data.py")}"')
    os.system(f'python "{os.path.join(scripts_dir, "gap_finder.py")}"')
    os.system(f'python "{os.path.join(scripts_dir, "generate_dashboard.py")}"')

    print("\n" + "=" * 70)
    print("   ACTION 3 COMPLETE!")
    print("=" * 70)

if __name__ == '__main__':
    main()
