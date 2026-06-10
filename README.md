# Chinese HSK 4 & Immersion Learning Tools

This workspace contains custom Python tools to analyze your Anki database, bridge your **Characters** memory palace (Mandarin Blueprint) and **Migaku** immersion cards, schedule your HSK 4 study efficiently, and diagnose card leeches.

**Last Run:** May 29, 2026 (Updated with the new `hsk4_vocab.csv` Spanish translation data, character palace, and Migaku deck entries).

---

## File Structure

### Data & Extraction
- [scripts/anki_db.py](file:///c:/Users/gabri/Documents/antigravity/anki/scripts/anki_db.py) - SQLite connection library that copies the Anki database (to bypass active locks) and queries notes, cards, and ease/lapse stats.
- [scripts/extract_anki_data.py](file:///c:/Users/gabri/Documents/antigravity/anki/scripts/extract_anki_data.py) - Backup extractor utility that dumps clean character and immersion cards to `data/anki_extract.json` with historical review stats.
- [data/anki_extract.json](file:///c:/Users/gabri/Documents/antigravity/anki/data/anki_extract.json) - Local data cache of characters, immersion notes, and card performance stats.
- [data/known_words.csv](file:///c:/Users/gabri/Documents/antigravity/anki/data/known_words.csv) - User-managed list of words they already know, letting you exclude them from missing HSK words calculations.

### Analytical Engines
- [scripts/gap_finder.py](file:///c:/Users/gabri/Documents/antigravity/anki/scripts/gap_finder.py) - Finds missing characters in your immersion and identifies zero-overhead HSK 4 synergies.
- [scripts/n1_sentence_finder.py](file:///c:/Users/gabri/Documents/antigravity/anki/scripts/n1_sentence_finder.py) - Scans immersion cards to isolate sentences with exactly one unknown character, sorted by frequency.
- [scripts/mbp_profiler.py](file:///c:/Users/gabri/Documents/antigravity/anki/scripts/mbp_profiler.py) - Maps your personal Mandarin Blueprint codebook (Actor/Set/Location), checks for typos, and detects memory leeches and mnemonic collisions (homophones/shared components).
- [tests/test_gap_finder.py](file:///c:/Users/gabri/Documents/antigravity/anki/tests/test_gap_finder.py) - Unit tests verifying analytical functions, pinyin splitting, and N+1 classification.

### Mnemonic & Image Generation
- [scripts/generate_scenes_and_images.py](file:///c:/Users/gabri/Documents/antigravity/anki/scripts/generate_scenes_and_images.py) - Generates mnemonic scene stories with Gemini 2.5 and illustrates them using Imagen, uploading them to Anki and syncing note fields.
- [scripts/generate_missing_images.py](file:///c:/Users/gabri/Documents/antigravity/anki/scripts/generate_missing_images.py) - Utility script to find tag `n1_added` character cards missing images and illustrates them.
- [scripts/update_card_image.py](file:///c:/Users/gabri/Documents/antigravity/anki/scripts/update_card_image.py) - Updates or replaces the illustration of a specific word or card in Anki using a custom prompt.

### Visualization & UI
- [scripts/generate_dashboard.py](file:///c:/Users/gabri/Documents/antigravity/anki/scripts/generate_dashboard.py) - Aggregates data from all analyzer scripts and outputs a self-contained web app.
- [dashboard.html](file:///c:/Users/gabri/Documents/antigravity/anki/dashboard.html) - A premium, interactive glassmorphic local dashboard (dark mode, search, statistics, conflict diagnostics, and live mnemonic generator).

### Reference
- [hsk_learning_agent.md](file:///c:/Users/gabri/Documents/antigravity/anki/hsk_learning_agent.md) - Context and system instructions for AI tutors.
- [docs/discarded_options.md](file:///c:/Users/gabri/Documents/antigravity/anki/docs/discarded_options.md) - Archive of initial brainstormed ideas.

---

## Installation & Setup

1. Ensure Anki is installed and running on your system.
2. The scripts connect to your default profile named **"Main"** in the Windows AppData directory:
   `%APPDATA%\Anki2\Main\collection.anki2`
3. If your profile name is different, instantiate `AnkiConnection(profile_name="YourProfile")` inside the extraction scripts.

---

## Usage

### 1. Run Unit Tests
To verify all analytical logic is sound:
```powershell
python -m unittest discover tests
```

### 2. Update Database Extract
To copy latest review state from your active Anki profiles:
```powershell
python scripts/extract_anki_data.py
```

### 3. Generate the Interactive Dashboard
To execute N+1 sorting, leech checks, codebook grids, and HSK synergy mapping:
```powershell
python scripts/generate_dashboard.py
```
This writes or overwrites **[dashboard.html](file:///c:/Users/gabri/Documents/antigravity/anki/dashboard.html)** in your workspace. Simply double-click this file to open it in Chrome, Edge, or Firefox.

### 4. Batch-Generate Mnemonic Scenes and Illustrations
To generate scenes for mined characters and illustrate them:
```powershell
python scripts/generate_scenes_and_images.py
```

### 5. Generate Missing Illustration Images
If any character illustrations fail to generate (e.g., due to rate limits), run this script to safely process only the missing cards:
```powershell
python scripts/generate_missing_images.py
```

### 6. Update a Specific Card's Image
To generate/overwrite the image of a specific card with a custom prompt:
```powershell
python scripts/update_card_image.py "单词" "Your custom illustration prompt here"
```

### 7. How to Use the Dashboard

Once you open `dashboard.html` in your browser, you will see a sidebar containing five main views:

1. **Overview**: Displays high-level stats of your learning journey (learned characters, processed immersion cards, unique character gaps, and ready-to-study HSK words).
2. **Leech Diagnostics**: Displays high-priority leech cards (cards with multiple lapses) and mnemonic conflicts (e.g. characters that share the same actor and final sets, causing interference in your palace).
3. **N+1 Sentences**: Highlights immersion sentences where you only lack exactly **one** character. Learning this missing character (highlighted in orange) unlocks readability for that entire sentence. They are sorted by how frequently that missing character appears in your total immersion.
4. **HSK Synergy**: Lists HSK words composed entirely of characters you already know. You can start studying these words immediately with **zero new character overhead**.
5. **MBP Palace Grid**: An interactive visualization mapping initials (Actors), finals (Sets), and tones (Locations) to identify vacant slots in your memory palace. Includes a **Mnemonic Helper** at the bottom: input a Hanzi and its Pinyin to instantly look up its MBP components.
6. **Missing Pieces**: Highlights the HSK 4 characters and words that are not present in your Anki database, complete with search filtering and direct copy buttons.

