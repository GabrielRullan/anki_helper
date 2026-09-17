import re
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

dashboard_script_path = os.path.abspath('scripts/generate_dashboard.py')

with open(dashboard_script_path, 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Check if traverse navigation link is in nav-links
if 'data-tab="traverse"' not in code:
    old_nav = '''                <a class="nav-item" data-tab="missing">
                    <i data-lucide="alert-circle"></i>
                    Missing Pieces
                    <span class="badge badge-red" id="missing-badge">0</span>
                </a>'''
    
    new_nav = '''                <a class="nav-item" data-tab="missing">
                    <i data-lucide="alert-circle"></i>
                    Missing Pieces
                    <span class="badge badge-red" id="missing-badge">0</span>
                </a>
                <a class="nav-item" data-tab="traverse">
                    <i data-lucide="layers"></i>
                    Traverse Words
                    <span class="badge badge-cyan" id="traverse-badge">0</span>
                </a>'''
    code = code.replace(old_nav, new_nav)
    print("Updated navigation links!")

# 2. Add panelTitles & panelDescs
if "'traverse': 'Traverse Words Manager'" not in code:
    old_titles = "'missing': 'Missing HSK Pieces'"
    new_titles = "'missing': 'Missing HSK Pieces',\n            'traverse': 'Traverse Words Manager'"
    code = code.replace(old_titles, new_titles)

    old_descs = "'missing': 'HSK 4 characters and vocabulary words that are not in your Anki decks.'"
    new_descs = "'missing': 'HSK 4 characters and vocabulary words that are not in your Anki decks.',\n            'traverse': 'Filter, review, ignore, or queue Mandarin Blueprint Traverse words for Anki study.'"
    code = code.replace(old_descs, new_descs)
    print("Updated panelTitles and panelDescs!")

# 3. Add traverse tab section HTML before closing </main>
if 'id="traverse-tab"' not in code:
    traverse_section_html = '''
            <!-- TAB 8: TRAVERSE WORDS MANAGER -->
            <section id="traverse-tab" class="tab-panel">
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-info">
                            <h4>Total Traverse Words</h4>
                            <div class="stat-value" id="stat-traverse-total">0</div>
                        </div>
                        <div class="stat-icon cyan">
                            <i data-lucide="layers"></i>
                        </div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-info">
                            <h4>In Anki Collection</h4>
                            <div class="stat-value" id="stat-traverse-in-anki" style="color:var(--green)">0</div>
                        </div>
                        <div class="stat-icon green">
                            <i data-lucide="check-circle-2"></i>
                        </div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-info">
                            <h4>Missing from Anki</h4>
                            <div class="stat-value" id="stat-traverse-missing" style="color:var(--accent-orange)">0</div>
                        </div>
                        <div class="stat-icon orange">
                            <i data-lucide="alert-triangle"></i>
                        </div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-info">
                            <h4>Ignored Words</h4>
                            <div class="stat-value" id="stat-traverse-ignored" style="color:var(--text-muted)">0</div>
                        </div>
                        <div class="stat-icon purple">
                            <i data-lucide="eye-off"></i>
                        </div>
                    </div>
                </div>

                <div class="panel">
                    <div class="panel-header">
                        <h3><i data-lucide="layers"></i> Mandarin Blueprint Traverse Words</h3>
                        <div style="display: flex; gap: 0.5rem; align-items: center;">
                            <button class="btn btn-sm" id="btn-batch-ignore" onclick="batchIgnoreTraverseWords(true)">
                                <i data-lucide="eye-off" style="width:14px;height:14px;"></i> Ignore Selected
                            </button>
                            <button class="btn btn-sm" id="btn-batch-unignore" onclick="batchIgnoreTraverseWords(false)">
                                <i data-lucide="eye" style="width:14px;height:14px;"></i> Un-ignore Selected
                            </button>
                            <button class="btn btn-sm btn-primary" id="btn-batch-add-anki" onclick="batchAddTraverseWordsToAnki()">
                                <i data-lucide="plus-circle" style="width:14px;height:14px;"></i> Add Selected to Anki
                            </button>
                        </div>
                    </div>
                    <p style="color: var(--text-secondary); margin-bottom: 1.5rem; font-size: 0.95rem;">
                        Review words introduced across Mandarin Blueprint lessons (Lessons 68–88). Select words to ignore or batch-add to your Anki study queue.
                    </p>

                    <!-- Filters bar -->
                    <div class="controls-row" style="flex-wrap: wrap; gap: 1rem;">
                        <div class="search-wrapper" style="flex: 1; min-width: 250px;">
                            <i data-lucide="search"></i>
                            <input type="text" id="traverse-search" placeholder="Search by word or character (e.g. 比萨, 隔)..." oninput="renderTraverseWords()">
                        </div>
                        
                        <div style="display:flex; gap:0.75rem; flex-wrap:wrap; align-items:center;">
                            <select id="traverse-lesson-select" class="btn" style="height:42px; background:var(--bg-slate);" onchange="renderTraverseWords()">
                                <option value="all">All Lessons (68-88)</option>
                            </select>

                            <select id="traverse-class-select" class="btn" style="height:42px; background:var(--bg-slate);" onchange="renderTraverseWords()">
                                <option value="all">All Classifications</option>
                                <option value="Nouns 名词">Nouns 名词</option>
                                <option value="Verbs 动词">Verbs 动词</option>
                                <option value="Adjectives 形容词">Adjectives 形容词</option>
                                <option value="Adverbs 副词">Adverbs 副词</option>
                                <option value="Pronouns 代词">Pronouns 代词</option>
                                <option value="Measure 量词">Measure 量词</option>
                                <option value="Numbers 数词">Numbers 数词</option>
                                <option value="Prepositions 介词">Prepositions 介词</option>
                                <option value="Conjunction 连词">Conjunction 连词</option>
                                <option value="Particles 助词">Particles 助词</option>
                                <option value="Mood 语气词">Mood 语气词</option>
                                <option value="Other 其他">Other 其他</option>
                            </select>

                            <select id="traverse-status-select" class="btn" style="height:42px; background:var(--bg-slate);" onchange="renderTraverseWords()">
                                <option value="all">All Statuses</option>
                                <option value="missing" selected>Missing from Anki</option>
                                <option value="in_anki">In Anki</option>
                                <option value="ignored">Ignored</option>
                            </select>
                        </div>
                    </div>

                    <div class="custom-table-container">
                        <table id="traverse-words-table">
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
                            </thead>
                            <tbody>
                                <!-- Inserted dynamically -->
                            </tbody>
                        </table>
                    </div>
                </div>
            </section>
'''
    code = code.replace('</main>', traverse_section_html + '\n        </main>')
    print("Added traverse tab section HTML!")

# 4. Add data loading in python main section
if "'traverse_words': traverse_words_list" not in code:
    old_data_loading = "# 6. Build the data JSON structure"
    new_data_loading = '''    # Load Traverse words database
    traverse_words_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "traverse_words_db.json")
    traverse_words_list = []
    if os.path.exists(traverse_words_path):
        try:
            with open(traverse_words_path, 'r', encoding='utf-8') as f:
                traverse_words_list = json.load(f)
        except Exception as e:
            print(f"Warning: Could not load traverse_words_db.json ({e})")

    # 6. Build the data JSON structure'''
    code = code.replace(old_data_loading, new_data_loading)

    old_db_dict = "'props': props_list"
    new_db_dict = "'props': props_list,\n        'traverse_words': traverse_words_list"
    code = code.replace(old_db_dict, new_db_dict)
    print("Added python data loading for traverse_words!")

# Write updated generate_dashboard.py code
with open(dashboard_script_path, 'w', encoding='utf-8') as f:
    f.write(code)

print(f"Updated {dashboard_script_path} successfully!")
