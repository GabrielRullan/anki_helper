import os
import sys
import json
import time
import urllib.request
import urllib.parse
import hashlib
import base64
import re
from collections import Counter, defaultdict

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

# 15 HSK 4 Synergy Words Data
HSK_SYNERGY_WORDS = [
    {
        "word": "安排",
        "pinyin": "ān pái",
        "meaning": "(v.) organizar; (n.) arreglo",
        "sentence": "这周的工作我已经安排好了。",
        "translation": "Ya he organizado el trabajo de esta semana.",
        "peanuts_prompt": "Charlie Brown organizing a weekly schedule on a large bulletin board. Linus and Lucy watch closely."
    },
    {
        "word": "导游",
        "pinyin": "dǎo yóu",
        "meaning": "(n.) guía turístico",
        "sentence": "导游带着我们参观了长城。",
        "translation": "El guía turístico nos llevó a visitar la Gran Muralla.",
        "peanuts_prompt": "Snoopy wearing a tour guide hat and holding a small flag, leading Charlie Brown and Sally along a scenic path."
    },
    {
        "word": "对于",
        "pinyin": "duì yú",
        "meaning": "(prep.) respecto; en lo que respecta a algo",
        "sentence": "对于这个问题，每个人都有不同的看法。",
        "translation": "Con respecto a este problema, cada uno tiene una opinión diferente.",
        "peanuts_prompt": "Linus and Lucy standing around a puzzle board, pointing at a piece with different thoughtful expressions."
    },
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

# 3 Missing Immersion Characters Data
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
    print("  EXECUTING ACTION 1 (15 HSK 4 WORDS) AND ACTION 3 (3 CHAR GAPS)")
    print("=" * 70)

    # -------------------------------------------------------------
    # STEP 1: ACTION 1 - SYNC 15 HSK 4 WORDS TO Chinese::Words
    # -------------------------------------------------------------
    print("\n[ACTION 1] Adding 15 HSK 4 Synergy Words to 'Chinese::Words' deck...")
    word_deck = "Chinese::Words"

    added_words = 0
    for item in HSK_SYNERGY_WORDS:
        word = item["word"]
        sent = item["sentence"]
        trans = item["translation"]
        pinyin = item["pinyin"]
        meaning = item["meaning"]
        notes = item["peanuts_prompt"]
        defs = f"<b>{word}</b> [{pinyin}] {meaning}"

        print(f"  Processing word: {word} ({pinyin})...", end=" ", flush=True)

        # Download & store audio
        w_hash = hashlib.md5(word.encode('utf-8')).hexdigest()[:10]
        s_hash = hashlib.md5(sent.encode('utf-8')).hexdigest()[:10]
        w_fn = f"zh_word_{w_hash}.mp3"
        s_fn = f"zh_sent_{s_hash}.mp3"

        w_audio = fetch_tts(word, 'zh-CN')
        if w_audio:
            store_audio(w_audio, w_fn)

        s_audio = fetch_tts(sent, 'zh-CN')
        if s_audio:
            store_audio(s_audio, s_fn)

        fields = {
            "Word": word,
            "Sentence": sent,
            "Translated Sentence": trans,
            "Definitions": defs,
            "Notes": notes,
            "Images": "",
            "Word Audio": f"[sound:{w_fn}]" if w_audio else "",
            "Sentence Audio": f"[sound:{s_fn}]" if s_audio else "",
            "Characters": ""
        }

        payload = {
            "deckName": word_deck,
            "modelName": "Migaku Word",
            "fields": fields,
            "options": {"allowDuplicate": False},
            "tags": ["hsk4", "synergy"]
        }

        res = req("addNote", note=payload)
        if res:
            print(f"Added! Note ID: {res}", flush=True)
            added_words += 1
        else:
            print("Skipped or duplicate.", flush=True)

    print(f"Completed Action 1: {added_words}/15 words added to 'Chinese::Words'.")

    # -------------------------------------------------------------
    # STEP 2: ACTION 3 - ADD 3 MISSING CHARACTERS TO Chinese::Char
    # -------------------------------------------------------------
    print("\n[ACTION 3] Adding 3 missing immersion characters to 'Chinese::Char' deck...")
    char_deck = "Chinese::Char"
    timestamp_sec = int(time.time())

    added_chars = 0
    for idx, c in enumerate(CHAR_GAPS):
        char = c["character"]
        pinyin = c["pinyin"]
        english = c["english"]
        
        print(f"  Processing character: {char} ({pinyin})...", end=" ", flush=True)

        c_hash = hashlib.md5(char.encode('utf-8')).hexdigest()[:10]
        c_fn = f"zh_char_{c_hash}.mp3"

        c_audio = fetch_tts(char, 'zh-CN')
        if c_audio:
            store_audio(c_audio, c_fn)

        field_id = str(timestamp_sec + idx + 1000)

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
            'Frequency': 'Immersion',
            'Sound': f"[sound:{c_fn}]" if c_audio else "",
            'Words_Sound': '',
            'Words_English_Sound': '',
            'Image': '',
            'Notes': 'Added automatically via gap finder immersion scan'
        }

        payload = {
            "deckName": char_deck,
            "modelName": "Chinese (Characters)",
            "fields": fields,
            "options": {"allowDuplicate": False},
            "tags": ["immersion_gap", "n1_added"]
        }

        res = req("addNote", note=payload)
        if res:
            print(f"Added! Note ID: {res}", flush=True)
            added_chars += 1
        else:
            print("Skipped or duplicate.", flush=True)

    print(f"Completed Action 3: {added_chars}/3 characters added to 'Chinese::Char'.")

    # -------------------------------------------------------------
    # STEP 3: LINK WORD CHARACTERS
    # -------------------------------------------------------------
    print("\nRunning character linking script to connect word cards with character cards...")
    base_dir = r"c:\Users\gabri\Documents\anki_helper"
    scripts_dir = os.path.join(base_dir, "scripts")
    
    os.system(f'python "{os.path.join(scripts_dir, "link_word_characters.py")}"')

    # -------------------------------------------------------------
    # STEP 4: REFRESH EXPORTS, GAP REPORT & DASHBOARD
    # -------------------------------------------------------------
    print("\nRefreshing extract, gap finder, and dashboard...")
    os.system(f'python "{os.path.join(scripts_dir, "extract_anki_data.py")}"')
    os.system(f'python "{os.path.join(scripts_dir, "gap_finder.py")}"')
    os.system(f'python "{os.path.join(scripts_dir, "generate_dashboard.py")}"')

    print("\n" + "=" * 70)
    print("  ALL ACTIONS COMPLETED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == '__main__':
    main()
