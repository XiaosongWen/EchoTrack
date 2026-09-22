# Dashboard + Pursuits — UI/UX Design

> **App layout redesign** unifying Habits, Tasks, Goals, and Planner into two primary pages: a daily journal-style Dashboard and a unified Pursuits browse page. Desktop-first, mobile adaptation deferred.

---

## 1. Navigation Structure

```
Sidebar (Collapsible Drawer with toggle button)
├── Mission Control
│   ├── 📅 Dashboard          ← 日记式每日视图（打卡 + 任务 + 进度 + planner 记录）
│   ├── 🎯 Pursuits          ← 统一浏览页（filter 切换 All / Habits / Goals / Tasks）
│   └── 🧠 Knowledge
├── Media
│   ├── 📷 Photos
│   ├── 🎬 Videos
│   └── 📚 Books
└── Theme
    └── (Color toggle dots)
```

- Dashboard answers: **"What did I do today? What do I need to do?"**
- Pursuits answers: **"What commitments do I have? How is progress overall?"**

---

## 1.1 Global App Header

```text
[ 🔍 Search commitments, logs, or type a command... (Cmd+K) ]       [🔔] [(Avatar)]
```

- Sits persistently at the top of the main container, across all views.
- **Left:** Global search bar for quick navigation, querying records, and command execution.
- **Right:** Quick actions including a Notification bell and a circular User Profile avatar.

---

## 2. Dashboard — Daily Journal View

### 2.1 Page Structure


```
┌─ Header: Flip Clock (Time/Date) ─────── 5-Day Weather & Time Progress ─┐
├─ 📋 Today's Tasks (4x fixed size) │ 📝 Daily Log (4x fixed size)       │
├─ 🔄 Habits (4x fixed size)        │ 🎯 Goal Progress (4x fixed size)   │
└─ 📅 Month at a Glance (月历视图) ──────────────────────────────────────────┘
```

### 2.2 Header

```
[ 09 : 41 : 12 ] CDT          [ Wed ⛅ ] [ Thu ☀️ ] [ Fri 🌧️ ]
Wednesday | July 15, 2026     [ Month 48% ] [ Quarter 16% ] [ Year 54% ]
```

- Left: Premium mechanical flip clock with timezone indicator and date.
- Right (Top Row): 5-Day Weather forecast widget with emojis and temperatures.
- Right (Bottom Row): Time progress widget tracking percentage of Month, Quarter, and Year completion.

### 2.3 ☀️ Morning Routine (Habit Check-in)

**Layout:**

```
🔄 Habits                         🔥 21-day streak
──────────────────────────────────────────────────
[☑] Morning Meditation   Wellness   14 days   🟢
[☐] Exercise (30m)       Health      5 days   ○
[☐] Read 30 Pages        Growth      3 days   ○
[☐] Deep Work (2 hrs)    Work        1 day    ○
```
*Note: All items across Dashboard cards include colored label tags (e.g. Wellness, Health) to match the Pursuits module.*

**States:**

| State | UI |
|---|---|
| Normal | List of active habits, each with checkbox + name + streak count |
| Habit checked today | ☑ green background, subtle scale animation (100ms) |
| All habits done | Header shows ✅ "All done today!" with confetti-like badge |
| No active habits | "🌱 No habits yet. Start tracking something!" + [Create Habit] CTA |
| API failure | Checkbox turns ❌ red, shows "Retry" label on hover |
| Loading | Skeleton: 4 rows of [□ icon + 60% width bar] |
| Offline | Checkboxes disabled, shows "Offline — changes will sync later" |

**Interactions:**
- Tap ☐ → immediate POST `/api/v1/pursuits/records/batch`
- Checkbox animation: 0→1 with 100ms scale bounce, green fill
- Each habit row has a `⋯` menu: Skip today / Edit / View history
- Header date selector: `< Jul 14 | Jul 15 | Jul 16 >` — allows back-filling missed days

### 2.4 📝 Daily Log (Planner Entries)

**Layout:**

