"""
Web-based SQLite Database Viewer
Similar to phpMyAdmin but for SQLite
Run this and open http://localhost:5001 in your browser
"""
from flask import Flask, render_template_string, jsonify, request
import sqlite3
import json
from datetime import datetime

app = Flask(__name__)
DB_PATH = 'database/story_scenes.db'

# HTML Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Database Viewer - Story Scenes</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: #1a1b1e;
            color: #e4e4e7;
            padding: 20px;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        h1 {
            color: #f4f4f5;
            margin-bottom: 30px;
            font-size: 28px;
        }
        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            border-bottom: 2px solid #3f3f46;
        }
        .tab {
            padding: 12px 24px;
            background: #27272a;
            border: none;
            color: #a1a1aa;
            cursor: pointer;
            border-radius: 8px 8px 0 0;
            font-size: 14px;
            transition: all 0.2s;
        }
        .tab:hover {
            background: #3f3f46;
            color: #e4e4e7;
        }
        .tab.active {
            background: #3f3f46;
            color: #f4f4f5;
            border-bottom: 2px solid #60a5fa;
        }
        .table-container {
            background: #27272a;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        thead {
            background: #18181b;
        }
        th {
            padding: 12px 16px;
            text-align: left;
            font-weight: 600;
            color: #f4f4f5;
            border-bottom: 2px solid #3f3f46;
        }
        td {
            padding: 12px 16px;
            border-bottom: 1px solid #3f3f46;
            color: #d4d4d8;
        }
        tr:hover {
            background: #3f3f46;
        }
        .badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 500;
        }
        .badge-success { background: #10b981; color: white; }
        .badge-pending { background: #f59e0b; color: white; }
        .badge-free { background: #6366f1; color: white; }
        .text-truncate {
            max-width: 300px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .expandable {
            cursor: pointer;
            color: #60a5fa;
        }
        .expandable:hover {
            text-decoration: underline;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: #27272a;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #60a5fa;
        }
        .stat-card h3 {
            color: #a1a1aa;
            font-size: 14px;
            margin-bottom: 8px;
        }
        .stat-card .value {
            color: #f4f4f5;
            font-size: 32px;
            font-weight: 600;
        }
        .search-box {
            margin-bottom: 20px;
        }
        .search-box input {
            width: 100%;
            padding: 12px;
            background: #27272a;
            border: 1px solid #3f3f46;
            border-radius: 6px;
            color: #e4e4e7;
            font-size: 14px;
        }
        .search-box input:focus {
            outline: none;
            border-color: #60a5fa;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Database Viewer - Story Scenes</h1>
        
        <div class="stats" id="stats">
            <div class="stat-card">
                <h3>Total Users</h3>
                <div class="value" id="user-count">-</div>
            </div>
            <div class="stat-card">
                <h3>Total Stories</h3>
                <div class="value" id="story-count">-</div>
            </div>
            <div class="stat-card">
                <h3>Total Scenes</h3>
                <div class="value" id="scene-count">-</div>
            </div>
        </div>

        <div class="tabs">
            <button class="tab active" onclick="showTable('users')">👥 Users</button>
            <button class="tab" onclick="showTable('stories')">📚 Stories</button>
            <button class="tab" onclick="showTable('scenes')">🎬 Scenes</button>
            <button class="tab" onclick="showTable('metadata')">📋 Metadata</button>
        </div>

        <div class="search-box">
            <input type="text" id="search" placeholder="Search..." onkeyup="filterTable()">
        </div>

        <div class="table-container" id="table-container">
            <table id="data-table">
                <thead id="table-head"></thead>
                <tbody id="table-body"></tbody>
            </table>
        </div>
    </div>

    <script>
        let currentTable = 'users';
        let allData = {};

        async function loadStats() {
            const res = await fetch('/api/stats');
            const stats = await res.json();
            document.getElementById('user-count').textContent = stats.users;
            document.getElementById('story-count').textContent = stats.stories;
            document.getElementById('scene-count').textContent = stats.scenes;
        }

        async function loadTable(tableName) {
            currentTable = tableName;
            const res = await fetch(`/api/table/${tableName}`);
            const data = await res.json();
            allData[tableName] = data;
            renderTable(data);
        }

        function renderTable(data) {
            if (!data || data.length === 0) {
                document.getElementById('table-body').innerHTML = '<tr><td colspan="100%" style="text-align: center; padding: 40px;">No data found</td></tr>';
                return;
            }

            const thead = document.getElementById('table-head');
            const tbody = document.getElementById('table-body');
            
            // Headers
            const headers = Object.keys(data[0]);
            thead.innerHTML = '<tr>' + headers.map(h => `<th>${h}</th>`).join('') + '</tr>';
            
            // Rows
            tbody.innerHTML = data.map(row => {
                return '<tr>' + headers.map(header => {
                    let value = row[header];
                    if (value === null) value = '<em style="color: #71717a;">null</em>';
                    else if (typeof value === 'string' && value.length > 100) {
                        value = `<span class="text-truncate" title="${value}">${value.substring(0, 100)}...</span>`;
                    }
                    else if (header === 'status') {
                        value = `<span class="badge badge-${value}">${value}</span>`;
                    }
                    else if (header === 'plan') {
                        value = `<span class="badge badge-free">${value}</span>`;
                    }
                    return `<td>${value}</td>`;
                }).join('') + '</tr>';
            }).join('');
        }

        function showTable(tableName) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            event.target.classList.add('active');
            loadTable(tableName);
        }

        function filterTable() {
            const search = document.getElementById('search').value.toLowerCase();
            const rows = document.querySelectorAll('#table-body tr');
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(search) ? '' : 'none';
            });
        }

        // Load on page load
        loadStats();
        loadTable('users');
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/stats')
def stats():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM users")
    users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM stories")
    stories = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM scenes")
    scenes = cursor.fetchone()[0]
    
    conn.close()
    
    return jsonify({
        'users': users,
        'stories': stories,
        'scenes': scenes
    })

@app.route('/api/table/<table_name>')
def get_table(table_name):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Validate table name to prevent SQL injection
    valid_tables = ['users', 'stories', 'scenes', 'metadata', 'conversations', 'agent_decisions', 'user_queries', 'reports']
    if table_name not in valid_tables:
        return jsonify({'error': 'Invalid table name'}), 400
    
    try:
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        data = [dict(row) for row in rows]
        conn.close()
        return jsonify(data)
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🗄️  Database Viewer Starting...")
    print("="*60)
    print(f"📊 Database: {DB_PATH}")
    print(f"🌐 Open in browser: http://localhost:5001")
    print("="*60 + "\n")
    app.run(host='0.0.0.0', port=5001, debug=False)

