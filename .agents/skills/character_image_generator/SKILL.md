---
name: Character Image Generator
description: Skill for creating minimalist Peanuts-style cartoon illustrations for Chinese character cards with scene descriptions using Google Gemini Imagen, uploading media to Anki, and updating note fields.
---

# Character Image Generator Skill

This skill automates the creation of visual illustrations for Chinese character cards (`Chinese::Char`) based on their Mandarin Blueprint (MBP) scene descriptions (`Scene` field), using Google Gemini Imagen models.

---

## 1. Overview & Requirements

- **Deck Name**: `Chinese::Char` (Note Types: `Chinese Character - Single`, `Chinese Character - Double`).
- **Key Note Fields**:
  - `Hanzi`: The target Chinese character.
  - `English`: The English meaning of the character.
  - `Scene`: The mnemonic story integrating Actor, Set, Tone-Location, Props, and Meaning.
  - `Image`: The HTML `<img>` field where the generated illustration tag is inserted.
- **Dependencies**:
  - `google-genai` SDK with `GOOGLE_API_KEY` set in `.env`.
  - Anki running locally with **AnkiConnect** (`http://127.0.0.1:8765`).

---

## 2. Image Prompt Formulation

Illustrations follow the project's minimalist Peanuts cartoon aesthetic:

```text
Minimalist Peanuts cartoon style illustration of: {scene_text}. On a plain white background, simple lines, flat colors, centered, no text, no letters.
```

- Avoid text, letters, or Chinese characters inside the generated image (`no text, no letters`).
- Focus on rendering the action and visual components described in `{scene_text}`.

---

## 3. Core Execution Protocol

When requested to generate images for character cards:

### Step 1: Identify Target Character Cards
- Query Anki via AnkiConnect or SQLite database:
  - Reviewed today: `deck:"Chinese::Char" rated:1`
  - Missing image: `deck:"Chinese::Char" -Image:*<img*`
- Extract `note_id`, `hanzi`, `english`, and `scene_text` from the note fields.
- Verify that `scene_text` is non-empty. If empty, generate or query the scene first before attempting image creation.

### Step 2: Generate Image with Gemini Imagen
- Use models in fallback order:
  1. `imagen-4.0-generate-001`
  2. `imagen-4.0-fast-generate-001`
  3. `imagen-4.0-ultra-generate-001`
  4. `imagen-3.0-generate-002`
- Parameters: `aspect_ratio="1:1"`, `output_mime_type="image/png"`, `number_of_images=1`.
- Clean English meaning to create a concise media filename:
  `media_filename = f"mbp_{hanzi}_{meaning_keyword}.png"`
- Save the raw image bytes to `imagenes_vocabulario/{media_filename}`.

### Step 3: Sync Media and Update Anki
- Call AnkiConnect `storeMediaFile` with `filename=media_filename` and `path=abspath(img_path)`.
- Call AnkiConnect `updateNoteFields` for `id=note_id`:
  ```json
  {
    "note": {
      "id": note_id,
      "fields": {
        "Image": "<img src=\"mbp_...png\">"
      }
    }
  }
  ```

### Step 4: Rebuild Dashboard
- Execute `python scripts/extract_anki_data.py`
- Execute `python scripts/generate_dashboard.py`

---

## 4. Reference Implementation

Refer to `scripts/generate_missing_images.py` and `scripts/generate_scenes_and_images.py` for Python logic:

```python
import os, re, time, json, urllib.request
from dotenv import load_dotenv
from google import genai
from google.genai import types

def generate_character_image(hanzi, english, scene_text, client, output_dir):
    meaning_kw = re.sub(r'[^a-zA-Z]', '', english.split(',')[0].split(';')[0].strip()).lower() or "char"
    filename = f"mbp_{hanzi}_{meaning_kw}.png"
    filepath = os.path.join(output_dir, filename)
    
    prompt = f"Minimalist Peanuts cartoon style illustration of: {scene_text}. On a plain white background, simple lines, flat colors, centered, no text, no letters."
    
    for model_id in ['imagen-4.0-generate-001', 'imagen-4.0-fast-generate-001', 'imagen-3.0-generate-002']:
        try:
            res = client.models.generate_images(
                model=model_id,
                prompt=prompt,
                config=types.GenerateImagesConfig(number_of_images=1, output_mime_type="image/png", aspect_ratio="1:1")
            )
            if res and res.generated_images:
                with open(filepath, "wb") as f:
                    f.write(res.generated_images[0].image.image_bytes)
                return filename, filepath
        except Exception as e:
            time.sleep(3)
            continue
    return None, None
```
