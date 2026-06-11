from flask import Blueprint, render_template, jsonify, request
import sqlite3, os

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')
DB_PATH  = os.path.join(os.path.dirname(__file__), 'project_mgmt.db')

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

# ── STEP 1: WorkCalendar ──────────────────────────────────────
@admin_bp.route('/api/workcalendar', methods=['GET'])
def wc_list():
    rows = db().execute("SELECT * FROM WorkCalendar ORDER BY WorkingHrsCode").fetchall()
    return jsonify([dict(r) for r in rows])

@admin_bp.route('/api/workcalendar', methods=['POST'])
def wc_save():
    d = request.json
    conn = db()
    existing = conn.execute("SELECT WorkingHrsCode FROM WorkCalendar WHERE WorkingHrsCode=?", [d['WorkingHrsCode']]).fetchone()
    if existing:
        conn.execute("""UPDATE WorkCalendar SET Description=?,ShiftStart=?,ShiftEnd=?,WorkDays=?,Timezone=?,Is24x7=?
            WHERE WorkingHrsCode=?""",
            [d.get('Description'),d.get('ShiftStart'),d.get('ShiftEnd'),d.get('WorkDays'),d.get('Timezone'),d.get('Is24x7',0),d['WorkingHrsCode']])
    else:
        conn.execute("""INSERT INTO WorkCalendar(WorkingHrsCode,Description,ShiftStart,ShiftEnd,WorkDays,Timezone,Is24x7)
            VALUES(?,?,?,?,?,?,?)""",
            [d['WorkingHrsCode'],d.get('Description'),d.get('ShiftStart'),d.get('ShiftEnd'),d.get('WorkDays'),d.get('Timezone'),d.get('Is24x7',0)])
    conn.commit()
    return jsonify({'ok': True})

@admin_bp.route('/api/workcalendar/<code>', methods=['DELETE'])
def wc_delete(code):
    conn = db()
    conn.execute("DELETE FROM WorkCalendar WHERE WorkingHrsCode=?", [code])
    conn.commit()
    return jsonify({'ok': True})

# ── STEP 2: ProjectInfo ───────────────────────────────────────
@admin_bp.route('/api/projects', methods=['GET'])
def proj_list():
    rows = db().execute("SELECT * FROM ProjectInfo ORDER BY ProjectName").fetchall()
    return jsonify([dict(r) for r in rows])

@admin_bp.route('/api/projects', methods=['POST'])
def proj_save():
    d = request.json
    conn = db()
    existing = conn.execute("SELECT Client FROM ProjectInfo WHERE Client=? AND ProjectName=? AND Release=?",
        [d['Client'],d['ProjectName'],d['Release']]).fetchone()
    if existing:
        conn.execute("""UPDATE ProjectInfo SET TeamName=?,CutoverStartDateTime=?,Timezone=?
            WHERE Client=? AND ProjectName=? AND Release=?""",
            [d.get('TeamName'),d.get('CutoverStartDateTime'),d.get('Timezone'),
             d['Client'],d['ProjectName'],d['Release']])
    else:
        conn.execute("""INSERT INTO ProjectInfo(Client,ProjectName,Release,TeamName,CutoverStartDateTime,Timezone)
            VALUES(?,?,?,?,?,?)""",
            [d['Client'],d['ProjectName'],d['Release'],d.get('TeamName'),d.get('CutoverStartDateTime'),d.get('Timezone')])
    conn.commit()
    return jsonify({'ok': True})

@admin_bp.route('/api/projects/<client>/<project>/<release>', methods=['DELETE'])
def proj_delete(client, project, release):
    conn = db()
    conn.execute("DELETE FROM ProjectInfo WHERE Client=? AND ProjectName=? AND Release=?", [client,project,release])
    conn.commit()
    return jsonify({'ok': True})

# ── STEP 3: ProjectUsers ──────────────────────────────────────
@admin_bp.route('/api/projectusers', methods=['GET'])
def pu_list():
    client  = request.args.get('client','')
    project = request.args.get('project','')
    release = request.args.get('release','')
    rows = db().execute("""SELECT * FROM ProjectUsers WHERE Client=? AND ProjectName=? AND Release=?
        ORDER BY UserName""", [client,project,release]).fetchall()
    return jsonify([dict(r) for r in rows])

@admin_bp.route('/api/projectusers', methods=['POST'])
def pu_save():
    d = request.json
    conn = db()
    if d.get('ID'):
        conn.execute("UPDATE ProjectUsers SET UserName=?,UserEmailID=? WHERE ID=?",
            [d['UserName'],d.get('UserEmailID'),d['ID']])
    else:
        conn.execute("""INSERT INTO ProjectUsers(Client,ProjectName,Release,UserName,UserEmailID)
            VALUES(?,?,?,?,?)""",
            [d['Client'],d['ProjectName'],d['Release'],d['UserName'],d.get('UserEmailID')])
    conn.commit()
    return jsonify({'ok': True})

@admin_bp.route('/api/projectusers/<int:uid>', methods=['DELETE'])
def pu_delete(uid):
    conn = db()
    conn.execute("DELETE FROM ProjectUsers WHERE ID=?", [uid])
    conn.commit()
    return jsonify({'ok': True})

