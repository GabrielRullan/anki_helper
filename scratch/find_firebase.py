import re

with open('scratch/index.js', 'r', encoding='utf-8') as f:
    js = f.read()

matches = re.findall(r'projectId:[^,}]+', js)
print('projectId matches:', matches)

matches2 = re.findall(r'alley-d0944[^\s"\']*', js)
print('alley-d0944 matches:', matches2[:10])

# Search for httpsCallable region or cloud function URL
matches3 = re.findall(r'https://[a-zA-Z0-9\.\-]+\.cloudfunctions\.net/[a-zA-Z0-9_\-]+', js)
print('Cloud functions URLs:', matches3)
