# Anki Helper — Chinese & Japanese Study Tools

This workspace contains custom Python tools to analyze your Anki database, bridge your **Characters** memory palace (Mandarin Blueprint) and **Migaku** immersion cards, schedule your HSK 4 and JLPT N5 study efficiently, link notes bidirectionally, diagnose card leeches, and integrate Japanese curriculum feeds.

**Last Updated:** November 1, 2026 (Updated with MBP 55-initial + 13-set decomposition, Props deck retirement, bidirectional Hanzi/Word linker, automated scene/image pipelines, Japanese Kaishi integration, and updated dashboard).

---

## Active Scripts Reference

### Database & Extraction
- [scripts/anki_db.py](file:///c:/Users/gabri/Documents/antigravity/anki/scripts/anki_db.py) — SQLite connection library copying the active database to bypass locks during queries.
- [scripts/extract_anki_data.py](file:///c:/Users/gabri/Documents/antigravity/anki/scripts/extract_anki_data.py) — Backup utility dumping card performance and ease stats into `data/anki_extract.json`.
- [scripts/export_anki_data_folder.py](file:///c:/Users/gabri/Documents/antigravity/anki/scripts/export_anki_data_folder.py) — Snapshot and backup utility.

### Analytical Engines & Dashboard
- [scripts/generate_dashboard.py](file:///c:/Users/gabri/Documents/antigravity/anki/scripts/generate_dashboard.py) — Analytical engine compiling gap synergies, N+1 sentences, leeches, MBP grid, Traverse Words, and JLPT N5 differential into `dashboard.html`.
- [dashboard.html](file:///c:/Users/gabri/Documents/antigravity/anki/dashboard.html) — Interactive glassmorphic local dashboard.
- [scripts/gap_finder.py](file:///c:/Users/gabri/Documents/antigravity/anki/scripts/gap_finder.py) — Analyzes character gaps, HSK synergies, and card overlaps.
- [scripts/n1_sentence_finder.py](file:///c:/Users/gabri/Documents/antigravity/anki/scripts/n1_sentence_finder.py) — Scans immersion sentences to isolate target sentences with exactly 1 unknown character.
- [scripts/mbp_profiler.py](file:///c:/Users/gabri/Documents/antigravity/anki/scripts/mbp_profiler.py) — Profiles Mandarin Blueprint actors, sets, and tone rooms; detects homophone collisions and leeches.
- [scripts/server.py](file:///c:/Users/gabri/Documents/antigravity/anki/scripts/server.py) — Local web server hosting `dashboard.html` at `http://localhost:8000`.

### Chinese Automation & Note Linking
- [scripts/fix_mbp_assignments.py](file:///c:/Users/gabri/Documents/antigravity/anki/scripts/fix_mbp_assignments.py) — Robust Mandarin Blueprint parser implementing the full 55-initial and 13-set codebook.
- [scripts/link_notes.py](file:///c:/Users/gabri/Documents/antigravity/anki/scripts/link_notes.py) — Automated linker establishing clean bidirectional links between Hanzi notes and Word notes (cleans legacy prop links and maintains `[Hanzi|nid]` cross-references).
- [scripts/link_word_characters.py](file:///c:/Users/gabri/Documents/antigravity/anki/scripts/link_word_characters.py) — Discovers unlinked Hanzi in `Chinese::Words`, auto-creates missing `Chinese::Char` cards with Gemini, and populates bidirectional links.
- [scripts/add_n1_characters.py](file:///c:/Users/gabri/Documents/antigravity/anki/scripts/add_n1_characters.py) — Automatically creates missing N+1 character cards with proper MBP actors, sets, tone-locations, and HSK levels.
- [scripts/flag_suspended_chars.py](file:///c:/Users/gabri/Documents/antigravity/anki/scripts/flag_suspended_chars.py) — Audits and flags suspended characters in the database.
- [scripts/update_char_translations.py](file:///c:/Users/gabri/Documents/antigravity/anki/scripts/update_char_translations.py) — Batch updates character cards with improved concise English definitions.

### Mnemonic & Media Generation
- [scripts/sync_all_missing_scenes.py](file:///c:/Users/gabri/Documents/antigravity/anki/scripts/sync_all_missing_scenes.py) — Generates and synchronizes mnemonic scenes for character cards missing scenes.
- [scripts/apply_generated_scenes_and_images.py](file:///c:/Users/gabri/Documents/antigravity/anki/scripts/apply_generated_scenes_and_images.py) — Applies generated mnemonic scenes and media links to notes.
- [scripts/prepare_next_image_wave.py](file:///c:/Users/gabri/Documents/antigravity/anki/scripts/prepare_next_image_wave.py) — Prepares prioritized batches and prompt queues for cards missing illustration images.
- [scripts/generate_scenes_and_images.py](file:///c:/Users/gabri/Documents/antigravity/anki/scripts/generate_scenes_and_images.py) — Generates MBP mnemonic stories via Gemini and illustrates them with Imagen.
- [scripts/generate_missing_images.py](file:///c:/Users/gabri/Documents/antigravity/anki/scripts/generate_missing_images.py) — Retry script to illustrate cards tagged `n1_added` lacking images.
- [scripts/generate_images_for_reviewed_today.py](file:///c:/Users/gabri/Documents/antigravity/anki/scripts/generate_images_for_reviewed_today.py) — Generates illustration images for Anki cards reviewed today.
- [scripts/update_card_image.py](file:///c:/Users/gabri/Documents/antigravity/anki/scripts/update_card_image.py) — Updates or replaces the illustration of a specific card using a custom prompt.

### Japanese Curriculum & JLPT N5
- [scripts/search_kaishi.py](file:///c:/Users/gabri/Documents/antigravity/anki/scripts/search_kaishi.py) — Fast CLI query utility searching the Kaishi-ESP 1.5k database for vocabulary, sentences, pitch accents, native audio, and illustrations.
- [scripts/build_n5_dataset.py](file:///c:/Users/gabri/Documents/antigravity/anki/scripts/build_n5_dataset.py) — Compiles the canonical JLPT N5 vocabulary dataset (`data/jlpt_n5_vocab.json`).

### Skills & Agent Instructions
- [.agents/skills/anki-chinese/SKILL.md](file:///.agents/skills/anki-chinese/SKILL.md) — Comprehensive Antigravity workspace skill for automating Anki workflows, MBP decomposition, and note linking.
- [.agents/skills/chinese_study_assistant/SKILL.md](file:///.agents/skills/chinese_study_assistant/SKILL.md) — Assistant skill for feed parsing, MBP mnemonics, and Anki card creation.
- [.agents/skills/japanese_study_assistant/SKILL.md](file:///.agents/skills/japanese_study_assistant/SKILL.md) — Assistant skill for Japanese feed parsing and Kaishi deck integration.
- [.agents/skills/character_image_generator/SKILL.md](file:///.agents/skills/character_image_generator/SKILL.md) — Skill for character illustration workflows.
- [.agents/rules/anki_card_preservation.md](file:///.agents/rules/anki_card_preservation.md) — Mandatory rule: always update existing cards in place; never delete or recreate cards or wipe review history.

---

## Usage

### 1. Run Unit Tests
```powershell
python -m unittest discover tests
```

### 2. Update Database Extract & Dashboard
```powershell
python scripts/extract_anki_data.py
python scripts/generate_dashboard.py
```
Open `dashboard.html` in any browser.

### 3. Bidirectional Note Linking
```powershell
python scripts/link_notes.py
```

### 4. Search Kaishi Japanese Database
```powershell
python scripts/search_kaishi.py "comer"
```

### 5. Add Missing N+1 Characters & Generate Scenes
```powershell
python scripts/add_n1_characters.py
python scripts/sync_all_missing_scenes.py
python scripts/apply_generated_scenes_and_images.py
python scripts/prepare_next_image_wave.py
```
