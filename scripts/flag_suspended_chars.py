import json
import urllib.request
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath('scripts'))
from extract_anki_data import clean_html

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
    with urllib.request.urlopen(req, timeout=15) as response:
        res = json.loads(response.read().decode('utf-8'))
        if res.get('error'):
            raise RuntimeError(f"AnkiConnect error on {action}: {res['error']}")
        return res.get('result')

def main():
    char_nids = request_anki("findNotes", query='deck:"Chinese::Char"')
    word_nids = request_anki("findNotes", query='deck:"Chinese::Words"')
    char_notes = request_anki("notesInfo", notes=char_nids)
    word_notes = request_anki("notesInfo", notes=word_nids)

    all_char_cids = []
    for n in char_notes:
        all_char_cids.extend(n.get('cards', []))

    suspended_flags = request_anki("areSuspended", cards=all_char_cids)
    cid_to_susp = dict(zip(all_char_cids, suspended_flags))

    word_char_map = {}
    for wn in word_notes:
        w_raw = wn.get('fields', {}).get('Word', {}).get('value', '')
        w = clean_html(w_raw)
        for ch in set(w):
            if '\u4e00' <= ch <= '\u9fff':
                word_char_map.setdefault(ch, []).append(w)

    matched = []
    cids_to_flag = []

    for cn in char_notes:
        cids = cn.get('cards', [])
        susp_cids = [c for c in cids if cid_to_susp.get(c, False)]
        if not susp_cids:
            continue
        h = cn.get('fields', {}).get('Hanzi', {}).get('value', '').strip()
        simp = cn.get('fields', {}).get('Simplified', {}).get('value', '').strip()
        words = list(word_char_map.get(h, []))
        if simp and simp != h:
            for item in word_char_map.get(simp, []):
                if item not in words:
                    words.append(item)
        if words:
            pinyin = cn.get('fields', {}).get('Pinyin', {}).get('value', '').strip()
            english = cn.get('fields', {}).get('English', {}).get('value', '').strip()
            matched.append({
                'nid': cn['noteId'],
                'hanzi': h,
                'simplified': simp,
                'pinyin': pinyin,
                'english': english,
                'tags': cn.get('tags', []),
                'total_cards': len(cids),
                'susp_cards': len(susp_cids),
                'susp_cids': susp_cids,
                'words': words
            })
            cids_to_flag.extend(susp_cids)

    # Flag all suspended cards of matched character notes with Red Flag (1) using multi
    actions = [
        {
            "action": "setSpecificValueOfCard",
            "params": {
                "card": cid,
                "keys": ["flags"],
                "newValues": [1]
            }
        }
        for cid in cids_to_flag
    ]
    res = request_anki("multi", actions=actions)
    flagged_now = request_anki("findCards", query='deck:"Chinese::Char" flag:1')
    print(f"Flagged {len(cids_to_flag)} suspended cards across {len(matched)} character notes.")
    print(f"Verified via Anki query `deck:\"Chinese::Char\" flag:1`: {len(flagged_now)} cards.")
    print("\n--- RESULTS ---")
    for idx, item in enumerate(matched, 1):
        status = "Fully suspended" if item['susp_cards'] == item['total_cards'] else f"Partially suspended ({item['susp_cards']}/{item['total_cards']} cards)"
        words_str = ", ".join(item['words'])
        print(f"{idx}. {item['hanzi']} ({item['pinyin']}) - {item['english']} | {status} | Words: {words_str}")

if __name__ == "__main__":
    main()
