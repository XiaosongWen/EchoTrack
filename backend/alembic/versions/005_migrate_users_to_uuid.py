"""migrate users to uuid

Revision ID: 005
Revises: 004
Create Date: 2026-09-03
"""

import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # 1. Truncate existing data to safely change column types and foreign keys
    op.execute("TRUNCATE TABLE entity_labels, records, commitment_links, commitments, labels CASCADE;")
    op.execute("TRUNCATE TABLE habit_logs, habits CASCADE;" if op.get_bind().dialect.has_table(op.get_bind(), "habits") else "SELECT 1;")

    # 2. Drop existing foreign key constraints pointing to users.id
    op.drop_constraint("fk_labels_user_id", "labels", type_="foreignkey")
    op.drop_constraint("fk_commitments_user_id", "commitments", type_="foreignkey")
    op.drop_constraint("uq_labels_user_name", "labels", type_="unique")

    # Drop habit fk constraints if tables exist
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "habits" in inspector.get_table_names():
        try:
            op.drop_constraint("fk_habits_user_id", "habits", type_="foreignkey")
            op.drop_constraint("fk_habit_logs_user_id", "habit_logs", type_="foreignkey")
        except Exception:
            pass

    # 3. Drop users table and recreate with UUID primary key
    op.drop_table("users")
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=True),
        sa.Column("username", sa.String(100), unique=False, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 4. Alter commitments.user_id to UUID and recreate FK
    op.drop_index(op.f("ix_commitments_user_id"), table_name="commitments")
    op.drop_column("commitments", "user_id")
    op.add_column("commitments", sa.Column("user_id", UUID(as_uuid=True), nullable=False))
    op.create_index(op.f("ix_commitments_user_id"), "commitments", ["user_id"])
    op.create_foreign_key("fk_commitments_user_id", "commitments", "users", ["user_id"], ["id"], ondelete="CASCADE")

    # 5. Alter labels.user_id to UUID and recreate FK + UniqueConstraint
    op.drop_index(op.f("ix_labels_user_id"), table_name="labels")
    op.drop_column("labels", "user_id")
    op.add_column("labels", sa.Column("user_id", UUID(as_uuid=True), nullable=False))
    op.create_index(op.f("ix_labels_user_id"), "labels", ["user_id"])
    op.create_unique_constraint("uq_labels_user_name", "labels", ["user_id", "name"])
    op.create_foreign_key("fk_labels_user_id", "labels", "users", ["user_id"], ["id"], ondelete="CASCADE")


def downgrade():
    raise NotImplementedError("Downgrade from UUID migration not supported.")
