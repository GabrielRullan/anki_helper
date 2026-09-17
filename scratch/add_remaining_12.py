import os
import sys
import json
import time
import urllib.request
import urllib.parse
import hashlib
import base64
import re
from dotenv import load_dotenv

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

def generate_peanuts_image(prompt_desc, client):
    full_prompt = f"Minimalist Peanuts cartoon style illustration of: {prompt_desc}. Simple clean lines, flat soft colors, plain white background, centered composition, no text, no letters, no words."
    for model_id in ['gemini-2.5-flash-image', 'gemini-3.1-flash-image']:
        try:
            res = client.models.generate_content(
                model=model_id,
                contents=full_prompt
            )
            if res and res.candidates:
                for part in res.candidates[0].content.parts:
                    if getattr(part, 'inline_data', None):
                        return part.inline_data.data
        except Exception as e:
            time.sleep(2)
    return None

REMAINING_WORDS = [
    {
        "word": "开玩笑",
        "pinyin": "kāi wán xiào",
        "meaning": "bromear; hacer chistes",
        "sentence": "他只是在开玩笑，你别生气。",
        "translation": "Él solo está bromeando, no te enfades.",
        "peanuts_prompt": "Snoopy laughing playfully while Charlie Brown shakes his head with a mild smile."
    },
    {
        "word": "民族",
        "pinyin": "mín zú",
        "meaning": "(n.) nación; etnia",
        "sentence": "中国是一个有许多民族的国家。",
        "translation": "China es un país con muchas etnias.",
        "peanuts_prompt": "Peanuts characters standing together holding colourful traditional flags, smiling in harmony."
    },
    {
        "word": "难道",
        "pinyin": "nán dào",
        "meaning": "(adv.) ¿acaso...? (en preguntas retóricas)",
        "sentence": "这么简单的事，难道你不知道吗？",
        "translation": "Una cosa tan simple, ¿acaso no lo sabes?",
        "peanuts_prompt": "Lucy looking shocked with wide eyes and hands on hips while asking Charlie Brown a question."
    },
    {
        "word": "难受",
        "pinyin": "nán shòu",
        "meaning": "(adj.) incómodo; afligido",
        "sentence": "今天我身体有点难受，想早点休息。",
        "translation": "Hoy me siento un poco mal físicamente, quiero descansar temprano.",
        "peanuts_prompt": "Charlie Brown lying in bed wrapped in a blanket, with Snoopy sitting beside him concerned."
    },
    {
        "word": "千万",
        "pinyin": "qiān wàn",
        "meaning": "(adv.) por todos los medios; sin falta",
        "sentence": "出门前千万要关好门窗。",
        "translation": "Antes de salir de casa, por todos los medios asegúrate de cerrar bien puertas y ventanas.",
        "peanuts_prompt": "Linus pointing sternly at a front door, reminding Charlie Brown with an emphasized sign."
    },
    {
        "word": "填空",
        "pinyin": "tián kòng",
        "meaning": "(v.) rellenar el espacio en blanco",
        "sentence": "请在括号里填空，选择正确的答案。",
        "translation": "Por favor, rellena el espacio en blanco en los paréntesis y elige la respuesta correcta.",
        "peanuts_prompt": "Sally sitting at a classroom desk filling in blank boxes on a test paper with a pencil."
    },
    {
        "word": "同情",
        "pinyin": "tóng qíng",
        "meaning": "(v.) simpatizar; compadecerse",
        "sentence": "我们都很同情他的不幸遭遇。",
        "translation": "Todos simpatizamos mucho con su desgraciada situación.",
        "peanuts_prompt": "Marcy placing a comforting hand on Peppermint Patty's shoulder as she looks sad."
    },
    {
        "word": "压力",
        "pinyin": "yā lì",
        "meaning": "(n.) presión; estrés",
        "sentence": "最近工作压力很大，需要放松一下。",
        "translation": "Últimamente la presión laboral es muy grande, necesito relajarme un poco.",
        "peanuts_prompt": "Charlie Brown sitting at a desk piled high with stack of books and papers, letting out a heavy sigh."
    },
    {
        "word": "真正",
        "pinyin": "zhēn zhèng",
        "meaning": "(adj.) genuino; verdadero",
        "sentence": "只有在困难时才能找到真正的朋友。",
        "translation": "Solo en las dificultades se pueden encontrar verdaderos amigos.",
        "peanuts_prompt": "Snoopy and Woodstock hugging warmly under a small umbrella during a rainstorm."
    },
    {
        "word": "正常",
        "pinyin": "zhèng cháng",
        "meaning": "(adj.) normal; regular",
        "sentence": "机器现在恢复了正常运行。",
        "translation": "La máquina ha vuelto ahora a su funcionamiento normal.",
        "peanuts_prompt": "Schroeder listening to his toy piano sound crisp and clear, giving a thumbs up."
    },
    {
        "word": "正好",
        "pinyin": "zhèng hǎo",
        "meaning": "(adv.) justo a tiempo; casualmente",
        "sentence": "我准备去超市，正好我也要买点东西。",
        "translation": "Me dispongo a ir al supermercado; da la casualidad de que yo también necesito comprar cosas.",
        "peanuts_prompt": "Linus and Lucy meeting at the front door both carrying empty shopping bags at the exact same moment."
    },
    {
        "word": "正式",
        "pinyin": "zhèng shì",
        "meaning": "(adj.) formal; oficial",
        "sentence": "明天我们将正式开始这项工程。",
        "translation": "Mañana comenzaremos oficialmente este proyecto.",
        "peanuts_prompt": "Charlie Brown in a small bow tie holding a rolled-up ribbon blueprint, standing solemnly."
    }
]

