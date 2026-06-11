# Cutover Prototype

DB-based cutover project management tool.

## Database: `project_mgmt.db`

| Table | Rows | Description |
|-------|------|-------------|
| ProjectInfo | 1 | Project: ABC Company / Vanguard / Mock 1 |
| ProjectUsers | 3 | Authorized users |
| NumberRange | 1 | UniqueID tracker (key: ABCVANMOC) |
| Resources | 151 | All project resources with dummy emails |
| Tasks | 786 | Full task list with WBS hierarchy + rollups |
| WorkCalendar | 5 | Named shift templates (EST/CST/PST/IST/24x7) |
| ResourceCalendar | 0 | Per-resource date-range schedules (TBD) |
| Holidays | 0 | Blackout dates (TBD) |

## WBS Structure
- MS Project style hierarchy (1, 1.1, 1.1.1...)
- Header task Duration = sum of leaf children durations
- Header PerComplete = weighted avg by duration

## Local path
`C:\Users\sudha\OneDrive\00-Codex Projects\Cutover Prototype\`
