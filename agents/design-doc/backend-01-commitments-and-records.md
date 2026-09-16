# Commitments + Records — Unified Core Module

> **A single, flexible module** that replaces separate Habit Tracker, Task Manager, and Goals modules with 3 core tables that can represent anything trackable.

---

## 1. Motivation

The original design had separate modules for habits, tasks, and goals. In practice, these share a common pattern:

- Each is **something you commit to doing** (a commitment)
- Progress is measured through **time-bound records** (a record)
- Commitments form **hierarchies** (goals contain sub-goals contain tasks)
- A single record can relate to any type of commitment

A unified module eliminates duplication, simplifies cross-module queries (habits that serve a goal, tasks that belong to a sub-goal), and makes it trivial to add new types later.

---

## 2. Core Tables

Three tables, one self-referential relationship:

### 2.1 `commitments` — Everything You Track

| Field | Type | Description |
|---|---|---|
| `id` | UUID | PK |
| `user_id` | UUID | FK → users |
| `type` | `enum` | `habit` / `goal` / `task` |
| `title` | `varchar(255)` | |
| `description` | `text` | Optional verbose description |
| `status` | `enum` | `active` / `in_progress` / `archived` / `completed` / `paused` |
| `priority` | `enum` | `none` / `low` / `medium` / `high` |
| `config` | `jsonb` | Type-specific configuration (see below) |
| `due_date` | `date` | Optional deadline (tasks, goals) |
| `sort_order` | `integer` | Manual ordering within a group; also used for checklist item order on tasks |
| `created_at` | `timestamptz` | |
| `updated_at` | `timestamptz` | |

**`config` JSONB contents per type:**

```jsonc
// type: habit
{ "target_count": 7 } // Hardcoded to weekly (e.g. 7 = daily, 3 = 3x/week)

// type: goal
{ "progress_type": "checklist" }         // done when all children done
{ "progress_type": "percentage",         // progress bar
  "target_value": 100,                   // e.g. "100 books"
  "unit": "books" }

// type: task — no extra config, `status` field is sufficient.
// A task may carry checklist items as records (status: done/not_done, sort_order set).
// When any records exist with sort_order set, the UI renders them as a checklist.
```

### 2.2 `commitment_links` — Parent-Child Hierarchy

| Field | Type | Description |
|---|---|---|
| `parent_id` | UUID | PK, FK → commitments |
| `child_id` | UUID | PK, FK → commitments |
| `sort_order` | `integer` | Order among siblings |

**Primary key:** composite `(parent_id, child_id)` — each parent↔child link is unique.

**Purpose:** Allows arbitrary trees — a goal can contain sub-goals, sub-goals can contain tasks, a habit can be linked to a goal. One commitment can have multiple parents if needed (e.g., a task serving two goals), though a single parent is the common case.

### 2.3 `records` — Time-Bound Logs

| Field | Type | Description |
|---|---|---|
| `id` | UUID | PK |
| `commitment_id` | UUID | FK → commitments, nullable (for standalone entries) |
| `date` | `date` | The day this record belongs to |
| `content` | `text` | Free-text note / description |
| `status` | `enum` | `done` / `not_done` / `partial` / `skip` |
| `value` | `numeric` | Optional: for progress tracking (e.g., "ran 5 km") |
| `sort_order` | `integer` | Checklist item order when records are used as task checklist items |
| `created_at` | `timestamptz` | |

---

## 3. Usage Patterns

### 3.1 Habit Tracking

```
Commitment (type: habit): "Morning Meditation"
├── config: { target_count: 7 }
│
├── Record (date: 2026-07-15, status: done)
├── Record (date: 2026-07-14, status: done)
├── Record (date: 2026-07-13, status: done)
└── ...
```

- Streak = consecutive `done` records going backward from yesterday or today
- Completion rate = `done` records / days in month
- All habits are evaluated on a weekly cadence using `target_count` (e.g. 7 times a week = daily).

### 3.2 Goal Tracking

```
Commitment (type: goal): "Read 100 books"
├── config: { progress_type: "percentage", target_value: 100, unit: "books" }
├── status: active
│
├── Commitment (type: goal): "July: read 8 books"
│   ├── Record (date: 2026-07-10, status: done, content: "Finished 'Atomic Habits'")
│   ├── Record (date: 2026-07-05, status: done, content: "Finished 'Deep Work'")
│   └── ...
│
└── Commitment (type: habit): "Read 30 min daily"  ← habit linked to goal
    └── Record (date..., status: done)
```

- Progress is computed by aggregating children (auto_sub) or counting records (checklist)
- A goal with `progress_type: "checklist"` is complete when all sub-commitments marked complete
- A goal with `progress_type: "percentage"` uses target_value vs sum(records.value)

### 3.3 Task Management

```
Commitment (type: task): "Design mobile UI"
├── status: in_progress        ← task status is on the commitment itself
├── priority: high
│
└── Record (date: 2026-07-14, content: "Finished wireframes", status: done)
```

