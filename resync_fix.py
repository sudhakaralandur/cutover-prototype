"""
One-time fix: resync NumberRange.LastUsedNumber to the actual MAX(UniqueID)
in Tasks for each project. Run this locally against your real project_mgmt.db.
"""
import sqlite3

DB_PATH = "project_mgmt.db"  # adjust path if running from elsewhere

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

projects = conn.execute("SELECT DISTINCT Client,ProjectName,Release FROM ProjectInfo").fetchall()

for p in projects:
    client, project, release = p['Client'], p['ProjectName'], p['Release']
    max_row = conn.execute(
        "SELECT MAX(UniqueID) as maxid FROM Tasks WHERE Client=? AND ProjectName=? AND Release=?",
        [client, project, release]
    ).fetchone()
    max_id = max_row['maxid'] or 0

    nr = conn.execute(
        "SELECT RangeKey, LastUsedNumber FROM NumberRange WHERE Client=? AND ProjectName=? AND Release=?",
        [client, project, release]
    ).fetchone()

    if nr:
        if nr['LastUsedNumber'] < max_id:
            conn.execute("UPDATE NumberRange SET LastUsedNumber=? WHERE RangeKey=?", [max_id, nr['RangeKey']])
            print(f"FIXED: {client}/{project}/{release} -> LastUsedNumber {nr['LastUsedNumber']} -> {max_id}")
        else:
            print(f"OK: {client}/{project}/{release} already in sync ({nr['LastUsedNumber']})")
    else:
        print(f"NO NumberRange row for {client}/{project}/{release} — skipping (created on first save)")

conn.commit()
conn.close()
print("Done.")
