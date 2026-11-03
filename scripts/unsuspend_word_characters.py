import argparse
import json
import os
import re
import sys
import urllib.request

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from anki_db import AnkiConnection

ANKI_CONNECT_URL = "http://127.0.0.1:8765"
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ACTIVE_SCENES_PATH = os.path.join(ROOT_DIR, "data", "active_scenes_merged.json")


def clean_html(text):
    if not text:
        return ""
    return re.sub(r"<[^>]+>", "", text).strip()


def invoke_ankiconnect(action, **params):
    payload = json.dumps({"action": action, "version": 6, "params": params}).encode("utf-8")
    req = urllib.request.Request(
        ANKI_CONNECT_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if data.get("error"):
        raise RuntimeError(f"AnkiConnect error ({action}): {data['error']}")
    return data.get("result")


def is_cjk(ch):
    cp = ord(ch)
    return (0x4E00 <= cp <= 0x9FFF) or (0x3400 <= cp <= 0x4DBF)


def load_regenerated_nids():
    if not os.path.exists(ACTIVE_SCENES_PATH):
        return set()
    try:
        with open(ACTIVE_SCENES_PATH, "r", encoding="utf-8") as f:
            items = json.load(f)
        return {int(x["nid"]) for x in items if "nid" in x}
    except Exception:
        return set()


def find_suspended_word_characters(profile_name="Main", active_words_only=False):
    """
    Scans Chinese::Words and Chinese::Char to find any character cards that are
    currently suspended (queue == -1) whose Hanzi appears in a Word card.
    """
    regenerated_nids = load_regenerated_nids()

    with AnkiConnection(profile_name=profile_name) as anki:
        char_deck = anki.best_match_deck(
            ["Chinese::Char", "Chinese\x1fChar", "Chinese::Characters", "Chinese\x1fCharacters", "Characters"]
        )
        word_deck = anki.best_match_deck(
            ["Chinese::Words", "Chinese\x1fWords", "Words"]
        )

        char_notes = anki.get_notes_in_deck(char_deck)
        word_notes = anki.get_notes_in_deck(word_deck)

        cur = anki.conn.cursor()
        decks = anki.get_decks()
        char_did = [d for d, name in decks.items() if name == char_deck][0]
        word_did = [d for d, name in decks.items() if name == word_deck][0]

        cur.execute(
            """
            SELECT c.id, c.nid, c.queue, c.type, c.flags
            FROM cards c
            WHERE c.did = ? OR c.odid = ?
            """,
            (char_did, char_did),
        )
        char_card_rows = cur.fetchall()

        cur.execute(
            """
            SELECT c.id, c.nid, c.queue
            FROM cards c
            WHERE c.did = ? OR c.odid = ?
            """,
            (word_did, word_did),
        )
        word_card_rows = cur.fetchall()

    word_nid_suspended = {}
    for cid, nid, queue in word_card_rows:
        word_nid_suspended.setdefault(nid, []).append(queue == -1)

    # Map each CJK character to the list of words in Chinese::Words containing it
    word_char_map = {}
    for wn in word_notes:
        nid = wn["id"]
        if active_words_only and all(word_nid_suspended.get(nid, [False])):
            continue
        word_text = clean_html(wn["fields"].get("Word", ""))
        if not word_text:
            continue
        for ch in set(word_text):
            if is_cjk(ch):
                if word_text not in word_char_map.setdefault(ch, []):
                    word_char_map[ch].append(word_text)

    nid_to_cards = {}
    for cid, nid, queue, ctype, flags in char_card_rows:
        nid_to_cards.setdefault(nid, []).append(
            {
                "cid": cid,
                "queue": queue,
                "type": ctype,
                "flags": flags & 7,
            }
        )

    matches = []
    for cn in char_notes:
        nid = cn["id"]
        cards = nid_to_cards.get(nid, [])
        # queue == -1 means suspended in Anki (whereas -2 / -3 are buried)
        suspended_cards = [c for c in cards if c["queue"] == -1]
        if not suspended_cards:
            continue

        hanzi = clean_html(cn["fields"].get("Hanzi", ""))
        simplified = clean_html(cn["fields"].get("Simplified", ""))
        traditional = clean_html(cn["fields"].get("Traditional", ""))

        matched_words = []
        for candidate in (hanzi, simplified, traditional):
            if candidate:
                for w in word_char_map.get(candidate, []):
                    if w not in matched_words:
                        matched_words.append(w)

        if matched_words:
            tags = cn["tags"]
            needs_regen_img = ("mbp_fixed" in tags and nid not in regenerated_nids) or (
                "needs_image_update" in tags
            )
            matches.append(
                {
                    "nid": nid,
                    "id_field": clean_html(cn["fields"].get("ID", "")),
                    "hanzi": hanzi,
                    "pinyin": clean_html(cn["fields"].get("Pinyin", "")),
                    "english": clean_html(cn["fields"].get("English", "")),
                    "actor": clean_html(cn["fields"].get("Actor", "")),
                    "set": clean_html(cn["fields"].get("Set", "")),
                    "tone_loc": clean_html(
                        cn["fields"].get("Tone-Location", cn["fields"].get("ToneLocation", ""))
                    ),
                    "components": clean_html(cn["fields"].get("Components", "")),
                    "scene": clean_html(cn["fields"].get("Scene", "")),
                    "image": cn["fields"].get("Image", "").strip(),
                    "tags": tags,
                    "needs_regen_img": needs_regen_img,
                    "words": matched_words,
                    "cards": suspended_cards,
                }
            )

    return matches


def main():
    parser = argparse.ArgumentParser(
        description="Find and unsuspend any Chinese::Char card whose Hanzi appears in a Chinese::Words card."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only list matching suspended character cards without unsuspending them.",
    )
    parser.add_argument(
        "--active-words-only",
        action="store_true",
        help="Only match characters from non-suspended word cards in Chinese::Words.",
    )
    parser.add_argument(
        "--clear-red-flag",
        action="store_true",
        help="Also clear Red Flag (flag 1) on unsuspended character cards.",
    )
    parser.add_argument(
        "--profile",
        default="Main",
        help="Anki profile name (default: Main).",
    )
    args = parser.parse_args()

    matches = find_suspended_word_characters(
        profile_name=args.profile,
        active_words_only=args.active_words_only,
    )

    if not matches:
        print("No suspended character cards found whose Hanzi appears in Chinese::Words.")
        return

    all_card_ids = []
    red_flagged_card_ids = []
    needs_attention = []
    print(f"Found {len(matches)} suspended character note(s) appearing in Chinese::Words:\n")
    for idx, item in enumerate(matches, 1):
        cids = [c["cid"] for c in item["cards"]]
        flags = [c["flags"] for c in item["cards"]]
        all_card_ids.extend(cids)
        for c in item["cards"]:
            if c["flags"] == 1:
                red_flagged_card_ids.append(c["cid"])
        has_scene = "yes" if item["scene"] else "MISSING"
        has_img = "yes" if item["image"] else "MISSING"
        regen_str = " [NEEDS_MBP_IMAGE_REGEN]" if item["needs_regen_img"] else ""
        if not item["scene"] or not item["image"] or item["needs_regen_img"]:
            needs_attention.append(item)
        print(
            f"  {idx}. {item['hanzi']} ({item['pinyin']}) - {item['english']} "
            f"[nid={item['nid']}, cids={cids}, flags={flags}, scene={has_scene}, img={has_img}]{regen_str}"
        )
        print(f"     Words: {', '.join(item['words'])}")
        if item["scene"]:
            print(f"     Scene: {item['scene']}")

    if args.dry_run:
        print(f"\n[DRY RUN] Would unsuspend {len(all_card_ids)} card(s) across {len(matches)} note(s).")
        if needs_attention:
            print(
                f"[ATTENTION] {len(needs_attention)} note(s) need scene/image generation or MBP image refresh: "
                f"{[x['hanzi'] for x in needs_attention]}"
            )
        return

    print(f"\nUnsuspending {len(all_card_ids)} card(s) via AnkiConnect...")
    invoke_ankiconnect("unsuspend", cards=all_card_ids)
    print(f"Successfully unsuspended {len(all_card_ids)} card(s) in Anki!")

    if args.clear_red_flag and red_flagged_card_ids:
        print(f"Clearing Red Flag (flag:1) on {len(red_flagged_card_ids)} card(s)...")
        actions = [
            {
                "action": "setSpecificValueOfCard",
                "params": {"card": cid, "keys": ["flags"], "newValues": [0]},
            }
            for cid in red_flagged_card_ids
        ]
        invoke_ankiconnect("multi", actions=actions)
        print(f"Cleared Red Flag on {len(red_flagged_card_ids)} card(s).")

    if needs_attention:
        print(
            f"\n[ATTENTION] {len(needs_attention)} newly unsuspended note(s) need scene/image generation or MBP image refresh: "
            f"{[x['hanzi'] for x in needs_attention]}"
        )


if __name__ == "__main__":
    main()