- A task's current state lives in `commitments.status` (not inferred from records)
- Tasks are dynamically grouped at runtime based on their `due_date`:
  - **Inbox**: `due_date IS NULL`
  - **Today**: `due_date = CURRENT_DATE`
  - **Upcoming**: `due_date > CURRENT_DATE`
- Records on a task serve as **activity log / history** — what happened when
- Status transitions can be recorded via records for future audit

**Checklist mode (replaces the former `list` type):**

```
Commitment (type: task): "Grocery Shopping"
├── status: in_progress
├── Record (sort_order: 1, content: "Milk",  status: not_done)
├── Record (sort_order: 2, content: "Eggs",  status: done)
└── Record (sort_order: 3, content: "Bread", status: not_done)
```

- A task enters checklist mode when it has one or more records with `sort_order` set
- Progress = `done` records / total records (same formula, no new logic)
- The UI detects checklist mode from the presence of ordered records and renders them inline
- No schema change required — checklist items are just records with `sort_order` populated

### 3.5 Planner / Daily Log

```
Record (date: 2026-07-15, content: "Met with team about project X")
Record (date: 2026-07-15, content: "Ordered new monitor", commitment_id: uuid-of-todo)
Record (date: 2026-07-15, content: "Had coffee with Alice")
```

- Records can exist without a commitment (independent journal entries)
- Or be attached to a commitment for context ("Ordered monitor" → attached to todo item)

---

## 4. API Design

### 4.1 Base URL

```
/api/v1/pursuits/
```

The module is named `pursuits` (the API namespace), containing `commitments` and `records` resources.

### 4.2 Commitments

```
POST   /api/v1/pursuits/commitments            — Create
GET    /api/v1/pursuits/commitments             — List
GET    /api/v1/pursuits/commitments/:id         — Detail (includes progress, children, recent records)
PUT    /api/v1/pursuits/commitments/:id         — Update
PUT    /api/v1/pursuits/commitments/reorder     — Batch update sort_order [{id, sort_order}]
DELETE /api/v1/pursuits/commitments/:id         — Delete
```

**List filters:**
```
?type=habit|goal|task
&status=active|in_progress|archived|completed|paused
&priority=high|medium|low
&parent_id=uuid       — children of a specific commitment
&root=true            — top-level only (no parent)
&date=2026-07-15      — commitments with records on this date
&due_date_from=2026-07-01&due_date_to=2026-07-31 — filter by deadline range (for month calendars)
&q=search term        — text search on title
```

**Progress computation (automatically returned in GET /:id):**

```jsonc
"progress": {
  "method": "streak" | "percentage" | "auto_sub" | "checklist" | "checklist_items" | "records",
  "done": 32,
  "total": 100,
  "percent": 32,
  "streak": 21 // Habit streak via consecutive done records going backward from today/yesterday.
}
```

- **streak:** For habits; backend computes this by traversing consecutive `done` records backward from today/yesterday.
- **percentage:** For goals with `progress_type: "percentage"` — `done` = sum of record values, `total` = target_value.
- **auto_sub:** Average percent of children (goal with sub-goals).
- **checklist:** Children with `status = completed` / total children (goal with checklist progress type).
- **checklist_items:** Records with `sort_order` set and `status = done` / total such records (task in checklist mode).
- **records:** Default fallback — zero progress.

### 4.3 Records

```
POST   /api/v1/pursuits/records                — Create
POST   /api/v1/pursuits/records/batch          — Batch create (habit check-in)
GET    /api/v1/pursuits/records                — List
GET    /api/v1/pursuits/records/:id            — Detail
PUT    /api/v1/pursuits/records/:id            — Update
PUT    /api/v1/pursuits/records/reorder        — Batch update sort_order [{id, sort_order}]
DELETE /api/v1/pursuits/records/:id            — Delete
```

**List filters:**
```
?commitment_id=uuid    — records for a specific commitment
&date=2026-07-15       — single day
&date_from=&date_to=   — date range
&status=done|not_done   — filter by status
```

### 4.4 Special Endpoints

```
GET /api/v1/pursuits/daily/:date
GET /api/v1/pursuits/heatmap?from=:date&to=:date
```

- **Daily:** Returns a consolidated daily view: all active habits with today's check-in status, today's tasks, goal progress overview, and free records for that date.
- **Heatmap:** Returns date-count pairs for records with `status: done` across all the user's commitments in the given date range.

---

## 5. Data Flow Examples

### 5.1 Habit Check-in (Morning Routine)

```
1. User opens MyWorld → hits Dashboard
2. GET /api/v1/pursuits/daily/2026-07-15
   → Returns all active habits, each with `today_record: { status: "done" | null }`
3. User taps checkboxes for "Meditation" and "Exercise"
4. POST /api/v1/pursuits/records/batch
   [{ commitment_id: "med-uuid", date: "2026-07-15", status: "done" },
    { commitment_id: "ex-uuid", date: "2026-07-15", status: "done" }]
5. Dashboard re-fetches → heatmap updates, streak shown
```

### 5.2 Goal Progress Update

