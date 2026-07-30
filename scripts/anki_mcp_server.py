import os
import sys
import json
import re
import urllib.request
import urllib.parse
import time
import traceback
from dotenv import load_dotenv

# Ensure stdout uses UTF-8 encoding
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Load environment
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")
ANKICONNECT_URL = 'http://127.0.0.1:8765'

# Initialize Gemini Client if key available
client = None
if API_KEY and API_KEY != "YOUR_API_KEY_HERE":
    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=API_KEY)
    except Exception as e:
        print(f"Error initializing Gemini client: {e}", file=sys.stderr)

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
        with urllib.request.urlopen(req, timeout=15) as response:
            res = json.loads(response.read().decode('utf-8'))
            if res.get('error'):
                raise Exception(res.get('error'))
            return res.get('result')
    except Exception as e:
        raise Exception(f"AnkiConnect Request Failed: {e}")

# Tool Handlers

def handle_list_decks(arguments):
    try:
        decks = request_anki("deckNames")
        return {"content": [{"type": "text", "text": json.dumps(decks, ensure_ascii=False, indent=2)}]}
    except Exception as e:
        return {"isError": True, "content": [{"type": "text", "text": f"Error: {str(e)}"}]}

def handle_get_notes(arguments):
    deck_name = arguments.get("deckName")
    if not deck_name:
        return {"isError": True, "content": [{"type": "text", "text": "Missing 'deckName' argument"}]}
    
    try:
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from anki_db import AnkiConnection
        with AnkiConnection() as anki:
            notes = anki.get_notes_in_deck(deck_name)
        return {"content": [{"type": "text", "text": json.dumps(notes, ensure_ascii=False, indent=2)}]}
    except Exception as e:
        return {"isError": True, "content": [{"type": "text", "text": f"Error: {str(e)}"}]}

def handle_add_note(arguments):
    deck_name = arguments.get("deckName")
    model_name = arguments.get("modelName")
    fields = arguments.get("fields")
    tags = arguments.get("tags", [])
    
    if not deck_name or not model_name or not fields:
        return {"isError": True, "content": [{"type": "text", "text": "Missing required arguments: deckName, modelName, or fields"}]}
    
    payload = {
        "deckName": deck_name,
        "modelName": model_name,
        "fields": fields,
        "options": {
            "allowDuplicate": False
        },
        "tags": tags
    }
    try:
        note_id = request_anki("addNote", note=payload)
        return {"content": [{"type": "text", "text": f"Successfully created note with ID {note_id}"}]}
    except Exception as e:
        return {"isError": True, "content": [{"type": "text", "text": f"Error adding note: {str(e)}"}]}

def handle_store_media_file(arguments):
    filename = arguments.get("filename")
    file_path = arguments.get("filePath")
    if not filename or not file_path:
        return {"isError": True, "content": [{"type": "text", "text": "Missing 'filename' or 'filePath' argument"}]}
    
    try:
        res = request_anki("storeMediaFile", filename=filename, path=os.path.abspath(file_path))
        return {"content": [{"type": "text", "text": f"Successfully stored media file '{filename}': {res}"}]}
    except Exception as e:
        return {"isError": True, "content": [{"type": "text", "text": f"Error storing media file: {str(e)}"}]}

