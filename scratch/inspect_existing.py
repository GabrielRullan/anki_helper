import json
import csv
import os

print("--- Checking known_words.csv ---")
kw_path = r"c:\Users\gabri\Documents\anki_helper\data\known_words.csv"
if os.path.exists(kw_path):
    with open(kw_path, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]
        print(f"known_words count: {len(lines)}")
        print("First 10 words:", lines[:10])

print("\n--- Checking anki_extract.json ---")
ae_path = r"c:\Users\gabri\Documents\anki_helper\data\anki_extract.json"
if os.path.exists(ae_path):
    with open(ae_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        if isinstance(data, dict):
            print("anki_extract keys:", list(data.keys()))
            for k in data:
                if isinstance(data[k], list):
                    print(f"Key '{k}': {len(data[k])} items")
                    if len(data[k]) > 0:
                        print(f"Sample item from '{k}':", data[k][0])
        elif isinstance(data, list):
            print(f"anki_extract list count: {len(data)}")
            print("Sample item:", data[0])

print("\n--- Checking kaishi_cards.json ---")
kc_path = r"c:\Users\gabri\Documents\anki_helper\data\kaishi_cards.json"
if os.path.exists(kc_path):
    with open(kc_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        print(f"kaishi_cards count: {len(data) if isinstance(data, list) else len(data.keys())}")
