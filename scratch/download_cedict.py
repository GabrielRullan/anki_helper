import urllib.request
import zipfile
import io
import re
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

url = 'https://www.mdbg.net/chinese/export/cedict/cedict_1_0_ts_utf-8_mdbg.zip'
print("Downloading official CC-CEDICT from MDBG...")

req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        zip_bytes = resp.read()
        print(f"Downloaded zip file ({len(zip_bytes)} bytes). Extracting...")
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            for fn in zf.namelist():
                print("  Zip entry:", fn)
                with zf.open(fn) as f:
                    content = f.read().decode('utf-8')
                    with open('data/cedict_ts.u8', 'w', encoding='utf-8') as out:
                        out.write(content)
                    print(f"Extracted {fn} to data/cedict_ts.u8 ({len(content)} chars)")
except Exception as e:
    print("Error:", e)
