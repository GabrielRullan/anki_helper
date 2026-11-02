# Deprecated & One-Off Scripts Archive

This document catalogs scripts in `anki_helper` that have fulfilled their original operational purpose and have been retired from the active `scripts/` directory.

These scripts represent one-time data migrations, early architectural prototypes, batch card importers, and direct SQLite/AnkiConnect data fixers. They are documented here so their historical logic, schemas, and operational context remain accessible if similar migrations are needed in the future.

---

## Retained Active Scripts Reference

For reference, the following **15 core scripts** remain active in `scripts/` and are actively used by the Antigravity Skills, MCP server, analytical pipeline, or UI dashboard:

| Script | Category | Purpose / Active Usage |
|---|---|---|
| [`scripts/anki_db.py`](file:///c:/Users/gabri/Documents/anki_helper/scripts/anki_db.py) | Database Connector | Safe SQLite reader copying `collection.anki2` to query notes, cards, and review stats without database locking. |
| [`scripts/anki_mcp_server.py`](file:///c:/Users/gabri/Documents/anki_helper/scripts/anki_mcp_server.py) | MCP Protocol | Model Context Protocol server exposing AnkiConnect, TTS, Imagen, and analysis tools to Antigravity agents. |
| [`scripts/extract_anki_data.py`](file:///c:/Users/gabri/Documents/anki_helper/scripts/extract_anki_data.py) | Data Extraction | Syncs character and immersion card performance and ease stats into `data/anki_extract.json`. |
| [`scripts/generate_dashboard.py`](file:///c:/Users/gabri/Documents/anki_helper/scripts/generate_dashboard.py) | Analytics Engine | Compiles character gaps, HSK synergies, N+1 immersion sentences, leeches, MBP grid, and JLPT N5 differential into `dashboard.html`. |
| [`scripts/gap_finder.py`](file:///c:/Users/gabri/Documents/anki_helper/scripts/gap_finder.py) | Analytical Library | Analyzes Hanzi knowledge gaps, HSK synergies, and card overlaps. Used by `generate_dashboard.py` and test suite. |
| [`scripts/n1_sentence_finder.py`](file:///c:/Users/gabri/Documents/anki_helper/scripts/n1_sentence_finder.py) | Immersion Analyzer | Scans immersion sentences to isolate target sentences with exactly 1 unknown character (N+1). Used by `generate_dashboard.py`. |
| [`scripts/mbp_profiler.py`](file:///c:/Users/gabri/Documents/anki_helper/scripts/mbp_profiler.py) | Mnemonic Profiler | Profiles Mandarin Blueprint actors, sets, and tone rooms; detects homophone collisions and memory leeches. Used by `generate_dashboard.py`. |
| [`scripts/export_anki_data_folder.py`](file:///c:/Users/gabri/Documents/anki_helper/scripts/export_anki_data_folder.py) | Backup Utility | Exports database snapshots and JSON extracts to data backup folders. |
| [`scripts/server.py`](file:///c:/Users/gabri/Documents/anki_helper/scripts/server.py) | Local Web Server | Serves `dashboard.html` at `http://localhost:8000` with live API endpoints for marking words/characters known. |
| [`scripts/search_kaishi.py`](file:///c:/Users/gabri/Documents/anki_helper/scripts/search_kaishi.py) | Japanese Assistant | Fast CLI lookup searching the Kaishi-ESP 1.5k database for Japanese vocabulary, grammar, audio, and illustrations. Used by `japanese_study_assistant`. |
| [`scripts/build_n5_dataset.py`](file:///c:/Users/gabri/Documents/anki_helper/scripts/build_n5_dataset.py) | Japanese Dataset | Compiles the canonical JLPT N5 vocabulary dataset (`data/jlpt_n5_vocab.json`) used by the dashboard differential engine. |
| [`scripts/generate_scenes_and_images.py`](file:///c:/Users/gabri/Documents/anki_helper/scripts/generate_scenes_and_images.py) | AI Generation | Generates Gemini 2.5 Flash MBP mnemonic scenes and Imagen 3 illustrations for Hanzi character cards. |
| [`scripts/generate_missing_images.py`](file:///c:/Users/gabri/Documents/anki_helper/scripts/generate_missing_images.py) | AI Generation | Targeted retry batch script to illustrate cards tagged `n1_added` that lack images. |
| [`scripts/update_card_image.py`](file:///c:/Users/gabri/Documents/anki_helper/scripts/update_card_image.py) | AI Generation | CLI utility to regenerate an individual card illustration with a custom user prompt. |
| [`scripts/link_word_characters.py`](file:///c:/Users/gabri/Documents/anki_helper/scripts/link_word_characters.py) | Card Linker | Discovers unlinked Hanzi in `Chinese::Words`, auto-creates missing `Chinese::Char` cards with Gemini, and populates bidirectional links. |
| [`scripts/anki-migaku.js`](file:///c:/Users/gabri/Documents/anki_helper/scripts/anki-migaku.js) | Front-end Asset | JavaScript runtime script used in Anki card templates for interactive Migaku card rendering. |

---

## Deprecated & One-Off Scripts Catalog

### 1. Japanese Data Import & Kaishi Processing (One-Off Migration)

These scripts were created and executed to extract the Kaishi-ESP APKG package, import grammar structures, and populate the `Japanese::Murasaki` deck.

#### `parse_kaishi.py`
- **Original Purpose**: Extracted SQLite tables from `data/Kaishi_15k_Espaol.apkg` (Anki zip package), unzipped audio/image media files into `data/kaishi_media/`, parsed all 1,500 Kaishi note fields, and generated `data/kaishi_cards.json`.
- **Why Deprecated**: The extraction was completed successfully. The resulting database is statically queried via `scripts/search_kaishi.py`.

#### `inspect_kaishi.py`
- **Original Purpose**: Quick diagnostic script to inspect the SQLite schema, models, field names, and sample notes of `data/Kaishi_15k_Espaol.apkg`.
- **Why Deprecated**: Inspection completed during initial integration research.

#### `import_japanese_grammar.py`
- **Original Purpose**: Batch imported 20 Japanese grammar cards (`〜枚`, `〜冊`, `〜てください`, `〜が` subject marker, `〜が欲しい`, etc.) into `Japanese::Murasaki` using note type `Migaku Word Japanese`, generating TTS audio via Google TTS and writing Spanish explanations.
- **Why Deprecated**: Execution completed; all 20 grammar cards are permanently in Anki. Future grammar cards are added via `japanese_study_assistant` and `anki_mcp_server.py`.

#### `import_japanese_kaishi_vocab.py`
- **Original Purpose**: Batch matched and imported 139 vocabulary cards extracted from course book index photos that existed in the Kaishi-ESP dataset into `Japanese::Murasaki`, uploading native word audio, sentence audio, pitch accents, and illustrations to Anki.
- **Why Deprecated**: Execution completed; all 139 Kaishi notes are in Anki. Ongoing lookups are handled by `search_kaishi.py`.

#### `generate_and_import_remaining_vocab.py`
- **Original Purpose**: Batch generated and imported the remaining 137 N5 vocabulary cards (not found in Kaishi) into `Japanese::Murasaki`, generating contextual sentences via Gemini 2.5 Flash, clean furigana, Spanish translations, and TTS audio.
- **Why Deprecated**: Execution completed; all 137 notes are in Anki (totaling 296 notes in `Japanese::Murasaki`). New cards are processed on-demand via the skill workflow.

---

### 2. Card Creation & Feed Synchronization (Legacy Prototypes)

Early synchronization scripts that preceded the unified Antigravity Skill and MCP Server pipeline.

#### `sync_grammar.py`
- **Original Purpose**: Parsed `chinese/lessons/semana.md`, split grammar points and exercises, generated TTS audio, and created notes in `Chinese::Sent` via AnkiConnect.
- **Why Deprecated**: Superseded by `anki_mcp_server.py` (`parse_feed_file`, `add_note`) and `chinese_study_assistant`.

#### `sync_islands.py`
- **Original Purpose**: Early synchronizer prototype to build structured "Grammar Island" cards from markdown notes.
- **Why Deprecated**: Grammar card structure was standardized into `Chinese Sentence - Single` and `Chinese Sentence - Double` note types managed through MCP tools.

#### `sync_lesson_grammar.py`
- **Original Purpose**: One-off sync script dedicated to lessons 15 and 16 markdown grammar points.
- **Why Deprecated**: Completed; all lesson grammar was ingested into Anki.

#### `create_cards.py`
- **Original Purpose**: Early CLI script for creating immersion cards in Anki with raw JSON payloads.
- **Why Deprecated**: Replaced by standard `add_note` in `anki_mcp_server.py`.

#### `add_proposed_cards.py`
- **Original Purpose**: Batch script to take proposed card JSON files and call AnkiConnect to insert them.
- **Why Deprecated**: Replaced by interactive AI proposals and `add_note` tool inside Antigravity agent workflows.

#### `add_n1_characters.py`
- **Original Purpose**: Batch script that scanned immersion cards for N+1 gaps and automatically inserted character cards into `Chinese::Char`.
- **Why Deprecated**: Superseded by `link_word_characters.py`, which generates full Mandarin Blueprint actors, sets, tone rooms, and character definitions via Gemini before adding notes.

#### `execute_character_actions.py`
- **Original Purpose**: Took proposed character card actions generated from gap analysis and executed them in Anki.
- **Why Deprecated**: Integrated directly into `link_word_characters.py` and MCP server tools.

---

### 3. Note Linking & Graph Building

#### `link_notes.py`
- **Original Purpose**: First-generation note linking script that used regular expressions to scan word text and insert HTML anchor tags (`[char|nidNoteID]`) linking word notes to character notes in Anki.
- **Why Deprecated**: Superseded by [`scripts/link_word_characters.py`](file:///c:/Users/gabri/Documents/anki_helper/scripts/link_word_characters.py), which also synthesizes missing character cards using Gemini and updates bidirectional links atomically.

---

### 4. Media & Illustration Generation (Legacy Batch Scripts)

Early image and audio generation scripts used during initial setup and testing.

#### `generate_images.py`
- **Original Purpose**: Initial prototype script testing Imagen API image generation for cards.
- **Why Deprecated**: Replaced by [`scripts/generate_scenes_and_images.py`](file:///c:/Users/gabri/Documents/anki_helper/scripts/generate_scenes_and_images.py), which integrates the complete Mandarin Blueprint scene story with Imagen 3.

#### `generate_sentence_images.py`
- **Original Purpose**: One-off script testing illustration generation for full immersion sentences.
- **Why Deprecated**: Sentence card design was simplified to focus on minimalist visual prompts or character-level memory palace illustrations.

#### `generate_missing_word_images.py`
- **Original Purpose**: One-off batch script that iterated through `Chinese::Words` to generate illustrations for cards with empty image fields.
- **Why Deprecated**: One-time backfill completed. On-demand regeneration is handled by `update_card_image.py`.

#### `update_missing_scenes_and_images.py`
- **Original Purpose**: Scanned `Chinese::Char` cards and backfilled mnemonic scenes and Imagen illustrations for cards created before the automated generator existed.
- **Why Deprecated**: All historical character cards have been populated; active additions are illustrated at creation time.

#### `update_low_retrievability_images.py`
- **Original Purpose**: One-off script that identified cards with low retrievability (high lapse count / leeches) and regenerated their visual illustrations with new prompts.
- **Why Deprecated**: Leech cards are now monitored dynamically via the Leech Diagnostics tab in `dashboard.html`. Individual card images can be updated using `update_card_image.py`.

#### `generate_character_audio.py`
- **Original Purpose**: One-off batch script that generated TTS audio files for character cards lacking audio.
- **Why Deprecated**: All character cards now have audio; new cards receive audio automatically upon insertion.

#### `generate_missing_audios.py`
- **Original Purpose**: Scanned all Chinese decks for missing audio tags and generated Google TTS mp3s.
- **Why Deprecated**: One-time audit and backfill completed.

---

### 5. Anki Database & Note Field Fixers (One-Off Data Migrations)

One-off cleanup and normalization scripts executed against the live Anki collection.

#### `fix_due_cards.py`
- **Original Purpose**: Modified SQLite tables directly in `collection.anki2` to reset abnormal due dates or rescheduling anomalies.
- **Why Deprecated**: One-time database fix. Direct SQLite writes to scheduling tables are avoided in favor of AnkiConnect or Anki's native scheduler.

#### `fix_junda_cards.py`
- **Original Purpose**: Recalculated and updated the Jun Da frequency rank field on Chinese character cards.
- **Why Deprecated**: One-time database backfill completed.

#### `fix_last_200_chars.py`
- **Original Purpose**: One-off script that corrected field formatting errors in the most recent 200 character cards created in Anki.
- **Why Deprecated**: Specific batch fix completed.

#### `fix_traditional_fields.py`
- **Original Purpose**: Cleaned up and backfilled the Traditional Hanzi fields across notes where conversion had failed or left empty values.
- **Why Deprecated**: One-time field migration completed.

#### `clean_components.py`
- **Original Purpose**: Normalized component fields on character cards (removing HTML artifacts, extra spaces, and inconsistent delimiters).
- **Why Deprecated**: Logic was consolidated directly into `mbp_profiler.py` and `link_word_characters.py`.

#### `split_has_comma_cards.py`
- **Original Purpose**: Split notes that accidentally contained multiple characters or comma-separated compound targets into separate individual cards.
- **Why Deprecated**: One-time data cleaning completed.

#### `capitalize_translations.py`
- **Original Purpose**: Iterated through immersion notes and capitalized the first letter of Spanish and English translations for consistent presentation.
- **Why Deprecated**: One-time typography fix completed.

#### `populate_common_words.py`
- **Original Purpose**: Populated the "Common Words" field on character cards by cross-referencing immersion and HSK vocabulary lists.
- **Why Deprecated**: One-time migration completed.

#### `enrich_new_characters.py`
- **Original Purpose**: Enriched newly added character cards with stroke counts, radical data, and HSK level tags.
- **Why Deprecated**: Character creation pipeline in `link_word_characters.py` now populates complete metadata at creation time.

#### `update_frequency_fields.py`
- **Original Purpose**: Backfilled frequency tier tags and integer rankings on vocabulary cards.
- **Why Deprecated**: One-time migration completed.

---

### 6. Card Template & Layout Setup (One-Off Configuration)

#### `update_card_templates.py`
- **Original Purpose**: Programmatically updated CSS styling, font sizes, and HTML structure in Anki card models via AnkiConnect.
- **Why Deprecated**: Note type templates are stable and configured in Anki.

#### `setup_traditional_cards.py`
- **Original Purpose**: Configured card templates to display Traditional characters alongside Simplified characters.
- **Why Deprecated**: Card layout setup completed.

#### `add_traditional_card_type.py`
- **Original Purpose**: Added a second card template (Traditional -> Meaning/Reading) to existing note models.
- **Why Deprecated**: Model template configuration completed.

---

### 7. Diagnostics & Audits

#### `check_cards.py`
- **Original Purpose**: Scratch diagnostic script used to print raw note fields, note types, and deck IDs for debugging during early development.
- **Why Deprecated**: Superseded by `anki_mcp_server.py` (`get_notes`, `list_decks`) and `anki_db.py`.

#### `review_character_frequencies.py`
- **Original Purpose**: Audit script comparing character cards against the Jun Da frequency table to find frequency distribution coverage.
- **Why Deprecated**: Replaced by interactive coverage metrics and the Missing Pieces tab in `dashboard.html`.
