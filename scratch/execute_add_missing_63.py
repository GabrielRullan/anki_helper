import urllib.request
import urllib.parse
import json
import base64
import hashlib
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

# Resolve target deck name
decks = invoke('deckNames')
target_deck = 'Chinese::Char'
for d in decks:
    if d.lower() == 'chinese::char' or d.lower() == 'chinese char':
        target_deck = d
        break
print(f"Target Deck for Characters: {target_deck}")

def download_tts(text, lang='zh-CN'):
    url = "https://translate.google.com/translate_tts"
    params = {
        'ie': 'UTF-8',
        'tl': lang,
        'client': 'tw-ob',
        'q': text[:100]
    }
    query = urllib.parse.urlencode(params)
    req = urllib.request.Request(f"{url}?{query}", headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.read()
    except Exception as e:
        print(f"TTS fetch error for {text}: {e}")
        return None

def store_audio(audio_bytes, filename):
    b64 = base64.b64encode(audio_bytes).decode('utf-8')
    return invoke('storeMediaFile', filename=filename, data=b64)

with open('scratch/proposed_63_cards.json', 'r', encoding='utf-8') as f:
    proposed = json.load(f)

print(f"Loaded {len(proposed)} proposed cards. Starting insertion to Anki...")

added_count = 0
failed_count = 0

for idx, card in enumerate(proposed, 1):
    h = card['hanzi']
    lvl = card['lesson']
    tag = card['tag']

    # Generate TTS audio
    audio_bytes = download_tts(h, 'zh-CN')
    sound_tag = ""
    if audio_bytes:
        h_hash = hashlib.md5(h.encode('utf-8')).hexdigest()[:8]
        fn = f"zh_char_{h}_{h_hash}.mp3"
        try:
            stored_fn = store_audio(audio_bytes, fn)
            if stored_fn:
                sound_tag = f"[sound:{stored_fn}]"
        except Exception as e:
            print(f"Failed to store audio for {h}: {e}")

    fields = {
        "ID": f"mbp_{lvl}_{h}",
        "Hanzi": h,
        "Pinyin": card['pinyin'],
        "English": card['english'],
        "Initial": card['initial'],
        "Actor": card['actor'],
        "Set": card['set'],
        "Tone": card['tone'],
        "Tone-Location": card['tone_location'],
        "Components": card['components'],
        "Scene": card['scene'],
        "MBP_Phase": "Phase 5",
        "MBP_Level": str(lvl),
        "HSK_2": card['hsk'],
        "Simplified": h,
        "Traditional": h,
        "FrequencyTier": "Tier 2",
        "FrequencyRank": str(card['frequency_rank']),
        "Sound": sound_tag
    }

    note_payload = {
        "deckName": target_deck,
        "modelName": "Chinese Character - Double",
        "fields": fields,
        "tags": [tag, "traverse_import", f"lesson_{lvl}"]
    }

    try:
        n_id = invoke('addNote', note=note_payload)
        added_count += 1
        print(f"[{idx}/{len(proposed)}] Added '{h}' (Lesson {lvl}) -> Note ID {n_id}")
    except Exception as e:
        failed_count += 1
        print(f"[{idx}/{len(proposed)}] FAILED to add '{h}' (Lesson {lvl}): {e}")

print(f"\n==========================================")
print(f"SUCCESSFULLY ADDED: {added_count} cards")
print(f"FAILED: {failed_count} cards")
print(f"==========================================")
