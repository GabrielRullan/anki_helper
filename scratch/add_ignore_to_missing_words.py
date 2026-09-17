import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
dashboard_script_path = os.path.abspath('scripts/generate_dashboard.py')

with open(dashboard_script_path, 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Add "Hide Ignored Words" checkbox and "Export Ignored" button in HSK Missing Words header/controls HTML
if 'id="hide-ignored-missing-words"' not in code:
    old_missing_words_header = '''                            <button class="btn btn-sm" id="btn-reset-known-words" onclick="resetLocalKnownWords()" style="background: rgba(239, 68, 68, 0.1); border-color: rgba(239, 68, 68, 0.2); color: var(--accent-red);" title="Reset browser-saved known words">
                                <i data-lucide="rotate-ccw" style="width:14px;height:14px;"></i> Reset Local
                            </button>'''

    new_missing_words_header = '''                            <button class="btn btn-sm" id="btn-export-ignored-words" onclick="exportIgnoredHskWords()" style="background: rgba(255, 255, 255, 0.05); color: var(--text-secondary);" title="Copy ignored missing words CSV">
                                <i data-lucide="eye-off" style="width:14px;height:14px;"></i> Export Ignored
                            </button>
                            <button class="btn btn-sm" id="btn-reset-known-words" onclick="resetLocalKnownWords()" style="background: rgba(239, 68, 68, 0.1); border-color: rgba(239, 68, 68, 0.2); color: var(--accent-red);" title="Reset browser-saved known words">
                                <i data-lucide="rotate-ccw" style="width:14px;height:14px;"></i> Reset Local
                            </button>'''
    code = code.replace(old_missing_words_header, new_missing_words_header)

    old_controls_row = '''                    <div class="controls-row">
                        <div class="search-wrapper">
                            <i data-lucide="search"></i>
                            <input type="text" id="missing-words-search" placeholder="Search missing HSK words by Hanzi, Pinyin, or Meaning...">
                        </div>
                    </div>'''

    new_controls_row = '''                    <div class="controls-row" style="flex-wrap:wrap; gap:1rem;">
                        <div class="search-wrapper" style="flex:1; min-width:250px;">
                            <i data-lucide="search"></i>
                            <input type="text" id="missing-words-search" placeholder="Search missing HSK words by Hanzi, Pinyin, or Meaning...">
                        </div>
                        <label style="display:flex;align-items:center;gap:0.5rem;font-size:0.85rem;cursor:pointer;color:var(--text-secondary);user-select:none;">
                            <input type="checkbox" id="hide-ignored-missing-words" checked onchange="renderMissingWords()" style="width:16px;height:16px;accent-color:var(--accent-orange);">
                            Hide Ignored Words
                        </label>
                    </div>'''
    code = code.replace(old_controls_row, new_controls_row)
    print("Updated HSK Missing Words HTML controls!")

# 2. Add JavaScript functions for ignoring HSK missing words
js_hsk_ignore_code = '''
        // ==========================================
        // HSK MISSING WORDS IGNORE LOGIC
        // ==========================================
        function getIgnoredHskMissingWords() {
            try {
                return JSON.parse(safeLocalStorage.getItem('ignored_hsk_missing_words') || '[]');
            } catch (e) {
                return [];
            }
        }

        function setIgnoredHskMissingWords(list) {
            safeLocalStorage.setItem('ignored_hsk_missing_words', JSON.stringify(list));
        }

        function ignoreMissingHskWord(word) {
            let ignored = getIgnoredHskMissingWords();
            if (!ignored.includes(word)) {
                ignored.push(word);
                setIgnoredHskMissingWords(ignored);
                showToast(`"${word}" added to ignored list.`);
            }
            renderMissingWords(document.getElementById('missing-words-search').value);
        }

        function unignoreMissingHskWord(word) {
            let ignored = getIgnoredHskMissingWords();
            if (ignored.includes(word)) {
                ignored = ignored.filter(w => w !== word);
                setIgnoredHskMissingWords(ignored);
                showToast(`"${word}" restored from ignored list.`);
            }
            renderMissingWords(document.getElementById('missing-words-search').value);
        }

        function exportIgnoredHskWords() {
            const ignored = getIgnoredHskMissingWords();
            if (ignored.length === 0) {
                showToast('No ignored HSK words to export.');
                return;
            }
            const csvContent = "Word\\n" + ignored.join("\\n");
            copyToClipboard(csvContent);
            showToast('Ignored HSK words CSV copied to clipboard!');
        }
'''

if 'function getIgnoredHskMissingWords()' not in code:
    code = code.replace('// 1. Populate Top Gaps Table (Overview)', js_hsk_ignore_code + '\n\n        // 1. Populate Top Gaps Table (Overview)')
    print("Injected HSK Missing Words JS ignore logic!")

# 3. Update renderMissingWords logic to handle hideIgnored, status badges, and action buttons
old_render_missing = '''        const missingWordsTableBody = document.querySelector('#missing-words-table tbody');
        
        function renderMissingWords(filterText = '') {
            missingWordsTableBody.innerHTML = '';
            const filtered = DATA.missing_hsk_words_in_migaku.filter(word => {
                const t = filterText.toLowerCase();
                return word.word.toLowerCase().includes(t) || 
                       word.pinyin.toLowerCase().includes(t) || 
                       word.meaning.toLowerCase().includes(t);
            });

            if (filtered.length === 0) {
                missingWordsTableBody.innerHTML = '<tr><td colspan="4" class="empty-state"><i data-lucide="search"></i>No missing HSK words match your search.</td></tr>';
                lucide.createIcons();
                return;
            }

            filtered.slice(0, 100).forEach(w => {
                const tr = document.createElement('tr');
                tr.id = `missing-word-row-${w.word}`;
                tr.innerHTML = `
                    <td class="hanzi-col" style="color:var(--accent-magenta)">${w.word}</td>
                    <td>${w.pinyin}</td>
                    <td style="font-size:0.85rem;color:var(--text-secondary);max-width:500px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="${w.meaning}">
                        ${w.meaning}
                    </td>
                    <td>
                        <div style="display: flex; gap: 0.5rem;">
                            <button class="btn btn-sm" onclick="copyToClipboard('${w.word}')" title="Copy Word">
                                <i data-lucide="copy" style="width:12px;height:12px;"></i>
                             </button>
                             <button class="btn btn-sm btn-primary" style="background: linear-gradient(135deg, #34D399 0%, #059669 100%); color: #0B0F19; border: none; padding: 0.4rem 0.6rem;" onclick="markWordAsKnown('${w.word}')" title="Mark as Known">
                                 <i data-lucide="check" style="width:12px;height:12px;"></i>
                             </button>
                        </div>
                    </td>
                `;
                missingWordsTableBody.appendChild(tr);
            });

            if (filtered.length > 100) {
                const tr = document.createElement('tr');
                tr.innerHTML = `<td colspan="4" style="color:var(--text-muted);text-align:center;">Showing top 100 of ${filtered.length} missing HSK words.</td>`;
                missingWordsTableBody.appendChild(tr);
            }
            lucide.createIcons();
        }'''

new_render_missing = '''        const missingWordsTableBody = document.querySelector('#missing-words-table tbody');
        
        function renderMissingWords(filterText = '') {
            missingWordsTableBody.innerHTML = '';
            const ignoredWords = getIgnoredHskMissingWords();
            const hideIgnored = document.getElementById('hide-ignored-missing-words') ? document.getElementById('hide-ignored-missing-words').checked : true;

            const allMissing = DATA.missing_hsk_words_in_migaku || [];
            const activeMissingCount = allMissing.filter(w => !ignoredWords.includes(w.word)).length;

            // Update stats badge
            const wordsBadge = document.getElementById('missing-words-badge');
            const statWordsCount = document.getElementById('stat-missing-words-count');
            if (wordsBadge) wordsBadge.textContent = activeMissingCount + ' Words';
            if (statWordsCount) statWordsCount.textContent = activeMissingCount;

            const filtered = allMissing.filter(word => {
                const isIgnored = ignoredWords.includes(word.word);
                if (hideIgnored && isIgnored) return false;

                const t = filterText.toLowerCase();
                return word.word.toLowerCase().includes(t) || 
                       word.pinyin.toLowerCase().includes(t) || 
                       word.meaning.toLowerCase().includes(t);
            });

            if (filtered.length === 0) {
                missingWordsTableBody.innerHTML = '<tr><td colspan="4" class="empty-state"><i data-lucide="search"></i>No missing HSK words match your search.</td></tr>';
                lucide.createIcons();
                return;
            }

            filtered.slice(0, 100).forEach(w => {
                const isIgnored = ignoredWords.includes(w.word);
                const tr = document.createElement('tr');
                tr.id = `missing-word-row-${w.word}`;

                let actionsHtml = '';
                if (isIgnored) {
                    actionsHtml = `
                        <span class="badge" style="background:rgba(255,255,255,0.05);color:var(--text-muted);border:1px solid var(--glass-border);margin-right:0.5rem;">🚫 Ignored</span>
                        <button class="btn btn-sm" onclick="unignoreMissingHskWord('${w.word}')" title="Un-ignore Word">
                            <i data-lucide="eye" style="width:12px;height:12px;"></i> Restore
                        </button>
                    `;
                } else {
                    actionsHtml = `
                        <button class="btn btn-sm" onclick="copyToClipboard('${w.word}')" title="Copy Word">
                            <i data-lucide="copy" style="width:12px;height:12px;"></i>
                        </button>
                        <button class="btn btn-sm btn-primary" style="background: linear-gradient(135deg, #34D399 0%, #059669 100%); color: #0B0F19; border: none; padding: 0.4rem 0.6rem;" onclick="markWordAsKnown('${w.word}')" title="Mark as Known">
                            <i data-lucide="check" style="width:12px;height:12px;"></i> Known
                        </button>
                        <button class="btn btn-sm" style="background:rgba(255,255,255,0.05);color:var(--text-muted);" onclick="ignoreMissingHskWord('${w.word}')" title="Ignore Word">
                            <i data-lucide="eye-off" style="width:12px;height:12px;"></i> Ignore
                        </button>
                    `;
                }

                tr.innerHTML = `
                    <td class="hanzi-col" style="color:${isIgnored ? 'var(--text-muted)' : 'var(--accent-magenta)'}">${w.word}</td>
                    <td>${w.pinyin}</td>
                    <td style="font-size:0.85rem;color:var(--text-secondary);max-width:500px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="${w.meaning}">
                        ${w.meaning}
                    </td>
                    <td>
                        <div style="display: flex; gap: 0.4rem; align-items: center;">
                            ${actionsHtml}
                        </div>
                    </td>
                `;
                missingWordsTableBody.appendChild(tr);
            });

            if (filtered.length > 100) {
                const tr = document.createElement('tr');
                tr.innerHTML = `<td colspan="4" style="color:var(--text-muted);text-align:center;">Showing top 100 of ${filtered.length} missing HSK words.</td>`;
                missingWordsTableBody.appendChild(tr);
            }
            lucide.createIcons();
        }'''

if 'const ignoredWords = getIgnoredHskMissingWords();' not in code:
    code = code.replace(old_render_missing, new_render_missing)
    print("Updated renderMissingWords JS function!")

with open(dashboard_script_path, 'w', encoding='utf-8') as f:
    f.write(code)

print("Saved updated generate_dashboard.py!")
