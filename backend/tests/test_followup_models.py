import uuid
from datetime import datetime, timezone
import importlib.util
from pathlib import Path
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.modules.followup.models import Followup


def test_followup_model_columns_and_table_name():
    table = Followup.__table__
    assert table.name == "followups"
    expected_columns = {
        "id",
        "user_id",
        "routine_id",
        "scheduled_week",
        "due_date",
        "status",
        "sent_at",
        "response_rating",
        "response_notes",
        "response_symptoms",
        "completed_at",
        "action_taken",
        "created_at",
        "updated_at",
    }
    actual_columns = {c.name for c in table.columns}
    assert expected_columns.issubset(actual_columns)
    assert table.primary_key.columns.keys() == ["id"]
    assert table.columns["user_id"].nullable is False
    assert table.columns["routine_id"].nullable is False
    assert table.columns["scheduled_week"].nullable is False
    assert table.columns["due_date"].nullable is False
    assert table.columns["status"].nullable is False


def test_followup_model_defaults_on_instantiation():
    u_id = uuid.uuid4()
    r_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    followup = Followup(
        user_id=u_id,
        routine_id=r_id,
        scheduled_week=2,
        due_date=now,
    )
    assert followup.user_id == u_id
    assert followup.routine_id == r_id
    assert followup.scheduled_week == 2
    assert followup.due_date == now
    assert isinstance(followup.id, uuid.UUID)
    assert followup.status == "scheduled"
    assert followup.response_symptoms == []
    assert followup.sent_at is None
    assert followup.response_rating is None
    assert followup.response_notes is None
    assert followup.completed_at is None
    assert followup.action_taken is None


def test_followup_in_alembic_target_metadata():
    env_path = Path(__file__).parent.parent / "alembic" / "env.py"
    assert env_path.exists()
    spec = importlib.util.spec_from_file_location("alembic_env", env_path)
    assert spec is not None
    assert spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert hasattr(mod, "target_metadata")
    assert "followups" in mod.target_metadata.tables


def test_migration_010_metadata():
    migration_path = Path(__file__).parent.parent / "alembic" / "versions" / "010_create_followups.py"
    assert migration_path.exists()
    spec = importlib.util.spec_from_file_location("migration_010", migration_path)
    assert spec is not None
    assert spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.revision == "010_create_followups"
    assert mod.down_revision == "009_add_routine_progress_tracking"
    assert hasattr(mod, "upgrade")
    assert hasattr(mod, "downgrade")


def test_followup_sqlite_compatibility():
    engine = create_engine("sqlite:///:memory:")
    Followup.__table__.create(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    u_id = uuid.uuid4()
    r_id = uuid.uuid4()
    due = datetime.now(timezone.utc)
    item = Followup(
        user_id=u_id,
        routine_id=r_id,
        scheduled_week=4,
        due_date=due,
        response_symptoms=["dryness", "itching"],
    )
    session.add(item)
    session.commit()

    retrieved = session.query(Followup).filter(Followup.user_id == u_id).first()
    assert retrieved is not None
    assert retrieved.scheduled_week == 4
    assert retrieved.status == "scheduled"
    assert retrieved.response_symptoms == ["dryness", "itching"]
    session.close()
