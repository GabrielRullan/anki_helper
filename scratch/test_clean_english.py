import re
import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')
ANKICONNECT_URL = 'http://127.0.0.1:8765'

def invoke(action, **params):
    req = urllib.request.Request(
        ANKICONNECT_URL,
        data=json.dumps({'action': action, 'version': 6, 'params': params}).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        if res.get('error'):
            raise Exception(res['error'])
        return res.get('result')

def clean_term(term):
    # Remove HTML tags
    term = re.sub(r'<[^>]+>', '', term).strip()
    # Remove variant of ... if present
    term = re.sub(r'Variant of [^\s;]+', '', term, flags=re.IGNORECASE).strip()
    # Remove leading to / a / an / (bound form)
    term = re.sub(r'^\(Bound form\)\s*', '', term, flags=re.IGNORECASE)
    term = re.sub(r'^to\s+', '', term, flags=re.IGNORECASE)
    term = re.sub(r'^(a|an)\s+', '', term, flags=re.IGNORECASE)
    # Remove parenthetical notes e.g. (playfully), (loanword), (abbr. ...)
    term = re.sub(r'\([^\)]*\)', '', term).strip()
    # Remove extra spaces/punctuation
    term = re.sub(r'\s+', ' ', term).strip(' ;,/.')
    if not term:
        return ""
    # Capitalize each word or Title Case
    words = term.split()
    capitalized_words = [w.capitalize() if not w.isupper() else w for w in words]
    return ' '.join(capitalized_words)

def format_english_definition(raw_def):
    if not raw_def:
        return ""
    # Split on ; or / or ,
    # First try splitting by ; or /
    parts = re.split(r'[;/]', raw_def)
    cleaned_terms = []
    seen = set()

    for p in parts:
        # Also split by , if part has multiple commas
        subparts = p.split(',')
        for sp in subparts:
            ct = clean_term(sp)
            if ct and ct.lower() not in seen:
                seen.add(ct.lower())
                cleaned_terms.append(ct)
                if len(cleaned_terms) >= 2:
                    break
        if len(cleaned_terms) >= 2:
            break

    if not cleaned_terms:
        # Fallback to direct clean
        fallback = clean_term(raw_def)
        return fallback if fallback else raw_def

    return '; '.join(cleaned_terms[:2])

# Test sample definitions
test_cases = [
    "overflow; swirl, ripple; to be tosssed by waves",
    "raise, lift up; tight-fisted",
    "terminate, end, finish; quit",
    "high mound; soar",
    "oppose, deviate, be contrary to",
    "whirlwind, stormy gale",
    "flourishing, thriving, abundant",
    "To tease (playfully); To entice",
    "Variant of 崑|昆[kun1]",
    "alligator, crocodile",
    "to be tosssed by waves",
    "Stump; Stake; Pile",
    "(Bound form) rib"
]

print("Testing format_english_definition function:")
for tc in test_cases:
    print(f"  BEFORE: '{tc}'")
    print(f"  AFTER:  '{format_english_definition(tc)}'\n")
