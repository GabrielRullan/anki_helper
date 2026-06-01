# Discarded Options

This file contains the initial concepts that were proposed but put on hold or discarded in favor of other priorities.

---

## Concept 1: MBP Mnemonic Hover Tooltip (Anki Add-on)
* **Goal**: Bridge the gap between character memorization and sentence immersion. While reading/reviewing immersion sentences in the `Migaku` deck, hover over any character to see its Mandarin Blueprint mnemonic.
* **How it worked**:
  - The add-on injects custom Javascript/CSS into your `Migaku Sentence` card template.
  - When reviewing, it parses the Chinese characters in the `Sentence` field.
  - Hovering over a character (e.g. `况`) triggers a tooltip displaying its MBP details fetched from your `Characters` deck:
    > **况 (kuàng)** - Situation
    > * **Actor**: Kenny (South Park) (Initial: K)
    > * **Set**: -ang (Final)
    > * **Tone-Location**: Backyard [Tone 4]
    > * **Components**: 冫 (Ice), 兄 (Elder Brother)
* **Reason for Discarding**: Put on hold for now by user preference. Concept 3 is prioritized first.

---

## Concept 2: AI-Powered MBP Mnemonic Scene Generator (Python Tool / Editor Add-on)
* **Goal**: Automate the creation of Mandarin Blueprint mnemonic stories for new characters.
* **How it worked**:
  - A script or editor button that triggers an LLM when creating a new character note.
  - It reads the character's target `Hanzi`, `Pinyin`, `English`, and `Components`.
  - It automatically maps the correct **Actor** (based on Initial) and **Set** (based on Final) using your existing profile conventions (e.g. Initial `G` -> Chef Gordon Ramsay, Set `-an` -> Samuel L Jackson's set, Tone 4 -> Backyard).
  - The LLM generates **3 creative, memorable Mnemonic Scenes** combining these elements, which are pasted directly into the `Scene` field.
* **Reason for Discarding**: Put on hold for now by user preference. Concept 3 is prioritized first.
