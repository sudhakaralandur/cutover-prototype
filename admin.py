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

# ── STEP 7: Tasks ─────────────────────────────────────────────
@admin_bp.route('/api/tasks/list', methods=['GET'])
def tasks_list():
    client  = request.args.get('client','')
    project = request.args.get('project','')
    release = request.args.get('release','')
    rows = db().execute("""
        SELECT TaskID,UniqueID,WBS,TaskDesc,Duration,StartDateTime,FinishDateTime,
               PerComplete,ResourceName,TeamName,Predecessor,Successors,Notes,
               BaselineStartDateTime,BaselineFinishDateTime,
               WorkCalendarOverride,ScheduleType
        FROM Tasks WHERE Client=? AND ProjectName=? AND Release=?
        ORDER BY TaskID
    """, [client,project,release]).fetchall()

    wbs_list = [str(r['WBS']) for r in rows]
    tasks = []
    for i, r in enumerate(rows):
        wbs    = str(r['WBS']) if r['WBS'] else ''
        is_hdr = any(w != wbs and w.startswith(wbs+'.') for w in wbs_list)
        tasks.append({
            'taskId':              r['TaskID'],
            'uniqueId':            r['UniqueID'],
            'rowNum':              i + 1,
            'wbs':                 wbs,
            'depth':               wbs.count('.'),
            'isHeader':            is_hdr,
            'taskDesc':            r['TaskDesc'] or '',
            'duration':            r['Duration'] or 0,
            'start':               r['StartDateTime'] or '',
            'finish':              r['FinishDateTime'] or '',
            'pctComplete':         r['PerComplete'] or 0,
            'resource':            r['ResourceName'] or '',
            'team':                r['TeamName'] or '',
            'predecessor':         r['Predecessor'] or '',
            'successors':          r['Successors'] or '',
            'notes':               r['Notes'] or '',
            'wcOverride':          r['WorkCalendarOverride'] or '',
            'scheduleType':        r['ScheduleType'] or 'Auto',
        })
    return jsonify(tasks)

