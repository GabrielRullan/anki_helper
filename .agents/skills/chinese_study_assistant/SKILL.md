---
name: Chinese Study Assistant
description: Skill for parsing Chinese study feeds, generating Mandarin Blueprint mnemonics, and syncing Chinese cards to Anki.
---

# Chinese Study Assistant Skill

This skill helps the user learn Chinese vocabulary and characters by interfacing with their Anki deck and using the Mandarin Blueprint (MBP) movie method.

## Card Safety Policy
> [!IMPORTANT]
> **ALWAYS UPDATE, NEVER OVERWRITE OR DELETE**
> - Always update existing cards in place (`updateNoteFields`).
> - Never delete, recreate, or overwrite existing notes/cards as this wipes review history (`revlog`).
> - Never reset card progress (`reps`, `ivl`, `type`, `queue`).


## Deck and Card configuration

### 1. Immersion Vocabulary Deck (`Chinese::Words`)
- **Note Type**: `Migaku Word`
- **Fields**:
  - `Word`: Target Chinese word.
  - `Sentence`: Example Chinese sentence.
  - `Translated Sentence`: English translation.
  - `Definitions`: Word, pinyin, and definitions.
  - `Notes`: Minimalist Peanuts cartoon visual description prompt.
  - `Images`: The minimalist cartoon image tag.
  - `Word Audio`, `Sentence Audio`: TTS audio media fields.

### 2. Non-Grammar Phrases / Stand-alone Sentences (`Chinese::Sent`)
- **Note Type**: `Chinese Sentence - Single`
- **Fields**:
  - `Word`: `""` (Empty)
  - `Grammar_Point`: `""` (Empty)
  - `Sentence`: `<Chinese Example Sentence>`
  - `Translated_Sentence`: `<English Translation>`
  - `Definitions`: `""` (Empty)
  - `Notes`: `<Sentence Pinyin>`
  - `Sentence_Audio`: `[sound:zh_tts_<hash>.mp3]`
  - `Translated_Audio`: `[sound:en_tts_<hash>.mp3]`

### 3. Grammar Sentences (`Chinese::Sent`)
- **Note Type**: `Chinese Sentence - Double`
- **Fields**:
  - `Word`: `""` (Empty)
  - `Grammar_Point`: `<Grammar Pattern (e.g., 是否)>`
  - `Sentence`: `<Chinese Sentence>`
  - `Translated_Sentence`: `<English Translation>`
  - `Notes`: `<Sentence Pinyin>\n\n<Grammar Rule Explanation>`
  - `Sentence_Audio`: `[sound:zh_tts_<hash>.mp3]`
  - `Translated_Audio`: `[sound:en_tts_<hash>.mp3]`

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
- **Actor** (Consonant Initial): Batman (`b`), Samuel L. Jackson (`s`), etc. (Refer to `scripts/fix_mbp_assignments.py` for full 55-initial standard codebook).
- **Set** (Vowel Final): Sandbox (`-an`), etc. (13 standard sets).
- **Tone-Location**:
  - Tone 1: Front Yard/Entrance.
  - Tone 2: Hallway/Kitchen.
  - Tone 3: Bedroom/Bathroom.
  - Tone 4: Backyard.
  - Tone 5: Roof.
- **Props / Components**: Radicals / visual building blocks of the Hanzi. Note that the legacy `Props` deck has been decommissioned; components are stored as plain text without prop links.
Create a vivid, memorable scene where the Actor is at the Tone-Location of their Set, using the Components to perform an action related to the character's Meaning.

### 3. Reviewing and Linking Word Characters
When the user asks to review character linking or populate empty `Characters` fields in `Chinese::Words`:
1. Use `python scripts/link_notes.py` for comprehensive bidirectional linking:
   - Populates `Characters` field on word cards (`[char|nidNoteID]`).
   - Inserts or updates the marked section in `Notes` on word cards (`<!-- ANKI_LINKER_START --><div><b>Characters in word:</b> ...</div><!-- ANKI_LINKER_END -->`).
   - Updates `Notes` on character cards (`<!-- ANKI_LINKER_START --><div><b>Words containing [Hanzi]:</b> ...</div><!-- ANKI_LINKER_END -->`).
   - Cleans legacy prop links from `Components` and removes deprecated 'Derived characters' sections.
2. Alternatively, run `python scripts/link_word_characters.py` if missing characters need to be auto-generated on the fly with Gemini before linking.
