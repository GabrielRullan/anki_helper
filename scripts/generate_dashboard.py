import os
import re
import json
import sys
import csv
from gap_finder import load_data_from_live_db, load_data_from_backup_json, download_hsk_list, analyze_gap_and_synergy
from n1_sentence_finder import find_n1_sentences
from mbp_profiler import profile_mbp_palace

# Reconfigure stdout to use UTF-8 on Windows console
sys.stdout.reconfigure(encoding='utf-8')

# The HTML/CSS/JS template for the dashboard
DASHBOARD_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HSK 4 & Immersion Learning Dashboard</title>
    <!-- Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <!-- Lucide Icons -->
    <script src="https://unpkg.com/lucide@latest"></script>
    <!-- vis.js Network -->
    <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style>
        :root {
            --bg-dark: #0B0F19;
            --bg-slate: #161B26;
            --glass-bg: rgba(22, 27, 38, 0.7);
            --glass-border: rgba(255, 255, 255, 0.08);
            --text-primary: #F3F4F6;
            --text-secondary: #9CA3AF;
            --text-muted: #6B7280;
            --accent-cyan: #00F2FE;
            --accent-blue: #4FACFE;
            --accent-purple: #C084FC;
            --accent-magenta: #F472B6;
            --accent-orange: #FB923C;
            --accent-red: #F87171;
            --green: #34D399;
            --card-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            background-color: var(--bg-dark);
            background-image: 
                radial-gradient(at 10% 10%, rgba(79, 172, 254, 0.05) 0px, transparent 50%),
                radial-gradient(at 90% 90%, rgba(192, 132, 252, 0.05) 0px, transparent 50%);
            color: var(--text-primary);
            font-family: 'Inter', sans-serif;
            min-height: 100vh;
            overflow-x: hidden;
        }

        h1, h2, h3, h4, .outfit {
            font-family: 'Outfit', sans-serif;
        }

        /* Layout structure */
        .container {
            display: flex;
            min-height: 100vh;
        }

        /* Sidebar styling */
        .sidebar {
            width: 280px;
            background: var(--bg-slate);
            border-right: 1px solid var(--glass-border);
            padding: 2rem 1.5rem;
            display: flex;
            flex-direction: column;
            gap: 2rem;
            position: fixed;
            height: 100vh;
            z-index: 10;
        }

        .logo-area {
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }

        .logo-area svg {
            color: var(--accent-cyan);
            width: 32px;
            height: 32px;
        }

        .logo-title {
            font-size: 1.25rem;
            font-weight: 800;
            background: linear-gradient(135deg, var(--accent-cyan) 0%, var(--accent-blue) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .nav-links {
            list-style: none;
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
            flex-grow: 1;
        }

        .nav-item {
            display: flex;
            align-items: center;
            gap: 1rem;
            padding: 0.85rem 1.25rem;
            border-radius: 12px;
            color: var(--text-secondary);
            text-decoration: none;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s ease;
            border: 1px solid transparent;
        }

        .nav-item:hover {
            color: var(--text-primary);
            background: rgba(255, 255, 255, 0.03);
        }

        .nav-item.active {
            color: var(--text-primary);
            background: rgba(79, 172, 254, 0.1);
            border-color: rgba(79, 172, 254, 0.2);
            box-shadow: 0 4px 12px rgba(79, 172, 254, 0.05);
        }

        .nav-item svg {
            width: 20px;
            height: 20px;
        }

        .sidebar-footer {
            font-size: 0.75rem;
            color: var(--text-muted);
            text-align: center;
            border-top: 1px solid rgba(255, 255, 255, 0.05);
            padding-top: 1rem;
        }

        /* Main content area */
        .main-content {
            margin-left: 280px;
            flex-grow: 1;
            padding: 2.5rem;
            max-width: 1400px;
            width: calc(100% - 280px);
        }

        header {
            margin-bottom: 2.5rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .header-title h1 {
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }

        .header-title p {
            color: var(--text-secondary);
        }

        .last-updated {
            font-size: 0.85rem;
            color: var(--text-muted);
            background: rgba(255, 255, 255, 0.03);
            padding: 0.5rem 1rem;
            border-radius: 20px;
            border: 1px solid var(--glass-border);
        }

        /* Tabs view container */
        .tab-panel {
            display: none;
            animation: fadeIn 0.4s ease forwards;
        }

        .tab-panel.active {
            display: block;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* Cards and Grids */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2.5rem;
        }

        .stat-card {
            background: var(--glass-bg);
            border: 1px solid var(--glass-border);
            border-radius: 20px;
            padding: 1.75rem;
            box-shadow: var(--card-shadow);
            backdrop-filter: blur(20px);
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            transition: transform 0.3s ease, border-color 0.3s ease;
        }

        .stat-card:hover {
            transform: translateY(-5px);
            border-color: rgba(255, 255, 255, 0.15);
        }

        .stat-info h4 {
            color: var(--text-secondary);
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.5rem;
        }

        .stat-info .stat-value {
            font-size: 2.25rem;
            font-weight: 700;
            color: var(--text-primary);
        }

        .stat-icon {
            padding: 0.75rem;
            border-radius: 12px;
            background: rgba(255, 255, 255, 0.03);
        }

        .stat-icon.cyan svg { color: var(--accent-cyan); }
        .stat-icon.blue svg { color: var(--accent-blue); }
        .stat-icon.purple svg { color: var(--accent-purple); }
        .stat-icon.orange svg { color: var(--accent-orange); }
        .stat-icon.red svg { color: var(--accent-red); }

        /* General dashboard panels */
        .panel {
            background: var(--glass-bg);
            border: 1px solid var(--glass-border);
            border-radius: 24px;
            padding: 2rem;
            box-shadow: var(--card-shadow);
            backdrop-filter: blur(20px);
            margin-bottom: 2rem;
        }

        .panel-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.5rem;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            padding-bottom: 1rem;
        }

        .panel-header h3 {
            font-size: 1.35rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }

        /* Search and controls */
        .controls-row {
            display: flex;
            gap: 1rem;
            margin-bottom: 1.5rem;
            flex-wrap: wrap;
        }

        .search-wrapper {
            position: relative;
            flex-grow: 1;
            min-width: 250px;
        }

        .search-wrapper input {
            width: 100%;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid var(--glass-border);
            border-radius: 12px;
            padding: 0.85rem 1rem 0.85rem 2.75rem;
            color: var(--text-primary);
            font-size: 0.95rem;
            transition: all 0.3s ease;
        }

        .search-wrapper input:focus {
            outline: none;
            border-color: var(--accent-blue);
            background: rgba(255, 255, 255, 0.06);
            box-shadow: 0 0 10px rgba(79, 172, 254, 0.15);
        }

        .search-wrapper svg {
            position: absolute;
            left: 1rem;
            top: 50%;
            transform: translateY(-50%);
            color: var(--text-secondary);
            width: 18px;
            height: 18px;
        }

        /* Leech & Conflict Layout */
        .diagnostics-grid {
            display: grid;
            grid-template-columns: 1.2fr 0.8fr;
            gap: 1.5rem;
        }

        @media (max-width: 1100px) {
            .diagnostics-grid {
                grid-template-columns: 1fr;
            }
        }

        /* Tables and Lists styling */
        .custom-table-container {
            overflow-x: auto;
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }

        table {
            width: 100%;
            border-collapse: collapse;
            text-align: left;
            font-size: 0.95rem;
        }

        th {
            background: rgba(255, 255, 255, 0.02);
            color: var(--text-secondary);
            font-weight: 500;
            padding: 1rem 1.25rem;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            text-transform: uppercase;
            font-size: 0.75rem;
            letter-spacing: 0.05em;
        }

        td {
            padding: 1rem 1.25rem;
            border-bottom: 1px solid rgba(255, 255, 255, 0.03);
            vertical-align: middle;
        }

        tr:last-child td {
            border-bottom: none;
        }

        tr:hover td {
            background: rgba(255, 255, 255, 0.01);
        }

        .hanzi-col {
            font-size: 1.25rem;
            font-weight: 600;
        }

        .badge {
            display: inline-flex;
            align-items: center;
            padding: 0.25rem 0.6rem;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
        }

        .badge-red { background: rgba(248, 113, 113, 0.1); color: var(--accent-red); border: 1px solid rgba(248, 113, 113, 0.2); }
        .badge-orange { background: rgba(251, 146, 60, 0.1); color: var(--accent-orange); border: 1px solid rgba(251, 146, 60, 0.2); }
        .badge-purple { background: rgba(192, 132, 252, 0.1); color: var(--accent-purple); border: 1px solid rgba(192, 132, 252, 0.2); }
        .badge-cyan { background: rgba(0, 242, 254, 0.1); color: var(--accent-cyan); border: 1px solid rgba(0, 242, 254, 0.2); }
        .badge-green { background: rgba(52, 211, 153, 0.1); color: var(--green); border: 1px solid rgba(52, 211, 153, 0.2); }

        /* Leech warnings */
        .leech-card {
            background: rgba(248, 113, 113, 0.03);
            border: 1px solid rgba(248, 113, 113, 0.1);
            border-radius: 16px;
            padding: 1.25rem;
            margin-bottom: 1rem;
            transition: all 0.3s ease;
        }

        .leech-card:hover {
            border-color: rgba(248, 113, 113, 0.3);
            background: rgba(248, 113, 113, 0.05);
        }

        .leech-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.5rem;
        }

        .conflict-list {
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }

        .conflict-item {
            background: rgba(251, 146, 60, 0.02);
            border: 1px solid rgba(251, 146, 60, 0.1);
            border-radius: 16px;
            padding: 1.25rem;
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
            transition: all 0.3s ease;
        }

        .conflict-item:hover {
            border-color: rgba(251, 146, 60, 0.3);
            background: rgba(251, 146, 60, 0.04);
        }

        .conflict-header {
            display: flex;
            align-items: center;
            gap: 1.5rem;
            font-size: 1.1rem;
        }

        .conflict-char {
            font-size: 1.5rem;
            font-weight: 700;
        }

        .conflict-reasons {
            list-style: none;
            padding-left: 0.5rem;
            display: flex;
            flex-direction: column;
            gap: 0.35rem;
            font-size: 0.9rem;
            color: var(--text-secondary);
        }

        .conflict-reasons li {
            position: relative;
            padding-left: 1.25rem;
        }

        .conflict-reasons li::before {
            content: "•";
            color: var(--accent-orange);
            position: absolute;
            left: 0;
            font-weight: bold;
        }

        /* N+1 Sentences styling */
        .sentence-card {
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid var(--glass-border);
            border-radius: 16px;
            padding: 1.5rem;
            margin-bottom: 1.25rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 1.5rem;
            transition: all 0.3s ease;
        }

        .sentence-card:hover {
            border-color: rgba(255, 255, 255, 0.15);
            background: rgba(255, 255, 255, 0.03);
            transform: translateX(4px);
        }

        .sentence-left {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
            flex-grow: 1;
        }

        .chinese-text {
            font-size: 1.4rem;
            font-weight: 500;
            letter-spacing: 0.05em;
            line-height: 1.6;
        }

        .chinese-text t {
            background: rgba(79, 172, 254, 0.1);
            border-bottom: 2px solid var(--accent-blue);
            color: var(--text-primary);
            padding: 0 2px;
        }

        .chinese-text .gap-char {
            background: rgba(251, 146, 60, 0.15);
            border-bottom: 2px solid var(--accent-orange);
            color: #FFB067;
            padding: 0 4px;
            font-weight: 700;
            border-radius: 4px;
        }

        .sentence-translation {
            color: var(--text-secondary);
            font-size: 0.95rem;
        }

        .sentence-actions {
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }

        .btn {
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid var(--glass-border);
            color: var(--text-primary);
            padding: 0.6rem 1rem;
            border-radius: 8px;
            font-size: 0.85rem;
            font-weight: 500;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            transition: all 0.3s ease;
        }

        .btn:hover {
            background: rgba(255, 255, 255, 0.08);
            border-color: rgba(255, 255, 255, 0.2);
        }

        .btn-primary {
            background: linear-gradient(135deg, var(--accent-cyan) 0%, var(--accent-blue) 100%);
            border: none;
            color: #0B0F19;
            font-weight: 600;
        }

        .btn-primary:hover {
            opacity: 0.9;
            box-shadow: 0 4px 14px rgba(0, 242, 254, 0.3);
        }

        /* MBP Grid Explorer styling */
        .mbp-section-title {
            font-size: 1.15rem;
            margin: 1.5rem 0 1rem 0;
            color: var(--accent-cyan);
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            padding-bottom: 0.5rem;
        }

        .mbp-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(210px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }

        .mbp-card {
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid var(--glass-border);
            border-radius: 12px;
            padding: 1rem;
            display: flex;
            flex-direction: column;
            gap: 0.25rem;
            transition: all 0.3s ease;
        }

        .mbp-card:hover {
            border-color: rgba(255, 255, 255, 0.15);
            background: rgba(255, 255, 255, 0.04);
        }

        .mbp-card.vacant {
            border-style: dashed;
            opacity: 0.5;
        }

        .mbp-key {
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-secondary);
        }

        .mbp-val {
            font-size: 1.05rem;
            font-weight: 600;
            color: var(--text-primary);
        }

        /* Interactive Mnemonic Helper form */
        .mnemonic-helper-form {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1.5rem;
            margin-top: 1rem;
        }

        @media (max-width: 800px) {
            .mnemonic-helper-form {
                grid-template-columns: 1fr;
            }
        }

        .input-group {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }

        .input-group label {
            font-size: 0.85rem;
            color: var(--text-secondary);
            font-weight: 500;
        }

        .input-group input {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid var(--glass-border);
            border-radius: 10px;
            padding: 0.8rem;
            color: var(--text-primary);
            font-size: 0.95rem;
            transition: all 0.3s ease;
        }

        .input-group input:focus {
            outline: none;
            border-color: var(--accent-cyan);
            background: rgba(255, 255, 255, 0.05);
        }

        .mnemonic-result {
            grid-column: 1 / -1;
            background: rgba(0, 242, 254, 0.03);
            border: 1px solid rgba(0, 242, 254, 0.1);
            border-radius: 16px;
            padding: 1.5rem;
            margin-top: 1rem;
            display: none;
            animation: fadeIn 0.3s ease forwards;
        }

        .mnemonic-result-header {
            font-size: 1.2rem;
            font-weight: 700;
            color: var(--accent-cyan);
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .mnemonic-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1rem;
        }

        @media (max-width: 600px) {
            .mnemonic-grid {
                grid-template-columns: 1fr;
            }
        }

        /* Inconsistency warning items */
        .inconsistency-item {
            padding: 0.75rem 1rem;
            background: rgba(251, 146, 60, 0.03);
            border-left: 3px solid var(--accent-orange);
            border-radius: 0 8px 8px 0;
            margin-bottom: 0.75rem;
            font-size: 0.9rem;
        }

        /* Scrollbar styling */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }

        ::-webkit-scrollbar-track {
            background: var(--bg-dark);
        }

        ::-webkit-scrollbar-thumb {
            background: #2A3347;
            border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: #3B4762;
        }

        .empty-state {
            text-align: center;
            padding: 3rem 0;
            color: var(--text-muted);
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 1rem;
        }

        .empty-state svg {
            width: 48px;
            height: 48px;
            opacity: 0.5;
        }

        /* Toast notifications */
        .toast {
            position: fixed;
            bottom: 2rem;
            right: 2rem;
            background: var(--bg-slate);
            border: 1px solid var(--glass-border);
            border-radius: 10px;
            padding: 1rem 1.5rem;
            box-shadow: var(--card-shadow);
            color: var(--green);
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 0.75rem;
            transform: translateY(100px);
            opacity: 0;
            transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            z-index: 100;
        }

        .toast.show {
            transform: translateY(0);
            opacity: 1;
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Sidebar Navigation -->
        <aside class="sidebar">
            <div class="logo-area">
                <i data-lucide="compass"></i>
                <div class="logo-title">Anki Paladin</div>
            </div>
            
            <nav class="nav-links">
                <a class="nav-item active" data-tab="overview">
                    <i data-lucide="pie-chart"></i>
                    Overview
                </a>
                <a class="nav-item" data-tab="leeches">
                    <i data-lucide="skull"></i>
                    Leech Diagnostics
                </a>
                <a class="nav-item" data-tab="sentences">
                    <i data-lucide="arrow-right-left"></i>
                    N+1 Sentences
                    <span class="badge badge-orange" id="n1-badge">0</span>
                </a>
                <a class="nav-item" data-tab="synergy">
                    <i data-lucide="sparkles"></i>
                    HSK Synergy
                </a>
                <a class="nav-item" data-tab="codebook">
                    <i data-lucide="database"></i>
                    MBP Palace Grid
                </a>
                <a class="nav-item" data-tab="graph">
                    <i data-lucide="network"></i>
                    Connection Graph
                </a>
                <a class="nav-item" data-tab="missing">
                    <i data-lucide="alert-circle"></i>
                    Missing Pieces
                    <span class="badge badge-red" id="missing-badge">0</span>
                </a>
            </nav>

            <div class="sidebar-footer">
                HSK 4 Immersion v1.1
            </div>
        </aside>

        <!-- Main Content Panel -->
        <main class="main-content">
            <header>
                <div class="header-title">
                    <h1 id="panel-title-text">Palace Dashboard</h1>
                    <p id="panel-desc-text">Overview of HSK 4 characters and immersion sentence statistics.</p>
                </div>
                <div class="last-updated" id="timestamp-tag">
                    Last sync: Live
                </div>
            </header>

            <!-- TAB 1: OVERVIEW -->
            <section id="overview-tab" class="tab-panel active">
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-info">
                            <h4>Characters Learned</h4>
                            <div class="stat-value" id="stat-learned-count">0</div>
                        </div>
                        <div class="stat-icon cyan">
                            <i data-lucide="book-open"></i>
                        </div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-info">
                            <h4>Mined Immersion Cards</h4>
                            <div class="stat-value" id="stat-immersion-count">0</div>
                        </div>
                        <div class="stat-icon blue">
                            <i data-lucide="milestone"></i>
                        </div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-info">
                            <h4>Active Gaps in Immersion</h4>
                            <div class="stat-value" id="stat-gaps-count">0</div>
                        </div>
                        <div class="stat-icon orange">
                            <i data-lucide="alert-triangle"></i>
                        </div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-info">
                            <h4>Ready HSK Words</h4>
                            <div class="stat-value" id="stat-synergy-count">0</div>
                        </div>
                        <div class="stat-icon purple">
                            <i data-lucide="award"></i>
                        </div>
                    </div>
                </div>

                <div class="panel">
                    <div class="panel-header">
                        <h3><i data-lucide="trending-up"></i> Top Character Gaps (Action Items)</h3>
                        <span class="badge badge-orange" id="top-gaps-badge">0 Gaps</span>
                    </div>
                    <p style="color: var(--text-secondary); margin-bottom: 1.5rem; font-size: 0.95rem;">
                        These characters appear frequently in your immersion sentences but are missing from your Characters deck. Learning these characters will unlock multiple mined sentences.
                    </p>
                    <div class="custom-table-container">
                        <table id="top-gaps-table">
                            <thead>
                                <tr>
                                    <th>Character</th>
                                    <th>Occurrences in Immersion</th>
                                    <th>Tone Location</th>
                                    <th>Action</th>
                                </tr>
                            </thead>
                            <tbody>
                                <!-- Inserted dynamically -->
                            </tbody>
                        </table>
                    </div>
                </div>
            </section>

            <!-- TAB 2: LEECH DIAGNOSTICS -->
            <section id="leeches-tab" class="tab-panel">
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-info">
                            <h4>Total Leech Cards</h4>
                            <div class="stat-value" id="stat-leech-count" style="color: var(--accent-red)">0</div>
                        </div>
                        <div class="stat-icon red">
                            <i data-lucide="skull"></i>
                        </div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-info">
                            <h4>Mnemonic Conflicts</h4>
                            <div class="stat-value" id="stat-conflict-count" style="color: var(--accent-orange)">0</div>
                        </div>
                        <div class="stat-icon orange">
                            <i data-lucide="help-circle"></i>
                        </div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-info">
                            <h4>Palace Inconsistencies</h4>
                            <div class="stat-value" id="stat-inconsistent-count">0</div>
                        </div>
                        <div class="stat-icon purple">
                            <i data-lucide="activity"></i>
                        </div>
                    </div>
                </div>

                <div class="diagnostics-grid">
                    <!-- Left column: Leeches and Conflicts -->
                    <div class="diagnostics-left">
                        <div class="panel">
                            <div class="panel-header">
                                <h3><i data-lucide="alert-octagon"></i> Mnemonic Conflicts & Homophones</h3>
                            </div>
                            <p style="color: var(--text-secondary); margin-bottom: 1.5rem; font-size: 0.9rem;">
                                Conflicts occur when hard characters share visual components or have the same pronunciation/actor/set, leading to confusion. Review these pairs to differentiate their scenes.
                            </p>
                            <div class="conflict-list" id="conflict-list-container">
                                <!-- Dynamically populated -->
                            </div>
                        </div>

                        <div class="panel">
                            <div class="panel-header">
                                <h3><i data-lucide="frown"></i> Top Palace Leeches (Review Immediately)</h3>
                            </div>
                            <div class="custom-table-container">
                                <table id="leeches-table">
                                    <thead>
                                        <tr>
                                            <th>Hanzi</th>
                                            <th>Pinyin</th>
                                            <th>Lapses</th>
                                            <th>Ease</th>
                                            <th>Mnemonic Details</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <!-- Dynamically populated -->
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>

                    <!-- Right column: Palace Inconsistencies -->
                    <div class="diagnostics-right">
                        <div class="panel">
                            <div class="panel-header">
                                <h3><i data-lucide="settings-2"></i> Palace Inconsistencies</h3>
                            </div>
                            <p style="color: var(--text-secondary); margin-bottom: 1rem; font-size: 0.85rem;">
                                Cards that deviate from your standard mapping codebook (e.g. character has initial "b" but uses a non-standard Actor).
                            </p>
                            <div id="inconsistency-list" style="max-height: 550px; overflow-y: auto; padding-right: 0.25rem;">
                                <!-- Dynamically populated -->
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            <!-- TAB 3: N+1 SENTENCE MINER -->
            <section id="sentences-tab" class="tab-panel">
                <div class="panel">
                    <div class="panel-header">
                        <h3><i data-lucide="book-open"></i> N+1 Sentence Miner</h3>
                        <span class="badge badge-cyan" id="n1-count-badge">0 Sentences</span>
                    </div>
                    <p style="color: var(--text-secondary); margin-bottom: 1.5rem; font-size: 0.95rem;">
                        These mined sentences have <strong>exactly one</strong> unknown character (highlighted in orange). Learning this single character immediately unlocks the readability of that sentence!
                    </p>

                    <div class="controls-row">
                        <div class="search-wrapper">
                            <i data-lucide="search"></i>
                            <input type="text" id="sentences-search" placeholder="Filter sentences by character, translation, or missing character...">
                        </div>
                        <label style="display:flex;align-items:center;gap:0.5rem;font-size:0.9rem;cursor:pointer;user-select:none;color:var(--text-secondary);">
                            <input type="checkbox" id="hide-low-context" style="width:16px;height:16px;accent-color:var(--accent-orange);">
                            Hide Low-Context Phrases
                        </label>
                    </div>

                    <div id="sentences-list-container">
                        <!-- Sentences populated dynamically -->
                    </div>
                </div>
            </section>

            <!-- TAB 4: HSK SYNERGY -->
            <section id="synergy-tab" class="tab-panel">
                <div class="panel">
                    <div class="panel-header">
                        <h3><i data-lucide="award"></i> HSK 1-4 Synergy Words</h3>
                        <span class="badge badge-purple" id="synergy-count-badge">0 Words</span>
                    </div>
                    <p style="color: var(--text-secondary); margin-bottom: 1.5rem; font-size: 0.95rem;">
                        You already know all the characters in these vocabulary words! You can add them to your study rotation with <strong>zero character memory overhead</strong>.
                    </p>

                    <div class="controls-row">
                        <div class="search-wrapper">
                            <i data-lucide="search"></i>
                            <input type="text" id="synergy-search" placeholder="Search HSK words by Hanzi, Pinyin, or Meaning...">
                        </div>
                    </div>

                    <div class="custom-table-container">
                        <table id="synergy-table">
                            <thead>
                                <tr>
                                    <th>Word</th>
                                    <th>Pinyin</th>
                                    <th>Meaning</th>
                                </tr>
                            </thead>
                            <tbody>
                                <!-- Dynamically populated -->
                            </tbody>
                        </table>
                    </div>
                </div>
            </section>

            <!-- TAB 5: CODEBOOK & HELPERS -->
            <section id="codebook-tab" class="tab-panel">
                <!-- Mnemonic Generator Panel -->
                <div class="panel">
                    <div class="panel-header">
                        <h3><i data-lucide="sparkles"></i> Mnemonic Palace Helper</h3>
                    </div>
                    <p style="color: var(--text-secondary); margin-bottom: 1.5rem; font-size: 0.95rem;">
                        Type a new character and its pinyin below. The helper will parse the pinyin and automatically lookup the correct Actor, Set, and Tone-Location based on your active palace codebook!
                    </p>
                    <div class="mnemonic-helper-form">
                        <div class="input-group">
                            <label for="helper-hanzi">Hanzi</label>
                            <input type="text" id="helper-hanzi" placeholder="e.g. 况" maxlength="2">
                        </div>
                        <div class="input-group">
                            <label for="helper-pinyin">Pinyin</label>
                            <input type="text" id="helper-pinyin" placeholder="e.g. kuàng">
                        </div>
                        
                        <div class="mnemonic-result" id="helper-result">
                            <div class="mnemonic-result-header">
                                <i data-lucide="check-circle-2"></i>
                                Recommended Mnemonic Template
                            </div>
                            <div class="mnemonic-grid">
                                <div class="mbp-card">
                                    <div class="mbp-key" id="result-actor-title">Actor (Initial)</div>
                                    <div class="mbp-val" id="result-actor-val">-</div>
                                </div>
                                <div class="mbp-card">
                                    <div class="mbp-key" id="result-set-title">Set (Final)</div>
                                    <div class="mbp-val" id="result-set-val">-</div>
                                </div>
                                <div class="mbp-card">
                                    <div class="mbp-key">Tone Location</div>
                                    <div class="mbp-val" id="result-loc-val">-</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Codebook display grid -->
                <div class="panel">
                    <div class="panel-header">
                        <h3><i data-lucide="database"></i> Palace System Codebook</h3>
                    </div>
                    
                    <div class="mbp-section-title">Actors (Initials)</div>
                    <div class="mbp-grid" id="actors-grid">
                        <!-- Dynamically populated -->
                    </div>

                    <div class="mbp-section-title">Sets (Finals)</div>
                    <div class="mbp-grid" id="sets-grid">
                        <!-- Dynamically populated -->
                    </div>

                    <div class="mbp-section-title">Tone Locations</div>
                    <div class="mbp-grid" id="locations-grid">
                        <!-- Dynamically populated -->
                    </div>
                </div>
            </section>

            <!-- TAB 7: CONNECTION GRAPH -->
            <section id="graph-tab" class="tab-panel">
                <div class="panel">
                    <div class="panel-header">
                        <h3><i data-lucide="network"></i> Connection Graph Explorer</h3>
                    </div>
                    <p style="color: var(--text-secondary); margin-bottom: 1.5rem; font-size: 0.95rem;">
                        Search for any character or word in your collection to visualize its connection network, visual components, derived characters, and word usage.
                    </p>

                    <div class="controls-row">
                        <div class="search-wrapper" style="max-width: 500px;">
                            <i data-lucide="search"></i>
                            <input type="text" id="graph-search" placeholder="Type a character (e.g. 明) or word (e.g. 明天)..." autocomplete="off">
                            <div id="graph-search-results" style="position: absolute; top: 100%; left: 0; right: 0; background: var(--bg-slate); border: 1px solid var(--glass-border); border-radius: 0 0 12px 12px; max-height: 250px; overflow-y: auto; z-index: 1000; display: none; box-shadow: var(--card-shadow);">
                                <!-- Suggestions inserted dynamically -->
                            </div>
                        </div>
                        <button class="btn" id="btn-random-graph" style="height: 46px;">
                            <i data-lucide="dices"></i> Random Card
                        </button>
                    </div>

                    <div style="display: grid; grid-template-columns: 1.4fr 0.6fr; gap: 1.5rem; min-height: 600px; height: calc(100vh - 350px); margin-top: 1rem;">
                        <!-- Graph viewport -->
                        <div id="graph-network-container" style="background: rgba(0, 0, 0, 0.2); border: 1px solid var(--glass-border); border-radius: 16px; position: relative; overflow: hidden; height: 100%;">
                            <!-- vis.js canvas will render here -->
                        </div>

                        <!-- Detail panel -->
                        <div class="panel" style="margin-bottom: 0; padding: 1.5rem; display: flex; flex-direction: column; gap: 1.25rem; overflow-y: auto; height: 100%;">
                            <h3 style="border-bottom: 1px solid rgba(255, 255, 255, 0.05); padding-bottom: 0.75rem; color: var(--accent-cyan);">
                                <i data-lucide="info"></i> Card Inspector
                            </h3>
                            
                            <div id="graph-inspector-empty" class="empty-state" style="padding: 2rem 0; height: 100%; justify-content: center; display: flex; flex-direction: column; align-items: center; gap: 1rem;">
                                <i data-lucide="mouse-pointer-click" style="width: 48px; height: 48px; opacity: 0.5;"></i>
                                <span>Click a node in the graph or search above to view detailed card information.</span>
                            </div>

                            <div id="graph-inspector-content" style="display: none; flex-direction: column; gap: 1.25rem;">
                                <!-- Details dynamically filled -->
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            <!-- TAB 6: MISSING PIECES -->
            <section id="missing-tab" class="tab-panel">
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-info">
                            <h4>Missing HSK Characters</h4>
                            <div class="stat-value" id="stat-missing-chars-count">0</div>
                        </div>
                        <div class="stat-icon red">
                            <i data-lucide="alert-circle"></i>
                        </div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-info">
                            <h4>Missing HSK Words</h4>
                            <div class="stat-value" id="stat-missing-words-count">0</div>
                        </div>
                        <div class="stat-icon orange">
                            <i data-lucide="alert-triangle"></i>
                        </div>
                    </div>
                </div>

                <!-- Missing HSK Characters grid panel -->
                <div class="panel">
                    <div class="panel-header">
                        <h3><i data-lucide="alert-circle"></i> HSK Characters Missing from Palace</h3>
                        <div style="display: flex; gap: 0.75rem; align-items: center;">
                            <button class="btn btn-sm btn-primary" id="btn-export-missing-chars" onclick="exportMissingCharacters()" title="Copy missing characters as CSV format">
                                <i data-lucide="download" style="width:14px;height:14px;"></i> Export Missing
                            </button>
                            <button class="btn btn-sm" id="btn-export-known-chars" onclick="exportKnownCharacters()" title="Copy known characters as CSV format">
                                <i data-lucide="clipboard" style="width:14px;height:14px;"></i> Export Known
                            </button>
                            <button class="btn btn-sm" id="btn-reset-known-chars" onclick="resetLocalKnownCharacters()" style="background: rgba(239, 68, 68, 0.1); border-color: rgba(239, 68, 68, 0.2); color: var(--accent-red);" title="Reset browser-saved known characters">
                                <i data-lucide="rotate-ccw" style="width:14px;height:14px;"></i> Reset Local
                            </button>
                        </div>
                    </div>
                    <p style="color: var(--text-secondary); margin-bottom: 1.5rem; font-size: 0.95rem;">
                        These characters are required for HSK 4 vocabulary but have not yet been added to your Characters deck.
                    </p>
                    <div id="file-protocol-tip" style="display:none; margin-bottom: 1.5rem; padding: 1rem; background: rgba(79, 172, 254, 0.05); border: 1px solid rgba(79, 172, 254, 0.15); border-radius: 12px; font-size: 0.9rem; color: var(--text-secondary);">
                        <div style="display: flex; align-items: center; gap: 0.75rem;">
                            <i data-lucide="info" style="color: var(--accent-blue); flex-shrink: 0;"></i>
                            <div>
                                You are viewing the dashboard as a static file. Marking characters as known will be saved in browser storage. 
                                To save permanently to disk and update Python reports, run <code style="background: rgba(255,255,255,0.06); padding: 0.2rem 0.4rem; border-radius: 4px; color: var(--accent-cyan);">python server.py</code> and open <a href="http://localhost:8000" style="color: var(--accent-blue); text-decoration: underline;">http://localhost:8000</a>.
                            </div>
                        </div>
                    </div>
                    <div id="missing-chars-container" class="mbp-grid">
                        <!-- Dynamically populated -->
                    </div>
                    <div id="missing-chars-pagination" style="display: flex; justify-content: center; align-items: center; gap: 1.5rem; margin-top: 2rem; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 1.5rem;">
                        <button class="btn" id="btn-prev-missing-chars" onclick="changeMissingCharsPage(-1)">
                            <i data-lucide="chevron-left" style="width:16px;height:16px;"></i> Previous
                        </button>
                        <span id="missing-chars-page-info" style="font-size: 0.95rem; color: var(--text-secondary); font-weight: 500;">Page 1 of 1</span>
                        <button class="btn" id="btn-next-missing-chars" onclick="changeMissingCharsPage(1)">
                            Next <i data-lucide="chevron-right" style="width:16px;height:16px;"></i>
                        </button>
                    </div>
                </div>

                <!-- Missing HSK Words table panel -->
                <div class="panel">
                    <div class="panel-header">
                        <h3><i data-lucide="alert-triangle"></i> HSK Words Missing from Migaku Deck</h3>
                        <div style="display: flex; gap: 0.75rem; align-items: center;">
                            <span class="badge badge-red" id="missing-words-badge">0 Words</span>
                            <button class="btn btn-sm btn-primary" id="btn-export-missing-words" onclick="exportMissingWords()" title="Copy missing words as CSV format">
                                <i data-lucide="download" style="width:14px;height:14px;"></i> Export Missing Words
                            </button>
                            <button class="btn btn-sm" id="btn-export-known-words" onclick="exportKnownWords()" title="Copy known words as CSV format">
                                <i data-lucide="clipboard" style="width:14px;height:14px;"></i> Export Known Words
                            </button>
                            <button class="btn btn-sm" id="btn-reset-known-words" onclick="resetLocalKnownWords()" style="background: rgba(239, 68, 68, 0.1); border-color: rgba(239, 68, 68, 0.2); color: var(--accent-red);" title="Reset browser-saved known words">
                                <i data-lucide="rotate-ccw" style="width:14px;height:14px;"></i> Reset Local
                            </button>
                        </div>
                    </div>
                    <p style="color: var(--text-secondary); margin-bottom: 1.5rem; font-size: 0.95rem;">
                        These vocabulary words from HSK 4 are missing from your Migaku deck.
                    </p>
                    <div class="controls-row">
                        <div class="search-wrapper">
                            <i data-lucide="search"></i>
                            <input type="text" id="missing-words-search" placeholder="Search missing HSK words by Hanzi, Pinyin, or Meaning...">
                        </div>
                    </div>

                    <div class="custom-table-container">
                        <table id="missing-words-table">
                            <thead>
                                <tr>
                                    <th>Word</th>
                                    <th>Pinyin</th>
                                    <th>Spanish Meaning</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                <!-- Dynamically populated -->
                            </tbody>
                        </table>
                    </div>
                </div>
            </section>
        </main>
    </div>

    <!-- Toast message for copies -->
    <div class="toast" id="toast">
        <i data-lucide="check-circle"></i>
        Copied to clipboard!
    </div>

    <!-- Embedded Data Object -->
    <script id="dashboard-data" type="application/json">
        __DATA_PLACEHOLDER__
    </script>

    <script>
        // Load data from embedded JSON script block
        const rawData = document.getElementById('dashboard-data').textContent;
        const DATA = JSON.parse(rawData);

        // Safe localStorage helper to prevent SecurityError on file:/// protocol in some browsers
        const safeLocalStorage = {
            getItem(key) {
                try {
                    return localStorage.getItem(key);
                } catch (e) {
                    console.warn("localStorage.getItem failed:", e);
                    return null;
                }
            },
            setItem(key, value) {
                try {
                    localStorage.setItem(key, value);
                } catch (e) {
                    console.warn("localStorage.setItem failed:", e);
                }
            },
            removeItem(key) {
                try {
                    localStorage.removeItem(key);
                } catch (e) {
                    console.warn("localStorage.removeItem failed:", e);
                }
            }
        };

        // Merge known characters from server data and browser localStorage
        const serverKnownChars = new Set(DATA.known_characters || []);
        const localKnownChars = JSON.parse(safeLocalStorage.getItem('known_hsk_characters') || '[]');
        
        // Cleanup local storage if they are already saved to server disk
        const filteredLocalKnown = localKnownChars.filter(c => !serverKnownChars.has(c));
        safeLocalStorage.setItem('known_hsk_characters', JSON.stringify(filteredLocalKnown));
        
        const allKnownChars = new Set([...serverKnownChars, ...filteredLocalKnown]);
        DATA.missing_chars_hsk = DATA.missing_chars_hsk.filter(char => !allKnownChars.has(char));

        // Merge known words from server data and browser localStorage
        const serverKnownWords = new Set(DATA.known_words || []);
        const localKnownWords = JSON.parse(safeLocalStorage.getItem('known_hsk_words') || '[]');
        
        // Cleanup local storage if they are already saved to server disk
        const filteredLocalKnownWords = localKnownWords.filter(w => !serverKnownWords.has(w));
        safeLocalStorage.setItem('known_hsk_words', JSON.stringify(filteredLocalKnownWords));
        
        const allKnownWords = new Set([...serverKnownWords, ...filteredLocalKnownWords]);
        DATA.missing_hsk_words_in_migaku = DATA.missing_hsk_words_in_migaku.filter(w => !allKnownWords.has(w.word));

        // Render stats and values
        document.getElementById('stat-learned-count').textContent = DATA.stats.learned_chars_count;
        document.getElementById('stat-immersion-count').textContent = DATA.stats.total_immersion_cards;
        document.getElementById('stat-gaps-count').textContent = DATA.stats.total_gaps_count;
        document.getElementById('stat-synergy-count').textContent = DATA.synergy_words.length;
        document.getElementById('stat-leech-count').textContent = DATA.leeches.length;
        document.getElementById('stat-conflict-count').textContent = DATA.conflicts.length;
        document.getElementById('stat-inconsistent-count').textContent = DATA.inconsistencies.length;
        
        document.getElementById('n1-badge').textContent = DATA.n1_sentences.length;
        document.getElementById('n1-count-badge').textContent = DATA.n1_sentences.length + ' Sentences';
        document.getElementById('synergy-count-badge').textContent = DATA.synergy_words.length + ' Words';
        document.getElementById('top-gaps-badge').textContent = DATA.stats.top_gaps.length + ' Gaps';
        
        // Populate missing pieces counts
        document.getElementById('stat-missing-chars-count').textContent = DATA.missing_chars_hsk.length;
        document.getElementById('stat-missing-words-count').textContent = DATA.missing_hsk_words_in_migaku.length;
        document.getElementById('missing-badge').textContent = DATA.missing_hsk_words_in_migaku.length;
        document.getElementById('missing-words-badge').textContent = DATA.missing_hsk_words_in_migaku.length + ' Words';
        
        if (DATA.timestamp) {
            document.getElementById('timestamp-tag').textContent = 'Last sync: ' + DATA.timestamp;
        }

        // Initialize Lucide Icons
        lucide.createIcons();

        // Auto-sync local storage to server disk on page load (runs only on localhost)
        async function syncLocalStorageToServer() {
            const isLiveServer = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
            if (!isLiveServer) return;

            let needsReload = false;

            // Sync characters
            if (filteredLocalKnown.length > 0) {
                console.log(`Syncing ${filteredLocalKnown.length} characters to server...`);
                for (const char of filteredLocalKnown) {
                    try {
                        const response = await fetch('http://localhost:8000/api/known_characters', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ character: char })
                        });
                        if (response.ok) {
                            needsReload = true;
                        }
                    } catch (e) {
                        console.error('Failed to auto-sync character:', char, e);
                    }
                }
            }

            // Sync words
            if (filteredLocalKnownWords.length > 0) {
                console.log(`Syncing ${filteredLocalKnownWords.length} words to server...`);
                for (const word of filteredLocalKnownWords) {
                    try {
                        const response = await fetch('http://localhost:8000/api/known_words', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ word: word })
                        });
                        if (response.ok) {
                            needsReload = true;
                        }
                    } catch (e) {
                        console.error('Failed to auto-sync word:', word, e);
                    }
                }
            }

            if (needsReload) {
                // Clear successfully synced items from localStorage
                safeLocalStorage.setItem('known_hsk_characters', JSON.stringify([]));
                safeLocalStorage.setItem('known_hsk_words', JSON.stringify([]));
                showToast('Synchronized local selections to disk!');
                setTimeout(() => {
                    location.reload();
                }, 1000);
            }
        }

        // Run sync on load
        syncLocalStorageToServer();

        // Toast Helper
        function showToast(message) {
            const toast = document.getElementById('toast');
            toast.innerHTML = '<i data-lucide="check-circle"></i> ' + message;
            lucide.createIcons();
            toast.classList.add('show');
            setTimeout(() => {
                toast.classList.remove('show');
            }, 2000);
        }

        // Copy Text Helper
        function copyToClipboard(text) {
            navigator.clipboard.writeText(text).then(() => {
                showToast('Copied to clipboard!');
            });
        }

        // Mark Character as Known logic
        async function markCharacterAsKnown(char) {
            // Add to local browser storage
            const localKnown = JSON.parse(safeLocalStorage.getItem('known_hsk_characters') || '[]');
            if (!localKnown.includes(char)) {
                localKnown.push(char);
                safeLocalStorage.setItem('known_hsk_characters', JSON.stringify(localKnown));
            }
            
            // Immediately animate out and remove card from DOM
            const card = document.getElementById(`missing-char-${char}`);
            if (card) {
                card.style.transition = 'all 0.3s ease';
                card.style.opacity = '0';
                card.style.transform = 'scale(0.9)';
                setTimeout(() => {
                    DATA.missing_chars_hsk = DATA.missing_chars_hsk.filter(c => c !== char);
                    renderMissingCharacters();
                }, 300);
            }
            
            // Adjust statistics dynamically
            const charCountElement = document.getElementById('stat-missing-chars-count');
            if (charCountElement) {
                const currentVal = parseInt(charCountElement.textContent) || 0;
                charCountElement.textContent = Math.max(0, currentVal - 1);
            }
            
            // Try to send POST request to the local server
            try {
                const response = await fetch('http://localhost:8000/api/known_characters', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ character: char })
                });
                
                if (response.ok) {
                    showToast(`"${char}" saved to known_characters.csv on disk!`);
                } else {
                    throw new Error('Server returned non-ok status');
                }
            } catch (e) {
                showToast(`"${char}" saved to browser storage. Run server.py to save to disk.`);
            }
        }

        // Export all known characters (local + server) to CSV copied to clipboard
        function exportKnownCharacters() {
            const serverKnown = DATA.known_characters || [];
            const localKnown = JSON.parse(safeLocalStorage.getItem('known_hsk_characters') || '[]');
            const allKnown = Array.from(new Set([...serverKnown, ...localKnown]));
            
            if (allKnown.length === 0) {
                showToast('No known characters to export.');
                return;
            }
            
            const csvContent = "Character\\n" + allKnown.join("\\n");
            copyToClipboard(csvContent);
            showToast('Known characters CSV copied to clipboard!');
        }

        // Export all missing characters to CSV copied to clipboard
        function exportMissingCharacters() {
            const missing = DATA.missing_chars_hsk || [];
            if (missing.length === 0) {
                showToast('No missing characters to export.');
                return;
            }
            const csvContent = "Character\\n" + missing.join("\\n");
            copyToClipboard(csvContent);
            showToast('Missing characters CSV copied to clipboard!');
        }

        // Reset local storage known characters
        function resetLocalKnownCharacters() {
            if (confirm('Are you sure you want to clear all browser-saved known characters? (This will not delete characters already saved to known_characters.csv on disk)')) {
                safeLocalStorage.removeItem('known_hsk_characters');
                showToast('Browser storage cleared! Reloading page...');
                setTimeout(() => {
                    location.reload();
                }, 1000);
            }
        }

        // Mark HSK Word as Known logic
        async function markWordAsKnown(word) {
            // Add to local browser storage
            const localKnown = JSON.parse(safeLocalStorage.getItem('known_hsk_words') || '[]');
            if (!localKnown.includes(word)) {
                localKnown.push(word);
                safeLocalStorage.setItem('known_hsk_words', JSON.stringify(localKnown));
            }
            
            // Immediately animate out and remove card/row from DOM
            const row = document.getElementById(`missing-word-row-${word}`);
            if (row) {
                row.style.transition = 'all 0.3s ease';
                row.style.opacity = '0';
                setTimeout(() => {
                    row.remove();
                    // Recalculate row counts or show empty state if necessary
                    const tbody = document.querySelector('#missing-words-table tbody');
                    if (tbody && tbody.children.length === 0) {
                        tbody.innerHTML = '<tr><td colspan="4" class="empty-state"><i data-lucide="search"></i>No missing HSK words.</td></tr>';
                        lucide.createIcons();
                    }
                }, 300);
            }
            
            // Adjust statistics dynamically
            const wordCountElements = [
                document.getElementById('stat-missing-words-count'),
                document.getElementById('missing-words-badge'),
                document.getElementById('missing-badge')
            ];
            wordCountElements.forEach(elem => {
                if (elem) {
                    const currentVal = parseInt(elem.textContent) || 0;
                    const newVal = Math.max(0, currentVal - 1);
                    if (elem.id === 'missing-words-badge') {
                        elem.textContent = newVal + ' Words';
                    } else {
                        elem.textContent = newVal;
                    }
                }
            });
            
            // Try to send POST request to the local server
            try {
                const response = await fetch('http://localhost:8000/api/known_words', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ word: word })
                });
                
                if (response.ok) {
                    showToast(`"${word}" saved to known_words.csv on disk!`);
                } else {
                    throw new Error('Server returned non-ok status');
                }
            } catch (e) {
                showToast(`"${word}" saved to browser storage. Run server.py to save to disk.`);
            }
        }

        // Export all known words (local + server) to CSV copied to clipboard
        function exportKnownWords() {
            const serverKnown = DATA.known_words || [];
            const localKnown = JSON.parse(safeLocalStorage.getItem('known_hsk_words') || '[]');
            const allKnown = Array.from(new Set([...serverKnown, ...localKnown]));
            
            if (allKnown.length === 0) {
                showToast('No known words to export.');
                return;
            }
            
            const csvContent = "Word\\n" + allKnown.join("\\n");
            copyToClipboard(csvContent);
            showToast('Known words CSV copied to clipboard!');
        }

        // Export all missing words to CSV copied to clipboard
        function exportMissingWords() {
            const missing = DATA.missing_hsk_words_in_migaku || [];
            if (missing.length === 0) {
                showToast('No missing words to export.');
                return;
            }
            
            const escapeCsv = (str) => {
                if (!str) return '';
                const clean = str.replace(/"/g, '""');
                return clean.includes(',') || clean.includes('\\n') || clean.includes('"') ? `"${clean}"` : clean;
            };
            
            let csvContent = "Word,Pinyin,Meaning\\n";
            missing.forEach(w => {
                csvContent += `${escapeCsv(w.word)},${escapeCsv(w.pinyin)},${escapeCsv(w.meaning)}\\n`;
            });
            
            copyToClipboard(csvContent);
            showToast('Missing words CSV copied to clipboard!');
        }

        // Reset local storage known words
        function resetLocalKnownWords() {
            if (confirm('Are you sure you want to clear all browser-saved known words? (This will not delete words already saved to known_words.csv on disk)')) {
                safeLocalStorage.removeItem('known_hsk_words');
                showToast('Browser storage cleared! Reloading page...');
                setTimeout(() => {
                    location.reload();
                }, 1000);
            }
        }

        // Tab Switching Logic
        const navItems = document.querySelectorAll('.nav-item');
        const panels = document.querySelectorAll('.tab-panel');
        
        const panelTitles = {
            'overview': 'Palace Dashboard',
            'leeches': 'Leech Diagnostics & Memory Health',
            'sentences': 'N+1 Immersion Sentence Miner',
            'synergy': 'HSK 1-4 Synergy Study Guide',
            'codebook': 'Mnemonic Palace Codebook & Helper',
            'graph': 'Connection Graph Explorer',
            'missing': 'Missing HSK Pieces'
        };

        const panelDescs = {
            'overview': 'Overview of HSK 4 characters and immersion sentence statistics.',
            'leeches': 'Identify card fatigue, memory lapses, and visual or phonetic overlaps.',
            'sentences': 'Sentences from your immersion deck that require exactly one character to read.',
            'synergy': 'Vocabulary words ready for study with zero new characters to memorize.',
            'codebook': 'Your configured Actor, Set, and Location maps, plus a card creation guide.',
            'graph': 'Search and visualize the relationships between characters, components, and vocabulary.',
            'missing': 'HSK 4 characters and vocabulary words that are not in your Anki decks.'
        };

        navItems.forEach(item => {
            item.addEventListener('click', () => {
                const targetTab = item.getAttribute('data-tab');
                
                navItems.forEach(nav => nav.classList.remove('active'));
                panels.forEach(p => p.classList.remove('active'));
                
                item.classList.add('active');
                document.getElementById(targetTab + '-tab').classList.add('active');
                
                // Update header titles
                document.getElementById('panel-title-text').textContent = panelTitles[targetTab];
                document.getElementById('panel-desc-text').textContent = panelDescs[targetTab];
                
                if (targetTab === 'graph') {
                    initGraphView();
                }
            });
        });

        // 1. Populate Top Gaps Table (Overview)
        const gapsTableBody = document.querySelector('#top-gaps-table tbody');
        if (DATA.stats.top_gaps.length === 0) {
            gapsTableBody.innerHTML = '<tr><td colspan="4" class="empty-state"><i data-lucide="smile"></i>No character gaps! You can read all characters in your immersion.</td></tr>';
        } else {
            DATA.stats.top_gaps.slice(0, 20).forEach(gap => {
                const char = gap[0];
                const count = gap[1];
                
                // Find potential pinyin/tone/loc for this gap character if it exists in HSK list
                let hskInfo = '';
                let toneLoc = 'Unknown';
                // Try HSK lookup for details
                const unlocked = DATA.unlocked_chars.find(u => u.character === char);
                if (unlocked && unlocked.unlocked_words.length > 0) {
                    hskInfo = ` (Unlocks: ${unlocked.unlocked_words[0].word})`;
                }
                
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td class="hanzi-col">${char}</td>
                    <td><span class="badge badge-orange">${count} cards</span>${hskInfo}</td>
                    <td><span class="badge badge-purple">${toneLoc}</span></td>
                    <td>
                        <button class="btn btn-primary btn-sm" onclick="copyToClipboard('${char}')">
                            <i data-lucide="copy" style="width:14px;height:14px;"></i> Copy Hanzi
                        </button>
                    </td>
                `;
                gapsTableBody.appendChild(tr);
            });
            if (DATA.stats.top_gaps.length > 20) {
                const tr = document.createElement('tr');
                tr.innerHTML = `<td colspan="4" style="color:var(--text-muted);text-align:center;">Showing top 20 of ${DATA.stats.top_gaps.length} character gaps. Run scripts to refresh.</td>`;
                gapsTableBody.appendChild(tr);
            }
        }

        // 2. Populate Leeches Tab
        const leechesTableBody = document.querySelector('#leeches-table tbody');
        if (DATA.leeches.length === 0) {
            leechesTableBody.innerHTML = '<tr><td colspan="5" class="empty-state"><i data-lucide="smile"></i>No leeches found! Your memory palace is solid.</td></tr>';
        } else {
            DATA.leeches.slice(0, 30).forEach(leech => {
                const tr = document.createElement('tr');
                const badgeClass = leech.lapses >= 10 ? 'badge-red' : (leech.lapses >= 5 ? 'badge-orange' : 'badge-purple');
                const mnemonic = leech.actor || leech.set || leech.location 
                    ? `<strong>Actor</strong>: ${leech.actor || '-'}, <strong>Set</strong>: ${leech.set || '-'}, <strong>Loc</strong>: ${leech.location || '-'}`
                    : 'No mnemonic data';
                tr.innerHTML = `
                    <td class="hanzi-col" style="color:var(--accent-red)">${leech.hanzi}</td>
                    <td>${leech.pinyin}</td>
                    <td><span class="badge ${badgeClass}">${leech.lapses} lapses</span></td>
                    <td><span class="badge badge-cyan">${leech.ease / 10}%</span></td>
                    <td style="font-size:0.85rem;color:var(--text-secondary);">${mnemonic}</td>
                `;
                leechesTableBody.appendChild(tr);
            });
            if (DATA.leeches.length > 30) {
                const tr = document.createElement('tr');
                tr.innerHTML = `<td colspan="5" style="color:var(--text-muted);text-align:center;">Showing top 30 of ${DATA.leeches.length} leeches.</td>`;
                leechesTableBody.appendChild(tr);
            }
        }

        // Populate Conflicts List
        const conflictContainer = document.getElementById('conflict-list-container');
        if (DATA.conflicts.length === 0) {
            conflictContainer.innerHTML = '<div class="empty-state"><i data-lucide="check-circle-2"></i>No card conflicts detected! Your mnemonic markers are well-differentiated.</div>';
        } else {
            DATA.conflicts.forEach(c => {
                const item = document.createElement('div');
                item.className = 'conflict-item';
                
                let reasonsHtml = '';
                c.reasons.forEach(r => {
                    reasonsHtml += `<li>${r}</li>`;
                });
                
                item.innerHTML = `
                    <div class="conflict-header">
                        <div>
                            <span class="conflict-char" style="color:var(--accent-red)">${c.char1}</span> 
                            <span style="color:var(--text-secondary);font-size:0.9rem;">(${c.char1_pinyin}, ${c.char1_lapses} lapses)</span>
                        </div>
                        <div style="color:var(--accent-orange);font-weight:700;">VS</div>
                        <div>
                            <span class="conflict-char" style="color:var(--accent-red)">${c.char2}</span> 
                            <span style="color:var(--text-secondary);font-size:0.9rem;">(${c.char2_pinyin}, ${c.char2_lapses} lapses)</span>
                        </div>
                    </div>
                    <ul class="conflict-reasons">
                        ${reasonsHtml}
                    </ul>
                `;
                conflictContainer.appendChild(item);
            });
        }

        // Populate Inconsistencies List
        const incListContainer = document.getElementById('inconsistency-list');
        if (DATA.inconsistencies.length === 0) {
            incListContainer.innerHTML = '<div class="empty-state"><i data-lucide="check"></i>All cards match your standard codebook perfectly!</div>';
        } else {
            DATA.inconsistencies.forEach(inc => {
                const item = document.createElement('div');
                item.className = 'inconsistency-item';
                
                let issuesHtml = '';
                inc.issues.forEach(issue => {
                    issuesHtml += `<div>• ${issue}</div>`;
                });
                
                item.innerHTML = `
                    <div style="font-weight:600;margin-bottom:0.25rem;">
                        <span style="font-size:1.1rem;color:var(--text-primary);">${inc.hanzi}</span> (${inc.pinyin})
                    </div>
                    <div style="color:var(--text-secondary);font-size:0.8rem;line-height:1.4;">
                        ${issuesHtml}
                    </div>
                `;
                incListContainer.appendChild(item);
            });
        }

        // 3. Populate N+1 Sentences
        const sentContainer = document.getElementById('sentences-list-container');
        
        function renderN1Sentences(filterText = '') {
            sentContainer.innerHTML = '';
            const hideLow = document.getElementById('hide-low-context').checked;
            const filtered = DATA.n1_sentences.filter(sent => {
                const t = filterText.toLowerCase();
                const matchesText = sent.sentence.toLowerCase().includes(t) || 
                                    sent.translation.toLowerCase().includes(t) || 
                                    sent.missing_char.toLowerCase().includes(t);
                if (hideLow && sent.low_context) return false;
                return matchesText;
            });

            if (filtered.length === 0) {
                sentContainer.innerHTML = '<div class="empty-state"><i data-lucide="search"></i>No sentences match your filter.</div>';
                return;
            }

            // Show top 30 filtered items to avoid browser lag
            filtered.slice(0, 35).forEach(sent => {
                const card = document.createElement('div');
                card.className = 'sentence-card';
                
                // Format sentence to highlight missing character
                let formattedSentence = sent.sentence;
                // Surround missing character with a tag
                const mc = sent.missing_char;
                const escMc = mc.replace(/[-\/\\\\^$*+?.()|[\]{}]/g, '\\\\$&');
                formattedSentence = formattedSentence.replace(new RegExp(escMc, 'g'), `<span class="gap-char">${mc}</span>`);
                
                // Check if low context
                let warningHtml = '';
                if (sent.low_context) {
                    warningHtml = `<span class="badge" style="background: rgba(239, 68, 68, 0.1); color: #EF4444; border: 1px solid rgba(239, 68, 68, 0.2); margin-right: 0.5rem;" title="${sent.low_context_reason}">
                        <i data-lucide="alert-circle" style="width:12px;height:12px;display:inline-block;vertical-align:middle;margin-right:4px;"></i>Low Context
                    </span>`;
                }
                
                card.innerHTML = `
                    <div class="sentence-left">
                        <div class="chinese-text">${formattedSentence}</div>
                        <div class="sentence-translation">${sent.translation}</div>
                    </div>
                    <div class="sentence-actions">
                        ${warningHtml}
                        <span class="badge badge-orange" style="margin-right:1rem;">Missing: ${sent.missing_char} (seen ${sent.char_freq}x)</span>
                        <button class="btn btn-sm btn-primary" onclick="copyToClipboard('${sent.sentence}')">
                            <i data-lucide="copy" style="width:14px;height:14px;"></i> Copy Sentence
                        </button>
                    </div>
                `;
                sentContainer.appendChild(card);
            });

            if (filtered.length > 35) {
                const moreCard = document.createElement('div');
                moreCard.style.cssText = 'color:var(--text-muted);text-align:center;padding:1rem;';
                moreCard.textContent = `Showing 35 of ${filtered.length} matching sentences. Narrow your search for more.`;
                sentContainer.appendChild(moreCard);
            }
            lucide.createIcons();
        }

        document.getElementById('sentences-search').addEventListener('input', (e) => {
            renderN1Sentences(e.target.value);
        });

        document.getElementById('hide-low-context').addEventListener('change', () => {
            renderN1Sentences(document.getElementById('sentences-search').value);
        });

        renderN1Sentences();

        // 4. Populate HSK Synergy
        const synergyTableBody = document.querySelector('#synergy-table tbody');
        
        function renderSynergyWords(filterText = '') {
            synergyTableBody.innerHTML = '';
            const filtered = DATA.synergy_words.filter(word => {
                const t = filterText.toLowerCase();
                return word.word.toLowerCase().includes(t) || 
                       word.pinyin.toLowerCase().includes(t) || 
                       word.meanings.toLowerCase().includes(t);
            });

            if (filtered.length === 0) {
                synergyTableBody.innerHTML = '<tr><td colspan="3" class="empty-state"><i data-lucide="search"></i>No synergy words match your search.</td></tr>';
                return;
            }

            filtered.slice(0, 100).forEach(w => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td class="hanzi-col" style="color:var(--accent-purple)">${w.word}</td>
                    <td>${w.pinyin}</td>
                    <td style="font-size:0.85rem;color:var(--text-secondary);max-width:500px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="${w.meanings}">
                        ${w.meanings}
                    </td>
                `;
                synergyTableBody.appendChild(tr);
            });

            if (filtered.length > 100) {
                const tr = document.createElement('tr');
                tr.innerHTML = `<td colspan="3" style="color:var(--text-muted);text-align:center;">Showing top 100 of ${filtered.length} synergy words.</td>`;
                synergyTableBody.appendChild(tr);
            }
        }

        document.getElementById('synergy-search').addEventListener('input', (e) => {
            renderSynergyWords(e.target.value);
        });

        renderSynergyWords();

        // 5. Populate Codebook Grid
        const actorsGrid = document.getElementById('actors-grid');
        const setsGrid = document.getElementById('sets-grid');
        const locationsGrid = document.getElementById('locations-grid');

        // Render Actors
        const alphabet = ['b', 'p', 'm', 'f', 'd', 't', 'n', 'l', 'g', 'k', 'h', 'j', 'q', 'x', 'zh', 'ch', 'sh', 'r', 'z', 'c', 's', 'y', 'w'];
        alphabet.forEach(init => {
            const card = document.createElement('div');
            const actor = DATA.codebook.actors[init];
            card.className = actor ? 'mbp-card' : 'mbp-card vacant';
            card.innerHTML = `
                <div class="mbp-key">Initial: ${init.toUpperCase()}</div>
                <div class="mbp-val">${actor || 'Vacant'}</div>
            `;
            actorsGrid.appendChild(card);
        });

        // Render Sets
        const finalsList = ['a', 'o', 'e', 'i', 'u', 'v', 'ai', 'ei', 'ui', 'ao', 'ou', 'iu', 'ie', 've', 'er', 'an', 'en', 'in', 'un', 'vn', 'ang', 'eng', 'ing', 'ong'];
        finalsList.forEach(fin => {
            const card = document.createElement('div');
            const c_set = DATA.codebook.sets[fin];
            card.className = c_set ? 'mbp-card' : 'mbp-card vacant';
            card.innerHTML = `
                <div class="mbp-key">Final: -${fin}</div>
                <div class="mbp-val">${c_set || 'Vacant'}</div>
            `;
            setsGrid.appendChild(card);
        });

        // Render Locations
        ['1', '2', '3', '4', '5'].forEach(tone => {
            const card = document.createElement('div');
            const loc = DATA.codebook.locations[tone];
            card.className = loc ? 'mbp-card' : 'mbp-card vacant';
            card.innerHTML = `
                <div class="mbp-key">Tone ${tone}</div>
                <div class="mbp-val">${loc || 'Vacant'}</div>
            `;
            locationsGrid.appendChild(card);
        });

        // 6. Mnemonic Helper Logic
        const helperHanzi = document.getElementById('helper-hanzi');
        const helperPinyin = document.getElementById('helper-pinyin');
        const helperResult = document.getElementById('helper-result');
        const resultActorVal = document.getElementById('result-actor-val');
        const resultActorTitle = document.getElementById('result-actor-title');
        const resultSetVal = document.getElementById('result-set-val');
        const resultSetTitle = document.getElementById('result-set-title');
        const resultLocVal = document.getElementById('result-loc-val');

        function splitPinyinJS(pinyin) {
            pinyin = pinyin.toLowerCase().trim();
            // Remove numbers (tones)
            let tone = '';
            const toneMatch = pinyin.match(/[1-5]/);
            if (toneMatch) {
                tone = toneMatch[0];
            }
            
            pinyin = pinyin.replace(/[1-5]/g, '');
            
            // Tone vowel marks normalization
            const vowelMap = {
                'ā': ['a', '1'], 'á': ['a', '2'], 'ǎ': ['a', '3'], 'à': ['a', '4'],
                'ē': ['e', '1'], 'é': ['e', '2'], 'ě': ['e', '3'], 'è': ['e', '4'],
                'ī': ['i', '1'], 'í': ['i', '2'], 'ǐ': ['i', '3'], 'ì': ['i', '4'],
                'ō': ['o', '1'], 'ó': ['o', '2'], 'ǒ': ['o', '3'], 'ò': ['o', '4'],
                'ū': ['u', '1'], 'ú': ['u', '2'], 'ǔ': ['u', '3'], 'ù': ['u', '4'],
                'ǖ': ['v', '1'], 'ǘ': ['v', '2'], 'ǚ': ['v', '3'], 'ǜ': ['v', '4'],
                'ü': ['v', '0']
            };
            
            let cleanP = '';
            for (let char of pinyin) {
                if (vowelMap[char]) {
                    cleanP += vowelMap[char][0];
                    if (!tone) tone = vowelMap[char][1];
                } else {
                    cleanP += char;
                }
            }
            
            cleanP = cleanP.replace(/[^a-z]/g, '');
            
            if (!cleanP) return { init: '', fin: '', tone: tone || 'Unknown' };
            
            // Check double initials
            for (let doubleInit of ['zh', 'ch', 'sh']) {
                if (cleanP.startsWith(doubleInit)) {
                    return { init: doubleInit, fin: cleanP.substring(2), tone: tone || 'Unknown' };
                }
            }
            
            // Check single initials
            const singleInitials = ['b', 'p', 'm', 'f', 'd', 't', 'n', 'l', 'g', 'k', 'h', 'j', 'q', 'x', 'z', 'c', 's', 'y', 'w'];
            if (singleInitials.includes(cleanP[0])) {
                return { init: cleanP[0], fin: cleanP.substring(1), tone: tone || 'Unknown' };
            }
            
            return { init: '', fin: cleanP, tone: tone || 'Unknown' };
        }

        function updateMnemonicHelper() {
            const hz = helperHanzi.value.trim();
            const py = helperPinyin.value.trim();
            
            if (!py) {
                helperResult.style.display = 'none';
                return;
            }
            
            const { init, fin, tone } = splitPinyinJS(py);
            
            // Lookup Actor
            const actor = DATA.codebook.actors[init] || 'No Actor Configured';
            resultActorTitle.textContent = `Actor (Initial: ${init ? init.toUpperCase() : 'None'})`;
            resultActorVal.textContent = actor;
            
            // Lookup Set
            // Normalize finals list to find standard
            let finalKey = fin;
            if (finalKey === 'i' && !init) finalKey = 'i'; // e.g. yi
            const c_set = DATA.codebook.sets[finalKey] || 'No Set Configured';
            resultSetTitle.textContent = `Set (Final: -${finalKey || 'None'})`;
            resultSetVal.textContent = c_set;
            
            // Lookup Tone location
            const loc = DATA.codebook.locations[tone] || 'No Location Configured';
            resultLocVal.textContent = loc + (tone !== 'Unknown' ? ` [Tone ${tone}]` : '');
            
            helperResult.style.display = 'block';
            lucide.createIcons();
        }

        helperHanzi.addEventListener('input', updateMnemonicHelper);
        helperPinyin.addEventListener('input', updateMnemonicHelper);

        // 7. Populate Missing HSK Pieces Tab
        if (window.location.protocol === 'file:') {
            const tip = document.getElementById('file-protocol-tip');
            if (tip) tip.style.display = 'block';
        }

        let missingCharsPage = 1;
        const missingCharsPageSize = 24;

        function renderMissingCharacters() {
            const container = document.getElementById('missing-chars-container');
            if (!container) return;
            container.innerHTML = '';
            
            const totalItems = DATA.missing_chars_hsk.length;
            if (totalItems === 0) {
                container.innerHTML = '<div class="empty-state"><i data-lucide="smile"></i>All HSK characters are in your palace!</div>';
                document.getElementById('missing-chars-pagination').style.display = 'none';
                lucide.createIcons();
                return;
            }

            const totalPages = Math.ceil(totalItems / missingCharsPageSize);
            if (missingCharsPage > totalPages) {
                missingCharsPage = Math.max(1, totalPages);
            }

            const start = (missingCharsPage - 1) * missingCharsPageSize;
            const end = Math.min(start + missingCharsPageSize, totalItems);
            const pageItems = DATA.missing_chars_hsk.slice(start, end);

            pageItems.forEach(char => {
                const card = document.createElement('div');
                card.className = 'mbp-card';
                card.style.borderColor = 'rgba(239, 68, 68, 0.2)';
                card.id = `missing-char-${char}`;
                card.innerHTML = `
                    <div class="mbp-val" style="font-size: 1.8rem; text-align: center; color: var(--accent-red); margin-bottom: 0.5rem;">${char}</div>
                    <div style="display: flex; gap: 0.5rem; width: 100%;">
                        <button class="btn btn-sm" style="flex: 1; padding: 0.5rem; justify-content: center;" onclick="copyToClipboard('${char}')" title="Copy Hanzi to clipboard">
                            <i data-lucide="copy" style="width:14px;height:14px;"></i> Copy
                        </button>
                        <button class="btn btn-sm btn-primary" style="flex: 1; padding: 0.5rem; justify-content: center; background: linear-gradient(135deg, #34D399 0%, #059669 100%); color: #0B0F19;" onclick="markCharacterAsKnown('${char}')" title="Mark as already known">
                            <i data-lucide="check" style="width:14px;height:14px;"></i> Known
                        </button>
                    </div>
                `;
                container.appendChild(card);
            });

            const paginationContainer = document.getElementById('missing-chars-pagination');
            if (paginationContainer) {
                paginationContainer.style.display = totalPages > 1 ? 'flex' : 'none';
                document.getElementById('missing-chars-page-info').textContent = `Page ${missingCharsPage} of ${totalPages} (${totalItems} total)`;
                document.getElementById('btn-prev-missing-chars').disabled = missingCharsPage === 1;
                document.getElementById('btn-next-missing-chars').disabled = missingCharsPage === totalPages;
            }

            lucide.createIcons();
        }

        function changeMissingCharsPage(offset) {
            const totalItems = DATA.missing_chars_hsk.length;
            const totalPages = Math.ceil(totalItems / missingCharsPageSize);
            const targetPage = missingCharsPage + offset;
            if (targetPage >= 1 && targetPage <= totalPages) {
                missingCharsPage = targetPage;
                renderMissingCharacters();
                document.getElementById('missing-tab').scrollIntoView({ behavior: 'smooth' });
            }
        }

        renderMissingCharacters();

        const missingWordsTableBody = document.querySelector('#missing-words-table tbody');
        
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
        }

        document.getElementById('missing-words-search').addEventListener('input', (e) => {
            renderMissingWords(e.target.value);
        });

        renderMissingWords();

        // ==========================================
        // CONNECTION GRAPH EXPLORER CODE
        // ==========================================

        let network = null;
        let graphInitialized = false;

        // Build index lookup maps
        const charMap = new Map();
        DATA.characters.forEach(c => {
            if (c.hanzi) charMap.set(c.hanzi, c);
            if (c.simplified && c.simplified !== c.hanzi) charMap.set(c.simplified, c);
        });

        const wordMap = new Map();
        DATA.immersion.forEach(w => {
            if (w.word) wordMap.set(w.word, w);
        });

        const propMap = new Map();
        if (DATA.props) {
            DATA.props.forEach(p => {
                if (p.component) propMap.set(p.component, p);
            });
        }

        // Index: component/prop -> list of characters containing it
        const componentOfIndex = new Map();
        DATA.characters.forEach(c => {
            if (c.components && Array.isArray(c.components)) {
                c.components.forEach(comp => {
                    const cleanComp = comp.replace(/^\[([^|\]]+).*$/, '$1').trim();
                    if (cleanComp) {
                        if (!componentOfIndex.has(cleanComp)) {
                            componentOfIndex.set(cleanComp, []);
                        }
                        componentOfIndex.get(cleanComp).push(c.hanzi);
                    }
                });
            }
        });

        // Index: character -> list of words containing it
        const charToWordsIndex = new Map();
        DATA.immersion.forEach(w => {
            if (w.word) {
                for (const char of w.word) {
                    if (charMap.has(char)) {
                        const targetChar = charMap.get(char).hanzi;
                        if (!charToWordsIndex.has(targetChar)) {
                            charToWordsIndex.set(targetChar, []);
                        }
                        charToWordsIndex.get(targetChar).push(w.word);
                    }
                }
            }
        });

        // Function to draw local force-directed graph around a term
        function drawLocalGraph(searchTerm) {
            searchTerm = searchTerm.trim();
            if (!searchTerm) return;

            let centerNode = null;
            let centerType = ''; // 'char', 'word', or 'prop'

            if (charMap.has(searchTerm)) {
                centerNode = charMap.get(searchTerm);
                centerType = 'char';
            } else if (wordMap.has(searchTerm)) {
                centerNode = wordMap.get(searchTerm);
                centerType = 'word';
            } else if (propMap.has(searchTerm)) {
                centerNode = propMap.get(searchTerm);
                centerType = 'prop';
            } else {
                // Fuzzy substring match
                for (const [hanzi, data] of charMap.entries()) {
                    if (hanzi.includes(searchTerm)) {
                        centerNode = data;
                        centerType = 'char';
                        break;
                    }
                }
                if (!centerNode) {
                    for (const [comp, data] of propMap.entries()) {
                        if (comp.includes(searchTerm) || (data.prop && data.prop.toLowerCase().includes(searchTerm.toLowerCase()))) {
                            centerNode = data;
                            centerType = 'prop';
                            break;
                        }
                    }
                }
                if (!centerNode) {
                    for (const [word, data] of wordMap.entries()) {
                        if (word.includes(searchTerm)) {
                            centerNode = data;
                            centerType = 'word';
                            break;
                        }
                    }
                }
            }

            if (!centerNode) {
                alert("Term '" + searchTerm + "' not found in your decks.");
                return;
            }

            // Hide suggestions and set input
            document.getElementById('graph-search-results').style.display = 'none';
            document.getElementById('graph-search').value = centerType === 'char' ? centerNode.hanzi : (centerType === 'word' ? centerNode.word : centerNode.component);

            const nodes = [];
            const edges = [];
            const addedNodes = new Set();

            function addNode(id, label, type, sublabel = '', size = 25, isCenter = false) {
                if (addedNodes.has(id)) return;
                addedNodes.add(id);

                let color = {
                    background: '#1E293B',
                    border: 'rgba(255, 255, 255, 0.15)',
                    highlight: { background: '#334155', border: '#4FACFE' }
                };

                if (type === 'char') {
                    color = {
                        background: isCenter ? '#0A2540' : '#1A365D',
                        border: isCenter ? '#00F2FE' : '#4FACFE',
                        highlight: { background: '#204E7A', border: '#00F2FE' }
                    };
                } else if (type === 'word') {
                    color = {
                        background: isCenter ? '#4C1D3A' : '#3B0C2A',
                        border: isCenter ? '#F472B6' : '#EC4899',
                        highlight: { background: '#752A5A', border: '#F472B6' }
                    };
                } else if (type === 'comp') {
                    color = {
                        background: isCenter ? '#451a03' : '#1A1E29', // Warm dark gold for center prop, dark grey for secondary
                        border: isCenter ? '#EAB308' : '#6B7280',
                        highlight: { background: '#2D3748', border: '#EAB308' }
                    };
                }

                nodes.push({
                    id: id,
                    label: isCenter ? `${label}\n(${sublabel})` : label,
                    color: color,
                    shape: 'dot',
                    size: isCenter ? size * 1.3 : size,
                    borderWidth: isCenter ? 3.5 : 1.5,
                    font: {
                        color: '#F3F4F6',
                        size: isCenter ? 15 : 12,
                        face: 'Inter, sans-serif'
                    },
                    shadow: true
                });
            }

            function addEdge(from, to, label, colorVal = 'rgba(156, 163, 175, 0.4)') {
                edges.push({
                    from: from,
                    to: to,
                    label: label,
                    font: { align: 'middle', size: 9, color: '#9CA3AF', strokeWidth: 0 },
                    arrows: { to: { enabled: true, scaleFactor: 0.6 } },
                    color: { color: colorVal, highlight: '#4FACFE' },
                    width: 1.5
                });
            }

            if (centerType === 'char') {
                const centerId = 'c_' + centerNode.hanzi;
                addNode(centerId, centerNode.hanzi, 'char', centerNode.pinyin || '', 30, true);

                // 1. Add components of this character
                if (centerNode.components && Array.isArray(centerNode.components)) {
                    centerNode.components.forEach(comp => {
                        const cleanComp = comp.replace(/^\[([^|\]]+).*$/, '$1').trim();
                        if (cleanComp && cleanComp !== centerNode.hanzi) {
                            const compId = 'comp_' + cleanComp;
                            if (propMap.has(cleanComp)) {
                                const target = propMap.get(cleanComp);
                                addNode(compId, target.component, 'comp', target.prop || '', 22);
                                addEdge(compId, centerId, 'component', 'rgba(234, 179, 8, 0.5)'); // yellow edge for component -> char
                            } else if (charMap.has(cleanComp)) {
                                const target = charMap.get(cleanComp);
                                addNode('c_' + cleanComp, target.hanzi, 'char', target.pinyin || '', 22);
                                addEdge('c_' + cleanComp, centerId, 'component', 'rgba(79, 172, 254, 0.5)');
                            } else {
                                // External radical/component
                                addNode('comp_' + cleanComp, cleanComp, 'comp', '', 18);
                                addEdge('comp_' + cleanComp, centerId, 'radical', 'rgba(156, 163, 175, 0.3)');
                            }
                        }
                    });
                }

                // 2. Add derived characters (characters using this as component)
                const derived = componentOfIndex.get(centerNode.hanzi) || [];
                derived.forEach(parentHanzi => {
                    const parentId = 'c_' + parentHanzi;
                    if (charMap.has(parentHanzi)) {
                        const target = charMap.get(parentHanzi);
                        addNode(parentId, target.hanzi, 'char', target.pinyin || '', 22);
                        addEdge(centerId, parentId, 'part of', 'rgba(0, 242, 254, 0.5)');
                    }
                });

                // 3. Add words containing this character
                const words = charToWordsIndex.get(centerNode.hanzi) || [];
                words.slice(0, 15).forEach(word => {
                    const wId = 'w_' + word;
                    if (wordMap.has(word)) {
                        const target = wordMap.get(word);
                        addNode(wId, target.word, 'word', '', 20);
                        addEdge(centerId, wId, 'in word', 'rgba(236, 72, 153, 0.4)');
                    }
                });

            } else if (centerType === 'word') {
                const centerId = 'w_' + centerNode.word;
                addNode(centerId, centerNode.word, 'word', '', 30, true);

                // Add constituent characters
                for (const char of centerNode.word) {
                    if (charMap.has(char)) {
                        const charObj = charMap.get(char);
                        const cId = 'c_' + charObj.hanzi;
                        addNode(cId, charObj.hanzi, 'char', charObj.pinyin || '', 22);
                        addEdge(cId, centerId, 'composes', 'rgba(236, 72, 153, 0.5)');
                    }
                }
            } else if (centerType === 'prop') {
                const centerId = 'comp_' + centerNode.component;
                addNode(centerId, centerNode.component, 'comp', centerNode.prop || '', 30, true);

                // Add characters containing this component
                const derived = componentOfIndex.get(centerNode.component) || [];
                derived.slice(0, 30).forEach(hanzi => {
                    const charId = 'c_' + hanzi;
                    if (charMap.has(hanzi)) {
                        const target = charMap.get(hanzi);
                        addNode(charId, target.hanzi, 'char', target.pinyin || '', 22);
                        addEdge(centerId, charId, 'part of', 'rgba(79, 172, 254, 0.5)');
                    }
                });
            }

            // Render Network Graph
            const container = document.getElementById('graph-network-container');
            const graphData = {
                nodes: new vis.DataSet(nodes),
                edges: new vis.DataSet(edges)
            };

            const options = {
                physics: {
                    solver: 'forceAtlas2Based',
                    forceAtlas2Based: {
                        gravitationalConstant: -100,
                        centralGravity: 0.02,
                        springLength: 130,
                        springConstant: 0.07,
                        damping: 0.4
                    },
                    stabilization: { iterations: 100 }
                },
                interaction: {
                    hover: true,
                    tooltipDelay: 150,
                    selectable: true
                }
            };

            network = new vis.Network(container, graphData, options);

            // Double click navigates/centers
            network.on("doubleClick", function(params) {
                if (params.nodes.length > 0) {
                    const clickedId = params.nodes[0];
                    let term = '';
                    if (clickedId.startsWith('c_')) term = clickedId.substring(2);
                    else if (clickedId.startsWith('w_')) term = clickedId.substring(2);
                    else if (clickedId.startsWith('comp_')) term = clickedId.substring(5);

                    if (term) drawLocalGraph(term);
                }
            });

            // Single click inspects details
            network.on("selectNode", function(params) {
                if (params.nodes.length > 0) {
                    inspectNode(params.nodes[0]);
                }
            });

            // Inspect center node initially
            const centerNodeId = centerType === 'char' ? 'c_' + centerNode.hanzi : 'w_' + centerNode.word;
            inspectNode(centerNodeId);
        }

        // Show node card details in inspector side pane
        function inspectNode(nodeId) {
            const emptyEl = document.getElementById('graph-inspector-empty');
            const contentEl = document.getElementById('graph-inspector-content');

            emptyEl.style.display = 'none';
            contentEl.style.display = 'flex';

            let html = '';
            if (nodeId.startsWith('c_')) {
                const hanzi = nodeId.substring(2);
                const char = charMap.get(hanzi);
                if (char) {
                    const componentsClean = char.components ? char.components.map(c => c.replace(/^\[([^|\]]+).*$/, '$1').trim()).join(', ') : 'None';
                    html = `
                        <div style="text-align: center; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 1rem;">
                            <div style="font-size: 3.5rem; font-weight: bold; color: var(--accent-cyan); line-height: 1.2;">${char.hanzi}</div>
                            <div style="font-size: 1.25rem; color: var(--text-secondary); font-weight: 500;">${char.pinyin || ''}</div>
                            <div style="font-size: 0.9rem; color: var(--accent-orange); margin-top: 0.25rem;">Tone ${char.tone || 'Unknown'} — ${char.location || 'No location'}</div>
                        </div>
                        
                        <div style="display: flex; flex-direction: column; gap: 0.65rem; font-size: 0.9rem; border-bottom: 1px solid rgba(255,255,255,0.03); padding-bottom: 1rem;">
                            <div><span style="color: var(--text-muted);">Meaning:</span> <strong style="color: var(--text-primary);">${char.english || 'None'}</strong></div>
                            <div><span style="color: var(--text-muted);">Actor (Initial):</span> <strong style="color: var(--accent-purple);">${char.actor || 'None'}</strong></div>
                            <div><span style="color: var(--text-muted);">Set (Final):</span> <strong style="color: var(--accent-blue);">${char.set || 'None'}</strong></div>
                            <div><span style="color: var(--text-muted);">Components:</span> <strong style="color: var(--text-primary);">${componentsClean}</strong></div>
                        </div>

                        <div style="display: flex; flex-direction: column; gap: 0.5rem; font-size: 0.85rem; color: var(--text-secondary);">
                            <div style="display:flex; justify-content:space-between;"><span>Lapses:</span> <span class="badge ${char.lapses >= 4 ? 'badge-red' : 'badge-green'}">${char.lapses} lapses</span></div>
                            <div style="display:flex; justify-content:space-between;"><span>Ease Factor:</span> <span>${char.ease / 10}%</span></div>
                            <div style="display:flex; justify-content:space-between;"><span>Note ID:</span> <code style="font-size:0.75rem;">${char.note_id}</code></div>
                        </div>

                        <div style="display: flex; gap: 0.5rem; margin-top: 0.5rem;">
                            <button class="btn btn-sm btn-primary" style="flex:1; justify-content: center; height:36px;" onclick="window.location.href='anki://search?q=nid:${char.note_id}'">
                                <i data-lucide="external-link" style="width:14px;height:14px;"></i> Open in Anki
                            </button>
                            <button class="btn btn-sm" style="padding: 0.5rem; height:36px;" onclick="copyToClipboard('${char.hanzi}')" title="Copy character">
                                <i data-lucide="copy" style="width:14px;height:14px;"></i>
                            </button>
                        </div>
                    `;
                }
            } else if (nodeId.startsWith('w_')) {
                const wordStr = nodeId.substring(2);
                const word = wordMap.get(wordStr);
                if (word) {
                    html = `
                        <div style="text-align: center; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 1rem;">
                            <div style="font-size: 2.25rem; font-weight: bold; color: var(--accent-magenta); line-height: 1.2;">${word.word}</div>
                            <div style="font-size: 0.95rem; color: var(--text-muted); margin-top: 0.25rem;">Immersion Card</div>
                        </div>

                        <div style="display: flex; flex-direction: column; gap: 0.75rem; font-size: 0.9rem; border-bottom: 1px solid rgba(255,255,255,0.03); padding-bottom: 1rem;">
                            <div><span style="color: var(--text-muted);">Context Sentence:</span> <div style="color: var(--text-primary); font-size: 1.15rem; line-height: 1.45; margin-top: 0.25rem; font-weight: 500; letter-spacing:0.02em;">${word.sentence}</div></div>
                            <div><span style="color: var(--text-muted);">Translation:</span> <div style="color: var(--text-secondary); margin-top: 0.25rem; font-style: italic; line-height: 1.4;">${word.translation || 'None'}</div></div>
                        </div>

                        <div style="display: flex; flex-direction: column; gap: 0.5rem; font-size: 0.85rem; color: var(--text-secondary);">
                            <div style="display:flex; justify-content:space-between;"><span>Lapses:</span> <span class="badge ${word.lapses >= 4 ? 'badge-red' : 'badge-green'}">${word.lapses} lapses</span></div>
                            <div style="display:flex; justify-content:space-between;"><span>Ease:</span> <span>${word.ease / 10}%</span></div>
                            <div style="display:flex; justify-content:space-between;"><span>Note ID:</span> <code style="font-size:0.75rem;">${word.note_id}</code></div>
                        </div>

                        <div style="display: flex; gap: 0.5rem; margin-top: 0.5rem;">
                            <button class="btn btn-sm btn-primary" style="flex:1; justify-content: center; background: linear-gradient(135deg, var(--accent-magenta) 0%, var(--accent-purple) 100%); height:36px;" onclick="window.location.href='anki://search?q=nid:${word.note_id}'">
                                <i data-lucide="external-link" style="width:14px;height:14px;"></i> Open in Anki
                            </button>
                            <button class="btn btn-sm" style="padding: 0.5rem; height:36px;" onclick="copyToClipboard('${word.word}')" title="Copy word">
                                <i data-lucide="copy" style="width:14px;height:14px;"></i>
                            </button>
                        </div>
                    `;
                }
            } else if (nodeId.startsWith('comp_')) {
                const compHanzi = nodeId.substring(5);
                const prop = propMap.get(compHanzi);
                if (prop) {
                    html = `
                        <div style="text-align: center; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 1rem;">
                            <div style="font-size: 3.5rem; font-weight: bold; color: #EAB308; line-height: 1.2;">${prop.component}</div>
                            <div style="font-size: 1.25rem; color: var(--text-secondary); font-weight: 500;">Prop: ${prop.prop || 'Unnamed'}</div>
                            <div style="font-size: 0.85rem; color: var(--text-muted); margin-top: 0.25rem;">Prop Deck Card</div>
                        </div>

                        <div style="display: flex; flex-direction: column; gap: 0.5rem; font-size: 0.85rem; color: var(--text-secondary); margin-top: 1rem; border-bottom: 1px solid rgba(255,255,255,0.03); padding-bottom: 1rem;">
                            <div style="display:flex; justify-content:space-between;"><span>Note ID:</span> <code style="font-size:0.75rem;">${prop.note_id}</code></div>
                        </div>

                        <div style="display: flex; gap: 0.5rem; margin-top: 0.5rem;">
                            <button class="btn btn-sm btn-primary" style="flex:1; justify-content: center; background: linear-gradient(135deg, #EAB308 0%, #CA8A04 100%); border-color:#CA8A04; height:36px;" onclick="window.location.href='anki://search?q=nid:${prop.note_id}'">
                                <i data-lucide="external-link" style="width:14px;height:14px;"></i> Open in Anki
                            </button>
                            <button class="btn btn-sm" style="padding: 0.5rem; height:36px;" onclick="copyToClipboard('${prop.component}')" title="Copy component">
                                <i data-lucide="copy" style="width:14px;height:14px;"></i>
                            </button>
                        </div>
                    `;
                } else {
                    html = `
                        <div style="text-align: center; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 1rem;">
                            <div style="font-size: 3.5rem; font-weight: bold; color: var(--text-muted); line-height: 1.2;">${compHanzi}</div>
                            <div style="font-size: 0.85rem; color: var(--text-muted); margin-top: 0.25rem;">Component (No Prop / Character Card)</div>
                        </div>
                        
                        <p style="color: var(--text-secondary); font-size: 0.85rem; line-height: 1.45; text-align: center;">
                            This radical or visual component exists in your character composition fields, but you do not have a separate card for it in your Characters or Props deck yet.
                        </p>
                        
                        <div style="display: flex; justify-content: center; margin-top: 0.5rem;">
                            <button class="btn btn-sm" onclick="copyToClipboard('${compHanzi}')" title="Copy character" style="height:32px;">
                                <i data-lucide="copy" style="width:14px;height:14px;"></i> Copy Radical
                            </button>
                        </div>
                    `;
                }
            }

            contentEl.innerHTML = html;
            lucide.createIcons();
        }

        // Search Input Suggestions handler
        const graphSearch = document.getElementById('graph-search');
        const graphSearchResults = document.getElementById('graph-search-results');

        graphSearch.addEventListener('input', function() {
            const val = this.value.trim().toLowerCase();
            graphSearchResults.innerHTML = '';
            if (!val) {
                graphSearchResults.style.display = 'none';
                return;
            }

            const items = [];

            // Match Characters
            for (const [hanzi, c] of charMap.entries()) {
                if (hanzi.includes(val) || (c.pinyin && c.pinyin.toLowerCase().includes(val)) || (c.english && c.english.toLowerCase().includes(val))) {
                    items.push({ type: 'char', text: c.hanzi, label: `${c.hanzi} (${c.pinyin || ''}) — ${c.english || ''}` });
                }
            }

            // Match Props
            for (const [comp, p] of propMap.entries()) {
                if (comp.includes(val) || (p.prop && p.prop.toLowerCase().includes(val))) {
                    items.push({ type: 'prop', text: p.component, label: `${p.component} (${p.prop || ''}) — [Prop]` });
                }
            }

            // Match Words
            for (const [word, w] of wordMap.entries()) {
                if (word.includes(val) || (w.sentence && w.sentence.toLowerCase().includes(val))) {
                    items.push({ type: 'word', text: w.word, label: `${w.word} — [Word]` });
                }
            }

            if (items.length === 0) {
                graphSearchResults.style.display = 'none';
                return;
            }

            items.slice(0, 10).forEach(m => {
                const el = document.createElement('div');
                el.style.padding = '0.75rem 1rem';
                el.style.cursor = 'pointer';
                el.style.borderBottom = '1px solid rgba(255,255,255,0.03)';
                el.style.fontSize = '0.9rem';
                let itemColor = 'var(--text-muted)';
                if (m.type === 'char') itemColor = 'var(--accent-cyan)';
                else if (m.type === 'word') itemColor = 'var(--accent-magenta)';
                else if (m.type === 'prop') itemColor = '#EAB308';
                el.style.color = itemColor;
                el.textContent = m.label;
                el.addEventListener('click', () => {
                    drawLocalGraph(m.text);
                });
                graphSearchResults.appendChild(el);
            });

            graphSearchResults.style.display = 'block';
        });

        // Hide dropdown on clicking outside
        document.addEventListener('click', function(e) {
            if (e.target !== graphSearch && e.target !== graphSearchResults) {
                graphSearchResults.style.display = 'none';
            }
        });

        // Random selection button
        document.getElementById('btn-random-graph').addEventListener('click', () => {
            const isChar = Math.random() > 0.45;
            let target = '';
            if (isChar && DATA.characters.length > 0) {
                const idx = Math.floor(Math.random() * DATA.characters.length);
                target = DATA.characters[idx].hanzi;
            } else if (DATA.immersion.length > 0) {
                const idx = Math.floor(Math.random() * DATA.immersion.length);
                target = DATA.immersion[idx].word;
            }
            if (target) drawLocalGraph(target);
        });

        // Initialize view
        function initGraphView() {
            if (graphInitialized) {
                if (network) network.fit();
                return;
            }
            
            // Choose standard default card to load
            let defaultWord = '明';
            if (!charMap.has(defaultWord) && DATA.characters.length > 0) {
                defaultWord = DATA.characters[0].hanzi;
            }
            drawLocalGraph(defaultWord);
            graphInitialized = true;
        }
    </script>
