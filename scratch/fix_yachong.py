import urllib.request
import json
import os
import re

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
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Failed: {e}")
        return None

# 1. Update Anki note
print("Updating Anki note...")
new_definitions = "<p>蚜虫 (yáchóng)</p><p>∙ pulgón / aphid</p>"
update_res = request_anki("updateNoteFields", note={
    "id": 1781016138306,
    "fields": {
        "Definitions": new_definitions
    }
})
print("Anki update result:", update_res)

# 2. Update new_words.md
print("Updating new_words.md...")
new_words_path = r"c:\Users\gabri\Documents\antigravity\anki\new_words.md"
with open(new_words_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Remove the 蚜虫 entry from ## 🟡 Pendiente de incluir
# The entry looks like:
# - 蚜虫 (_piáochóng_)
#     
#     - **Frase:** 植物有很多蚜虫的时候，放几只**瓢虫**就能把它们吃光。
#         
#     - _Pinyin:_ Zhíwù...
#         
#     - _Traducción Español:_ ...
#         
#     - _Traducción Inglés:_ ...

pattern_to_remove = r'- 蚜虫 \(_piáochóng_\)\s*\n\s*- \*\*Frase:\*\* 植物有很多蚜虫的时候，放几只\*\*瓢虫\*\*就能把它们吃光。\s*\n\s*- _Pinyin:_ Zhíwù yǒu hěnduō yáchóng de shíhòu, fàng jǐ zhī piáochóng jiù néng bǎ tāmen chīguāng\.\s*\n\s*- _Traducción Español:_ Cuando las plantas tienen muchos pulgones, soltar unas pocas mariquitas basta para que se los coman todos\.\s*\n\s*- _Traducción Inglés:_ When plants have a lot of aphids, releasing a few ladybugs is enough to eat them all up\.\s*\n?'

# Let's do a more robust find and replace
modified_content = re.sub(pattern_to_remove, '', content)

# Also let's append it to ## 🟢 Incluido en Anki
# Let's find where ## 🟢 Incluido en Anki ends or starts
incluido_header = "## 🟢 Incluido en Anki"
parts = modified_content.split(incluido_header)
header = parts[0] + incluido_header
rest = parts[1]

# We append the new line to the top of the Included list or just after the header
rest_lines = rest.splitlines()
new_line = "- **蚜虫** (yáchóng) — pulgón / aphid"

# Insert new line after the header or first empty lines
insertion_idx = 0
for idx, line in enumerate(rest_lines):
    if line.strip().startswith('-') or line.strip().startswith('*'):
        insertion_idx = idx
        break

rest_lines.insert(insertion_idx, new_line)
final_content = header + "\n" + "\n".join(rest_lines)

with open(new_words_path, 'w', encoding='utf-8') as f:
    f.write(final_content)

print("new_words.md updated successfully!")
