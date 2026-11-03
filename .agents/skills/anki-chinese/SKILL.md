---
name: anki-chinese
description: >-
  Manage, analyze, and automate the Chinese HSK and Mandarin Blueprint (MBP) Anki collection.
  Use this skill whenever extracting Anki data, updating the interactive dashboard, adding N+1 characters,
  resolving MBP actors/sets, generating mnemonic scenes or illustrations, linking Hanzi and Word notes,
  updating translations, auditing card fatigue/leeches, or querying the Anki SQLite database.
---

# Chinese HSK & Mandarin Blueprint Anki Management

This skill provides step-by-step procedures, architecture rules, and reference commands for managing the Chinese HSK and Mandarin Blueprint (MBP) Anki collection.

---

## 1. Architecture & Safe Database Access

- **Anki Profile Path**: `%APPDATA%\Anki2\Main\collection.anki2`
- **Safe DB Query Pattern**:
  Always use `AnkiConnection` from `scripts.anki_db`. It automatically copies `collection.anki2` to a temporary file (`scripts/temp/collection_temp_*.anki2`) before reading to prevent database locking errors if Anki desktop is open:
  ```python
  from anki_db import AnkiConnection

  with AnkiConnection(profile_name="Main") as anki:
      char_deck = anki.best_match_deck(["Chinese::Characters", "Chinese\x1fCharacters"])
      notes = anki.get_notes_in_deck(char_deck)
  ```
- **Database Writes**:
  - If Anki desktop is running, communicate via **AnkiConnect** (`http://127.0.0.1:8765`).
  - If writing directly to SQLite, ensure Anki desktop is closed, and verify changes immediately after.

---

## 2. Decks & Models Schema

### `Chinese::Characters` (Mandarin Blueprint)
- **Primary Fields**:
  - `ID`: Unique identifier / timestamp string.
  - `Hanzi`: The single Chinese character.
  - `Pinyin`: Contextual pinyin with tone mark or number.
  - `English`: Concise English meaning.
  - `Initial`: Consonant initial (e.g. `B`, `ZH`, `NU`, `L`).
  - `Actor`: Mandarin Blueprint mnemonic persona.
  - `Set`: Mandarin Blueprint set / location anchor for the final.
  - `Tone`: 1, 2, 3, 4, or 5.
  - `Tone-Location`: Specific room or zone in the set:
    - Tone 1: Outside / Front entrance
    - Tone 2: Hallway / Kitchen
    - Tone 3: Bedroom / Bathroom
    - Tone 4: Backyard
    - Tone 5: Roof
  - `Components`: Radical / character building blocks (plain text, no links).
  - `Scene`: Sensory-rich mnemonic story combining Actor, Set, Tone-Location, and Components.
  - `Notes`: Contains marked HTML block with words containing this character:
    ```html
    <!-- ANKI_LINKER_START -->
    <div><b>Words containing 汉:</b> [汉字|nid123] [汉语|nid456]</div>
    <!-- ANKI_LINKER_END -->
    ```
  - `Image`: HTML `<img>` tag referencing media illustration.

### `Chinese::Words` (Migaku / Immersion)
- **Primary Fields**:
  - `Word`: Target vocabulary word.
  - `Characters`: Linked hanzi tokens: `[汉|nid123][字|nid456]`.
  - `Sentence`: Contextual sentence mined from immersion.
  - `Target Word` / `English`: Target gloss and sentence translation.
  - `Notes`: Marked HTML block linking individual characters:
    ```html
    <!-- ANKI_LINKER_START -->
    <div><b>Characters in word:</b> [汉|nid123] [字|nid456]</div>
    <!-- ANKI_LINKER_END -->
    ```
  - `Audio` / `Image`: Pronunciation and scene media.

> [!IMPORTANT]
> **Props Deck Retired**: The legacy `Props` deck has been decommissioned.
> - Do not re-add links to prop cards in `Components`.
> - Do not include `Derived characters` in character `Notes` fields.
> - Maintain strictly bidirectional Hanzi <-> Word links.

---

## 3. Mandarin Blueprint (MBP) Decomposition Rules

When parsing pinyin and assigning actors:
- Use `scripts/fix_mbp_assignments.py`:
  - `parse_mbp_pinyin(pinyin)`: Splits into initial, set, and tone using the 55-initial + 13-set standard MBP schema.
  - `STANDARD_ACTORS`: Standard actor codebook mapping.
  - Specials: `Nv` / `Lv` mapped to `Nu` / `Lu`.
  - Tone numbers: 1 to 5 mapped to their designated room/zone.

---

## 4. Key Workflows & Commands

### Workflow A: Refresh Data & Regenerate Dashboard
When the user studies cards or makes changes in Anki and wants updated statistics:
```powershell
python scripts/extract_anki_data.py
python scripts/generate_dashboard.py
```
- Writes updated cache to `data/anki_extract.json`.
- Regenerates standalone interactive `dashboard.html`.

### Workflow B: Bidirectional Note Linking & Unsuspending Word Characters
To scan and link all characters with corresponding vocabulary words:
```powershell
python scripts/link_notes.py
```
- Automatically cleans legacy prop links from `Components`.
- Updates `Characters` field on word cards.
- Adds or updates the `<!-- ANKI_LINKER_START -->` block in `Notes` on both character and word cards.
- Always run unit tests before/after changes:
  ```powershell
  python -m unittest tests/test_link_notes.py
  ```
- To find and unsuspend any suspended character cards (`queue == -1`) in `Chinese::Char` whose Hanzi appears in a `Chinese::Words` card (see also the `Unsuspend Word Characters` skill):
  ```powershell
  python scripts/unsuspend_word_characters.py --dry-run
  python scripts/unsuspend_word_characters.py --clear-red-flag
  ```

### Workflow C: Add Missing N+1 Characters
When new immersion cards introduce unlearned characters:
```powershell
python scripts/add_n1_characters.py
```
- Extracts high-frequency missing characters.
- Resolves pinyin, standard MBP actor, set, and tone location.
- Generates 24-field notes in Anki.

### Workflow D: Mnemonic Scene & Image Generation
1. **Sync Missing Mnemonic Scenes**:
   ```powershell
   python scripts/sync_all_missing_scenes.py
   python scripts/apply_generated_scenes_and_images.py
   ```
2. **Prepare Next Image Generation Wave**:
   ```powershell
   python scripts/prepare_next_image_wave.py
   ```
   Inspects character cards missing images, sorts by priority/active status, and divides into prompt batches in `data/next_image_batches.json` and `data/remaining_images_queue.json`.
3. **Illustrate a Specific Word or Character**:
   ```powershell
   python scripts/update_card_image.py <word_or_hanzi> "Custom prompt description"
   ```

### Workflow E: Update Character Definitions
To apply improved concise English definitions:
```powershell
python scripts/update_char_translations.py
```

### Workflow F: Run Verification Tests
```powershell
python -m unittest discover tests
```
Ensures all gap finding, pinyin splitting, and note linking unit tests pass.