# ── STEP 4: Resources ─────────────────────────────────────────
@admin_bp.route('/api/resources', methods=['GET'])
def res_list():
    client  = request.args.get('client','')
    project = request.args.get('project','')
    release = request.args.get('release','')
    rows = db().execute("""SELECT * FROM Resources WHERE Client=? AND ProjectName=? AND Release=?
        ORDER BY ResourceName""", [client,project,release]).fetchall()
    return jsonify([dict(r) for r in rows])

@admin_bp.route('/api/resources', methods=['POST'])
def res_save():
    d = request.json
    conn = db()
    if d.get('ResourceID'):
        conn.execute("UPDATE Resources SET ResourceName=?,ResourceEmail=? WHERE ResourceID=?",
            [d['ResourceName'],d.get('ResourceEmail'),d['ResourceID']])
    else:
        conn.execute("""INSERT INTO Resources(Client,ProjectName,Release,ResourceName,ResourceEmail)
            VALUES(?,?,?,?,?)""",
            [d['Client'],d['ProjectName'],d['Release'],d['ResourceName'],d.get('ResourceEmail')])
    conn.commit()
    return jsonify({'ok': True})

@admin_bp.route('/api/resources/<int:rid>', methods=['DELETE'])
def res_delete(rid):
    conn = db()
    conn.execute("DELETE FROM Resources WHERE ResourceID=?", [rid])
    conn.commit()
    return jsonify({'ok': True})

# ── STEP 5: ResourceCalendar ──────────────────────────────────
@admin_bp.route('/api/rescalendar', methods=['GET'])
def rc_list():
    client  = request.args.get('client','')
    project = request.args.get('project','')
    release = request.args.get('release','')
    # Filter by resources belonging to this project
    rows = db().execute("""
        SELECT rc.* FROM ResourceCalendar rc
        INNER JOIN Resources r ON rc.ResourceName = r.ResourceName
            AND r.Client=? AND r.ProjectName=? AND r.Release=?
        ORDER BY rc.ResourceName, rc.EffectiveFrom
    """, [client, project, release]).fetchall()
    return jsonify([dict(r) for r in rows])

@admin_bp.route('/api/rescalendar', methods=['POST'])
def rc_save():
    d = request.json
    conn = db()
    if d.get('CalendarID'):
        conn.execute("""UPDATE ResourceCalendar 
            SET ResourceName=?,ResourceEmail=?,EffectiveFrom=?,EffectiveTo=?,WorkingHrsCode=?,Notes=?
            WHERE CalendarID=?""",
            [d['ResourceName'],d.get('ResourceEmail'),d['EffectiveFrom'],d['EffectiveTo'],
             d.get('WorkingHrsCode'),d.get('Notes'),d['CalendarID']])
    else:
        conn.execute("""INSERT INTO ResourceCalendar(ResourceName,ResourceEmail,EffectiveFrom,EffectiveTo,WorkingHrsCode,Notes)
            VALUES(?,?,?,?,?,?)""",
            [d['ResourceName'],d.get('ResourceEmail'),d['EffectiveFrom'],d['EffectiveTo'],
             d.get('WorkingHrsCode'),d.get('Notes')])
    conn.commit()
    return jsonify({'ok': True})

@admin_bp.route('/api/rescalendar/<int:cid>', methods=['DELETE'])
def rc_delete(cid):
    conn = db()
    conn.execute("DELETE FROM ResourceCalendar WHERE CalendarID=?", [cid])
    conn.commit()
    return jsonify({'ok': True})

# ── STEP 6: Holidays ──────────────────────────────────────────
@admin_bp.route('/api/holidays', methods=['GET'])
def hol_list():
    rows = db().execute("SELECT * FROM Holidays ORDER BY HolidayDate").fetchall()
    return jsonify([dict(r) for r in rows])

@admin_bp.route('/api/holidays', methods=['POST'])
def hol_save():
    d = request.json
    conn = db()
    if d.get('HolidayID'):
        conn.execute("""UPDATE Holidays SET HolidayDate=?,Description=?,Region=?,IsRecurringYearly=?
            WHERE HolidayID=?""",
            [d['HolidayDate'],d['Description'],d.get('Region'),d.get('IsRecurringYearly',0),d['HolidayID']])
    else:
        conn.execute("""INSERT INTO Holidays(HolidayDate,Description,Region,IsRecurringYearly)
            VALUES(?,?,?,?)""",
            [d['HolidayDate'],d['Description'],d.get('Region'),d.get('IsRecurringYearly',0)])
    conn.commit()
    return jsonify({'ok': True})

@admin_bp.route('/api/holidays/<int:hid>', methods=['DELETE'])
def hol_delete(hid):
    conn = db()
    conn.execute("DELETE FROM Holidays WHERE HolidayID=?", [hid])
    conn.commit()
    return jsonify({'ok': True})

# ── SHARED: project list for dropdowns ───────────────────────
@admin_bp.route('/api/projlist', methods=['GET'])
def projlist():
    rows = db().execute("SELECT Client,ProjectName,Release FROM ProjectInfo ORDER BY ProjectName").fetchall()
    return jsonify([dict(r) for r in rows])

@admin_bp.route('/api/wccodes', methods=['GET'])
def wccodes():
    rows = db().execute("SELECT WorkingHrsCode,Description FROM WorkCalendar ORDER BY WorkingHrsCode").fetchall()
    return jsonify([dict(r) for r in rows])
