import os
import sys
sys.stdout.reconfigure(encoding='utf-8')

def main():
    appdata = os.getenv('APPDATA')
    if not appdata:
        print("APPDATA env var not found.")
        return
        
    addons_dir = os.path.join(appdata, "Anki2", "addons21")
    if not os.path.exists(addons_dir):
        print(f"Addons directory not found at {addons_dir}")
        return
        
    print(f"Addons directory: {addons_dir}")
    addons = os.listdir(addons_dir)
    print("Installed addons:")
    for addon in addons:
        addon_path = os.path.join(addons_dir, addon)
        if os.path.isdir(addon_path):
            # Try to read meta.json to find the addon name
            meta_path = os.path.join(addon_path, "meta.json")
            name = addon
            if os.path.exists(meta_path):
                try:
                    import json
                    with open(meta_path, 'r', encoding='utf-8') as f:
                        meta = json.load(f)
                        name = meta.get('name', addon)
                except Exception:
                    pass
            print(f"  - {addon}: {name}")

if __name__ == '__main__':
    main()