```
📝 Daily Log
──────────────────────────────────────────────────
🕐 09:00  Met with team about Q3 roadmap   Work
🕐 14:30  Bought groceries                 Errands
🕐 16:30  Finished Ch.3 "Atomic Habits"    Growth   → 🎯 Read 100 books

[📝 + Add what you did today...]              [@] [+]
```
*Note: Includes label tags on each entry to visually map to commitments.*

**States:**

| State | UI |
|---|---|
| Normal | List of records for today, newest first or time-sorted |
| Empty | A single empty input row with placeholder text |
| Associated to a commitment | Record shows right arrow → commitment title (clickable) |
| Unassociated | Plain text entry |
| Loading | 3 skeleton lines with varying widths |
| API failure on save | Rowed turns red ❌, "Tap to retry" |

**Interactions:**
- Bottom input: type → `Enter` creates a record immediately (optimistic update)
- `@` mention: type `@` → dropdown searches commitments → select one to link
- `@` results show: icon + type label + title, e.g. `🎯 Read 100 books`
- Click existing record → inline edit (content, time, association)
- Right `[🗑]` → delete with confirmation ("Delete this entry?")
- Time prefix: type `09:00 ` → auto-parsed into `🕐 09:00` display
- Multi-line paste: parse line-by-line, each line becomes a record

### 2.5 📋 Today's Tasks

**Layout:**

```
📋 Today's Tasks                    [View All →]
──────────────────────────────────────────────────
🔄  Design mobile UI screens        Work    [Edit]
📋  Buy groceries                   Errands [Edit]
✓   Setup Docker                    Tech    [Edit]
```
*Note: Includes label tags and Edit buttons for full feature parity with the Pursuits Tasks view.*

**States:**

| State | UI |
|---|---|
| Tasks exist | List of tasks with status icon, title, priority dot, deadline |
| No tasks today | "🌴 No tasks due today" |
| All done | All items show green ✓, header: "✅ All done!" |
| Loading | 2 skeleton rows |

**Interactions:**
- Click task → open commitment detail side panel (see section 4)
- Status icon: ☐ (Todo) / 🔄 (In Progress) / ✓ (Done) — click to cycle
- Priority shown as colored dot: 🔴 High / 🟡 Medium / ⚪ Low
- "View All →" link → navigates to Pursuits page with [Tasks] filter pre-selected

### 2.6 🎯 Goal Progress

**Layout:**

```
🎯 Goal Progress
──────────────────────────────────────────────────
Read 100 books     Growth    ████████░░░░░░  32%
Lose 20 lbs        Health    ███░░░░░░░░░░░  15%
Run a marathon     Health    ░░░░░░░░░░░░░░   0%
```
*Note: Goal titles include category label tags.*

**States:**

| State | UI |
|---|---|
| Normal | Up to 3 active goals with progress bars |
| Goal made progress today | Row shows `▲ +1 today` badge |
| Goal 100% complete | Green bar + 🎉 badge + subtle sparkle |
| Goal overdue | Red bar + 🔴 "Overdue" label |
| No active goals | Section hidden entirely |
| Loading | 3 skeleton progress bars |

**Interactions:**
- Click goal → open detail side panel
- Progress bar colors: 0-25% gray → 26-50% blue → 51-75% orange → 76-99% deep orange → 100% green
- Deadline text: if < 7 days away → shows "🔥 Due in 5 days"

### 2.7 📅 Month at a Glance

**Layout:**

```
July 2026                                  [Today] [<] [>]
┌─────┬─────┬─────┬─────┬─────┬─────┬─────┐
│ Sun │ Mon │ Tue │ Wed │ Thu │ Fri │ Sat │
├─────┼─────┼─────┼─────┼─────┼─────┼─────┤
│ 28  │ 29  │ 30  │ 1   │ 2   │ 3   │ 4   │
│     │     │     │     │     │     │     │
└─────┴─────┴─────┴─────┴─────┴─────┴─────┘
```

- Replaces the weekly calendar with a full month view spanning the bottom of the dashboard grid.
- Includes a styling-matched "Today" button sandwiched between left/right month navigation arrows.

---

## 3. Pursuits — Unified Browse Page

### 3.1 Page Structure

