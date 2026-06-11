from flask import Flask, render_template, jsonify, request
import sqlite3
import os

app = Flask(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), 'project_mgmt.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

@app.route('/')
def index():
    # Get distinct projects for dropdown
    conn = get_db()
    projects = conn.execute("""
        SELECT DISTINCT Client, ProjectName, Release 
        FROM ProjectInfo ORDER BY ProjectName
    """).fetchall()
    conn.close()
    return render_template('index.html', projects=projects)

@app.route('/api/tasks')
def get_tasks():
    client      = request.args.get('client', 'ABC Company')
    project     = request.args.get('project', 'Vanguard')
    release     = request.args.get('release', 'Mock 1')
    team        = request.args.get('team', '')
    search      = request.args.get('search', '')

    conn = get_db()

    query = """
        SELECT 
            TaskID,
            UniqueID,
            WBS,
            TaskDesc,
            Duration,
            StartDateTime,
            FinishDateTime,
            PerComplete,
            ResourceName,
            TeamName,
            Predecessor,
            Successors,
            Notes,
            BaselineStartDateTime,
            BaselineFinishDateTime
        FROM Tasks
        WHERE Client = ? AND ProjectName = ? AND Release = ?
    """
    params = [client, project, release]

    if team:
        query += " AND TeamName = ?"
        params.append(team)

    if search:
        query += " AND (TaskDesc LIKE ? OR ResourceName LIKE ? OR WBS LIKE ?)"
        params += [f'%{search}%', f'%{search}%', f'%{search}%']

    query += " ORDER BY TaskID"

    rows = conn.execute(query, params).fetchall()

    # Get distinct teams for filter
    teams = conn.execute("""
        SELECT DISTINCT TeamName FROM Tasks 
        WHERE Client=? AND ProjectName=? AND Release=? AND TeamName IS NOT NULL
        ORDER BY TeamName
    """, [client, project, release]).fetchall()

    conn.close()

    tasks = []
    for r in rows:
        # Determine WBS depth for indentation
        wbs = str(r['WBS']) if r['WBS'] else ''
        depth = wbs.count('.') if wbs else 0

        # Is this a header? Check if any task WBS starts with this WBS + '.'
        tasks.append({
            'taskId':       r['TaskID'],
            'uniqueId':     r['UniqueID'],
            'wbs':          wbs,
            'depth':        depth,
            'taskDesc':     r['TaskDesc'] or '',
            'duration':     r['Duration'] or 0,
            'start':        fmt_dt(r['StartDateTime']),
            'finish':       fmt_dt(r['FinishDateTime']),
            'pctComplete':  r['PerComplete'] or 0,
            'resource':     r['ResourceName'] or '',
            'team':         r['TeamName'] or '',
            'predecessor':  r['Predecessor'] or '',
            'successors':   r['Successors'] or '',
            'notes':        r['Notes'] or '',
            'blStart':      fmt_dt(r['BaselineStartDateTime']),
            'blFinish':     fmt_dt(r['BaselineFinishDateTime']),
        })

    # Mark header tasks (have children)
    wbs_set = set(t['wbs'] for t in tasks)
    for t in tasks:
        wbs = t['wbs']
        t['isHeader'] = any(
            w != wbs and w.startswith(wbs + '.') 
            for w in wbs_set
        )

    return jsonify({
        'tasks': tasks,
        'teams': [r['TeamName'] for r in teams]
    })

def fmt_dt(val):
    if not val:
        return ''
    # Already ISO string - format for display
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(str(val))
        return dt.strftime('%m/%d/%y %H:%M')
    except:
        return str(val)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
