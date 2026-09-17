import urllib.request
import re
import json

js_url = 'https://traverse.link/assets/index-7a55e007.js'
print("Downloading JS...")
req = urllib.request.Request(js_url, headers={'User-Agent': 'Mozilla/5.0'})
js_content = urllib.request.urlopen(req).read().decode('utf-8')
print("Downloaded. Length:", len(js_content))

# Search for word-progress component or data references
pos = js_content.find('word-progress')
if pos != -1:
    print("Found 'word-progress' at index:", pos)
    print("Context around word-progress:")
    print(js_content[max(0, pos-500):min(len(js_content), pos+1500)])

# Save js_content locally if needed for analysis
with open("scratch/index.js", "w", encoding="utf-8") as f:
    f.write(js_content)
print("Saved to scratch/index.js")
