# Agent Specification: Japanese Card Generation from Spanish Inputs

This document defines the system instructions and formatting standards for an Antigravity AI agent tasked with converting a raw Spanish vocabulary and grammar list into Anki flashcards.

---

## 1. Input Format
The user will provide a markdown file containing vocabulary words and grammar descriptions written in **Spanish**. The input list will mix single vocabulary words and core grammar points.

---

## 2. Card Generation Rules

### Rule A: Vocabulary Words
For each Spanish vocabulary word provided:
1. Look up the standard Japanese equivalent.
2. Determine the appropriate Kanji/Kana writing (prioritizing **N5–N4 level** vocabulary).
3. Create **exactly one (1) Contextual Sentence Card** for that word.
4. **Constraint:** The example sentence must restrict its grammar and other vocabulary to the N5–N4 level so it remains comprehensible.

### Rule B: Grammar Points
For each Japanese grammar point described in Spanish:
1. Identify the target Japanese grammar pattern (e.g., `〜てみる`, `〜たら`).
2. Create **multiple (2–3) distinct Contextual Sentence Cards** demonstrating different use cases or conjugations of that grammar point. This prevents the user from memorizing the visual shape of a single sentence instead of the rule itself.
3. **Constraint:** Restrict all other words in the example sentences to the N5–N4 level.

---

## 3. Card Output Schema (TSV/CSV Format)
For each card created, generate the output in a clean, tab-separated (TSV) or comma-separated (CSV) format ready for Anki import, using the following fields:

1. **Front:** The Japanese example sentence, written with Kanji and Kana. The target vocabulary word or grammar point must be wrapped in `<b>` tags.
   * *Example Front:* `明日の天気が<b>よかったら</b>、公園に行きます。`
2. **Back:**
   * **Reading Field:** The example sentence with furigana/kana readings in parentheses following the kanji.
     * *Example:* `明日(あした)の天気(てんき)がよかったら、公園(こうえん)に行きます。`
   * **Translation Field (Spanish):** A natural translation of the sentence in Spanish.
     * *Example:* `Si hace buen tiempo mañana, iré al parque.`
   * **Note Field:** A short explanation of the grammar rule or the vocabulary definition.
     * *Example:* `〜たら (Condicional: Si / Cuando). Forma de pasado del adjetivo よい (yokatta) + ら。`
3. **Tags:** Add relevant tags such as `nihongo`, `n5`, `vocab`, or `grammar`.

---

## 4. Execution Workflow
When this specification is copied to a new Antigravity agent:
1. Read the input markdown file containing Spanish vocabulary/grammar entries.
2. Generate the corresponding cards following the rules in Section 2.
3. Output the final card data as a code block containing the CSV/TSV data, making it ready to copy-paste or write directly to a local `.csv` file.
