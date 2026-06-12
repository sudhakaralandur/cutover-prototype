"""
scheduler.py — Working-hours-aware date calculator for Cutover Prototype
"""
import sqlite3
from datetime import datetime, timedelta, date, time as dtime
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'project_mgmt.db')

DAYS_MAP = {
    'MON': 0, 'TUE': 1, 'WED': 2, 'THU': 3,
    'FRI': 4, 'SAT': 5, 'SUN': 6
}

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ── FETCH CALENDAR ────────────────────────────────────────────
def get_work_calendar(code):
    """Return WorkCalendar row by code."""
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM WorkCalendar WHERE WorkingHrsCode=?", [code]
    ).fetchone()
    conn.close()
    return dict(row) if row else None

def get_resource_calendar(resource_name, check_dt):
    """
    Return the ResourceCalendar entry for a resource on a given datetime.
    Returns None if no match found.
    """
    conn = get_db()
    check_date = check_dt.strftime('%Y-%m-%d')
    row = conn.execute("""
        SELECT rc.*, wc.ShiftStart, wc.ShiftEnd, wc.WorkDays, wc.Timezone, wc.Is24x7
        FROM ResourceCalendar rc
        LEFT JOIN WorkCalendar wc ON rc.WorkingHrsCode = wc.WorkingHrsCode
        WHERE rc.ResourceName = ?
          AND ? >= rc.EffectiveFrom
          AND ? <= rc.EffectiveTo
        LIMIT 1
    """, [resource_name, check_date, check_date]).fetchone()
    conn.close()
    return dict(row) if row else None

def get_resource_calendar_for_range(resource_name, start_dt, finish_dt):
    """
    Validate that a resource has a single calendar entry covering
    the full task range. Returns (calendar, error_message).
    """
    conn = get_db()
    start_date  = start_dt.strftime('%Y-%m-%d')
    finish_date = finish_dt.strftime('%Y-%m-%d')
    rows = conn.execute("""
        SELECT rc.*, wc.ShiftStart, wc.ShiftEnd, wc.WorkDays, wc.Timezone, wc.Is24x7
        FROM ResourceCalendar rc
        LEFT JOIN WorkCalendar wc ON rc.WorkingHrsCode = wc.WorkingHrsCode
        WHERE rc.ResourceName = ?
          AND rc.EffectiveFrom <= ?
          AND rc.EffectiveTo   >= ?
    """, [resource_name, start_date, finish_date]).fetchall()
    conn.close()

    if len(rows) == 0:
        return None, f"No calendar found for '{resource_name}' covering {start_date} to {finish_date}. Update Resource Calendar first."
    if len(rows) > 1:
        return None, f"Overlapping calendar entries found for '{resource_name}'. Fix Resource Calendar first."
    return dict(rows[0]), None

# ── HOLIDAY CHECK ─────────────────────────────────────────────
def get_holidays():
    """Return set of holiday dates as strings YYYY-MM-DD."""
    conn = get_db()
    rows = conn.execute("SELECT HolidayDate FROM Holidays").fetchall()
    conn.close()
    return set(r['HolidayDate'] for r in rows)

# ── CALENDAR RESOLUTION ───────────────────────────────────────
def resolve_calendar(task):
    """
    Given a task dict, return the effective calendar dict to use.
    Priority: WorkCalendarOverride > first resource's calendar.
    Returns (calendar_dict, error_string)
    """
    override = task.get('WorkCalendarOverride')
    if override:
        wc = get_work_calendar(override)
        if not wc:
            return None, f"Work Calendar override '{override}' not found."
        return wc, None

    resources = task.get('ResourceName', '')
    if not resources:
        return None, "No resource assigned and no calendar override set."

    first_resource = resources.split(',')[0].strip()
    start_dt  = parse_dt(task.get('StartDateTime'))
    finish_dt = parse_dt(task.get('FinishDateTime'))

    if start_dt and finish_dt:
        return get_resource_calendar_for_range(first_resource, start_dt, finish_dt)
    elif start_dt:
        cal = get_resource_calendar(first_resource, start_dt)
        if not cal:
            return None, f"No calendar found for '{first_resource}' on {start_dt.strftime('%Y-%m-%d')}."
        return cal, None
    return None, "No start date set."

