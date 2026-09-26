from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "011_add_routine_status_and_followup_email"
down_revision: Union[str, None] = "010_create_followups"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("user_routines", sa.Column("status", sa.String(length=30), nullable=False, server_default="active"))
    op.add_column("followups", sa.Column("user_email", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("followups", "user_email")
    op.drop_column("user_routines", "status")
