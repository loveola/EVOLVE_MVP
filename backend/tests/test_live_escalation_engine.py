import importlib.util
from pathlib import Path
import pytest
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import CreateTable
from app.modules.recommendation.escalation import evaluate_escalation, EscalationResult
from app.modules.recommendation.models import EscalationFlagConfig


@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(type_, compiler, **kw):
    return "JSON"


@compiles(UUID, "sqlite")
def compile_uuid_sqlite(type_, compiler, **kw):
    return "TEXT"


@compiles(CreateTable, "sqlite")
def compile_create_table_sqlite(create, compiler, **kw):
    s = compiler.visit_create_table(create, **kw)
    s = s.replace("DEFAULT (gen_random_uuid())", "")
    s = s.replace("DEFAULT '{}'::jsonb", "DEFAULT '{}'")
    return s


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    EscalationFlagConfig.__table__.create(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    migration_path = Path(__file__).parent.parent / "alembic" / "versions" / "006_create_escalation_flags.py"
    spec = importlib.util.spec_from_file_location("migration_006", migration_path)
    migration_006 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration_006)

    for item in migration_006.SEED_FLAGS:
        flag = EscalationFlagConfig(
            flag_code=item["flag_code"],
            description=item["description"],
            trigger_reason=item["trigger_reason"],
            tier=item["tier"],
            conditions=item["conditions"],
            metadata_info=item.get("metadata", {}),
            active=item.get("active", True),
        )
        session.add(flag)
    session.commit()
    yield session
    session.close()


def test_escalation_matching_scarring_central(db_session):
    answers = {
        "h2_loss_location": ["crown_vertex"],
        "h3_smooth_shiny_no_visible_pores": "yes",
    }
    result = evaluate_escalation(answers, db=db_session)
    assert result.requires_escalation is True
    assert result.tier == "RED"
    assert result.flag_code == "RED_01_SCARRING_CENTRAL"
    assert result.trigger_reason is not None
    assert len(result.fired_flags) >= 1
    assert result.fired_flags[0]["flag_code"] == "RED_01_SCARRING_CENTRAL"


def test_escalation_matching_infection_inflammatory(db_session):
    answers = {
        "h5_scalp_lesions": ["pustules_pus_bumps"],
        "h13_swollen_glands_or_fever": "yes",
    }
    result = evaluate_escalation(answers, db=db_session)
    assert result.requires_escalation is True
    assert result.tier == "RED"
    assert result.flag_code == "RED_04_INFECTION_INFLAMMATORY"


def test_escalation_benign_traits_returns_green(db_session):
    answers = {
        "scalp": "balanced",
        "q1_treatments": ["none"],
        "g1_primary_concern": "length_retention",
        "g4_concern_duration": "lt_3m",
        "h3_smooth_shiny_no_visible_pores": "no",
        "h5_scalp_lesions": ["none"],
    }
    result = evaluate_escalation(answers, db=db_session)
    assert result.requires_escalation is False
    assert result.tier == "GREEN"
    assert result.flag_code is None


def test_escalation_priority_ordering(db_session):
    low_priority_flag = EscalationFlagConfig(
        flag_code="TEST_LOW_PRIORITY",
        description="Low priority flag",
        trigger_reason="Low priority triggered",
        tier="RED",
        conditions={"field": "test_marker", "equals": "present"},
        metadata_info={"priority": 10},
        active=True,
    )
    high_priority_flag = EscalationFlagConfig(
        flag_code="TEST_HIGH_PRIORITY",
        description="High priority flag",
        trigger_reason="High priority triggered",
        tier="RED",
        conditions={"field": "test_marker", "equals": "present"},
        metadata_info={"priority": 100},
        active=True,
    )
    db_session.add(low_priority_flag)
    db_session.add(high_priority_flag)
    db_session.commit()

    answers = {"test_marker": "present"}
    result = evaluate_escalation(answers, db=db_session)
    assert result.requires_escalation is True
    assert result.flag_code == "TEST_HIGH_PRIORITY"


def test_escalation_inactive_flags_ignored(db_session):
    inactive_flag = EscalationFlagConfig(
        flag_code="TEST_INACTIVE_FLAG",
        description="Inactive flag",
        trigger_reason="Should not trigger",
        tier="RED",
        conditions={"field": "inactive_marker", "equals": "present"},
        metadata_info={"priority": 999},
        active=False,
    )
    db_session.add(inactive_flag)
    db_session.commit()

    answers = {"inactive_marker": "present"}
    result = evaluate_escalation(answers, db=db_session)
    assert result.requires_escalation is False
    assert result.tier == "GREEN"
    assert result.flag_code is None


def test_escalation_session_fallback(monkeypatch, db_session):
    monkeypatch.setattr("app.modules.recommendation.escalation.SessionLocal", lambda: db_session)
    answers = {
        "h2_loss_location": ["crown_vertex"],
        "h3_smooth_shiny_no_visible_pores": "yes",
    }
    result = evaluate_escalation(answers)
    assert result.requires_escalation is True
    assert result.flag_code == "RED_01_SCARRING_CENTRAL"
