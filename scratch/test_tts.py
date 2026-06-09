import urllib.request
import urllib.parse
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

def download_tts(text, lang='zh-CN'):
    url = "https://translate.google.com/translate_tts"
    params = {
        'ie': 'UTF-8',
        'tl': lang,
        'client': 'tw-ob',
        'q': text
    }
    query_string = urllib.parse.urlencode(params)
    full_url = f"{url}?{query_string}"
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    req = urllib.request.Request(full_url, headers=headers)
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.read()
    except Exception as e:
        print(f"Error fetching TTS: {e}")
        return None

def main():
    test_word = "排列"
    test_phrase = "请把这些卡片排列好。"
    
    print(f"Downloading TTS for word '{test_word}'...")
    word_audio = download_tts(test_word)
    if word_audio:
        word_file = "temp_word.mp3"
        with open(word_file, "wb") as f:
            f.write(word_audio)
        print(f"Success! Saved word audio to {os.path.abspath(word_file)} (size: {len(word_audio)} bytes)")
        
    print(f"Downloading TTS for phrase '{test_phrase}'...")
    phrase_audio = download_tts(test_phrase)
    if phrase_audio:
        phrase_file = "temp_phrase.mp3"
        with open(phrase_file, "wb") as f:
            f.write(phrase_audio)
        print(f"Success! Saved phrase audio to {os.path.abspath(phrase_file)} (size: {len(phrase_audio)} bytes)")

if __name__ == "__main__":
    main()
