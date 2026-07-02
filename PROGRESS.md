# Cutover Prototype — Progress File
**Repo:** https://github.com/sudhakaralandur/cutover-prototype  
**Local:** `C:\Users\sudha\OneDrive\00-Codex Projects\Cutover Prototype`  
**GitHub PAT:** YOUR_GITHUB_PAT_HERE  
**Flask port:** 5001 (`host='0.0.0.0'`)  
**Python:** 3.14.4 | **Editor:** Notepad++  

---

## What's Built (Phase 1 — Complete)

### Files in repo
- `app.py` — Flask main app, registers admin blueprint, port 5001
- `admin.py` — Admin blueprint: all CRUD APIs for Steps 1–7 + Excel import
- `scheduler.py` — Working-hours finish calculator (None-safe, busy_timeout fixed)
- `migrate.py` — Adds WorkCalendarOverride + ScheduleType columns to Tasks
- `populate_calendars.py` — Bulk-assigns CST_8AM_5PM to all 151 resources
- `start_ngrok.bat` — Launches app.py then ngrok tunnel on port 5001
- `templates/index.html` — Live viewer (WBS tree, team badges, progress bars, chunked render)
- `templates/admin.html` — Admin wizard Steps 1–7 + Excel import modal

### Database: `project_mgmt.db` (SQLite)
**Tables:** ProjectInfo, ProjectUsers, NumberRange, Tasks, Resources, ResourceCalendar, WorkCalendar, Holidays  
**Project loaded:** ABC Company / Vanguard / Mock 1  
**Tasks:** 786 rows | **Resources:** 151 | **NumberRange key:** ABCVANMOC  
**WorkCalendar seeds:** EST_8AM_5PM, CST_8AM_5PM, PST_8AM_5PM, IST_9AM_6PM, 24x7  
**ResourceCalendar:** 151 entries, all CST_8AM_5PM, 2026-01-01 to 2026-12-31

### Tasks table extra columns (added via migrate.py)
- `WorkCalendarOverride TEXT` — FK to WorkCalendar, bypasses resource calendar
- `ScheduleType TEXT DEFAULT 'Auto'` — 'Auto' or 'Manual'
- `PerComplete REAL DEFAULT 0.0`

### Admin Wizard — Steps
- **Step 1** WorkCalendar CRUD
- **Step 2** ProjectInfo CRUD
- **Step 3** ProjectUsers (multiple per project)
- **Step 4** Resources (per project)
- **Step 5** ResourceCalendar — resource dropdown from Step 4, WC dropdown from Step 1, project-scoped
- **Step 6** Holidays (global)
- **Step 7** Task editor — modal-based, Add/Delete/Indent/Outdent/Save All + Excel import

### Key fixes applied (already in repo)
- `scheduler.py`: `calendar.get('X') or default` (was crashing on NULL WorkDays)
- `admin.py`: atomic UniqueID claiming (fixes UNIQUE constraint race condition)
- `admin.py`: `PRAGMA busy_timeout = 8000` + explicit `conn.close()` (fixes DB locked error)
- `admin.py`: blueprint-wide error handler returns JSON not HTML on crash
- `templates/admin.html`: `sortByWBS()` applied on load + after Save All
- `templates/admin.html`: predecessor auto-calc shows clear error if predecessor has no finish date
- `templates/index.html`: chunked rendering (150 rows at a time, no page freeze)

### Pending Phase 1 fixes (not yet done)
- Step 7: Auto Start/Finish calculation from predecessor still not working reliably for new tasks (resource calendar lookup fails when task dates don't match calendar range)
- Header task duration/% rollup not triggered after modal save (only runs on import)
- Export to Excel not built yet

---

## Phase 2 — What to Build Next

### Goal
Agent monitors task completions → sends MS Teams messages → parses replies with Claude AI → updates DB → logs Jira bugs on request

### Architecture
```
DB (Tasks table) → APScheduler monitor
  → predecessor complete → Agent wakes
  → Single resource: 1:1 Teams DM
  → Multiple resources: Teams group chat
  → Resource replies → Claude API classifies:
      ACK / DONE / DELAY / ISSUE / NO_REPLY
  → DB updated (PerComplete, StartDateTime, FinishDateTime)
  → ISSUE: agent asks "Log in Jira?" → Yes → POST to client Jira REST API → reply with ticket #
  → NO_REPLY after threshold → nudge → escalate to PMO
```

### Environment (confirmed)
- **Teams:** Running on personal PC, signed in with `sudhakar.alandur@outlook.com` (personal Microsoft account)
- **MS Graph API:** Works with personal M365 account — needs app registration at https://portal.azure.com (personal account, free tier)
- **Claude API:** Anthropic API key needed (user has access via claude.ai but needs API key)
- **Jira:** Client-provided API key (future — not blocking Phase 2 start)
- **Deployment:** Local only (no Azure subscription on Capgemini account, personal account has free trial available)
- **New packages needed:** `msal` (MS Graph auth), `anthropic` (Claude API)

### Phase 2 build order
1. Register MS Graph app in Azure portal (personal account) — get client_id, client_secret, tenant_id
2. Build `teams_agent.py` — APScheduler polls DB, sends Teams messages via MS Graph
3. Build `reply_parser.py` — Claude API classifies incoming Teams replies
4. Wire up: reply → DB update → cascade to next task
5. Add Jira integration (client provides API key)

### Pending question from last session
- Does user want to use the **free Azure trial** ($200 credit) for MS Graph app registration, or use the Capgemini tenant (they can see it but have no subscription)?
- User confirmed Teams is running with personal outlook.com — MS Graph personal account path is viable

---

## How to Start New Chat

Paste this at the start of a new chat:
```
I am continuing work on my Cutover Prototype project.
Repo: https://github.com/sudhakaralandur/cutover-prototype
PAT: YOUR_GITHUB_PAT_HERE
Local path: C:\Users\sudha\OneDrive\00-Codex Projects\Cutover Prototype
Flask port: 5001, Python 3.14.4, Notepad++

Please fetch PROGRESS.md from the repo and continue from where we left off.
We were about to start Phase 2 — MS Teams agent using MS Graph API.
Teams is running on this PC signed in with sudhakar.alandur@outlook.com (personal Microsoft account).
```
