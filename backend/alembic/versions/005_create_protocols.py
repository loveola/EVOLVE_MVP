from typing import Sequence, Union
import json
from pathlib import Path
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "005_create_protocols"
down_revision: Union[str, None] = "004_create_user_routines"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_BUNDLED_JSON = Path(__file__).parent.parent.parent / "app" / "modules" / "recommendation" / "seed_data" / "rules_config.json"
_ARTIFACTS_JSON = Path(__file__).parent.parent.parent.parent / "artifacts" / "rules_config.json"


def _load_json():
    if _BUNDLED_JSON.exists():
        target_path = _BUNDLED_JSON
    elif _ARTIFACTS_JSON.exists():
        target_path = _ARTIFACTS_JSON
    else:
        return {}
    with open(target_path, encoding="utf-8") as f:
        return json.load(f)


def upgrade() -> None:
    op.create_table(
        "protocols",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("problem_id", sa.String(), nullable=True),
        sa.Column("phases", JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )

    data = _load_json()
    protocols = data.get("protocols", [])
    if protocols:
        conn = op.get_bind()
        for p in protocols:
            conn.execute(
                sa.text(
                    "INSERT INTO protocols (id, name, problem_id, phases, is_active) "
                    "VALUES (:id, :name, :problem_id, CAST(:phases AS jsonb), true) "
                    "ON CONFLICT (id) DO NOTHING"
                ),
                {
                    "id": p["id"],
                    "name": p.get("name", p["id"]),
                    "problem_id": p.get("problem_id"),
                    "phases": json.dumps(p.get("phases", [])),
                }
            )


def downgrade() -> None:
    op.drop_table("protocols")
