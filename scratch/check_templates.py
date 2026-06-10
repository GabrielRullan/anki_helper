import sys
import os
import json
import urllib.request

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
    try:
        with urllib.request.urlopen(req, timeout=8) as response:
            res = json.loads(response.read().decode('utf-8'))
            if res.get('error'):
                print(f"Error: {res.get('error')}")
                return None
            return res.get('result')
    except Exception as e:
        print(f"Failed: {e}")
        return None

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    notetypes = request_anki("modelNames")
    print("Available Notetypes:", notetypes)
    
    target = 'Chinese (Characters)'
    if target in notetypes:
        print(f"\nFetching templates for: {target}")
        templates = request_anki("modelTemplates", modelName=target)
        if templates:
            for name, tmpl in templates.items():
                print("="*40)
                print(f"Template Name: {name}")
                print("-"*40)
                print("Front:")
                print(tmpl.get('Front', ''))
                print("-"*40)
                print("Back:")
                print(tmpl.get('Back', ''))
                print("="*40)
        
        styling = request_anki("modelStyling", modelName=target)
        print("\nStyling:")
        print(styling.get('css', ''))
    else:
        print(f"Notetype {target} not found.")

if __name__ == '__main__':
    main()
