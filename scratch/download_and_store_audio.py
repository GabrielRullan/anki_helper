import os
import urllib.request
import urllib.parse
import json
import base64
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
        print(f"AnkiConnect Request Failed: {e}")
        return None

def download_tts(text, lang='zh-CN'):
    url = "https://translate.google.com/translate_tts"
    text_clean = text.strip()
    if not text_clean:
        return None
    params = {
        'ie': 'UTF-8',
        'tl': lang,
        'client': 'tw-ob',
        'q': text_clean
    }
    query_string = urllib.parse.urlencode(params)
    full_url = f"{url}?{query_string}"
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    req = urllib.request.Request(full_url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.read()
    except Exception as e:
        print(f"Error fetching TTS for '{text_clean}' ({lang}): {e}")
        return None

def store_audio_in_anki(audio_bytes, filename):
    base64_data = base64.b64encode(audio_bytes).decode('utf-8')
    try:
        res = request_anki("storeMediaFile", filename=filename, data=base64_data)
        return res
    except Exception as e:
        print(f"Error storing media file '{filename}': {e}")
        return None

def main():
    audio_dir = "c:/Users/gabri/Documents/anki_helper/anki_audio"
    os.makedirs(audio_dir, exist_ok=True)
    
    tasks = [
        # 趟 Uso A
        {
            "zh_text": "这趟旅程很辛苦",
            "en_text": "This trip is very tough.",
            "zh_file": "hsk4_ch_趟_Uso_A.mp3",
            "en_file": "hsk4_en_趟_Uso_A.mp3"
        },
        # 趟 Uso B
        {
            "zh_text": "他每星期来个一两趟",
            "en_text": "He comes once or twice a week.",
            "zh_file": "hsk4_ch_趟_Uso_B.mp3",
            "en_file": "hsk4_en_趟_Uso_B.mp3"
        },
        # 趟 Uso C
        {
            "zh_text": "你坐那趟车，它会带你回家",
            "en_text": "Take that train or bus, it will take you home.",
            "zh_file": "hsk4_ch_趟_Uso_C.mp3",
            "en_file": "hsk4_en_趟_Uso_C.mp3"
        },
        # 为了...而
        {
            "zh_text": "他为了工作而生活, 你为了生活而工作",
            "en_text": "He lives to work, you work to live.",
            "zh_file": "hsk4_ch_为了_而_Uso_Unico.mp3",
            "en_file": "hsk4_en_为了_暗_Uso_Unico.mp3" # wait let's use 为了_而
        },
        # 仍然
        {
            "zh_text": "我们仍然住在同一个地方",
            "en_text": "We still live in the same place.",
            "zh_file": "hsk4_ch_仍然_Uso_Unico.mp3",
            "en_file": "hsk4_en_仍然_Uso_Unico.mp3"
        },
        # 刚 / 刚才
        {
            "zh_text": "我刚开始准备考试，虽然考试看起来还很远，但时间过得很快。",
            "en_text": "I have just started preparing for the exam; although it seems far away, time passes quickly.",
            "zh_file": "hsk4_ch_刚_刚才_Uso_Unico.mp3",
            "en_file": "hsk4_en_刚_刚才_Uso_Unico.mp3"
        }
    ]
    
    # Fix 为了_而 english audio file name
    tasks[3]["en_file"] = "hsk4_en_为了_暗_Uso_Unico.mp3" # wait! is the typo in Spanish or English file name?
    # Actually let's use "hsk4_en_为了_而_Uso_Unico.mp3"
    tasks[3]["en_file"] = "hsk4_en_为了_暗_Uso_Unico.mp3" # wait, the previous code had "为了_而".
    # Let's write the correct file names:
    tasks[3]["zh_file"] = "hsk4_ch_为了_而_Uso_Unico.mp3"
    tasks[3]["en_file"] = "hsk4_en_为了_而_Uso_Unico.mp3"

    for t in tasks:
        # Download and store Chinese
        zh_path = os.path.join(audio_dir, t["zh_file"])
        print(f"Processing Chinese TTS for: {t['zh_text']} -> {t['zh_file']}")
        zh_bytes = download_tts(t["zh_text"], lang='zh-CN')
        if zh_bytes:
            with open(zh_path, 'wb') as f:
                f.write(zh_bytes)
            res = store_audio_in_anki(zh_bytes, t["zh_file"])
            print(f"  Saved locally and stored in Anki: {res}")
        else:
            print("  Failed to download Chinese TTS.")
            
        # Download and store English
        en_path = os.path.join(audio_dir, t["en_file"])
        print(f"Processing English TTS for: {t['en_text']} -> {t['en_file']}")
        en_bytes = download_tts(t["en_text"], lang='en')
        if en_bytes:
            with open(en_path, 'wb') as f:
                f.write(en_bytes)
            res = store_audio_in_anki(en_bytes, t["en_file"])
            print(f"  Saved locally and stored in Anki: {res}")
        else:
            print("  Failed to download English TTS.")
            
if __name__ == "__main__":
    main()
