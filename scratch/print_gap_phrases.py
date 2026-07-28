import os
import sys

# Adjust path to find local modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts')))
from sync_islands import load_learned_characters, parse_islands_file, clean_hanzi

def main():
    learned_chars = load_learned_characters()
    islands_path = os.path.join(os.path.dirname(__file__), "..", "islands.md")
    blocks = parse_islands_file(islands_path)
    
    print("MATCHING_GAPS_START")
    for idx, b in enumerate(blocks, 1):
        q_chars = clean_hanzi(b['q'])
        a_chars = clean_hanzi(b['a'])
        missing = list(set([c for c in q_chars + a_chars if c not in learned_chars]))
        if missing:
            print(f"Block: {idx}")
            print(f"Q: {b['q']}")
            print(f"QP: {b.get('q_pinyin', '')}")
            print(f"A: {b['a']}")
            print(f"AP: {b.get('a_pinyin', '')}")
            print(f"EN: {b.get('en', '')}")
            print(f"Missing: {', '.join(missing)}")
            print("-" * 50)
    print("MATCHING_GAPS_END")

if __name__ == "__main__":
    main()
