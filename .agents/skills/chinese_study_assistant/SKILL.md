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
2. For each pending item:
   - Generate missing fields using Gemini (Spanish translation if missing, visual description for Imagen, and the Imagen prompt).
   - Generate TTS audio for the word and sentence using `generate_tts_media` (lang: `zh-CN`).
   - Generate illustration image using `generate_illustration_media` with the Peanuts-cartoon style prompt.
   - Insert the card to Anki via `add_note` tool.
3. Call `update_feed_file` to move successfully added cards to "Included in Anki".
4. Rebuild stats, dashboard, and export statistics/db copy by calling the `extract_anki_data`, `generate_dashboard`, and `export_anki_data` MCP tools.

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
