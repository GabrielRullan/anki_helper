# Chinese HSK 4 & Immersion Learning Tools

This workspace contains custom Python tools to analyze your Anki database, bridge your **Characters** memory palace (Mandarin Blueprint) and **Migaku** immersion cards, schedule your HSK 4 study efficiently, link notes bidirectionally, and diagnose card leeches.

**Last Run:** November 1, 2026 (Updated with MBP 55-initial + 13-set decomposition, Props deck retirement, bidirectional Hanzi/Word linker, automated scene/image pipelines, and updated dashboard).

---

## File Structure

### Data & Extraction
- [scripts/anki_db.py](file:///c:/Users/gabri/Documents/antigravity/anki/scripts/anki_db.py) - SQLite connection library that copies the Anki database (to bypass active locks) and queries notes, cards, and ease/lapse stats safely.
- [scripts/extract_anki_data.py](file:///c:/Users/gabri/Documents/antigravity/anki/scripts/extract_anki_data.py) - Backup extractor utility that dumps clean character and immersion cards to `data/anki_extract.json` with historical review stats.
- [data/anki_extract.json](file:///c:/Users/gabri/Documents/antigravity/anki/data/anki_extract.json) - Local data cache of characters, immersion notes, and card performance stats.
- [data/known_words.csv](file:///c:/Users/gabri/Documents/antigravity/anki/data/known_words.csv) - User-managed list of words already known, excluding them from missing HSK words calculations.

### Analytical Engines & Linking
- [scripts/gap_finder.py](file:///c:/Users/gabri/Documents/antigravity/anki/scripts/gap_finder.py) - Finds missing characters in your immersion and identifies zero-overhead HSK 4 synergies.
- [scripts/n1_sentence_finder.py](file:///c:/Users/gabri/Documents/antigravity/anki/scripts/n1_sentence_finder.py) - Scans immersion cards to isolate sentences with exactly one unknown character, sorted by frequency.
- [scripts/mbp_profiler.py](file:///c:/Users/gabri/Documents/antigravity/anki/scripts/mbp_profiler.py) - Maps your personal Mandarin Blueprint codebook (Actor/Set/Location), checks for typos, and detects memory leeches and mnemonic collisions.
- [scripts/fix_mbp_assignments.py](file:///c:/Users/gabri/Documents/antigravity/anki/scripts/fix_mbp_assignments.py) - Robust Mandarin Blueprint parser implementing the full 55-initial and 13-set codebook.
- [scripts/link_notes.py](file:///c:/Users/gabri/Documents/antigravity/anki/scripts/link_notes.py) - Automated linker establishing clean bidirectional links between Hanzi notes and Word notes (cleans legacy prop links and maintains `[Hanzi|nid]` cross-references).
- [scripts/flag_suspended_chars.py](file:///c:/Users/gabri/Documents/antigravity/anki/scripts/flag_suspended_chars.py) - Audits and flags suspended characters in the database.
- [tests/test_gap_finder.py](file:///c:/Users/gabri/Documents/antigravity/anki/tests/test_gap_finder.py) - Unit tests verifying analytical functions, pinyin splitting, and N+1 classification.
- [tests/test_link_notes.py](file:///c:/Users/gabri/Documents/antigravity/anki/tests/test_link_notes.py) - Unit tests verifying component cleaning, link generation, and note section updates.

### Mnemonic & Image Generation
- [scripts/add_n1_characters.py](file:///c:/Users/gabri/Documents/antigravity/anki/scripts/add_n1_characters.py) - Automatically creates missing N+1 character cards with proper MBP actors, sets, tone-locations, and HSK levels.
- [scripts/sync_all_missing_scenes.py](file:///c:/Users/gabri/Documents/antigravity/anki/scripts/sync_all_missing_scenes.py) - Generates and synchronizes mnemonic scenes for character cards missing scenes.
- [scripts/apply_generated_scenes_and_images.py](file:///c:/Users/gabri/Documents/antigravity/anki/scripts/apply_generated_scenes_and_images.py) - Applies generated mnemonic scenes and media links to notes.
- [scripts/prepare_next_image_wave.py](file:///c:/Users/gabri/Documents/antigravity/anki/scripts/prepare_next_image_wave.py) - Prepares prioritized batches and prompt queues for cards missing illustration images.
- [scripts/generate_scenes_and_images.py](file:///c:/Users/gabri/Documents/antigravity/anki/scripts/generate_scenes_and_images.py) - Generates mnemonic scene stories with Gemini and illustrates them using Imagen.
- [scripts/generate_missing_images.py](file:///c:/Users/gabri/Documents/antigravity/anki/scripts/generate_missing_images.py) - Utility script to find character cards missing images and generate illustrations.
- [scripts/update_card_image.py](file:///c:/Users/gabri/Documents/antigravity/anki/scripts/update_card_image.py) - Updates or replaces the illustration of a specific word or character using a custom prompt.
- [scripts/update_char_translations.py](file:///c:/Users/gabri/Documents/antigravity/anki/scripts/update_char_translations.py) - Batch updates character cards with improved concise English definitions.

### Visualization & UI
- [scripts/generate_dashboard.py](file:///c:/Users/gabri/Documents/antigravity/anki/scripts/generate_dashboard.py) - Aggregates data from all analyzer scripts and outputs a self-contained web app.
- [dashboard.html](file:///c:/Users/gabri/Documents/antigravity/anki/dashboard.html) - Interactive glassmorphic local dashboard (dark mode, search, statistics, conflict diagnostics, and live mnemonic generator).

### Skills & Agent Instructions
- [.agents/skills/anki-chinese/SKILL.md](file:///.agents/skills/anki-chinese/SKILL.md) - Official Antigravity workspace skill for automating Anki workflows.
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
To verify all analytical and linking logic:
```powershell
python -m unittest discover tests
```

### 2. Update Database Extract & Dashboard
To copy latest review state from your active Anki profile and regenerate the web dashboard:
```powershell
python scripts/extract_anki_data.py
python scripts/generate_dashboard.py
```
This writes or overwrites **[dashboard.html](file:///c:/Users/gabri/Documents/antigravity/anki/dashboard.html)** in your workspace. Simply double-click this file to open it in any browser.

### 3. Link Hanzi & Word Notes Bidirectionally
```powershell
python scripts/link_notes.py
```

### 4. Add Missing N+1 Characters
```powershell
python scripts/add_n1_characters.py
```

### 5. Generate Mnemonic Scenes & Illustration Queues
```powershell
python scripts/sync_all_missing_scenes.py
python scripts/apply_generated_scenes_and_images.py
python scripts/prepare_next_image_wave.py
```
