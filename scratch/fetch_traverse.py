import urllib.request
import re

url = 'https://traverse.link/Mandarin_Blueprint/word-progress/?level=68'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
html = urllib.request.urlopen(req).read().decode('utf-8')
print('HTML length:', len(html))
js_files = re.findall(r'src=["\'](/assets/[^"\']+)["\']', html)
print('JS files:', js_files)
for js in js_files:
    js_url = 'https://traverse.link' + js
    print('Fetching JS:', js_url)
    req_js = urllib.request.Request(js_url, headers={'User-Agent': 'Mozilla/5.0'})
    js_content = urllib.request.urlopen(req_js).read().decode('utf-8')
    print(f'JS {js} length: {len(js_content)}')
    # Check if there are word data or JSON files referenced inside the JS
    json_matches = re.findall(r'["\']([^"\']+\.json)["\']', js_content)
    print(f'JSON matches in {js}:', json_matches[:10])
    # Search for firebase or data URLs
    data_urls = re.findall(r'https://[^\s"\']+', js_content)
    firebase_urls = [u for u in data_urls if 'firebase' in u or 'storage' in u or 'traverse' in u or 'json' in u or 'api' in u]
    print(f'Firebase/API URLs in {js}:', firebase_urls[:20])
