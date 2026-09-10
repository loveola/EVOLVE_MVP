import uuid
import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import UserResponse
from app.core.database import get_db
from app.modules.assessment.models import HairAssessment
from app.modules.recommendation.models import RulesConfig, UserRoutine


@pytest.fixture
def mock_user():
    return UserResponse(
        uid=str(uuid.uuid4()),
        email="test@evolve.com",
        display_name="Test User",
        is_active=True,
        created_at="2026-09-09T00:00:00Z"
    )


def test_unauthenticated_request():
    app.dependency_overrides.clear()
    client = TestClient(app)
    response = client.post("/api/recommendations/generate", json={"concern": "breakage"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_invalid_concern_fails_pydantic_validation(mock_user):
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: MagicMock()
    client = TestClient(app)
    try:
        response = client.post("/api/recommendations/generate", json={"concern": "invalid_unknown"})
        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_missing_assessment_returns_400(mock_user):
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app)

    try:
        response = client.post("/api/recommendations/generate", json={"concern": "breakage"})
        assert response.status_code == 400
        assert "must be completed" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_incomplete_assessment_returns_400(mock_user):
    mock_assessment = MagicMock()
    mock_assessment.status = "in_progress"
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_assessment

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app)

    try:
        response = client.post("/api/recommendations/generate", json={"concern": "breakage"})
        assert response.status_code == 400
        assert "must be completed" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_red_tier_request_precondition_aborts(mock_user):
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: MagicMock()
    client = TestClient(app)

    try:
        response = client.post("/api/recommendations/generate", json={"concern": "breakage", "tier": "RED"})
        assert response.status_code == 400
        assert "tier is RED" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_successful_recommendation_generation(mock_user):
    mock_assessment = MagicMock()
    mock_assessment.id = uuid.uuid4()
    mock_assessment.status = "completed"
    mock_assessment.results = {"tier": "GREEN"}
    mock_assessment.answers = {
        "q1_treatments": ["none"],
        "q2_heat_frequency": "none",
        "q3_scalp_type": "normal",
        "q4_porosity": "normal",
        "q4_porosity_water_behaviour": "absorbs_normally",
        "q4_drying_time": "1_to_3_hours",
        "q5_elasticity": "low",
        "q6_thickness": "medium",
        "q7_density": "medium",
        "g1_primary_concern": ["dryness"],
        "g2_shed_hair_morphology": "full_length",
        "g4_concern_duration": "months",
        "g5_current_style": "natural_afro",
        "g6_style_tension_pain": "never",
        "g7_install_duration_weeks": 0,
        "g8_wash_interval_days": 7,
        "g9_detangle_method": "wet_conditioner",
        "g10_nighttime_protection": "satin_bonnet",
        "g13_protein_treatment_frequency": "never",
        "g14_hair_state": "natural",
    }

    mock_rule = MagicMock()
    mock_rule.problem_id = "chronic_dryness"
    mock_rule.display_name = "Chronic Dryness"
    mock_rule.classifier = {
        "any_of": [
            {
                "all_of": [
                    {"field": "g1_primary_concern", "contains": "dryness"},
                    {"field": "q5_elasticity", "in": ["low", "healthy"]}
                ]
            }
        ]
    }
    mock_rule.score_boosters = []
    mock_rule.hard_guards = []
    mock_rule.protocol_id = "PROTO_MOISTURE"
    mock_rule.primary_metric = "day3_softness_score"
    mock_rule.root_cause_explanation_key = "cause.dryness"
    mock_rule.realistic_timeline_weeks = {"first_measurable_change": 1}
    mock_rule.always_runs_as_module = False
    mock_rule.priority = 50

    mock_db = MagicMock()
    def mock_query(model):
        m = MagicMock()
        if model == HairAssessment:
            m.filter.return_value.first.return_value = mock_assessment
        elif model == RulesConfig:
            m.filter.return_value.all.return_value = [mock_rule]
        elif model == UserRoutine:
            m.filter.return_value.first.return_value = None
        return m

    mock_db.query.side_effect = mock_query

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app)

    try:
        response = client.post("/api/recommendations/generate", json={"concern": "dryness"})
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == mock_user.uid
        assert "chronic_dryness" in data["active_problems"]
        assert "cause.dryness" in data["cause_explanation_keys"]
        assert "PROTO_MOISTURE" in data["protocols"]
        assert len(data["roadmap"]) > 0
        assert data["product_weight_ceiling"] in ["ultralight", "light", "medium", "rich"]
    finally:
        app.dependency_overrides.clear()
