# Anki Card Preservation Rule

## CARD SAFETY & HISTORY PRESERVATION POLICY

1. **ALWAYS UPDATE, NEVER OVERWRITE OR RECREATE**:
   - When modifying cards in Anki, always update existing note fields and tags in place using `updateNoteFields` or non-destructive field edits.
   - Never delete and recreate a note, as deleting a note permanently destroys its card review history (`revlog`).
   
2. **NEVER DELETE CARDS OR NOTES**:
   - Never run card/note deletion operations (`deleteNotes`, `deleteCards`, or database `DELETE FROM notes` / `DELETE FROM cards`) unless explicitly ordered by the user with confirmation.

3. **NEVER RESET CARD PROGRESS**:
   - Never reset card review counters (`reps`), intervals (`ivl`), ease factors (`factor`), or card types (`type`/`queue`).
   - Card learning progress and review history must be strictly preserved across all automated scripts, pipelines, and tools.
