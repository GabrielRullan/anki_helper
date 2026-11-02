import sys
import os
import json
import re

sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from anki_db import AnkiConnection

with AnkiConnection(profile_name="Main") as anki:
    decks = anki.get_decks()
    for did, dname in decks.items():
        notes = anki.get_notes_in_deck(dname)
        prop_mentions = 0
        derived_mentions = 0
        comp_links = 0
        for n in notes:
            for fname, fval in n['fields'].items():
                if 'prop' in fval.lower() and ('nid' in fval.lower() or 'chinese' in fval.lower()):
                    prop_mentions += 1
                if 'derived character' in fval.lower():
                    derived_mentions += 1
                if fname.lower() == 'components' and '|nid' in fval:
                    comp_links += 1
        print(f"Deck '{dname}' ({len(notes)} notes):")
        print(f"  prop mentions in links: {prop_mentions}")
        print(f"  derived character mentions: {derived_mentions}")
        print(f"  components field with links: {comp_links}")
