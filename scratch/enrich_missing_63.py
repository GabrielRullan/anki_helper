import os
import json
import re
import sys
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")
print("API_KEY present:", bool(API_KEY))

from google import genai
client = genai.Client(api_key=API_KEY)

# Load existing character notes to learn standard MBP mapping (Actor, Set, Tone-Location)
import urllib.request

def invoke(action, **params):
    req = urllib.request.Request(
        'http://127.0.0.1:8765',
        data=json.dumps({'action': action, 'version': 6, 'params': params}).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        return res.get('result')

print("Fetching sample notes to map MBP Codebook (Actors, Sets, Tone-Locations)...")
all_notes = invoke('findNotes', query='note:"Chinese Character - Double"')
sample_info = invoke('notesInfo', notes=all_notes[:300])

actors_map = {} # Initial -> Actor
sets_map = {}    # Final -> Set
locations_map = {} # Tone -> Tone-Location

for info in sample_info:
    fields = info['fields']
    init = fields.get('Initial', {}).get('value', '').strip()
    actor = fields.get('Actor', {}).get('value', '').strip()
    final = fields.get('Set', {}).get('value', '').strip()
    set_val = fields.get('Set', {}).get('value', '').strip()
    tone = fields.get('Tone', {}).get('value', '').strip()
    loc = fields.get('Tone-Location', {}).get('value', '').strip()

    if init and actor and init not in actors_map:
        actors_map[init] = actor
    if tone and loc and tone not in locations_map:
        locations_map[tone] = loc

print(f"Loaded {len(actors_map)} Actors, {len(locations_map)} Tone-Locations.")
print("Actors sample:", dict(list(actors_map.items())[:10]))
print("Locations:", locations_map)
