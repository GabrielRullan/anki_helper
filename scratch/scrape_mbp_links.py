import urllib.request
import re
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

req = urllib.request.Request('https://courses.mandarinblueprint.com/products/the-blueprint', headers=HEADERS)
with urllib.request.urlopen(req, timeout=15) as resp:
    html = resp.read().decode('utf-8')

hrefs = re.findall(r'href=["\']([^"\']+)["\']', html)
print(f"Total hrefs found: {len(hrefs)}")
for h in hrefs:
    if 'level' in h.lower() or 'category' in h.lower() or 'post' in h.lower() or 'blueprint' in h.lower():
        print(h)
