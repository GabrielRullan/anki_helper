import json
import sys
import os
import re

sys.stdout.reconfigure(encoding='utf-8')

def normalize(text):
    if not text:
        return ""
    text = text.lower().strip()
    # Remove accents/diacritics for Spanish match comparison
    replacements = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'ü': 'u', 'ñ': 'n'
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text

def main():
    if len(sys.argv) < 2:
        print("[]")
        return

    queries = sys.argv[1:]
    json_path = "data/kaishi_cards.json"
    if not os.path.exists(json_path):
        print("[]")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        cards = json.load(f)

    results = {}
    for q in queries:
        norm_q = normalize(q)
        matched_cards = []
        for card in cards:
            word = card['word']
            word_meaning = card['word_meaning']
            sentence = card['sentence']
            
            # Check direct match
            if q == word or norm_q in normalize(word_meaning):
                matched_cards.append(card)
                continue
                
            # Check if it matches grammar/sentence pattern
            if norm_q in normalize(word) or norm_q in normalize(sentence):
                matched_cards.append(card)
                
        # Limit to top 3 matches per query
        results[q] = matched_cards[:3]

    print(json.dumps(results, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
