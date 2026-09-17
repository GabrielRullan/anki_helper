import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
dashboard_script_path = os.path.abspath('scripts/generate_dashboard.py')

with open(dashboard_script_path, 'r', encoding='utf-8') as f:
    code = f.read()

js_traverse_code = '''
        // ==========================================
        // TRAVERSE WORDS MANAGER LOGIC
        // ==========================================
        function getIgnoredTraverseWords() {
            try {
                return JSON.parse(safeLocalStorage.getItem('ignored_traverse_words') || '[]');
            } catch (e) {
                return [];
            }
        }

        function setIgnoredTraverseWords(list) {
            safeLocalStorage.setItem('ignored_traverse_words', JSON.stringify(list));
        }

        function populateTraverseLessonOptions() {
            const select = document.getElementById('traverse-lesson-select');
            if (!select || select.children.length > 1) return;
            for (let l = 68; l <= 88; l++) {
                const opt = document.createElement('option');
                opt.value = l;
                opt.textContent = `Lesson ${l}`;
                select.appendChild(opt);
            }
        }

        function toggleIgnoreTraverseWord(word) {
            let ignored = getIgnoredTraverseWords();
            if (ignored.includes(word)) {
                ignored = ignored.filter(w => w !== word);
                showToast(`"${word}" restored from ignored list.`);
            } else {
                ignored.push(word);
                showToast(`"${word}" added to ignored list.`);
            }
            setIgnoredTraverseWords(ignored);
            renderTraverseWords();
        }

        function toggleSelectAllTraverseWords(masterCb) {
            const checkboxes = document.querySelectorAll('.traverse-row-cb');
            checkboxes.forEach(cb => cb.checked = masterCb.checked);
        }

        function batchIgnoreTraverseWords(shouldIgnore) {
            const checkboxes = document.querySelectorAll('.traverse-row-cb:checked');
            if (checkboxes.length === 0) {
                showToast('Please select at least one word using the checkboxes.');
                return;
            }
            let ignored = getIgnoredTraverseWords();
            let count = 0;
            checkboxes.forEach(cb => {
                const w = cb.value;
                if (shouldIgnore && !ignored.includes(w)) {
                    ignored.push(w);
                    count++;
                } else if (!shouldIgnore && ignored.includes(w)) {
                    ignored = ignored.filter(item => item !== w);
                    count++;
                }
            });
            setIgnoredTraverseWords(ignored);
            showToast(`${count} words ${shouldIgnore ? 'ignored' : 'restored'}.`);
            renderTraverseWords();
        }

        async function addSingleTraverseWordToAnki(word) {
            try {
                // Call local server or AnkiConnect
                const response = await fetch('http://localhost:8000/api/known_words', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ word: word })
                });
                showToast(`Word "${word}" queued for Anki!`);
            } catch (e) {
                showToast(`Word "${word}" queued in local storage!`);
            }
            // Mark as known locally
            const localKnown = JSON.parse(safeLocalStorage.getItem('known_hsk_words') || '[]');
            if (!localKnown.includes(word)) {
                localKnown.push(word);
                safeLocalStorage.setItem('known_hsk_words', JSON.stringify(localKnown));
            }
            renderTraverseWords();
        }

        async function batchAddTraverseWordsToAnki() {
            const checkboxes = document.querySelectorAll('.traverse-row-cb:checked');
            if (checkboxes.length === 0) {
                showToast('Please select at least one word to add.');
                return;
            }
            const selectedWords = Array.from(checkboxes).map(cb => cb.value);
            for (const w of selectedWords) {
                await addSingleTraverseWordToAnki(w);
            }
            showToast(`Queued ${selectedWords.length} words for Anki!`);
            renderTraverseWords();
        }

        function renderTraverseWords() {
            populateTraverseLessonOptions();
            const allWords = DATA.traverse_words || [];
            const ignoredWords = getIgnoredTraverseWords();

            // Calculate overall statistics
            const totalCount = allWords.length;
            const inAnkiCount = allWords.filter(w => w.in_anki).length;
            const ignoredCount = allWords.filter(w => ignoredWords.includes(w.word)).length;
            const missingCount = allWords.filter(w => !w.in_anki && !ignoredWords.includes(w.word)).length;

            document.getElementById('stat-traverse-total').textContent = totalCount;
            document.getElementById('stat-traverse-in-anki').textContent = inAnkiCount;
            document.getElementById('stat-traverse-missing').textContent = missingCount;
            document.getElementById('stat-traverse-ignored').textContent = ignoredCount;
            document.getElementById('traverse-badge').textContent = missingCount;

            // Read filter inputs
            const searchText = (document.getElementById('traverse-search').value || '').trim().toLowerCase();
            const selectedLesson = document.getElementById('traverse-lesson-select').value;
            const selectedClass = document.getElementById('traverse-class-select').value;
            const selectedStatus = document.getElementById('traverse-status-select').value;

            // Filter logic
            const filtered = allWords.filter(item => {
                const isIgnored = ignoredWords.includes(item.word);

                // Search match
                if (searchText) {
                    const matchWord = item.word.toLowerCase().includes(searchText);
                    const matchHanzi = item.related_hanzi.some(h => h.includes(searchText));
                    if (!matchWord && !matchHanzi) return false;
                }

                // Lesson filter
                if (selectedLesson !== 'all' && str(item.lesson) !== str(selectedLesson)) {
                    if (String(item.lesson) !== String(selectedLesson)) return false;
                }

                // Classification filter
                if (selectedClass !== 'all' && item.classification !== selectedClass) {
                    return false;
                }

                // Status filter
                if (selectedStatus === 'missing') {
                    if (item.in_anki || isIgnored) return false;
                } else if (selectedStatus === 'in_anki') {
                    if (!item.in_anki) return false;
                } else if (selectedStatus === 'ignored') {
                    if (!isIgnored) return false;
                }

                return true;
            });

            const tbody = document.querySelector('#traverse-words-table tbody');
            tbody.innerHTML = '';

            if (filtered.length === 0) {
                tbody.innerHTML = '<tr><td colspan="7" class="empty-state"><i data-lucide="search"></i>No matching Traverse words found. Try adjusting your filters.</td></tr>';
                lucide.createIcons();
                return;
            }

            // Render top 150 matching items for high performance
            const displayLimit = 150;
            const displayItems = filtered.slice(0, displayLimit);

            displayItems.forEach(item => {
                const isIgnored = ignoredWords.includes(item.word);
                const tr = document.createElement('tr');
                tr.id = `traverse-row-${item.word}`;

                // Status badge
                let statusBadge = '<span class="badge badge-cyan">✅ In Anki</span>';
                if (isIgnored) {
                    statusBadge = '<span class="badge" style="background:rgba(255,255,255,0.05);color:var(--text-muted);border:1px solid var(--glass-border);">🚫 Ignored</span>';
                } else if (!item.in_anki) {
                    statusBadge = '<span class="badge badge-orange">❌ Missing</span>';
                }

                // Related Hanzi pills
                let hanziPillsHtml = '';
                item.related_hanzi.forEach(h => {
                    hanziPillsHtml += `<span class="badge badge-purple" style="cursor:pointer;margin-right:4px;" title="Click to filter by ${h}" onclick="document.getElementById('traverse-search').value='${h}';renderTraverseWords();">${h}</span>`;
                });

                // Classification badge color
                let classBadgeColor = 'badge-blue';
                if (item.classification.includes('Noun')) classBadgeColor = 'badge-cyan';
                else if (item.classification.includes('Verb')) classBadgeColor = 'badge-orange';
                else if (item.classification.includes('Adj')) classBadgeColor = 'badge-purple';

                const ignoreBtnLabel = isIgnored ? 'Un-ignore' : 'Ignore';
                const ignoreBtnIcon = isIgnored ? 'eye' : 'eye-off';

                tr.innerHTML = `
                    <td style="text-align:center;">
                        <input type="checkbox" class="traverse-row-cb" value="${item.word}">
                    </td>
                    <td class="hanzi-col" style="font-size:1.3rem;">${item.word}</td>
                    <td><span class="badge badge-cyan">Lesson ${item.lesson}</span></td>
                    <td><span class="badge ${classBadgeColor}">${item.classification}</span></td>
                    <td>${hanziPillsHtml}</td>
                    <td>${statusBadge}</td>
                    <td>
                        <div style="display:flex; gap:0.4rem;">
                            <button class="btn btn-sm" onclick="toggleIgnoreTraverseWord('${item.word}')" title="${ignoreBtnLabel} word">
                                <i data-lucide="${ignoreBtnIcon}" style="width:13px;height:13px;"></i> ${ignoreBtnLabel}
                            </button>
                            ${!item.in_anki ? `
                            <button class="btn btn-sm btn-primary" onclick="addSingleTraverseWordToAnki('${item.word}')" title="Queue for Anki">
                                <i data-lucide="plus" style="width:13px;height:13px;"></i> Add
                            </button>` : ''}
                        </div>
                    </td>
                `;
                tbody.appendChild(tr);
            });

            if (filtered.length > displayLimit) {
                const tr = document.createElement('tr');
                tr.innerHTML = `<td colspan="7" style="color:var(--text-muted);text-align:center;padding:1rem;">Showing ${displayLimit} of ${filtered.length} matching words. Use search or filters to narrow down.</td>`;
                tbody.appendChild(tr);
            }

            lucide.createIcons();
        }
'''

if 'function renderTraverseWords()' not in code:
    code = code.replace('// 1. Populate Top Gaps Table (Overview)', js_traverse_code + '\n\n        // 1. Populate Top Gaps Table (Overview)')
    code = code.replace('renderMissingCharacters();', 'renderMissingCharacters();\n        renderTraverseWords();')
    print("Injected renderTraverseWords() JS logic!")

with open(dashboard_script_path, 'w', encoding='utf-8') as f:
    f.write(code)

print("Updated JS code in generate_dashboard.py successfully!")
