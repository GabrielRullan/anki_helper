# Anki Helper — Chinese & Japanese Study Tools

This workspace contains custom Python tools to analyze your Anki database, bridge your **Characters** memory palace (Mandarin Blueprint) and **Migaku** immersion cards, schedule your HSK 4 and JLPT N5 study efficiently, diagnose card leeches, and integrate Japanese curriculum feeds.

---

## Active Scripts Reference

All core tools in `scripts/` are actively maintained and integrated with Antigravity Skills, MCP, or the interactive Dashboard:

### Core Database & Protocol
- [scripts/anki_db.py](file:///c:/Users/gabri/Documents/anki_helper/scripts/anki_db.py) — Safe SQLite connection library that copies the Anki database (bypassing desktop locks) and auto-detects profiles.
- [scripts/anki_mcp_server.py](file:///c:/Users/gabri/Documents/anki_helper/scripts/anki_mcp_server.py) — Antigravity Model Context Protocol server exposing AnkiConnect, TTS, Imagen, and sync tools.
- [scripts/extract_anki_data.py](file:///c:/Users/gabri/Documents/anki_helper/scripts/extract_anki_data.py) — Backup utility dumping card performance and ease stats into `data/anki_extract.json`.
- [scripts/export_anki_data_folder.py](file:///c:/Users/gabri/Documents/anki_helper/scripts/export_anki_data_folder.py) — Snapshot and backup utility.

### Analytical Engines & Dashboard
- [scripts/generate_dashboard.py](file:///c:/Users/gabri/Documents/anki_helper/scripts/generate_dashboard.py) — Analytical engine compiling gap synergies, N+1 sentences, leeches, MBP grid, and JLPT N5 differential into `dashboard.html`.
- [scripts/gap_finder.py](file:///c:/Users/gabri/Documents/anki_helper/scripts/gap_finder.py) — Analyzes character gaps, HSK synergies, and card overlaps.
- [scripts/n1_sentence_finder.py](file:///c:/Users/gabri/Documents/anki_helper/scripts/n1_sentence_finder.py) — Scans immersion sentences to isolate target sentences with exactly 1 unknown character.
- [scripts/mbp_profiler.py](file:///c:/Users/gabri/Documents/anki_helper/scripts/mbp_profiler.py) — Profiles Mandarin Blueprint actors, sets, and tone rooms; detects homophone collisions and leeches.
- [scripts/server.py](file:///c:/Users/gabri/Documents/anki_helper/scripts/server.py) — Local web server hosting `dashboard.html` at `http://localhost:8000`.

### Japanese Curriculum & JLPT N5
- [scripts/search_kaishi.py](file:///c:/Users/gabri/Documents/anki_helper/scripts/search_kaishi.py) — Fast CLI query utility searching the Kaishi-ESP 1.5k database for vocabulary, sentences, pitch accents, native audio, and illustrations.
- [scripts/build_n5_dataset.py](file:///c:/Users/gabri/Documents/anki_helper/scripts/build_n5_dataset.py) — Compiles the canonical JLPT N5 vocabulary dataset (`data/jlpt_n5_vocab.json`).

### AI Mnemonic & Media Generation
- [scripts/generate_scenes_and_images.py](file:///c:/Users/gabri/Documents/anki_helper/scripts/generate_scenes_and_images.py) — Generates MBP mnemonic stories via Gemini 2.5 and illustrates them with Imagen 3.
- [scripts/generate_missing_images.py](file:///c:/Users/gabri/Documents/anki_helper/scripts/generate_missing_images.py) — Retry script to illustrate cards tagged `n1_added` lacking images.
- [scripts/update_card_image.py](file:///c:/Users/gabri/Documents/anki_helper/scripts/update_card_image.py) — Updates or replaces the illustration of a specific card using a custom prompt.
- [scripts/link_word_characters.py](file:///c:/Users/gabri/Documents/anki_helper/scripts/link_word_characters.py) — Discovers unlinked Hanzi in `Chinese::Words`, auto-creates missing `Chinese::Char` cards with Gemini, and populates bidirectional links.

### Documentation & History
- [docs/deprecated_scripts.md](file:///c:/Users/gabri/Documents/anki_helper/docs/deprecated_scripts.md) — Comprehensive archive cataloging all 35 retired one-off migration and legacy prototype scripts.
- [README_deprecated_scripts.md](file:///c:/Users/gabri/Documents/anki_helper/README_deprecated_scripts.md) — Quick pointer to deprecated scripts documentation.
- [docs/discarded_options.md](file:///c:/Users/gabri/Documents/anki_helper/docs/discarded_options.md) — Archive of early architectural exploration.

---

## Usage

### 1. Run Unit Tests
```powershell
python -m unittest discover tests
```

### 2. Update Database Extract
```powershell
python scripts/extract_anki_data.py
```

### 3. Generate the Interactive Dashboard
```powershell
python scripts/generate_dashboard.py
```
Open [dashboard.html](file:///c:/Users/gabri/Documents/anki_helper/dashboard.html) in any web browser.

### 4. Search Kaishi Japanese Database
```powershell
python scripts/search_kaishi.py "comer"
```

### 5. Link Chinese Word Characters
```powershell
python scripts/link_word_characters.py
```