def handle_generate_tts_media(arguments):
    text = arguments.get("text")
    lang = arguments.get("lang")
    filename = arguments.get("filename")
    
    if not text or not lang or not filename:
        return {"isError": True, "content": [{"type": "text", "text": "Missing text, lang, or filename arguments"}]}
    
    # Save to temp directory first
    temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp")
    os.makedirs(temp_dir, exist_ok=True)
    local_path = os.path.join(temp_dir, filename)
    
    try:
        # Translate language code mapping
        if lang.lower() == 'chinese' or lang.lower() == 'zh':
            lang_code = 'zh-CN'
        elif lang.lower() == 'japanese' or lang.lower() == 'ja':
            lang_code = 'ja'
        else:
            lang_code = lang
            
        # Try gTTS
        from gtts import gTTS
        tts = gTTS(text=text, lang=lang_code)
        tts.save(local_path)
        
        # Store in Anki
        request_anki("storeMediaFile", filename=filename, path=os.path.abspath(local_path))
        
        # Clean up local temp file
        if os.path.exists(local_path):
            os.remove(local_path)
            
        return {"content": [{"type": "text", "text": f"[sound:{filename}]"}]}
    except Exception as e:
        # Fallback to direct HTTP download if gTTS fails
        try:
            url = "https://translate.google.com/translate_tts"
            params = {
                'ie': 'UTF-8',
                'tl': 'zh-CN' if lang.lower() in ('chinese', 'zh') else ('ja' if lang.lower() in ('japanese', 'ja') else lang),
                'client': 'tw-ob',
                'q': text
            }
            query_string = urllib.parse.urlencode(params)
            full_url = f"{url}?{query_string}"
            req = urllib.request.Request(full_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                with open(local_path, "wb") as f:
                    f.write(response.read())
            
            request_anki("storeMediaFile", filename=filename, path=os.path.abspath(local_path))
            if os.path.exists(local_path):
                os.remove(local_path)
            return {"content": [{"type": "text", "text": f"[sound:{filename}]"}]}
        except Exception as e2:
            return {"isError": True, "content": [{"type": "text", "text": f"TTS generation failed: {str(e)} / {str(e2)}"}]}

def handle_generate_illustration_media(arguments):
    word = arguments.get("word")
    prompt_text = arguments.get("prompt")
    filename = arguments.get("filename")
    
    if not word or not prompt_text or not filename:
        return {"isError": True, "content": [{"type": "text", "text": "Missing word, prompt, or filename arguments"}]}
        
    if not client:
        return {"isError": True, "content": [{"type": "text", "text": "Gemini client not initialized. Check GOOGLE_API_KEY in .env."}]}
        
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "imagenes_vocabulario")
    os.makedirs(output_dir, exist_ok=True)
    local_path = os.path.join(output_dir, f"{word}.png")
    
    MODELS_TO_TRY = [
        'imagen-4.0-generate-001',
        'imagen-4.0-fast-generate-001',
        'imagen-4.0-ultra-generate-001'
    ]
    
    image_bytes = None
    last_err = ""
    
    for model_id in MODELS_TO_TRY:
        for attempt in range(2):
            try:
                response = client.models.generate_images(
                    model=model_id,
                    prompt=prompt_text,
                    config=types.GenerateImagesConfig(
                        number_of_images=1,
                        output_mime_type="image/png",
                        aspect_ratio="1:1"
                    )
                )
                if response and response.generated_images:
                    image_bytes = response.generated_images[0].image.image_bytes
                    break
            except Exception as e:
                last_err = str(e)
                if "429" in last_err or "RESOURCE_EXHAUSTED" in last_err:
                    time.sleep(5)
                else:
                    break
        if image_bytes:
            break
            
    if not image_bytes:
        return {"isError": True, "content": [{"type": "text", "text": f"Failed to generate image: {last_err}"}]}
        
    try:
        with open(local_path, "wb") as f:
            f.write(image_bytes)
            
        # Store in Anki
        request_anki("storeMediaFile", filename=filename, path=os.path.abspath(local_path))
        return {"content": [{"type": "text", "text": f'<img src="{filename}">'}]}
    except Exception as e:
        return {"isError": True, "content": [{"type": "text", "text": f"Error storing image: {str(e)}"}]}

