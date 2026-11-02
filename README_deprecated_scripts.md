# Deprecated Scripts README

The complete documentation of all 35 retired one-off, data migration, and legacy prototype scripts can be found here:

👉 **[docs/deprecated_scripts.md](docs/deprecated_scripts.md)**

## Summary of Active vs Deprecated Scripts

### Active Scripts in `scripts/` (15 Python scripts + 1 JS asset)
- `anki_db.py`: Direct SQLite reader bypassing locks.
- `anki_mcp_server.py`: MCP tool server for Antigravity agents.
- `build_n5_dataset.py`: Builds JLPT N5 canonical dataset.
- `export_anki_data_folder.py`: Exports database snapshots.
- `extract_anki_data.py`: Extracts character & immersion stats.
- `gap_finder.py`: Hanzi gap and HSK synergy analyzer.
- `generate_dashboard.py`: Analytical engine compiling `dashboard.html`.
- `generate_missing_images.py`: Retries missing illustrations.
- `generate_scenes_and_images.py`: MBP scene and Imagen generator.
- `link_word_characters.py`: Links word cards and synthesizes missing Hanzi.
- `mbp_profiler.py`: Profiles Mandarin Blueprint memory palace & leeches.
- `n1_sentence_finder.py`: Classifies N+1 immersion sentences.
- `search_kaishi.py`: Kaishi-ESP 1.5k vocabulary and media searcher.
- `server.py`: Local web server for `dashboard.html`.
- `update_card_image.py`: Single-card illustration updater.
- `anki-migaku.js`: Card template runtime script.

### Deprecated Scripts
All 35 legacy scripts (including old import scripts, one-off SQLite patchers, and superseded prototypes) have been documented in **[docs/deprecated_scripts.md](docs/deprecated_scripts.md)** and removed from `scripts/`.