@admin_bp.route('/api/tasks/save', methods=['POST'])
def tasks_save():
    """Save a single task (insert or update)."""
    from scheduler import compute_finish, validate_task_calendar
    d = request.json

    # Validate calendar for Auto tasks
    if d.get('scheduleType') != 'Manual':
        err = validate_task_calendar({
            'ScheduleType':          d.get('scheduleType','Auto'),
            'WorkCalendarOverride':  d.get('wcOverride',''),
            'ResourceName':          d.get('resource',''),
            'StartDateTime':         d.get('start',''),
            'FinishDateTime':        d.get('finish',''),
        })
        if err:
            return jsonify({'ok': False, 'error': err}), 400

        # Recalculate finish if start + duration provided
        if d.get('start') and d.get('duration'):
            finish, err = compute_finish({
                'ScheduleType':         d.get('scheduleType','Auto'),
                'WorkCalendarOverride': d.get('wcOverride',''),
                'ResourceName':         d.get('resource',''),
                'StartDateTime':        d.get('start',''),
                'Duration':             d.get('duration',0),
            })
            if err:
                return jsonify({'ok': False, 'error': err}), 400
            d['finish'] = finish

    conn = db()
    client  = d['client']
    project = d['project']
    release = d['release']

    if d.get('taskId'):
        conn.execute("""
            UPDATE Tasks SET TaskDesc=?,Duration=?,StartDateTime=?,FinishDateTime=?,
            PerComplete=?,ResourceName=?,TeamName=?,Predecessor=?,Successors=?,Notes=?,
            WorkCalendarOverride=?,ScheduleType=?
            WHERE TaskID=?
        """, [d.get('taskDesc'),d.get('duration'),d.get('start'),d.get('finish'),
              d.get('pctComplete',0),d.get('resource'),d.get('team'),
              d.get('predecessor'),d.get('successors'),d.get('notes'),
              d.get('wcOverride') or None, d.get('scheduleType','Auto'),
              d['taskId']])
    else:
        # New task — get next UniqueID from NumberRange
        conn2 = db()
        nr = conn2.execute(
            "SELECT RangeKey,LastUsedNumber FROM NumberRange WHERE Client=? AND ProjectName=? AND Release=?",
            [client,project,release]
        ).fetchone()
        next_id = (nr['LastUsedNumber'] + 1) if nr else 1
        range_key = nr['RangeKey'] if nr else 'NEW'

        conn.execute("""
            INSERT INTO Tasks(Client,ProjectName,Release,UniqueID,WBS,TaskDesc,Duration,
            StartDateTime,FinishDateTime,PerComplete,ResourceName,TeamName,
            Predecessor,Successors,Notes,WorkCalendarOverride,ScheduleType)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, [client,project,release,next_id,d.get('wbs',''),
              d.get('taskDesc'),d.get('duration',0),d.get('start'),d.get('finish'),
              d.get('pctComplete',0),d.get('resource'),d.get('team'),
              d.get('predecessor'),d.get('successors'),d.get('notes'),
              d.get('wcOverride') or None, d.get('scheduleType','Auto')])

        conn.execute(
            "UPDATE NumberRange SET LastUsedNumber=? WHERE RangeKey=?",
            [next_id, range_key]
        )
        task_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        d['taskId'] = task_id

    conn.commit()
    return jsonify({'ok': True, 'taskId': d.get('taskId'), 'finish': d.get('finish')})

@admin_bp.route('/api/tasks/delete', methods=['POST'])
def tasks_delete():
    """Delete one or more tasks (with children check)."""
    d       = request.json
    ids     = d.get('taskIds', [])
    force   = d.get('force', False)
    conn    = db()

    if not force:
        # Check for children
        wbs_rows = conn.execute(
            f"SELECT TaskID,WBS FROM Tasks WHERE TaskID IN ({','.join('?'*len(ids))})", ids
        ).fetchall()
        all_wbs = [r['WBS'] for r in wbs_rows]
        # Check if any other task's WBS starts with one of these
        placeholders = ','.join('?' * len(ids))
        children = conn.execute(
            f"SELECT COUNT(*) as cnt FROM Tasks WHERE TaskID NOT IN ({placeholders}) AND ({' OR '.join(['WBS LIKE ?']*len(all_wbs))})",
            ids + [str(w)+'%' for w in all_wbs]
        ).fetchone()
        if children and children['cnt'] > 0:
            return jsonify({'ok': False, 'hasChildren': True,
                'message': f"One or more selected tasks have children. Delete all {children['cnt']} child tasks too?"})

    conn.execute(f"DELETE FROM Tasks WHERE TaskID IN ({','.join('?'*len(ids))})", ids)
    conn.commit()
    return jsonify({'ok': True})

@admin_bp.route('/api/tasks/reorder', methods=['POST'])
def tasks_reorder():
    """
    Update WBS for all tasks after indent/outdent/insert/delete.
    Receives full ordered list of {taskId, wbs}.
    """
    d    = request.json
    rows = d.get('tasks', [])
    conn = db()
    for r in rows:
        conn.execute("UPDATE Tasks SET WBS=? WHERE TaskID=?", [r['wbs'], r['taskId']])
    conn.commit()
    return jsonify({'ok': True})

@admin_bp.route('/api/tasks/compute_finish', methods=['POST'])
def tasks_compute_finish():
    """Compute finish datetime for a task given start + duration + calendar."""
    from scheduler import compute_finish, get_successor_start
    d = request.json

    if d.get('predecessorFinish') and d.get('resource'):
        start, err = get_successor_start(
            d['predecessorFinish'],
            d['resource'].split(',')[0].strip(),
            d.get('wcOverride')
        )
        if err:
            return jsonify({'ok': False, 'error': err}), 400
        d['start'] = start

    finish, err = compute_finish({
        'ScheduleType':         d.get('scheduleType','Auto'),
        'WorkCalendarOverride': d.get('wcOverride',''),
        'ResourceName':         d.get('resource',''),
        'StartDateTime':        d.get('start',''),
        'Duration':             d.get('duration',0),
    })
    if err:
        return jsonify({'ok': False, 'error': err}), 400
    return jsonify({'ok': True, 'start': d.get('start'), 'finish': finish})
