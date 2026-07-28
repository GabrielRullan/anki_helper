import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts')))
from anki_db import AnkiConnection

def main():
    try:
        with AnkiConnection(profile_name="Gabriel") as anki:
            print("Decks:")
            for did, name in sorted(anki.get_decks().items()):
                print(f" - {name} (ID: {did})")
            
            print("\nNote Types:")
            notetypes = anki.get_notetypes()
            for ntid, info in sorted(notetypes.items()):
                print(f" - {info['name']} (ID: {ntid})")
                print("   Fields:", ", ".join(f"{ord_val}:{name}" for ord_val, name in sorted(info['fields'].items())))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