</body>
</html>
"""

def generate_dashboard():
    # 1. Fetch live or JSON character and immersion data
    char_notes, migaku_notes = load_data_from_live_db()
    if char_notes is None:
        char_notes, migaku_notes = load_data_from_backup_json()
        
    # Fetch props notes
    from anki_db import AnkiConnection
    prop_notes = []
    try:
        with AnkiConnection(profile_name="Main") as anki:
            prop_deck = anki.best_match_deck(["Chinese::Props", "Chinese\x1fProps"])
            prop_notes = anki.get_notes_in_deck(prop_deck)
            print(f"Loaded {len(prop_notes)} prop notes from live DB.")
    except Exception as e:
        print(f"Could not connect to live DB for props ({e}). Trying backup JSON...")
        backup_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "anki_extract.json")
        if os.path.exists(backup_path):
            try:
                with open(backup_path, 'r', encoding='utf-8') as f:
                    backup_data = json.load(f)
                    prop_notes = [{'id': n['note_id'], 'fields': {'Component': n['component'], 'Prop': n['prop']}} for n in backup_data.get('props', [])]
                    print(f"Loaded {len(prop_notes)} prop notes from backup JSON.")
            except Exception as e_bak:
                print(f"Error reading props from backup: {e_bak}")
        
    if not char_notes:
        print("Error: Could not retrieve notes. Ensure Anki is running or anki_extract.json exists.")
        return
        
    # 2. Download HSK list
    hsk_words = download_hsk_list()
    if not hsk_words:
        print("Warning: HSK word list unavailable.")
        hsk_words = []
        
    # 3. Perform gap analysis
    print("Compiling basic HSK gap synergies...")
    gap_results = analyze_gap_and_synergy(char_notes, migaku_notes, hsk_words)
    
    # 4. Perform N+1 readability analysis
    print("Classifying N+1 sentences...")
    n0_sent, n1_sent, n2_sent = find_n1_sentences(char_notes, migaku_notes)
    
    # 5. Perform MBP codebook, leech, and conflict analysis
    print("Running memory palace profile and leech diagnostics...")
    profile = profile_mbp_palace(char_notes)
    
    # Compile date and time for timestamp tag
    import datetime
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # Load manually marked known characters list
    known_chars = []
    known_chars_csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "known_characters.csv"))
    if os.path.exists(known_chars_csv_path):
        try:
            with open(known_chars_csv_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader, None) # skip header
                for row in reader:
                    if row and row[0].strip():
                        known_chars.append(row[0].strip())
        except Exception as e:
            print(f"Warning: Could not read known_characters.csv ({e})")

    # Load manually marked known words list
    known_words = []
    known_words_csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "known_words.csv"))
    if os.path.exists(known_words_csv_path):
        try:
            with open(known_words_csv_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader, None) # skip header
                for row in reader:
                    if row and row[0].strip():
                        known_words.append(row[0].strip())
        except Exception as e:
            print(f"Warning: Could not read known_words.csv ({e})")
            
    # 6. Build the data JSON structure
    immersion_cards = []
    for note in migaku_notes:
        f = note['fields']
        word = f.get('Word', '').strip()
        sent = f.get('Sentence', '').strip()
        trans = f.get('Translated Sentence', '').strip()
        
        # simple html tag cleaner
        def clean_tags(t):
            return re.sub(r'<[^>]+>', '', t).replace('&nbsp;', ' ').strip()
            
        word_clean = clean_tags(word)
        sent_clean = clean_tags(sent)
        trans_clean = clean_tags(trans)
        
        if word_clean or sent_clean:
            immersion_cards.append({
                'note_id': note['id'],
                'word': word_clean,
                'sentence': sent_clean,
                'translation': trans_clean,
                'lapses': note.get('lapses', 0),
                'ease': note.get('ease', 2500)
            })

    props_list = []
    for note in prop_notes:
        f = note['fields']
        comp = f.get('Component', '').strip()
        prop_name = f.get('Prop', '').strip()
        if comp:
            props_list.append({
                'note_id': note['id'],
                'component': comp,
                'prop': prop_name
            })

    dashboard_data = {
        'timestamp': current_time,
        'stats': {
            'learned_chars_count': gap_results['learned_chars_count'],
            'total_immersion_cards': gap_results['total_immersion_cards'],
            'total_gaps_count': gap_results['total_gaps_count'],
            'top_gaps': gap_results['top_gaps']
        },
        'unlocked_chars': gap_results['unlocked_chars'],
        'n1_sentences': n1_sent,
        'n0_sentences': n0_sent,
        'synergy_words': gap_results['synergy_words'],
        'codebook': profile['codebook'],
        'inconsistencies': profile['inconsistencies'],
        'leeches': profile['leeches'],
        'conflicts': profile['conflicts'],
        'vacant_actors': profile['vacant_actors'],
        'vacant_sets': profile['vacant_sets'],
        'missing_chars_hsk': gap_results.get('missing_chars_hsk', []),
        'missing_hsk_words_in_migaku': gap_results.get('missing_hsk_words_in_migaku', []),
        'known_characters': known_chars,
        'known_words': known_words,
        'characters': profile['characters'],
        'immersion': immersion_cards,
        'props': props_list
    }
    
    # 7. Write the dashboard file
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "dashboard.html"))
    print(f"Generating static dashboard: {output_path}...")
    
    json_data_str = json.dumps(dashboard_data, ensure_ascii=False, indent=2)
    # Replace the placeholder in the template
    full_html = DASHBOARD_TEMPLATE.replace("__DATA_PLACEHOLDER__", json_data_str)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(full_html)
        
    print(f"Dashboard successfully generated! You can open it directly in any browser: {os.path.abspath(output_path)}")

def main():
    generate_dashboard()

if __name__ == "__main__":
    main()