def handle_parse_feed_file(arguments):
    file_path = arguments.get("filePath")
    language = arguments.get("language")
    
    if not file_path or not language:
        return {"isError": True, "content": [{"type": "text", "text": "Missing filePath or language"}]}
        
    if not os.path.exists(file_path):
        return {"isError": True, "content": [{"type": "text", "text": f"File not found: {file_path}"}]}
        
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if language == "chinese":
            # Split using new_words.md standard parser
            try:
                parts = content.split('## 🟡 Pendiente de incluir')
                pendiente_section = parts[-1].split('## 🔴 Suelto')[0]
            except IndexError:
                return {"isError": True, "content": [{"type": "text", "text": "Missing '## 🟡 Pendiente de incluir' or '## 🔴 Suelto' headers"}]}
                
            items = []
            current_item = None
            for line in pendiente_section.splitlines():
                line_stripped = line.strip()
                if not line_stripped:
                    continue
                    
                root_match = re.match(r'^[-*]\s+(?:\*\*)?([^*()]+?)(?:\*\*)?\s*\(([^)]+)\)(?:\s*(?:—|-)\s*(.+))?', line)
                if root_match:
                    if current_item:
                        items.append(current_item)
                    word = root_match.group(1).strip()
                    pinyin = root_match.group(2).strip().replace('_', '').replace('*', '').strip()
                    translation = root_match.group(3).strip() if root_match.group(3) else ""
                    current_item = {
                        'word': word,
                        'pinyin': pinyin,
                        'translation': translation,
                        'frase': "",
                        'traduccion': "",
                        'desc': "",
                        'prompt': "",
                        'orig_line': line.strip()
                    }
                    continue
                    
                if current_item:
                    frase_match = re.match(r'^\s*[-*]\s*(?:\*\*|\*|_|__)Frase:(?:\*\*|\*|_|__)\s*(.+)', line)
                    if frase_match:
                        current_item['frase'] = frase_match.group(1).strip()
                        continue
                        
                    traduccion_es_match = re.match(r'^\s*[-*]\s*(?:\*\*|\*|_|__)Traducción Español:(?:\*\*|\*|_|__)\s*(.+)', line)
                    if traduccion_es_match:
                        current_item['traduccion'] = traduccion_es_match.group(1).strip()
                        continue
                        
                    traduccion_generic_match = re.match(r'^\s*[-*]\s*(?:\*\*|\*|_|__)Traducción:(?:\*\*|\*|_|__)\s*(.+)', line)
                    if traduccion_generic_match and not current_item['traduccion']:
                        current_item['traduccion'] = traduccion_generic_match.group(1).strip()
                        continue

                    desc_match = re.match(r'^\s*[-*]\s*(?:\*\*|\*|_|__)Descripción:(?:\*\*|\*|_|__)\s*(.+)', line)
                    if desc_match:
                        current_item['desc'] = desc_match.group(1).strip()
                        continue
                        
                    prompt_match = re.match(r'^\s*[-*]\s*(?:\*\*|\*|_|__)Prompt:(?:\*\*|\*|_|__)\s*(.+)', line)
                    if prompt_match:
                        current_item['prompt'] = prompt_match.group(1).strip()
                        continue
            if current_item:
                items.append(current_item)
            return {"content": [{"type": "text", "text": json.dumps(items, ensure_ascii=False, indent=2)}]}
            
        elif language == "japanese":
            # Parse Words and Grammar points sections from Japanese file
            words_section = ""
            grammar_section = ""
            
            # Split by "4. Words" and "5. Grammar Points" or similar
            parts = re.split(r'(?:^|\n)(?:\d+\.|\#+)\s*Words', content, flags=re.IGNORECASE)
            if len(parts) > 1:
                subparts = re.split(r'(?:^|\n)(?:\d+\.|\#+)\s*Grammar\s*Points', parts[1], flags=re.IGNORECASE)
                words_section = subparts[0]
                if len(subparts) > 1:
                    grammar_section = subparts[1]
            else:
                parts_grammar = re.split(r'(?:^|\n)(?:\d+\.|\#+)\s*Grammar\s*Points', content, flags=re.IGNORECASE)
                if len(parts_grammar) > 1:
                    grammar_section = parts_grammar[1]
                    
            words = []
            for line in words_section.splitlines():
                line = line.strip()
                if line.startswith('-') or line.startswith('*'):
                    w = re.sub(r'^[-*]\s*', '', line).strip()
                    if w:
                        words.append({'type': 'vocab', 'item': w})
                        
            grammar_points = []
            for line in grammar_section.splitlines():
                line = line.strip()
                if line.startswith('-') or line.startswith('*'):
                    gp = re.sub(r'^[-*]\s*', '', line).strip()
                    if gp:
                        grammar_points.append({'type': 'grammar', 'item': gp})
                        
            return {"content": [{"type": "text", "text": json.dumps(words + grammar_points, ensure_ascii=False, indent=2)}]}
            
    except Exception as e:
        return {"isError": True, "content": [{"type": "text", "text": f"Error parsing feed: {str(e)}"}]}

