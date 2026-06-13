from flask import Flask, render_template, jsonify, request
import sqlite3, os

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(__file__), 'project_mgmt.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

# ── Register admin blueprint ──
from admin import admin_bp
app.register_blueprint(admin_bp)

@app.route('/')
def index():
    conn = get_db()
    projects = conn.execute("SELECT DISTINCT Client,ProjectName,Release FROM ProjectInfo ORDER BY ProjectName").fetchall()
    conn.close()
    return render_template('index.html', projects=projects)

@app.route('/api/tasks')
def get_tasks():
    client  = request.args.get('client','ABC Company')
    project = request.args.get('project','Vanguard')
    release = request.args.get('release','Mock 1')
    team    = request.args.get('team','')
    search  = request.args.get('search','')
    conn = get_db()
    q = """SELECT TaskID,UniqueID,WBS,TaskDesc,Duration,StartDateTime,FinishDateTime,
           PerComplete,ResourceName,TeamName,Predecessor,Successors,Notes,
           BaselineStartDateTime,BaselineFinishDateTime
           FROM Tasks WHERE Client=? AND ProjectName=? AND Release=?"""
    p = [client,project,release]
    if team:   q += " AND TeamName=?";                p.append(team)
    if search: q += " AND (TaskDesc LIKE ? OR ResourceName LIKE ? OR WBS LIKE ?)"; p += [f'%{search}%']*3
    q += " ORDER BY TaskID"
    rows  = conn.execute(q, p).fetchall()
    teams = conn.execute("""SELECT DISTINCT TeamName FROM Tasks
        WHERE Client=? AND ProjectName=? AND Release=? AND TeamName IS NOT NULL
        ORDER BY TeamName""", [client,project,release]).fetchall()
    conn.close()
    wbs_set = [str(r['WBS']) for r in rows]
    tasks = []
    for r in rows:
        wbs   = str(r['WBS']) if r['WBS'] else ''
        depth = wbs.count('.')
        is_hdr = any(w != wbs and w.startswith(wbs+'.') for w in wbs_set)
        tasks.append({'taskId':r['TaskID'],'uniqueId':r['UniqueID'],'wbs':wbs,'depth':depth,
            'isHeader':is_hdr,'taskDesc':r['TaskDesc'] or '','duration':r['Duration'] or 0,
            'start':fmt_dt(r['StartDateTime']),'finish':fmt_dt(r['FinishDateTime']),
            'pctComplete':r['PerComplete'] or 0,'resource':r['ResourceName'] or '',
            'team':r['TeamName'] or '','predecessor':r['Predecessor'] or '',
            'successors':r['Successors'] or '','notes':r['Notes'] or '',
            'blStart':fmt_dt(r['BaselineStartDateTime']),'blFinish':fmt_dt(r['BaselineFinishDateTime'])})
    return jsonify({'tasks':tasks,'teams':[r['TeamName'] for r in teams]})

def fmt_dt(val):
    if not val: return ''
    try:
        from datetime import datetime
        return datetime.fromisoformat(str(val)).strftime('%m/%d/%y %H:%M')
    except: return str(val)


@app.route('/admin')
def admin():
    return render_template('admin.html')

if __name__ == '__main__':
    app.run(debug=True, port=5001, host='0.0.0.0')
