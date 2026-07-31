---
name: Chinese Study Assistant
description: Skill for parsing Chinese study feeds, generating Mandarin Blueprint mnemonics, and syncing Chinese cards to Anki.
---

# Chinese Study Assistant Skill

This skill helps the user learn Chinese vocabulary and characters by interfacing with their Anki deck and using the Mandarin Blueprint (MBP) movie method.

## Deck and Card configuration
- **Deck**: `Chinese::Words` (using note type `Migaku Word`)
- **Fields**:
  - `Word`: Target Chinese word.
  - `Sentence`: Example Chinese sentence.
  - `Translated Sentence`: Spanish/English translation.
  - `Definitions`: Word, pinyin, and definitions.
  - `Notes`: Minimalist Peanuts cartoon visual description prompt.
  - `Images`: The minimalist cartoon image tag.
  - `Word Audio`, `Sentence Audio`: TTS audio media fields.

## Core Workflows

### 1. Processing the Feed
When the user asks to import new Chinese cards:
1. Call the MCP tool `parse_feed_file` with the path to `chinese/feed_me_cn.md` and language `"chinese"`.
2. For each pending item, generate the proposed card details (the target Chinese word/phrase, example sentences, Spanish/English translations, and visual descriptions/prompts).
3. **CRITICAL REQUIREMENT:** You MUST output the list of proposed cards (showing the generated Chinese sentences, translations, and short reasoning/definitions) to the user in the chat, and explicitly ask for confirmation before calling `add_note` or generating media.
4. Once the user approves:
   - For each approved card, generate TTS audio for the word and sentence using `generate_tts_media` (lang: `zh-CN`).
   - Generate illustration image using `generate_illustration_media` with the Peanuts-cartoon style prompt.
   - Insert the card to Anki via `add_note` tool.
5. Call `update_feed_file` to move successfully added cards to "Included in Anki".
6. Rebuild stats, dashboard, and export statistics/db copy by calling the `extract_anki_data`, `generate_dashboard`, and `export_anki_data` MCP tools.

### 2. Mandarin Blueprint (MBP) Mnemonic Generation
When generating mnemonics for Hanzi, map components to these visual categories:
- **Actor** (Consonant Initial): Batman (`b`), Samuel L. Jackson (`s`), etc.
- **Set** (Vowel Final): Sandbox (`-an`), etc.
- **Tone-Location**:
  - Tone 1: Front Yard/Entrance.
  - Tone 2: Hallway/Kitchen.
  - Tone 3: Bedroom/Bathroom.
  - Tone 4: Backyard.
  - Tone 5: Roof.
- **Props**: Radicals/visual parts of the Hanzi.
Create a vivid, memorable scene where the Actor is at the Tone-Location of their Set, using the Props to perform an action related to the character's Meaning.

### 3. Reviewing and Linking Word Characters
When the user asks to review character linking or populate empty `Characters` fields in `Chinese::Words`:
1. Check the word notes in deck `Chinese::Words`. For each note where the `Characters` field is empty:
   - Identify the constituent Chinese characters (`'\u4e00' <= char <= '\u9fff'`).
   - If the character exists in the `Chinese::Char` deck, generate the link `[char|nidNoteID]`.
   - If the character does NOT exist, automatically create the character note in `Chinese::Char`:
     - Query Gemini to get its Pinyin reading, English definition, and components.
     - Split its Pinyin to determine its tone and consonant initial.
     - Match the initial, final, and tone to the existing Actors, Sets, and Tone-Locations in the deck (building the standard MBP codebook mappings dynamically).
     - Call `addNote` to insert the new character card, obtaining its new note ID.
     - Link the new card `[char|nidNewNoteID]` in the word note's `Characters` field.
2. Run the linking script using: `python scripts/link_word_characters.py`.