def handle_update_feed_file(arguments):
    file_path = arguments.get("filePath")
    language = arguments.get("language")
    success_items = arguments.get("successItems", [])
    
    if not file_path or not language or not success_items:
        return {"isError": True, "content": [{"type": "text", "text": "Missing filePath, language, or successItems"}]}
        
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if language == "chinese":
            # Moves Chinese success items to Included
            header = content.split('## 🟢 Incluido en Anki')[0].rstrip()
            incluido_part = content.split('## 🟢 Incluido en Anki')[1].split('## 🟡 Pendiente de incluir')[0].strip()
            
            success_set = {x['word'] for x in success_items}
            new_incluido_part = incluido_part
            if new_incluido_part:
                new_incluido_part += "\n"
                
            for item in success_items:
                tags_part = ""
                if 'orig_line' in item and '#' in item['orig_line']:
                    tags = re.findall(r'#\w+', item['orig_line'])
                    if tags:
                        tags_part = " " + " ".join(tags)
                new_incluido_part += f"- **{item['word']}** ({item['pinyin']}) — {item['translation']}{tags_part}\n"
                
            all_pending = json.loads(handle_parse_feed_file({"filePath": file_path, "language": "chinese"})["content"][0]["text"])
            remaining_pending = [x for x in all_pending if x['word'] not in success_set]
            
            pendiente_section = "\n\n## 🟡 Pendiente de incluir\n*Aquí van las palabras en transición antes de añadirlas a Anki. Cada una debe incluir traducción y una frase memorable:*\n"
            for item in remaining_pending:
                w, p, t = item['word'], item['pinyin'], item.get('translation', '')
                f, tr = item.get('frase', ''), item.get('traduccion', '')
                d, pr = item.get('desc', ''), item.get('prompt', '')
                
                pendiente_section += f"- **{w}** ({p})"
                if t:
                    pendiente_section += f" — {t}"
                pendiente_section += "\n"
                if f:
                    pendiente_section += f"    - **Frase:** {f}\n"
                if tr:
                    pendiente_section += f"    - _Traducción Español:_ {tr}\n"
                if d:
                    pendiente_section += f"    - **Descripción:** {d}\n"
                if pr:
                    pendiente_section += f"    - **Prompt:** {pr}\n"
                    
            suelto_part = content.split('## 🔴 Suelto')[1].strip()
            
            final_content = (
                header + 
                "\n\n## 🟢 Incluido en Anki\n" + new_incluido_part.strip() + "\n" +
                pendiente_section +
                "\n## 🔴 Suelto\n*Palabras en caracteres chinos listas para estudio, con su pronunciación, significado y etiquetas de Obsidian:\n" +
                suelto_part
            )
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(final_content)
                
            return {"content": [{"type": "text", "text": "Successfully updated Chinese feed file"}]}
            
        elif language == "japanese":
            # For Japanese feed, we can prepend successfully created cards to a "## 3. Included in Anki" section
            # or remove the processed lines from Words / Grammar Points
            success_orig_set = {x['original'] for x in success_items}
            
            lines = content.splitlines()
            new_lines = []
            for line in lines:
                stripped = line.strip()
                if stripped.startswith('-') or stripped.startswith('*'):
                    item_text = re.sub(r'^[-*]\s*', '', stripped).strip()
                    if item_text in success_orig_set:
                        # Skip this line (removed since it was imported)
                        continue
                new_lines.append(line)
                
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(new_lines) + "\n")
                
            return {"content": [{"type": "text", "text": f"Successfully removed {len(success_orig_set)} items from Japanese feed file"}]}
            
    except Exception as e:
        return {"isError": True, "content": [{"type": "text", "text": f"Error updating feed file: {str(e)}"}]}

def handle_extract_anki_data(arguments):
    try:
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from extract_anki_data import main as run_extract
        run_extract()
        return {"content": [{"type": "text", "text": "Database extraction run successfully. Cached in data/anki_extract.json"}]}
    except Exception as e:
        return {"isError": True, "content": [{"type": "text", "text": f"Error running database extraction: {str(e)}"}]}

def handle_generate_dashboard(arguments):
    try:
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from generate_dashboard import generate_dashboard
        generate_dashboard()
        return {"content": [{"type": "text", "text": "Dashboard.html updated successfully."}]}
    except Exception as e:
        return {"isError": True, "content": [{"type": "text", "text": f"Error generating dashboard: {str(e)}"}]}

def handle_export_anki_data(arguments):
    try:
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from export_anki_data_folder import main as run_export
        run_export()
        return {"content": [{"type": "text", "text": "Successfully backed up Anki database and refreshed deck statistics in the anki_data/ directory."}]}
    except Exception as e:
        return {"isError": True, "content": [{"type": "text", "text": f"Error running database export: {str(e)}"}]}

