# Design Decision Log

> Record significant design decisions made during development. Each entry should capture the decision, context, alternatives considered, and rationale.

---

## Decision Index

| Domain | Layer | Title | Summary | Status | Created | Modified | File |
|--------|-------|-------|---------|--------|---------|----------|------|
| Pursuits | backend | Unified Commitments + Records | Replaced separate Habit Tracker, Task Manager, and Goals modules with a single flexible 3-table schema covering habits, goals, tasks, and planner entries; tasks support optional checklist mode via ordered records (no separate list type) | Accepted | 2026-07-15 | 2026-09-16 | [backend-01-commitments-and-records.md](backend-01-commitments-and-records.md) |
| Core | backend | GitHub-like Label System | Unified label system applying across commitments, records, knowledge, and documents using a polymorphic join table entity_labels. | Accepted | 2026-07-18 | 2026-07-18 | [backend-02-label-system.md](backend-02-label-system.md) |
| Dashboard / Pursuits | frontend | Dashboard + Pursuits UI/UX | Unified daily journal Dashboard and Pursuits browse page with filter-able views for habits, goals, and tasks (tasks support optional inline checklist mode, replacing the former Lists type) | Accepted | 2026-07-15 | 2026-09-16 | [frontend-01-dashboard-and-pursuits-ui.md](frontend-01-dashboard-and-pursuits-ui.md) |
| Core | backend | Standardized API Response Envelope | Refactored API responses to use a standardized JSON envelope with a request_id for consistent error handling and metadata | Accepted | 2026-07-19 | 2026-07-19 | [backend-03-api-response-envelope.md](backend-03-api-response-envelope.md) |
| Core | infra | Cloud-Native Deployment Architecture | Migrated from home PC self-hosting to Cloudflare Pages (Frontend) + Google Cloud Run (Backend) + Supabase (Database, Auth, Storage) | Accepted | 2026-08-24 | 2026-08-24 | [infra-01-cloud-deployment-architecture.md](infra-01-cloud-deployment-architecture.md) |

## Writing a Decision

Each decision lives in its own file (e.g., `backend-02-task-manager-redesign.md`) following this structure:

```
# YYYY-MM-DD: Decision Title

**Domain:** (pursuits / photos / videos / books / documents / knowledge / ...)

**Layer:** (backend / frontend / mobile / ai / infra / storage)

**Status:** (proposed / accepted / superseded)

**Context:** What prompted this decision.

**Decision:** What we chose.

**Alternatives considered:**
- Option A — why we didn't pick it
- Option B — why we didn't pick it

**Rationale:** Why this is the right choice.

**Consequences:** What this enables or constrains going forward.
```

After writing the file, add a row to the Decision Index table above.

### File Naming Convention

Format: `{layer}-{NN}-{short-description}.md`

- `layer`: backend / frontend / mobile / ai / infra / storage
- `NN`: incrementing two-digit number (01, 02, 03...), unique across all files
- `short-description`: kebab-case summary

This keeps files discoverable when browsing the directory — you can find all backend decisions sorted together.
