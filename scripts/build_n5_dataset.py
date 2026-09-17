import json
import os
import sys
import time
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv()

from google import genai
from google.genai import types

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
output_path = "data/jlpt_n5_vocab.json"

categories_prompts = [
    ("Verbos", "Provide all official JLPT N5 verbs (Godan, Ichidan, and irregular verbs like する, 来る). Expected ~110-120 verbs."),
    ("Adjetivos", "Provide all official JLPT N5 i-adjectives and na-adjectives (e.g. 大きい, 小さい, 新しい, 高い, 安い, 綺麗, 静か, 有名, 元気, etc.). Expected ~50-60 adjectives."),
    ("Katakana_y_Tiempo", "Provide all official JLPT N5 katakana loanwords (e.g. パン, テレビ, ラジオ, テーブル, ナイフ, シャツ, etc.) and time/calendar words (days of week, relative days, months, counters). Expected ~100-120 words."),
    ("Sustantivos_Vida", "Provide official JLPT N5 nouns related to people/family (父, 母, 友達, 先生, 学生, etc.), places/buildings (学校, 部屋, 病院, 駅, 庭, etc.), transportation (車, 電車, バス, 自転車, etc.), food/drink (水, お茶, ご飯, 肉, 魚, 野菜, etc.). Expected ~150 words."),
    ("Sustantivos_Objetos_Naturaleza", "Provide official JLPT N5 nouns related to nature/weather (雨, 雪, 空, 山, 川, 花, 木, etc.), clothing/body (服, 靴, 帽子, 手, 目, 口, etc.), everyday objects/study (本, 辞書, 鉛筆, 紙, 時計, 電話, 傘, 財布, etc.), and basic adverbs/question words (どこ, だれ, いつ, なに, とても, たくさん, 少し, もう, まだ, etc.). Expected ~150 words.")
]

all_vocab = []
seen_words = set()

for cat_name, cat_desc in categories_prompts:
    print(f"Fetching category: {cat_name}...")
    prompt = f"""
You are an expert Japanese lexicographer.
{cat_desc}

Return a valid JSON array where each item has:
- "word": standard written Japanese (Kanji where standard, or Kana)
- "reading": hiragana (or katakana for loanwords)
- "meaning": Spanish translation
- "category": high level category (e.g. "Verbo", "Adjetivo", "Sustantivo", "Katakana", "Adverbio / Expresión")

Return ONLY the JSON array.
"""
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        items = json.loads(response.text)
        print(f"  Got {len(items)} items for {cat_name}")
        for it in items:
            w = it.get("word", "").strip()
            if w and w not in seen_words:
                seen_words.add(w)
                all_vocab.append(it)
    except Exception as e:
        print(f"  Error on {cat_name}: {e}")
    time.sleep(1)

print(f"\nTotal collected JLPT N5 vocabulary words: {len(all_vocab)}")

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(all_vocab, f, ensure_ascii=False, indent=2)

print(f"Successfully saved complete N5 dataset to {output_path}!")
