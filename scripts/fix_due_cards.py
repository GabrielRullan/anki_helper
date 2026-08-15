import os
import sys
import json
import urllib.request
import time
from concurrent.futures import ThreadPoolExecutor

sys.stdout.reconfigure(encoding='utf-8')

ANKICONNECT_URL = 'http://127.0.0.1:8765'

def request_anki(action, retries=5, delay=2, **params):
    payload = {"action": action, "version": 6}
    if params:
        payload["params"] = params
    
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                ANKICONNECT_URL,
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                res = json.loads(response.read().decode('utf-8'))
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

def main():
    print("=" * 70, flush=True)
    print("   RESTORING REVIEW CARD DUE DATES IN CHINESE::CHAR DECK")
    print("=" * 70, flush=True)

    cids = request_anki("findCards", query='deck:Chinese::Char')
    if not cids:
        print("Error: No cards found in Chinese::Char", flush=True)
        return

    print(f"Fetching info for {len(cids):,} cards...", flush=True)
    info = request_anki("cardsInfo", cards=cids)

    # Group review cards (type == 2) that are currently due today by interval
    by_interval = {}
    review_cards_reset = 0

    for card in info:
        # type 2 = Review card, type 0 = New card
        if card.get('type') == 2 and card.get('due') == 226:
            interval = max(1, card.get('interval', 1))
            by_interval.setdefault(interval, []).append(card['cardId'])
            review_cards_reset += 1

    print(f"Found {review_cards_reset:,} review cards that were set to due today.", flush=True)

    if not by_interval:
        print("No review cards need due date restoration.", flush=True)
        return

    print("\nRestoring review card due dates back to their future intervals...", flush=True)

    for interval, card_group in by_interval.items():
        # Set due date to interval days from today
        request_anki("setDueDate", cards=card_group, days=str(interval))

    print(f"\nSuccessfully restored {review_cards_reset:,} review cards to their interval schedules!", flush=True)
    print("=" * 70, flush=True)

if __name__ == "__main__":
    main()