```
1. User finishes reading "Atomic Habits"
2. POST /api/v1/pursuits/records
   { commitment_id: "july-books-uuid", date: "2026-07-10",
     content: "Finished Atomic Habits - great chapter on habit stacking",
     status: "done" }
3. GET /api/v1/pursuits/commitments/read-100-books
   → progress.percent updated from sub-goal aggregation
```

### 5.3 Daily Planning

```
1. User opens "Today" view
2. GET /api/v1/pursuits/daily/2026-07-15
3. User adds free-form entries:
   POST /api/v1/pursuits/records
   { date: "2026-07-15", content: "Buy groceries - milk, eggs, bread" }
   POST /api/v1/pursuits/records
   { commitment_id: "design-task-uuid", date: "2026-07-15",
     content: "Work on mobile wireframes for 2h" }
4. View shows all entries grouped: habit check-ins, task activity, free notes
```

---

## 6. Calendar / Heatmap Integration

Records are inherently date-keyed, which makes calendar visualization natural:

- **Habit heatmap:** For a given habit, count records with `status: done` per day. Exposed via `GET /api/v1/pursuits/heatmap?from=&to=`.
- **Combined dashboard calendar:** For each day, show habit dots (done habits / total) + task chips
- **Goal timeline:** When were records created? Show progress over time

The same `records` table feeds all calendar views — no separate aggregation needed.

---

## 7. Integration with Other Modules

### Dashboard Module
- `GET /api/v1/pursuits/daily/:date` is the Dashboard's primary data source
- Shows: habit check-in status, today's tasks, goal progress bars, planner entries

### Knowledge Space Module (Future)
- Records with substantive `content` could be auto-imported into Knowledge Space
- Records with detailed content could auto-import into Knowledge Space as notes

### AI Queries (Future)
- "How many books did I read last month?" → count records with `status: done` for book-related goal
- "What did I do last Tuesday?" → query records by date range

---

## 8. Directory Structure

```
backend/
└── routers/
    └── pursuits.py              # API routes (commitments + records)

schemas/
├── commitment.py
├── record.py
└── daily.py                     # Daily view schema

services/
├── commitment_service.py
├── record_service.py
└── progress_service.py          # Progress computation logic

models/
├── commitment.py                # SQLAlchemy model
├── record.py
└── commitment_link.py
```

```
frontend/src/
├── views/
│   ├── Dashboard.jsx            # Daily overview (habits + tasks + planner)
│   ├── Commitments.jsx          # All commitments list (filterable by type)
│   ├── CommitmentDetail.jsx     # Single commitment detail + records timeline
│   └── DailyLog.jsx             // Today's planner / free-form recording
├── components/
│   ├── HabitChecklist.jsx       # Daily habit check-in list
│   ├── GoalCard.jsx             # Goal progress card with children
│   ├── TaskCard.jsx             # Task with status, priority, date
│   ├── CalendarHeatmap.jsx      # Shared heatmap component
│   ├── Timeline.jsx             # Records timeline for a commitment
│   └── PlannerEntry.jsx         # Free-form daily entry
└── stores/
    └── pursuitsStore.js         # Zustand store for commitments + records
```

---

## 9. Migration from Old Schema

The new module **replaces** the separate Habit Tracker and Task Manager tables:

```sql
-- Old tables (removed):
-- habits, habit_logs, projects, tasks, subtasks, tags, task_tags

-- New tables:
commitments, commitment_links, records
```

Migration path:
1. Old `habits` → commitments with `type: habit`
2. Old `habit_logs` → records with `commitment_id` pointing to the new commitment
3. Old `tasks` → commitments with `type: task` (status columns map directly)
4. Old `subtasks` → commitments with `type: task` and a `parent_id` link
5. Old `projects` → commitments with `type: goal` (or just a grouping tag)
6. Old `tags` / `task_tags` → **deferred**. Tagging will be revisited as a cross-cutting concern once more modules exist (photos, documents, etc.) so the tag system can serve all content types uniformly.

---

## 10. Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Separate `commitment_links` table vs `parent_id` on commitment | **Separate table** | Supports many-to-many relationships; cleaner to query |
| Types as `enum` on commitment vs polymorphic tables | **Single table with type enum** | Simpler queries, no JOIN explosion; JSONB handles type-specific config |
| Task status on commitment vs inferred from records | **On commitment** | A task's current state is a value, not a time series; records serve as history |
| Module name `pursuits` in API path | **pursuits** | Distinct from any single type; signals the breadth of the module |
| `records` without a commitment_id | **Nullable** | Enables free-form planner entries without forcing a commitment creation |
| `commitment_links` PK | **Composite `(parent_id, child_id)`** | Natural unique constraint; no need for a surrogate ID on a join table |
| Tags deferred | **Not migrated** | Old `tags`/`task_tags` dropped; tagging will be redesigned as a cross-cutting system for all content types |
| `list` type removed; merged into `task` | **Task with checklist-mode records** | A "list" is just a task where items are ordered records. Removing the type simplifies the mental model, the filter UI, and the enum without any schema change — checklist mode is detected automatically when records with `sort_order` exist on a task |
