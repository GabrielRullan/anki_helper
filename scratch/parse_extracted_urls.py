import re
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

filepath = r"C:\Users\gabri\.gemini\antigravity-ide\brain\f25e8e96-88ab-4901-8e66-09d0ed992355\browser\scratchpad_1uuthhbs.md"

if not os.path.exists(filepath):
    print("Scratchpad file not found!")
    sys.exit(1)

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Match lines like '- 萨: https://...'
mappings = re.findall(r'-\s*([\u4e00-\u9fa5])\s*:\s*(https?://\S+)', content)

print(f"Extracted {len(mappings)} Hanzi -> URL pairs from scratchpad!")

# Save to data/mbp_urls_68_88.json
url_dict = {}
for h, u in mappings:
    url_dict[h] = u.strip()

out_path = 'data/mbp_urls_68_88.json'
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(url_dict, f, ensure_ascii=False, indent=2)

print(f"Saved {len(url_dict)} unique character URLs to '{out_path}'")