```
┌─ Toolbar ──────────────────────────────────────────┐
│ [All] [Habits] [Goals] [Tasks]   [🔍] [+ ▾]        │
├─ Content (varies by filter) ──────────────────────┤
│                                                     │
└─────────────────────────────────────────────────────┘
```

**Filter behavior:** Single-select. Click "Habits" → only habits shown. Click "All" → return to grouped view.

**+ New menu:**
```
+ New ▾
├── Habit
├── Goal
├── Task
└── Note
```

### 3.2 Advanced Drag-and-Drop & Sorting

The Pursuits view utilizes a highly interactive and structured drag-and-drop engine:

*   **Task Reordering & Cross-Container Movement:** Tasks can be dragged seamlessly between Inbox, Today, and Upcoming lists. Dropping a task updates its date dynamically (e.g., dropping a task into Upcoming auto-adds a date badge).
*   **Strict Structural Boundaries:** Goal sub-items and List items are rigidly contained. You cannot accidentally drag a List item (e.g., "Eggs") into a Goal, or vice versa, preventing data corruption.
*   **Invisible Status Boundaries:** When reordering items, pending items are programmatically blocked from being dragged below completed items, and completed items are locked at the bottom.
*   **Auto-Sorting:** Clicking the checkbox on a Task or List item instantly marks it completed (strikethrough and opacity drop) and aggressively sorts it to the absolute bottom of the list. Goal sub-items are immune to auto-sorting to protect custom goal hierarchies.
*   **Infinite Nesting (Goals):** Dragging a task directly on top of another task inside a Goal card effortlessly creates a visually nested sub-task hierarchy.

### 3.3 All View (default)

Types grouped in sections. Each section shows first N items + "View all X →" link.

```
── Habits (4 active) ────────────────────────────
[☑] Meditation             🔥 14 days  85%
[☐] Read 30 Pages          🔥 3 days   90%
[☐] Exercise (30m)         🔥 5 days   60%
→ View all 4 habits

── Goals (3 active) ─────────────────────────────
Read 100 books     ████████░░  32%   Aug 15
Lose 20 lbs        ███░░░░░░░  15%   Sep 1
→ View all 3 goals

── Tasks (5 active) ──────────────────────────────
☐  Design mobile UI        In Progress · High
☐  Buy groceries           Todo · Low
☐  Grocery Shopping  ✓2/5  [checklist]  ← checklist-mode task shown with item count
→ View all 5 tasks
```

**States:**

| State | UI |
|---|---|
| Normal | Grouped sections with items |
| Type all done/empty | Section header shows ✅ or is hidden with inline text "No active habits" |
| Everything empty | Centered empty state: "Welcome! Create your first habit or goal to get started" + [Create] CTA |
| Loading | Each section shows a skeleton card |

### 3.3 Habits View

Selected filter: `[All] [Habits] [Goals] [Tasks]`

```
  ┌─ Calendar Heatmap ──────────────────────────┐
  │  ████████████░░░░░░░░░░░░░░░░░░             │
  │  Less ○○●○○ Less                              │
  └──────────────────────────────────────────────┘

  [☑] Meditation          🔥 14 days  85%   ░░███░░░  ← inline 6-week cal
  [☐] Read 30 Pages       🔥 3 days   90%   ░░░░░░░░
  [☐] Exercise (30m)      🔥 5 days   60%   ░░█░░░░░
  [☐] Deep Work (2 hrs)   🔥 1 day    45%   ░░░░░░░░
```

- Calendar heatmap identical to current prototype
- Inline mini-calendar: last 6 weeks, each cell is a day
- Click a habit → opens detail side panel with full stats + records timeline
- Direct check-in from list (same as Dashboard block)

### 3.4 Goals View

```
  🎯 Read 100 books
     ████████░░░░░░░░  32%  (32/100)
     Due: Aug 15, 2026
     ├─ July: read 8      ██░░  25%  (2/8)
     └─ August: read 8    ░░░░   0%  [paused]

  🎯 Lose 20 lbs
     ███░░░░░░░░░░░░░  15%  (3/20 lbs)
     Due: Sep 1, 2026
     └─ This month: 5 lbs  ██░░  40%  (2/5)
```