# Map of tool names to functions
TOOLS = {
    "list_decks": {
        "description": "List all Anki decks.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        },
        "handler": handle_list_decks
    },
    "get_notes": {
        "description": "Retrieve notes in a specific Anki deck.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "deckName": {"type": "string", "description": "The name of the deck (e.g. 'Chinese::Words')"}
            },
            "required": ["deckName"]
        },
        "handler": handle_get_notes
    },
    "add_note": {
        "description": "Add a new note/card to Anki via AnkiConnect.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "deckName": {"type": "string", "description": "The deck name (e.g. 'Chinese::Words')"},
                "modelName": {"type": "string", "description": "The card model/notetype name (e.g. 'Migaku Word')"},
                "fields": {
                    "type": "object",
                    "description": "Key-value dictionary mapping card fields to HTML/text content"
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional tags to attach to the note"
                }
            },
            "required": ["deckName", "modelName", "fields"]
        },
        "handler": handle_add_note
    },
    "store_media_file": {
        "description": "Store a local file (image or audio) into the Anki media folder.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "Target filename in Anki (e.g. 'word.mp3')"},
                "filePath": {"type": "string", "description": "Absolute local path to the media file"}
            },
            "required": ["filename", "filePath"]
        },
        "handler": handle_store_media_file
    },
    "generate_tts_media": {
        "description": "Generate a TTS sound file using gTTS (or Google Translate fallback) and store it in Anki. Returns Anki [sound:filename] format.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "The word or sentence text to read"},
                "lang": {"type": "string", "description": "Language code (e.g. 'zh-CN' or 'ja')"},
                "filename": {"type": "string", "description": "Desired Anki media filename (e.g. 'word_tts.mp3')"}
            },
            "required": ["text", "lang", "filename"]
        },
        "handler": handle_generate_tts_media
    },
    "generate_illustration_media": {
        "description": "Generate a minimalist flashcard illustration using Gemini/Imagen and store it in Anki. Returns Anki <img> tag.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "word": {"type": "string", "description": "The target vocabulary word for filename matching"},
                "prompt": {"type": "string", "description": "Detailed visual description prompt for Imagen"},
                "filename": {"type": "string", "description": "Desired Anki media filename (e.g. 'img_word.png')"}
            },
            "required": ["word", "prompt", "filename"]
        },
        "handler": handle_generate_illustration_media
    },
    "parse_feed_file": {
        "description": "Parse Spanish-written vocabulary/grammar points feed markdown file for Chinese or Japanese.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "filePath": {"type": "string", "description": "Absolute path to the markdown file"},
                "language": {"type": "string", "enum": ["chinese", "japanese"], "description": "The language module of the feed"}
            },
            "required": ["filePath", "language"]
        },
        "handler": handle_parse_feed_file
    },
    "update_feed_file": {
        "description": "Move successfully imported cards to the Included section in feed files, cleaning up Pending.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "filePath": {"type": "string", "description": "Absolute path to the markdown file"},
                "language": {"type": "string", "enum": ["chinese", "japanese"], "description": "The language module"},
                "successItems": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "List of successfully imported dicts"
                }
            },
            "required": ["filePath", "language", "successItems"]
        },
        "handler": handle_update_feed_file
    },
    "extract_anki_data": {
        "description": "Extract latest character and immersion notes from SQLite Anki DB to local data/anki_extract.json cache.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        },
        "handler": handle_extract_anki_data
    },
    "generate_dashboard": {
        "description": "Rebuild the visual glassmorphic dashboard (dashboard.html) with updated statistics.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        },
        "handler": handle_generate_dashboard
    },
    "export_anki_data": {
        "description": "Export a local copy of the Anki database and progress statistics to the anki_data/ directory.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        },
        "handler": handle_export_anki_data
    }
}

# Main JSON-RPC Loop

def main():
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            req = json.loads(line)
        except Exception:
            continue
            
        req_id = req.get("id")
        method = req.get("method")
        
        if method == "initialize":
            res = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "anki-helper-mcp",
                        "version": "1.0.0"
                    }
                }
            }
            sys.stdout.write(json.dumps(res, ensure_ascii=False) + "\n")
            sys.stdout.flush()
            
        elif method == "notifications/initialized":
            pass # No response needed
            
        elif method == "tools/list":
            tools_list = []
            for name, details in TOOLS.items():
                tools_list.append({
                    "name": name,
                    "description": details["description"],
                    "inputSchema": details["inputSchema"]
                })
            res = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "tools": tools_list
                }
            }
            sys.stdout.write(json.dumps(res, ensure_ascii=False) + "\n")
            sys.stdout.flush()
            
        elif method == "tools/call":
            params = req.get("params", {})
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            if tool_name in TOOLS:
                try:
                    tool_res = TOOLS[tool_name]["handler"](arguments)
                    res = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": tool_res
                    }
                except Exception as e:
                    res = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "error": {
                            "code": -32603,
                            "message": f"Internal error: {str(e)}",
                            "data": traceback.format_exc()
                        }
                    }
            else:
                res = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {
                        "code": -32601,
                        "message": f"Tool not found: {tool_name}"
                    }
                }
            sys.stdout.write(json.dumps(res, ensure_ascii=False) + "\n")
            sys.stdout.flush()

if __name__ == "__main__":
    main()