# ── WORKING DAY CHECK ─────────────────────────────────────────
def is_working_minute(dt, calendar, holidays):
    """
    Returns True if the given datetime falls within working hours
    for the given calendar.
    """
    if calendar.get('Is24x7'):
        date_str = dt.strftime('%Y-%m-%d')
        return date_str not in holidays

    # Check work days
    work_days_str = calendar.get('WorkDays', 'MON,TUE,WED,THU,FRI')
    work_days = set(d.strip() for d in work_days_str.split(','))
    day_names  = ['MON','TUE','WED','THU','FRI','SAT','SUN']
    if day_names[dt.weekday()] not in work_days:
        return False

    # Check holiday
    date_str = dt.strftime('%Y-%m-%d')
    if date_str in holidays:
        return False

    # Check shift hours
    shift_start = parse_time(calendar.get('ShiftStart', '08:00'))
    shift_end   = parse_time(calendar.get('ShiftEnd',   '17:00'))
    t = dt.time().replace(second=0, microsecond=0)
    return shift_start <= t < shift_end

# ── NEXT WORKING MINUTE ───────────────────────────────────────
def next_working_minute(dt, calendar, holidays):
    """
    Given a datetime, return the next datetime that is a working minute.
    If dt itself is a working minute, return dt.
    """
    # Start checking from the given dt (truncated to minute)
    current = dt.replace(second=0, microsecond=0)
    max_iterations = 60 * 24 * 365  # 1 year safety cap

    for _ in range(max_iterations):
        if is_working_minute(current, calendar, holidays):
            return current
        current += timedelta(minutes=1)

    raise ValueError(f"Could not find next working minute within 1 year from {dt}")

def next_working_start_after(dt, calendar, holidays):
    """
    Given a datetime (e.g. end of predecessor), return the next
    available working minute for the successor — respecting shift start.
    """
    if calendar.get('Is24x7'):
        # For 24x7 just go to next minute
        nxt = dt.replace(second=0, microsecond=0) + timedelta(minutes=1)
        return next_working_minute(nxt, calendar, holidays)

    shift_start = parse_time(calendar.get('ShiftStart', '08:00'))
    # Try same day first, then advance
    candidate = dt.replace(second=0, microsecond=0) + timedelta(minutes=1)

    for _ in range(365):
        day_names = ['MON','TUE','WED','THU','FRI','SAT','SUN']
        work_days_str = calendar.get('WorkDays', 'MON,TUE,WED,THU,FRI')
        work_days = set(d.strip() for d in work_days_str.split(','))
        date_str  = candidate.strftime('%Y-%m-%d')

        if day_names[candidate.weekday()] in work_days and date_str not in holidays:
            # Jump to shift start of this day
            start_of_day = candidate.replace(
                hour=shift_start.hour,
                minute=shift_start.minute,
                second=0, microsecond=0
            )
            if start_of_day >= candidate:
                return start_of_day
            # If we're already past shift start today, go to next working day
        # Advance to next day at shift start
        candidate = (candidate + timedelta(days=1)).replace(
            hour=shift_start.hour, minute=shift_start.minute,
            second=0, microsecond=0
        )
    raise ValueError("Could not find next working start within 1 year.")

# ── FINISH CALCULATOR ─────────────────────────────────────────
def calculate_finish(start_dt, duration_mins, calendar, holidays):
    """
    Calculate finish datetime by consuming `duration_mins` working minutes
    starting from start_dt using the given calendar.
    Returns FinishDateTime.
    """
    if duration_mins <= 0:
        return start_dt

    current   = start_dt.replace(second=0, microsecond=0)
    remaining = duration_mins
    max_iter  = duration_mins * 10 + 60 * 24 * 30  # safety cap

    for _ in range(max_iter):
        if is_working_minute(current, calendar, holidays):
            remaining -= 1
            if remaining <= 0:
                return current
        current += timedelta(minutes=1)

    raise ValueError(f"Could not calculate finish within safety limit.")

