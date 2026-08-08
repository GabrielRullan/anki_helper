---
name: Japanese Study Assistant
description: Skill for parsing Japanese study feeds, generating N5-N4 level Japanese example sentences, formatting furigana, and syncing Japanese cards to Anki.
---

# Japanese Study Assistant Skill

This skill helps the user study Japanese vocabulary and grammar by translating Spanish-written logs, generating N5–N4 level contextual sentence cards, and exporting them to Anki.

## Deck and Card configuration
- **Deck**: `Japanese::Migaku` (using note type `Migaku Word Japanese`)
- **Fields**:
  - `Word`: Target vocabulary word or grammar point (e.g. `食べる` or `〜たら`).
  - `Expression`: Example Japanese sentence with the target word/pattern wrapped in `<b>` tags.
  - `Reading`: Example Japanese sentence with furigana/kana in parentheses following kanji (e.g., `明日(あした)の天気(てんき)がよかったら、公園(こうえん)に行(い)きます。`).
  - `Translated Sentence`: Spanish translation of the sentence.
  - `Notes`: Short explanation of the grammar rule or the vocabulary definition.
  - `Definitions`: The target word / grammar pattern itself (e.g., `<b>{Word}</b>`).

## Core Workflows

### 1. Processing the Feed
When the user asks to import new Japanese cards:
1. Call the MCP tool `parse_feed_file` with the path to `japanese/feed_me_jp.md` and language `"japanese"`.
2. For each pending item in the returned list, identify whether it is a **vocabulary word** or a **grammar point**.
   - Check for matches in the local Kaishi-ESP database by running the command: `python scripts/search_kaishi.py "<Spanish/Japanese Query>"`.
   - **If a match is found in the Kaishi database**:
     - Reuse the Kaishi card's vocabulary (`Word`), sentence (`Expression` with target wrapped in `<b>` tags), furigana (`Reading`), Spanish translation (`Translated_Sentence`), and `Notes`.
     - Retrieve its local media files (Word Audio, Sentence Audio, and Picture/Image) from the paths listed under `media_mappings`.
     - Prepare to upload these media files to Anki using AnkiConnect's `storeMediaFile` action (converting the file bytes to base64 payload).
   - **If no match is found in the Kaishi database (or for additional grammar card variants)**:
     - Generate card details using Gemini:
       - **If Vocabulary Word**: Retrieve standard Japanese equivalent (Kanji/Kana, N5–N4). Generate **exactly one (1) sentence card**. Sentence must use only N5–N4 grammar and vocabulary.
       - **If Grammar Point**: Identify target pattern (e.g., `〜てみる`, `〜たら`). Generate **multiple (2–3) distinct sentence cards** showing different use cases/conjugations, keeping other vocabulary N5–N4.
       - For each card, generate:
         - **Front (Expression)**: Sentence with target wrapped in `<b>` tags.
         - **Furigana (Reading)**: Sentence with furigana in parentheses.
         - **Spanish Translation**: Natural Spanish translation of the sentence.
         - **Note**: Vocabulary definition or short grammar explanation.
3. **CRITICAL REQUIREMENT:** You MUST output the list of proposed cards (showing the Expression, Furigana, Translation, and short explanation/reasoning, and indicating whether it was found in the Kaishi database) to the user in the chat, and explicitly ask for confirmation before attempting to add them to Anki or generate media.
4. Once the user approves:
   - For each approved card, if it is a Kaishi-ESP card:
     - Upload its media files (Word Audio, Sentence Audio, and Picture) to Anki using AnkiConnect `storeMediaFile` (reading the file from the `media_mappings` paths, base64-encoding the bytes, and saving it under its original filename).
     - Add the note to Anki via `add_note` tool with the corresponding media filenames.
   - If it is a Gemini-generated card:
     - Generate TTS audio for the sentence using `generate_tts_media` (lang: `ja`, filename: `ja_tts_[uuid].mp3`).
     - Add the note to Anki via `add_note` tool.
5. Call `update_feed_file` to remove the processed items from `japanese/feed_me_jp.md`.
6. Rebuild stats, dashboard, and export statistics/db copy by calling the `extract_anki_data`, `generate_dashboard`, and `export_anki_data` MCP tools.
