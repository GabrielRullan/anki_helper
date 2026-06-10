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
            return res.get('result')
    except Exception as e:
        return None

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    models = request_anki("modelNames")
    if not models:
        print("No models found.")
        return
        
    for model in models:
        print(f"\nChecking model: {model}")
        templates = request_anki("modelTemplates", modelName=model)
        if templates:
            for t_name, t_val in templates.items():
                for part in ['Front', 'Back']:
                    content = t_val.get(part, '')
                    if '<script>' in content or 'javascript' in content.lower():
                        print(f"  Template '{t_name}' ({part}) contains script!")
                        # Print the script lines
                        lines = content.split('\n')
                        in_script = False
                        for line in lines:
                            if '<script>' in line:
                                in_script = True
                            if in_script:
                                print(f"    {line}")
                            if '</script>' in line:
                                in_script = False

if __name__ == '__main__':
    main()