# ── PUBLIC API ────────────────────────────────────────────────
def compute_finish(task):
    """
    Main entry point. Given a task dict with StartDateTime, Duration,
    ResourceName, WorkCalendarOverride, ScheduleType —
    returns (finish_datetime_str, error_string).
    """
    if task.get('ScheduleType') == 'Manual':
        return task.get('FinishDateTime'), None

    start_dt = parse_dt(task.get('StartDateTime'))
    if not start_dt:
        return None, "Start date/time is required."

    duration = int(task.get('Duration') or 0)
    if duration <= 0:
        return start_dt.strftime('%Y-%m-%dT%H:%M:%S'), None

    # Resolve calendar
    override = task.get('WorkCalendarOverride')
    if override:
        calendar = get_work_calendar(override)
        if not calendar:
            return None, f"Work Calendar '{override}' not found."
    else:
        resources = task.get('ResourceName', '')
        if not resources:
            return None, "No resource and no calendar override set."
        first_resource = resources.split(',')[0].strip()
        calendar = get_resource_calendar(first_resource, start_dt)
        if not calendar:
            return None, f"No calendar for '{first_resource}' on {start_dt.strftime('%Y-%m-%d')}."

    holidays = get_holidays()

    # Snap start to next working minute
    actual_start = next_working_minute(start_dt, calendar, holidays)
    finish_dt    = calculate_finish(actual_start, duration, calendar, holidays)

    return finish_dt.strftime('%Y-%m-%dT%H:%M:%S'), None

def validate_task_calendar(task):
    """
    Validate that the task's date range is fully covered by a single
    resource calendar entry. Returns error string or None.
    """
    if task.get('ScheduleType') == 'Manual':
        return None
    if task.get('WorkCalendarOverride'):
        return None  # Override bypasses validation

    resources = task.get('ResourceName', '')
    if not resources:
        return None  # No resource = no validation needed

    first_resource = resources.split(',')[0].strip()
    start_dt  = parse_dt(task.get('StartDateTime'))
    finish_dt = parse_dt(task.get('FinishDateTime'))

    if not start_dt or not finish_dt:
        return None

    _, error = get_resource_calendar_for_range(first_resource, start_dt, finish_dt)
    return error

def get_successor_start(predecessor_finish_str, resource_name, wc_override=None):
    """
    Given predecessor finish, return the next available working start
    for the successor resource. Returns (datetime_str, error).
    """
    finish_dt = parse_dt(predecessor_finish_str)
    if not finish_dt:
        return None, "Invalid predecessor finish date."

    if wc_override:
        calendar = get_work_calendar(wc_override)
        if not calendar:
            return None, f"Work Calendar '{wc_override}' not found."
    else:
        calendar = get_resource_calendar(resource_name, finish_dt)
        if not calendar:
            # Try next day
            calendar = get_resource_calendar(resource_name,
                finish_dt + timedelta(days=1))
        if not calendar:
            return None, f"No calendar for '{resource_name}' near {finish_dt.strftime('%Y-%m-%d')}."

    holidays = get_holidays()
    start_dt  = next_working_start_after(finish_dt, calendar, holidays)
    return start_dt.strftime('%Y-%m-%dT%H:%M:%S'), None

# ── HELPERS ───────────────────────────────────────────────────
def parse_dt(val):
    if not val:
        return None
    for fmt in ('%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d'):
        try:
            return datetime.strptime(str(val).strip(), fmt)
        except ValueError:
            continue
    return None

def parse_time(val):
    if not val:
        return dtime(8, 0)
    try:
        parts = str(val).strip().split(':')
        return dtime(int(parts[0]), int(parts[1]))
    except:
        return dtime(8, 0)

# ── QUICK TEST ────────────────────────────────────────────────
if __name__ == '__main__':
    # Test with EST_8AM_5PM
    cal = get_work_calendar('EST_8AM_5PM')
    print("Calendar:", cal)
    holidays = get_holidays()

    from datetime import datetime
    start = datetime(2026, 6, 1, 8, 0)
    finish = calculate_finish(start, 60, cal, holidays)  # 60 mins
    print(f"Start: {start}, Duration: 60 min → Finish: {finish}")

    finish2 = calculate_finish(start, 540, cal, holidays)  # 9 hrs = full day
    print(f"Start: {start}, Duration: 540 min → Finish: {finish2}")

    nxt = next_working_start_after(datetime(2026, 6, 5, 17, 0), cal, holidays)  # Friday 5pm
    print(f"Next working start after Friday 5pm: {nxt}")  # Should be Monday 8am
