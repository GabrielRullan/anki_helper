import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard.html', 'r', encoding='utf-8') as f:
    html = f.read()

print("dashboard.html length:", len(html))

# Find script tag in html and test compiling it or checking syntax
script_matches = re.findall(r'<script>(.*?)</script>', html, re.DOTALL)
print(f"Found {len(script_matches)} script tags.")

for idx, s in enumerate(script_matches):
    print(f"Script {idx} length: {len(s)}")

# Search around line 210166 or string literals in script
lines = html.splitlines()
print(f"Total lines in dashboard.html: {len(lines)}")