def main():
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    from google import genai
    client = genai.Client(api_key=api_key)

    word_deck = "Chinese::Words"

    added_count = 0
    for item in REMAINING_WORDS:
        word = item["word"]
        sent = item["sentence"]
        trans = item["translation"]
        pinyin = item["pinyin"]
        meaning = item["meaning"]
        notes = item["peanuts_prompt"]
        defs = f"<b>{word}</b> [{pinyin}] {meaning}"

        print(f"Adding word card: {word} ({pinyin})...", end=" ", flush=True)

        w_hash = hashlib.md5(word.encode('utf-8')).hexdigest()[:10]
        s_hash = hashlib.md5(sent.encode('utf-8')).hexdigest()[:10]
        w_fn = f"zh_word_{w_hash}.mp3"
        s_fn = f"zh_sent_{s_hash}.mp3"
        img_fn = f"peanuts_word_{w_hash}.png"

        w_audio = fetch_tts(word, 'zh-CN')
        if w_audio:
            store_audio(w_audio, w_fn)

        s_audio = fetch_tts(sent, 'zh-CN')
        if s_audio:
            store_audio(s_audio, s_fn)

        img_bytes = generate_peanuts_image(notes, client)
        if img_bytes:
            store_audio(img_bytes, img_fn)

        fields = {
            "Word": word,
            "Sentence": sent,
            "Translated Sentence": trans,
            "Definitions": defs,
            "Notes": notes,
            "Images": f'<img src="{img_fn}">' if img_bytes else "",
            "Word Audio": f"[sound:{w_fn}]" if w_audio else "",
            "Sentence Audio": f"[sound:{s_fn}]" if s_audio else "",
            "Characters": ""
        }

        payload = {
            "deckName": word_deck,
            "modelName": "Migaku Word",
            "fields": fields,
            "options": {"allowDuplicate": True},
            "tags": ["hsk4", "synergy"]
        }

        res = req("addNote", note=payload)
        if res:
            print(f"Success! Note ID: {res}", flush=True)
            added_count += 1
        else:
            print("Failed.", flush=True)

    print(f"\nAdded {added_count}/12 remaining HSK 4 words!")

    base_dir = r"c:\Users\gabri\Documents\anki_helper"
    scripts_dir = os.path.join(base_dir, "scripts")
    print("Linking word characters...")
    os.system(f'python "{os.path.join(scripts_dir, "link_word_characters.py")}"')
    print("Rebuilding extract, gap report, and dashboard...")
    os.system(f'python "{os.path.join(scripts_dir, "extract_anki_data.py")}"')
    os.system(f'python "{os.path.join(scripts_dir, "gap_finder.py")}"')
    os.system(f'python "{os.path.join(scripts_dir, "generate_dashboard.py")}"')

if __name__ == '__main__':
    main()
