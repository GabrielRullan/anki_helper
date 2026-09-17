import os
import urllib.request
import json
import re
import csv
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

# Load CC-CEDICT lookup dictionary
pinyin_tone_map = {
    'a': ['a', 'ā', 'á', 'ǎ', 'à', 'a'],
    'e': ['e', 'ē', 'é', 'ě', 'è', 'e'],
    'i': ['i', 'ī', 'í', 'ǐ', 'ì', 'i'],
    'o': ['o', 'ō', 'ó', 'ǒ', 'ò', 'o'],
    'u': ['u', 'ū', 'ú', 'ǔ', 'ù', 'u'],
    'v': ['ü', 'ǖ', 'ǘ', 'ǚ', 'ǜ', 'ü'],
    'u:': ['ü', 'ǖ', 'ǘ', 'ǚ', 'ǜ', 'ü']
}

cedict_lookup = {}
if os.path.exists('data/cedict_ts.u8'):
    with open('data/cedict_ts.u8', 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            m = re.match(r'^(\S+)\s+(\S+)\s+\[(.*?)\]\s+/(.*)/$', line)
            if m:
                trad, simp, pyn, defs_str = m.groups()
                defs = [d.strip() for d in defs_str.split('/') if d.strip()]
                clean_defs = [d for d in defs if not d.startswith('variant of') and not d.startswith('surname ')]
                if not clean_defs:
                    clean_defs = defs
                if simp not in cedict_lookup:
                    cedict_lookup[simp] = '; '.join(clean_defs[:3])

junda_lookup = {}
if os.path.exists('data/junda_freq.csv'):
    with open('data/junda_freq.csv', 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            c = row.get('character')
            if c:
                junda_lookup[c] = row.get('definition', '')

def clean_term(term):
    term = re.sub(r'<[^>]+>', '', term).strip()
    term = re.sub(r'^\(Bound form\)\s*', '', term, flags=re.IGNORECASE)
    term = re.sub(r'^to\s+', '', term, flags=re.IGNORECASE)
    term = re.sub(r'^(a|an)\s+', '', term, flags=re.IGNORECASE)
    term = re.sub(r'\([^\)]*\)', '', term).strip()
    term = re.sub(r'\s+', ' ', term).strip(' ;,/.')
    if not term:
        return ""
    words = term.split()
    capitalized_words = [w.capitalize() if not w.isupper() else w for w in words]
    return ' '.join(capitalized_words)

def format_english_definition(raw_def):
    if not raw_def:
        return ""
    parts = re.split(r'[;/]', raw_def)
    cleaned_terms = []
    seen = set()

    for p in parts:
        subparts = p.split(',')
        for sp in subparts:
            ct = clean_term(sp)
            if ct and ct.lower() not in seen and not ct.lower().startswith('variant of'):
                seen.add(ct.lower())
                cleaned_terms.append(ct)
                if len(cleaned_terms) >= 2:
                    break
        if len(cleaned_terms) >= 2:
            break

    if not cleaned_terms:
        fallback = clean_term(raw_def)
        return fallback if fallback else raw_def

    return '; '.join(cleaned_terms[:2])

print("Querying suspended character notes...")
suspended_note_ids = invoke('findNotes', query='is:suspended note:"Chinese Character - Double"')
if not suspended_note_ids:
    suspended_note_ids = invoke('findNotes', query='is:suspended deck:"Chinese::Char"')

print(f"Total suspended character notes to process: {len(suspended_note_ids)}")

updated_count = 0
skipped_count = 0

batch_size = 300
for i in range(0, len(suspended_note_ids), batch_size):
    batch = suspended_note_ids[i:i+batch_size]
    notes_info = invoke('notesInfo', notes=batch)

    for info in notes_info:
        n_id = info['noteId']
        fields = info['fields']
        h = fields.get('Hanzi', {}).get('value', '').strip() or fields.get('Simplified', {}).get('value', '').strip()
        raw_eng = fields.get('English', {}).get('value', '').strip()

        source_def = raw_eng
        if not source_def or 'variant of' in source_def.lower():
            if h in cedict_lookup:
                source_def = cedict_lookup[h]
            elif h in junda_lookup:
                source_def = junda_lookup[h]

        new_eng = format_english_definition(source_def)

        if new_eng and new_eng != raw_eng:
            invoke('updateNoteFields', note={
                'id': n_id,
                'fields': {
                    'English': new_eng
                }
            })
            updated_count += 1
            if updated_count <= 25 or updated_count % 100 == 0:
                print(f"Updated note {n_id} ('{h}'): '{raw_eng}' -> '{new_eng}'")
        else:
            skipped_count += 1

print("\n==========================================")
print(f"FINISHED! Updated {updated_count} suspended character notes.")
print(f"Skipped (already properly formatted): {skipped_count}")
print("==========================================")
