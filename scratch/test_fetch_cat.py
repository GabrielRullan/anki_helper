import urllib.request
import re
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

url = 'https://courses.mandarinblueprint.com/products/the-blueprint/categories/2148732477'
req = urllib.request.Request(url, headers=HEADERS)

try:
    with urllib.request.urlopen(req, timeout=15) as resp:
        print('Status:', resp.status)
        html = resp.read().decode('utf-8')
        print('Length:', len(html))
        posts = re.findall(r'href=["\'](/products/the-blueprint/categories/\d+/posts/\d+)["\'][^>]*>(.*?)</a>', html, re.DOTALL)
        print(f"Found {len(posts)} post links")
        for u, t in posts[:10]:
            clean_t = re.sub(r'<[^>]+>', '', t).strip()
            print(u, '->', clean_t)
except Exception as e:
    print('Error:', e)
