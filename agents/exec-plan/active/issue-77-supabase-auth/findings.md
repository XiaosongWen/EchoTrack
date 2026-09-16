# Findings: Supabase Auth & UUID Migration (Issue #77)

## Database Schema & Models
- `models/user.py`: Currently uses `id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)`.
- `models/commitment.py`: Uses `user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)`.
- `models/label.py`: Uses `user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)`.
- Routers have `USER_ID = 1` hardcoded in `routers/pursuits.py`, `routers/labels.py`, and `routers/user.py`.
- Supabase Auth users have a UUID `id` (e.g. `9f3bb06f-dbb0-4875-9dbf-408d7c80ce81`) present in the JWT `sub` claim.
- The user confirmed: "use 2, will be good, you can even clear entire db". So we can cleanly reset or migrate all user_id columns to UUID.
