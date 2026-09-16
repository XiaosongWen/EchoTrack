# Task Plan: Supabase Auth & UUID Migration (Issue #77)

## Goal
Migrate database user identifier from integer to UUID matching Supabase Auth user IDs (`auth.users.id`), reset/clear database tables if needed, update all models, schemas, services, and API routes to authenticate with Supabase JWT and use the authenticated user. Implement Frontend authentication (Supabase JS client, login view, auth state store, axios interceptors, and protected routes).

## Current Phase
Completed

## Phases

### Phase 1: Database & Model Migration to UUID
- [x] Clear database tables / create fresh migration resetting `users`, `commitments`, `labels` to use `UUID` for `user_id`. (Applied `005_migrate_users_to_uuid.py`)
- [x] Update SQLAlchemy models (`User`, `Commitment`, `Label`, etc.) to use `UUID` for user identity.
- [x] Update Pydantic schemas (`schemas/user.py`, `schemas/commitment.py`, `schemas/label.py`, etc.) to use `UUID` for `user_id`.
- [x] Status: complete

### Phase 2: Auth Dependency & User Synchronization
- [x] Update `backend/core/auth.py` to:
  - Validate Supabase JWT token with `settings.supabase_jwt_secret`.
  - Extract user UUID (`sub`), email, and metadata.
  - Automatically fetch or sync the corresponding `User` record in the database (`get_current_user` dependency).
- [x] Status: complete

### Phase 3: Update Services & Routers
- [x] Update `services/commitment_service.py`, `services/label_service.py`, `services/record_service.py` to accept `UUID` for `user_id`.
- [x] Update `routers/user.py`, `routers/pursuits.py`, `routers/labels.py` to remove hardcoded `USER_ID = 1` and require `current_user: User = Depends(get_current_user)`.
- [x] Status: complete

### Phase 4: Verification & Testing
- [x] Run backend tests (`pytest`).
- [x] Fix/update test fixtures to mock Supabase JWT authentication.
- [x] Added `tests/test_auth.py` for token verification and user auto-provisioning. All 64 tests passing.
- [x] Status: complete

### Phase 5: Frontend UI Authentication & Login
- [x] Installed `@supabase/supabase-js` dependency in `frontend/`.
- [x] Initialized Supabase client in `frontend/src/utils/supabase.js` with fallback support for tests.
- [x] Created Zustand auth store (`frontend/src/stores/authStore.js`) managing session, user info, login, logout, and auth state change listeners.
- [x] Attached Supabase JWT Bearer token in Axios request interceptor (`frontend/src/api/client.js`) for all backend API calls.
- [x] Created Login view (`frontend/src/views/Login.jsx`) supporting email/password sign-in and error handling.
- [x] Added Auth Guard (`frontend/src/components/ProtectedRoute.jsx`), wrapped routes in `App.jsx`, and added user profile / logout button to `Layout.jsx`.
- [x] Verified frontend build (`npm run build`) and test suite (all 27 tests passing).
- [x] Status: complete

## Errors Encountered
| Error | Attempt | Resolution |
|-------|---------|------------|
| Missing `app.dependency_overrides` during unit tests | 1 | Added default `get_current_user` override with `test_user` fixture in `conftest.py` |
| `app.dependency_overrides.clear()` wiping auth overrides in envelope tests | 1 | Changed teardown to `app.dependency_overrides.pop(get_db, None)` |
| `supabaseUrl is required` during vitest runs | 1 | Added placeholder fallbacks in `utils/supabase.js` and `envDir: "../"` in `vitest.config.js` |
