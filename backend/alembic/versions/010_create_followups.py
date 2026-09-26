from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision: str = "010_create_followups"
down_revision: Union[str, None] = "009_add_routine_progress_tracking"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(sa.text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
    op.create_table(
        "followups",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("auth.users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("routine_id", UUID(as_uuid=True), sa.ForeignKey("user_routines.id", ondelete="CASCADE"), nullable=False),
        sa.Column("scheduled_week", sa.Integer(), nullable=False),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="scheduled"),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("response_rating", sa.String(length=30), nullable=True),
        sa.Column("response_notes", sa.Text(), nullable=True),
        sa.Column("response_symptoms", JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("action_taken", sa.String(length=30), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_followups_user_id", "followups", ["user_id"])
    op.create_index("ix_followups_routine_id", "followups", ["routine_id"])
    op.create_index("ix_followups_due_date", "followups", ["due_date"])
    op.create_index("ix_followups_status", "followups", ["status"])


def downgrade() -> None:
    op.drop_index("ix_followups_status", table_name="followups")
    op.drop_index("ix_followups_due_date", table_name="followups")
    op.drop_index("ix_followups_routine_id", table_name="followups")
    op.drop_index("ix_followups_user_id", table_name="followups")
    op.drop_table("followups")