**States:**

| State | UI |
|---|---|
| Normal | Goal cards with progress bars + sub-goals |
| 100% complete | 🎉 confetti badge, green bar, callout text |
| Overdue | Red bar, 😬 "Overdue" label |
| No deadline | Deadline field hidden entirely from card |
| No sub-goals | Card shows records timeline instead of sub-items |
| Empty | "Create your first goal" CTA |

**Progress bar colors:**
| Range | Color |
|---|---|
| 0-25% | Gray (#888) |
| 26-50% | Blue (#4A90D9) |
| 51-75% | Orange (#E67E22) |
| 76-99% | Deep Orange (#D35400) |
| 100% | Green (#27AE60) |
| Overdue | Red (#E74C3C) |

### 3.5 Tasks View

```
  [Board ▾] [List] [Calendar]              ← View switcher
  [▶ All] [Todo] [In Progress] [Done]      ← Status filter  
  [🏷 All] [High] [Medium] [Low]           ← Priority filter

  Board view:
  ┌─ Todo (2) ─────┐  ┌─ In Progress (1) ┐  ┌─ Done (2) ────┐
  │ Buy groceries  │  │ Design mobile UI │  │ Setup Docker  │
  │ ...            │  │                  │  │ ...           │
  └────────────────┘  └──────────────────┘  └───────────────┘
```

- **Priority & Labels:** Tasks display colored priority dots (🔴 High, 🟡 Medium, ⚪ Low) that dynamically map to system theme variables, along with contextual colored pill tags (e.g., `Health`, `Work`) next to the task text.
- **Board view:** Kanban (migrated from current prototype's task board)
- **List view:** Flat table with sortable columns
- **Calendar view:** Month grid showing tasks on their due dates
- Status + priority filters are additional filters shown only when Tasks filter is active

**Checklist-mode tasks** (tasks with ordered checklist records) render inline-expanded in the List view:

```
  List view:
  ☐  Design mobile UI        In Progress · High          [Edit]
  ☐  Grocery Shopping        Todo        2/5 ██░░░░░░░░  [Edit]
     ☑ Milk
     ☑ Yogurt
     ☐ Eggs
     ☐ Bread
     ☐ Fruit
     [+ Add item...]
  ✓  Setup Docker             Done        · Low           [Edit]
```

- A task automatically enters checklist mode when it has any records with `sort_order` set
- Checklist items are toggled inline (same optimistic POST as habit check-in)
- Drag handle on the left of each item for reorder → `PUT /pursuits/records/reorder`
- Creating a new task with "+ Add checklist item" input auto-sets `sort_order`
- In Board view, checklist-mode tasks show a compact `✓2/5` progress badge on the card

---

## 4. Interaction Flows

### 4.1 Create Commitment (Side Panel)

Trigger: `+ New` in Pursuits page toolbar.

**Panel layout (slide-in from right, 480px wide):**

```
┌─ New Commitment ─────────────────── ✕ ─┐
│                                         │
│  Section 1: Basics                      │
│  ┌─────────────────────────────────────┐│
│  │  Title * [placeholder per type]    ││
│  └─────────────────────────────────────┘│
│  ┌─────────────────────────────────────┐│
│  │  Description (optional)             ││
│  └─────────────────────────────────────┘│
│                                         │
│  Section 2: Type-specific               │
│  ┌─────────────────────────────────────┐│
│  │  Type: [ Habit ▾ ]                  ││
│  │  Frequency: [ Daily ▾ ]            ││
│  │  Times/day: [ 1 ▾ ]                ││
│  │  Color: ○ ○ ● ○ ○                   ││
│  └─────────────────────────────────────┘│
│                                         │
│  Section 3: Links                       │
│  ├─ Parent goal: [Search... ▾] (opt)   │
│                                         │
│  ┌────────────    ────────────┐         │
│  │  [Cancel]   [Create]       │         │
│  └────────────────────────────┘         │
└─────────────────────────────────────────┘
```

**Per-type Section 2 fields:**

| Type | Fields |
|---|---|
| Habit | Frequency (Daily / Weekly X times / Custom), Color, Target count/day |
| Goal | Progress type (Checklist / Percentage target → target value + unit), Deadline (optional date picker) |
| Task | Priority, Deadline (optional), optional "Add checklist items" toggle (enters checklist mode) |
| Note | (none — opens note editor after creation) |

### 4.2 Edit Commitment vs Edit Record Modals

To respect the backend distinction between Commitments and Records, the UI implements highly context-aware editing mechanics:

**Edit Commitment:**
- **Trigger:** Clicking "Edit" on a Habit, Goal title, or Task title.
- **Behavior:** Reuses the Create Commitment modal but changes the title to "Edit Commitment" and the button to "Save Changes". It smartly detects the item's current type (e.g., Habit) and **hides the type selection buttons**, locking the commitment type to prevent data corruption while exposing its configurable properties.

**Edit Record:**
- **Trigger:** Clicking "Edit" on a checklist item (e.g., "Eggs" inside a task) or a Goal log entry.
- **Behavior:** Bypasses the complex Commitment modal entirely. Pops up a streamlined "Edit Record" modal containing only "Record Content", an optional "Comments / Notes" textarea, and a Date field.

**Validation:**
- Title: required, max 255 chars, shows error inline if empty on submit
- API error: banner at bottom "Failed to save — [message]"

**Post-creation:**
- Panel closes
- List auto-refreshes
- New item scrolls into view with highlight animation (2s fade)

### 4.2 Create Daily Log Entry

Trigger: bottom input bar in Dashboard Daily Log block.

```
[📝 + Add what you did today...]              [@] [+]
```

**Flow:**
1. User types text
2. (Optional) Type `@` → search dropdown of recent/related commitments
3. Press `Enter` → optimistically create record, POST in background
4. On success: record appears in list, input clears
5. On failure: entry turns red, "Tap to retry"

**Multi-line paste:**
- Paste 3+ lines → prompt "Add all as separate entries? [Yes] [No]"
- Yes → batch create
- No → paste as single entry

### 4.3 View Commitment Detail (Side Panel)

Trigger: click any commitment card/title anywhere in the app.

**Panel layout (slide-in from right, 600px):**

```
┌─ Read 100 Books ─────────────────── ✕ ─┐
│                                          │
│  🎯 Goal · Active · High Priority       │
│  Deadline: Aug 15, 2026                  │
│                                          │
│  32/100 books                            │
│  ████████░░░░░░░░  32%                   │
│                                          │
│  ── Sub-commitments ────────            │
│  ▸ July: read 8     ██░░ 25%       [→]  │
│  ▸ August: read 8   ░░░░  0%       [→]  │
│  [+ Add sub-goal]  [+ Link habit]       │
│                                          │
│  ── Recent Records ──────               │
│  Jul 10  Finished Atomic Habits    [🗑]  │
│  Jul 5   Finished Deep Work        [🗑]  │
│  [+ Add record]                          │
│                                          │
│  ── Linked Habits ──────                │
│  ☑ Read 30 min daily   🔥 3 days        │
│                                          │
│  [Edit]  [Archive]                       │
└──────────────────────────────────────────┘
```

**Per-type content:**

| Type | Panel sections |
|---|---|
| Habit | Calendar heatmap, stats card (streak/rate), records timeline, edit |
| Goal | Progress bar, sub-goals, records timeline, linked habits, edit |
| Task | Status + priority, change log, linked records, edit; if checklist-mode: all items + checkboxes, progress bar, add item |
| Note | Full note editor (markdown), save button |

**Navigation within panel:**
- Click sub-goal or linked commitment → panel replaces content (push transition)
- Back button (←) in header returns to previous panel
- Panel stays open on background click-outside (must click ✕ or Cancel)

### 4.4 Batch Check-in (Habit)

Trigger: Dashboard Morning Routine or Habits view.

**Check-in flow:**
1. User taps ☐
2. Immediate optimistic UI: ☐ → ☑ with green fill + scale animation
3. POST `/api/v1/pursuits/records/batch` in background
4. Success: streak counter updates, no further action
5. Failure: ☑ → ❌, "Retry" tooltip on hover

**Cross-day check-in:**
- Header date arrows `< Yesterday | Today | Tomorrow >`
- Past dates show existing check-ins, allow toggling
- Future dates: not editable

---

## 5. Error & Edge Cases

### 5.1 Network Failures

| Scenario | Behavior |
|---|---|
| Create record fails | Item shown with red ❌, "Tap to retry" |
| Batch check-in fails | Checkbox reverts to ☐, shake animation, "Sync failed" toast |
| Load fails | Retry button in place of content + toast "Couldn't load — check connection" |
| Offline (detected) | Banner at top: "You're offline — changes saved locally" |

### 5.2 Empty States

| Page/section | Empty message | CTA |
|---|---|---|
| Dashboard — Morning Routine | "🌱 No habits yet" | [Create Habit] |
| Dashboard — Daily Log | "Start recording what you did today" | (input bar is already visible) |
| Dashboard — Today's Tasks | "🌴 Nothing due today" | [Create Task] |
| Dashboard — Goal Progress | (section hidden) | — |
| Dashboard — no data at all | "Welcome to MyWorld! Let's set up your first habit." | [Create Habit] [Create Goal] |
| Pursuits — All view | "Get started! Create your first commitment." | [Create] |
| Pursuits — Habits | "No habits — start building routines" | [Create Habit] |
| Pursuits — Goals | "No goals — set something to work toward" | [Create Goal] |
| Pursuits — Tasks | "No tasks yet" | [Create Task] |

### 5.3 Loading States

All data-fetching sections use skeleton screens (not spinners):

```
┌─ Morning Routine skeleton ──────────┐
│ □ ████████████████   ██████          │
│ □ ██████████         ██████          │
│ □ █████████████████  ██████          │
└──────────────────────────────────────┘
```

- Skeleton mimics the real layout structure
- Animation: shimmer sweep (linear gradient moving left to right, 1.5s cycle)
- Transition to real content: fade-in 200ms, no layout shift

### 5.4 Edge Cases

| Edge case | Behavior |
|---|---|
| User creates record for future date | Allowed (pre-planning). UI shows "Scheduled" badge |
| User deletes a record that was the only progress on a goal | Goal progress recalculates automatically. If goal has no sub-goals and no records → 0% |
| Goal with `deadline` in the past but not 100% | Red progress bar, "Overdue" badge, still editable |
| Habit with 0 records ever | Streak = 0, completion = 0%, "Start your streak!" prompt |
| User has 50+ habits/goals | Pursuits view defaults to showing active only. Archived items hidden behind "Show archived" toggle |
| Very long title (>50 chars) | Truncated with ellipsis in card view, full title visible on hover tooltip and in detail panel |
| Daily Log entry with very long content (>500 chars) | Truncated at 3 lines in list, expandable with "Show more" |

---

## 6. Responsive Breakpoints

(Outline only — mobile design deferred)

| Breakpoint | Behavior |
|---|---|
| >1024px (desktop) | Full layout as designed |
| 768-1024px (tablet) | Sidebar collapses to icons only; panels overlay |
| <768px (mobile) | Sidebar → bottom nav; panels full-screen; deferred to future phase |

---

## 7. Key Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Detail views: page vs panel | **Slide-in side panel** | Preserves context; fast to open/close; no full-page navigation |
| Form for new commitment | **Side panel, not modal or full page** | Consistent with detail view; more spacious than modal |
| Check-in: optimistic UI | **Immediate visual feedback** | Daily check-in is the #1高频操作; waiting for API confirmation feels slow |
| Empty states: call to action | **Each section has its own CTA** | Guides user to take action where they are, not send them elsewhere |
| Skeleton screens vs spinners | **Skeleton screens** | Show layout structure immediately; no layout shift on load |
| Goal progress bar colors | **Gradient from gray → green via blue/orange** | Provides at-a-glance urgency without needing to read numbers |
| Filter chips: single vs multi-select | **Single-select** | Simpler mental model; multi-select edge cases add complexity for little gain |
