import re
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
dashboard_script_path = os.path.abspath('scripts/generate_dashboard.py')

with open(dashboard_script_path, 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Update table headers in traverse-words-table
old_thead = '''                        <table id="traverse-words-table">
                            <thead>
                                <tr>
                                    <th style="width: 40px; text-align: center;">
                                        <input type="checkbox" id="traverse-select-all" onclick="toggleSelectAllTraverseWords(this)">
                                    </th>
                                    <th>Word</th>
                                    <th>MBP Lesson</th>
                                    <th>Classification</th>
                                    <th>Related Hanzi</th>
                                    <th>Anki Status</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>'''

new_thead = '''                        <table id="traverse-words-table">
                            <thead>
                                <tr>
                                    <th style="width: 40px; text-align: center;">
                                        <input type="checkbox" id="traverse-select-all" onclick="toggleSelectAllTraverseWords(this)">
                                    </th>
                                    <th>Word</th>
                                    <th>Pinyin & Meaning</th>
                                    <th>MBP Lesson</th>
                                    <th>Classification</th>
                                    <th>Related Hanzi</th>
                                    <th>Anki Status</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>'''

if '<th>Pinyin & Meaning</th>' not in code:
    code = code.replace(old_thead, new_thead)
    print("Updated table headers in generate_dashboard.py!")

# 2. Update renderTraverseWords JS logic to include Pinyin & Meaning column and search matching
old_render_js = '''            displayItems.forEach(item => {
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
            });'''

new_render_js = '''            displayItems.forEach(item => {
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

                const pinyinStr = item.pinyin ? `<div style="font-weight:600;color:var(--text-primary);">${item.pinyin}</div>` : '';
                const meaningStr = item.meaning ? `<div style="font-size:0.85rem;color:var(--text-secondary);max-width:320px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="${item.meaning}">${item.meaning}</div>` : '<div style="font-size:0.85rem;color:var(--text-muted);">-</div>';

                tr.innerHTML = `
                    <td style="text-align:center;">
                        <input type="checkbox" class="traverse-row-cb" value="${item.word}">
                    </td>
                    <td class="hanzi-col" style="font-size:1.3rem;">${item.word}</td>
                    <td>
                        ${pinyinStr}
                        ${meaningStr}
                    </td>
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
            });'''

# Also update search filter matching in JS
old_search_filter = '''                if (searchText) {
                    const matchWord = item.word.toLowerCase().includes(searchText);
                    const matchHanzi = item.related_hanzi.some(h => h.includes(searchText));
                    if (!matchWord && !matchHanzi) return false;
                }'''

new_search_filter = '''                if (searchText) {
                    const matchWord = item.word.toLowerCase().includes(searchText);
                    const matchPinyin = (item.pinyin || '').toLowerCase().includes(searchText);
                    const matchMeaning = (item.meaning || '').toLowerCase().includes(searchText);
                    const matchHanzi = item.related_hanzi.some(h => h.includes(searchText));
                    if (!matchWord && !matchPinyin && !matchMeaning && !matchHanzi) return false;
                }'''

code = code.replace(old_search_filter, new_search_filter)

if 'Meaning' in old_render_js or 'displayItems.forEach' in code:
    code = code.replace(old_render_js, new_render_js)
    print("Updated JS render function in generate_dashboard.py!")

with open(dashboard_script_path, 'w', encoding='utf-8') as f:
    f.write(code)

print("Saved updated generate_dashboard.py!")
