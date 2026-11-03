---
name: Unsuspend Word Characters
description: >-
  Find and unsuspend any suspended character card in Chinese::Char whose Hanzi appears
  in any vocabulary card in Chinese::Words, link bidirectional Hanzi <-> Word notes,
  and audit newly unsuspended cards for missing or outdated Mandarin Blueprint scenes/images.
---

# Unsuspend Word Characters Skill

Use this skill whenever the user wants to unsuspend character cards (`Chinese::Char`) whose Hanzi appears in vocabulary word cards (`Chinese::Words`), or after importing new Chinese word cards to ensure all constituent character cards are active and linked.

---

## 1. Safety & Architecture Rules

- **Strictly Distinguish Suspended vs. Buried Cards**:
  - In Anki's `cards` table, `queue == -1` is **Suspended** (`is:suspended`), whereas `queue == -2` or `-3` is **Buried** (automatically unburies the next day).
  - Only target cards with `queue == -1`.
- **Preserve Review History**:
  - Always unsuspend cards in place via AnkiConnect's `unsuspend` action (`scripts/unsuspend_word_characters.py`).
  - Never recreate or overwrite existing notes/cards.

---

## 2. Step-by-Step Workflow

### Step 1: Preview Suspended Character Cards Appearing in Word Cards (Dry Run)
Run the inspection in the sandbox first to see which suspended character cards match words in `Chinese::Words`:

```powershell
python scripts/unsuspend_word_characters.py --dry-run
```

- Matches every CJK character in the `Word` field of `Chinese::Words` against `Hanzi`, `Simplified`, and `Traditional` fields in `Chinese::Char`.
- Optional flag `--active-words-only`: only matches characters from non-suspended word cards in `Chinese::Words`.
- Reports:
  - Note ID (`nid`), Card IDs (`cids`), current card flags (`flags`), and the matching words from `Chinese::Words`.
  - Whether `Scene` and `Image` are present.
  - `[NEEDS_MBP_IMAGE_REGEN]` if the card has tag `mbp_fixed` (meaning its Mandarin Blueprint `Actor`/`Set`/`Scene` were updated while it was suspended, so its illustration still shows the old actor) or `needs_image_update`.

### Step 2: Unsuspend Matching Character Cards via AnkiConnect
Ensure Anki Desktop is open with AnkiConnect (`http://127.0.0.1:8765`), then run outside the sandbox (`BypassSandbox: true`) so it can reach localhost AnkiConnect:

```powershell
python scripts/unsuspend_word_characters.py --clear-red-flag
```

- Calls AnkiConnect `unsuspend` on all matching suspended card IDs.
- `--clear-red-flag` (optional): removes Red Flag (`flag:1`) if the card was previously flagged as a suspended word character.

### Step 3: Update Bidirectional Hanzi <-> Word Links
Whenever new words or newly unsuspended characters are synced, update the bidirectional links between `Chinese::Words` and `Chinese::Char`:

```powershell
python scripts/link_notes.py
```

### Step 4: Handle Any Missing or Outdated MBP Scenes/Images
If Step 1/2 reported `[NEEDS_MBP_IMAGE_REGEN]` or `MISSING` for `Scene` or `Image` on any newly unsuspended character card:
1. Verify or generate its Mandarin Blueprint `Scene` (combining `Actor`, `Set`, `Tone-Location`, `Components`, and `English` meaning).
2. Generate a minimalist Peanuts-style illustration (using Antigravity's built-in `image-generator` subagent or `scripts/update_card_image.py`) and sync it to Anki via `scripts/apply_generated_scenes_and_images.py`.

### Step 5: Refresh Extract & Dashboard
Refresh the local cache and interactive study dashboard:

```powershell
python scripts/extract_anki_data.py
python scripts/generate_dashboard.py
```
