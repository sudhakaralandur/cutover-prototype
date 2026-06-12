import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'project_mgmt.db')
conn = sqlite3.connect(db_path)
cols = [r[1] for r in conn.execute('PRAGMA table_info(Tasks)').fetchall()]

if 'WorkCalendarOverride' not in cols:
    conn.execute('ALTER TABLE Tasks ADD COLUMN WorkCalendarOverride TEXT')
    print('Added WorkCalendarOverride')
else:
    print('WorkCalendarOverride already exists')

if 'ScheduleType' not in cols:
    conn.execute("ALTER TABLE Tasks ADD COLUMN ScheduleType TEXT DEFAULT 'Auto'")
    print('Added ScheduleType')
else:
    print('ScheduleType already exists')

conn.commit()
conn.close()
print('Migration complete')
