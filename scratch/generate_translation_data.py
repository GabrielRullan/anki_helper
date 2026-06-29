import os
import json
import urllib.request
import urllib.parse
import hashlib
import re
from dotenv import load_dotenv
from google import genai

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    print("Error: GOOGLE_API_KEY not found.")
    exit(1)

client = genai.Client(api_key=API_KEY)

sentences_to_process = [
    {
        "grammar_point": "趟",
        "sentence": "这趟旅程很辛苦",
        "usage": "Uso A",
        "desc_es": "Clasificador para viajes o trayectos"
    },
    {
        "grammar_point": "趟",
        "sentence": "他每星期来个一两趟",
        "usage": "Uso B",
        "desc_es": "Clasificador para indicar la cantidad de veces que se realiza un trayecto/viaje"
    },
    {
        "grammar_point": "趟",
        "sentence": "你坐那趟车，它会带你回家",
        "usage": "Uso C",
        "desc_es": "Clasificador para vehículos de transporte en un trayecto específico"
    },
    {
        "grammar_point": "为了...而",
        "sentence": "他为了工作而生活, 你为了生活而工作",
        "usage": "Uso Unico",
        "desc_es": "Indicar el propósito o motivo de una acción (para... y por tanto...)"
    },
    {
        "grammar_point": "仍然",
        "sentence": "我们仍然住在同一个地方",
        "usage": "Uso Unico",
        "desc_es": "Continuar en el mismo estado / Todavía, aún"
    },
    {
        "grammar_point": "刚 / 刚才",
        "sentence": "我刚开始准备考试，虽然考试看起来还很远，但时间过得很快。",
        "usage": "Uso Unico",
        "desc_es": "Indicar una acción ocurrida hace muy poco tiempo / Acabar de"
    }
]

print("Starting generation using Gemini...")

for item in sentences_to_process:
    # 1. Pinyin
    prompt_pinyin = f"For the Chinese sentence '{item['sentence']}', provide the Hanyu Pinyin with correct tone marks. Return ONLY the pinyin, with no other text or explanation."
    resp = client.models.generate_content(model='gemini-2.5-flash', contents=prompt_pinyin)
    item['pinyin'] = resp.text.strip().strip('"').strip("'")
    
    # 2. English translation
    prompt_en = f"Translate the following Chinese sentence into clear, natural English: '{item['sentence']}'. Return ONLY the translation, with no other text, explanation, or markdown."
    resp = client.models.generate_content(model='gemini-2.5-flash', contents=prompt_en)
    item['english'] = resp.text.strip().strip('"').strip("'")
    
    # 3. Spanish translation
    prompt_es = f"Translate the following Chinese sentence into clear, natural Spanish: '{item['sentence']}'. Return ONLY the translation, with no other text, explanation, or markdown."
    resp = client.models.generate_content(model='gemini-2.5-flash', contents=prompt_es)
    item['spanish'] = resp.text.strip().strip('"').strip("'")

    print(f"Processed: {item['sentence']}")
    print(f"  Pinyin: {item['pinyin']}")
    print(f"  English: {item['english']}")
    print(f"  Spanish: {item['spanish']}")
    print("-" * 20)

with open("scratch/generated_data.json", "w", encoding="utf-8") as f:
    json.dump(sentences_to_process, f, ensure_ascii=False, indent=2)
