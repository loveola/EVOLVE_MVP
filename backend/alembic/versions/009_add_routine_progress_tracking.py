from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "009_add_routine_progress_tracking"
down_revision: Union[str, None] = "008_create_waitlist"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("user_routines", sa.Column("current_phase", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("user_routines", sa.Column("current_day", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("user_routines", sa.Column("started_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("user_routines", sa.Column("completed_actions", JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")))
    op.add_column("user_routines", sa.Column("progress_percentage", sa.Integer(), nullable=False, server_default="0"))


def downgrade() -> None:
    op.drop_column("user_routines", "progress_percentage")
    op.drop_column("user_routines", "completed_actions")
    op.drop_column("user_routines", "started_at")
    op.drop_column("user_routines", "current_day")
    op.drop_column("user_routines", "current_phase")
