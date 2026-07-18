"""
One-time migration: convert Predecessor/Successors from row-position numbers
(fragile - breaks when tasks are inserted/reordered) to stable TaskID references.

Assumes existing Predecessor/Successors values are 1-based row-position numbers
from the original import order (TaskID insertion order = import order).

Run ONCE against your real project_mgmt.db, with the app stopped, before
deploying the updated admin.py.
"""
import sqlite3

DB_PATH = "project_mgmt.db"

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

projects = conn.execute("SELECT DISTINCT Client,ProjectName,Release FROM ProjectInfo").fetchall()

def parse_refs(val):
    """Parse comma/semicolon separated numbers from a Predecessor/Successors string."""
    if not val:
        return []
    parts = [p.strip() for p in val.replace(';', ',').split(',') if p.strip()]
    out = []
    for p in parts:
        try:
            out.append(int(p))
        except ValueError:
            pass  # already non-numeric (e.g. already migrated, or malformed) - skip
    return out

total_fixed = 0
for proj in projects:
    client, project, release = proj['Client'], proj['ProjectName'], proj['Release']
    tasks = conn.execute(
        "SELECT TaskID, Predecessor, Successors FROM Tasks WHERE Client=? AND ProjectName=? AND Release=? ORDER BY TaskID",
        [client, project, release]
    ).fetchall()

    if not tasks:
        continue

    # ordinal position (1-based, in original insertion/import order) -> TaskID
    ordinal_to_taskid = {i + 1: t['TaskID'] for i, t in enumerate(tasks)}

    for t in tasks:
        pred_nums = parse_refs(t['Predecessor'])
        succ_nums = parse_refs(t['Successors'])

        new_pred = [str(ordinal_to_taskid[n]) for n in pred_nums if n in ordinal_to_taskid]
        new_succ = [str(ordinal_to_taskid[n]) for n in succ_nums if n in ordinal_to_taskid]

        new_pred_str = ','.join(new_pred)
        new_succ_str = ','.join(new_succ)

        if new_pred_str != (t['Predecessor'] or '') or new_succ_str != (t['Successors'] or ''):
            conn.execute(
                "UPDATE Tasks SET Predecessor=?, Successors=? WHERE TaskID=?",
                [new_pred_str, new_succ_str, t['TaskID']]
            )
            total_fixed += 1

    print(f"{client}/{project}/{release}: {len(tasks)} tasks scanned")

conn.commit()
conn.close()
print(f"Done. {total_fixed} task(s) had Predecessor/Successors converted to TaskID references.")
