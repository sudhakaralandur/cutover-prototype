import sqlite3, os

db_path = os.path.join(os.path.dirname(__file__), 'project_mgmt.db')
conn = sqlite3.connect(db_path)

# Get all resources
resources = conn.execute("""
    SELECT ResourceName, ResourceEmail FROM Resources
    WHERE Client='ABC Company' AND ProjectName='Vanguard' AND Release='Mock 1'
    ORDER BY ResourceName
""").fetchall()

# Clear existing auto-populated entries and re-insert
conn.execute("DELETE FROM ResourceCalendar WHERE Notes='Auto-populated'")

inserted = 0
for r in resources:
    conn.execute("""
        INSERT INTO ResourceCalendar
        (ResourceName, ResourceEmail, EffectiveFrom, EffectiveTo, WorkingHrsCode, Notes)
        VALUES (?, ?, ?, ?, ?, ?)
    """, [r[0], r[1] or '', '2026-01-01', '2026-12-31', 'CST_8AM_5PM', 'Auto-populated'])
    inserted += 1

conn.commit()
print(f"Inserted {inserted} resource calendar entries")
print(f"Total: {conn.execute('SELECT COUNT(*) FROM ResourceCalendar').fetchone()[0]}")
conn.close()
