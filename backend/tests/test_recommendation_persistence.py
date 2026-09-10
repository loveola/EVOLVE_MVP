import uuid
import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import UserResponse
from app.core.database import get_db
from app.modules.recommendation.models import UserRoutine


@pytest.fixture
def mock_user():
    return UserResponse(
        uid=str(uuid.uuid4()),
        email="user@evolve.com",
        display_name="Evolve User",
        is_active=True,
        created_at="2026-09-09T00:00:00Z"
    )


def test_get_my_routine_unauthenticated():
    app.dependency_overrides.clear()
    client = TestClient(app)
    response = client.get("/api/recommendations/me")
    assert response.status_code == 401


def test_get_my_routine_not_found(mock_user):
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app)

    try:
        response = client.get("/api/recommendations/me")
        assert response.status_code == 404
        assert "No active routine found" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_get_my_routine_success(mock_user):
    mock_routine = MagicMock()
    mock_routine.user_id = uuid.UUID(mock_user.uid)
    mock_routine.active_problems = ["chronic_dryness"]
    mock_routine.cause_explanation_keys = ["cause.dryness"]
    mock_routine.protocols = ["PROTO_MOISTURE"]
    mock_routine.roadmap = [
        {
            "phase": 1,
            "name": "Reset & Restore",
            "days": "Day 1 - 14",
            "actions": [
                {"type": "wash", "instruction": "Hydrating shampoo"}
            ],
            "checkpoint_day": 14,
            "checkpoint_metric": "softness"
        }
    ]
    mock_routine.product_weight_ceiling = "light"
    mock_routine.hard_guards_fired = []
    mock_routine.realistic_timeline_weeks = {"min": 6, "max": 12}
    mock_routine.is_customized = True
    mock_routine.admin_notes = "Customized by Senior Trichologist"

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_routine

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app)

    try:
        response = client.get("/api/recommendations/me")
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == mock_user.uid
        assert data["is_customized"] is True
        assert data["admin_notes"] == "Customized by Senior Trichologist"
        assert len(data["roadmap"]) == 1
        assert data["roadmap"][0]["actions"][0]["instruction"] == "Hydrating shampoo"
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def mock_admin():
    return UserResponse(
        uid=str(uuid.uuid4()),
        email="admin@evolve.com",
        display_name="Admin Trichologist",
        is_active=True,
        is_admin=True,
        created_at="2026-09-09T00:00:00Z"
    )


def test_admin_update_user_routine_forbidden_for_non_admin(mock_user):
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: MagicMock()
    client = TestClient(app)

    try:
        response = client.patch(
            f"/api/recommendations/admin/users/{str(uuid.uuid4())}",
            json={"admin_notes": "Unauthorized attempt"}
        )
        assert response.status_code == 403
        assert "Administrative privileges required" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_admin_update_user_routine_invalid_uuid(mock_admin):
    app.dependency_overrides[get_current_user] = lambda: mock_admin
    app.dependency_overrides[get_db] = lambda: MagicMock()
    client = TestClient(app)

    try:
        response = client.patch(
            "/api/recommendations/admin/users/invalid-uuid-string",
            json={"admin_notes": "Note"}
        )
        assert response.status_code == 400
        assert "Invalid user UUID" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_admin_update_user_routine_not_found(mock_admin):
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None

    app.dependency_overrides[get_current_user] = lambda: mock_admin
    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app)

    try:
        target_uid = str(uuid.uuid4())
        response = client.patch(
            f"/api/recommendations/admin/users/{target_uid}",
            json={"admin_notes": "Note"}
        )
        assert response.status_code == 404
        assert "User routine not found" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_admin_update_user_routine_success(mock_admin):
    target_id = uuid.uuid4()
    mock_routine = MagicMock()
    mock_routine.user_id = target_id
    mock_routine.active_problems = ["chronic_dryness"]
    mock_routine.cause_explanation_keys = ["cause.dryness"]
    mock_routine.protocols = ["PROTO_MOISTURE"]
    mock_routine.roadmap = [
        {
            "phase": 1,
            "name": "Phase 1",
            "days": "Day 1 - 7",
            "actions": [],
            "checkpoint_day": None,
            "checkpoint_metric": None
        }
    ]
    mock_routine.product_weight_ceiling = "light"
    mock_routine.hard_guards_fired = []
    mock_routine.realistic_timeline_weeks = {}
    mock_routine.is_customized = False
    mock_routine.admin_notes = None

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_routine

    app.dependency_overrides[get_current_user] = lambda: mock_admin
    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app)

    try:
        payload = {
            "roadmap": [
                {
                    "phase": 1,
                    "name": "Custom Phased Routine",
                    "days": "Day 1 - 21",
                    "actions": [
                        {
                            "type": "clarify",
                            "instruction": "Chelating wash on Day 1",
                            "cadence": "once"
                        }
                    ],
                    "checkpoint_day": 21,
                    "checkpoint_metric": "scalp_clarity"
                }
            ],
            "admin_notes": "Added clarifying wash due to persistent hardness",
            "product_weight_ceiling": "rich"
        }
        response = client.patch(
            f"/api/recommendations/admin/users/{str(target_id)}",
            json=payload
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_customized"] is True
        assert data["admin_notes"] == "Added clarifying wash due to persistent hardness"
        assert data["product_weight_ceiling"] == "rich"
        assert len(data["roadmap"]) == 1
        assert data["roadmap"][0]["actions"][0]["type"] == "clarify"
        assert mock_db.commit.called
        assert mock_db.refresh.called
    finally:
        app.dependency_overrides.clear()


def test_generate_resets_customized_routine_state(mock_user):
    from app.modules.assessment.models import HairAssessment
    from app.modules.recommendation.models import RulesConfig

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
        "g1_primary_concern": "dryness",
        "g2_shed_hair_morphology": "full_length",
        "g4_concern_duration": "months",
        "g5_current_style": "natural_afro",
        "g6_style_tension_pain": "never",
        "g7_install_duration_weeks": "invalid_str",
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
    mock_rule.primary_metric = "softness"
    mock_rule.root_cause_explanation_key = "cause.dryness"
    mock_rule.realistic_timeline_weeks = {}
    mock_rule.always_runs_as_module = False
    mock_rule.priority = 50

    existing_routine = MagicMock()
    existing_routine.user_id = uuid.UUID(mock_user.uid)
    existing_routine.is_customized = True
    existing_routine.admin_notes = "Old custom trichologist note"
    existing_routine.roadmap = []
    existing_routine.active_problems = []
    existing_routine.cause_explanation_keys = []
    existing_routine.protocols = []
    existing_routine.product_weight_ceiling = "light"
    existing_routine.hard_guards_fired = []
    existing_routine.realistic_timeline_weeks = {}

    mock_db = MagicMock()
    def mock_query(model):
        m = MagicMock()
        if model == HairAssessment:
            m.filter.return_value.first.return_value = mock_assessment
        elif model == RulesConfig:
            m.filter.return_value.all.return_value = [mock_rule]
        elif model == UserRoutine:
            m.filter.return_value.first.return_value = existing_routine
        return m

    mock_db.query.side_effect = mock_query

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app)

    try:
        response = client.post("/api/recommendations/generate", json={"concern": "dryness"})
        assert response.status_code == 200
        data = response.json()
        assert data["is_customized"] is False
        assert data["admin_notes"] is None
        assert existing_routine.is_customized is False
        assert existing_routine.admin_notes is None
    finally:
        app.dependency_overrides.clear()


def test_admin_update_empty_payload_fails(mock_admin):
    target_id = uuid.uuid4()
    mock_routine = MagicMock()
    mock_routine.user_id = target_id
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_routine

    app.dependency_overrides[get_current_user] = lambda: mock_admin
    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app)

    try:
        response = client.patch(
            f"/api/recommendations/admin/users/{str(target_id)}",
            json={}
        )
        assert response.status_code == 400
        assert "No valid fields provided for update" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_admin_update_clears_admin_notes_to_none(mock_admin):
    target_id = uuid.uuid4()
    mock_routine = MagicMock()
    mock_routine.user_id = target_id
    mock_routine.active_problems = ["chronic_dryness"]
    mock_routine.cause_explanation_keys = ["cause.dryness"]
    mock_routine.protocols = ["PROTO_MOISTURE"]
    mock_routine.roadmap = []
    mock_routine.product_weight_ceiling = "light"
    mock_routine.hard_guards_fired = []
    mock_routine.realistic_timeline_weeks = {}
    mock_routine.is_customized = True
    mock_routine.admin_notes = "Old notes"

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_routine

    app.dependency_overrides[get_current_user] = lambda: mock_admin
    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app)

    try:
        response = client.patch(
            f"/api/recommendations/admin/users/{str(target_id)}",
            json={"admin_notes": None}
        )
        assert response.status_code == 200
        assert mock_routine.admin_notes is None
        assert mock_routine.is_customized is True
    finally:
        app.dependency_overrides.clear()


def test_admin_update_invalid_product_weight_ceiling(mock_admin):
    target_id = uuid.uuid4()
    mock_routine = MagicMock()
    mock_routine.user_id = target_id
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_routine

    app.dependency_overrides[get_current_user] = lambda: mock_admin
    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app)

    try:
        response = client.patch(
            f"/api/recommendations/admin/users/{str(target_id)}",
            json={"product_weight_ceiling": "ultra_super_heavy"}
        )
        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_generate_handles_concurrent_integrity_error(mock_user):
    from sqlalchemy.exc import IntegrityError
    from app.modules.assessment.models import HairAssessment
    from app.modules.recommendation.models import RulesConfig

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
        "g1_primary_concern": "dryness",
        "g2_shed_hair_morphology": "full_length",
        "g4_concern_duration": "months",
        "g5_current_style": "natural_afro",
        "g6_style_tension_pain": "never",
        "g7_install_duration_weeks": 4,
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
    mock_rule.primary_metric = "softness"
    mock_rule.root_cause_explanation_key = "cause.dryness"
    mock_rule.realistic_timeline_weeks = {}
    mock_rule.always_runs_as_module = False
    mock_rule.priority = 50

    fallback_routine = MagicMock()
    fallback_routine.user_id = uuid.UUID(mock_user.uid)
    fallback_routine.is_customized = False
    fallback_routine.admin_notes = None
    fallback_routine.roadmap = []
    fallback_routine.active_problems = []
    fallback_routine.cause_explanation_keys = []
    fallback_routine.protocols = []
    fallback_routine.product_weight_ceiling = "light"
    fallback_routine.hard_guards_fired = []
    fallback_routine.realistic_timeline_weeks = {}

    mock_db = MagicMock()
    first_lookup = True

    def mock_query(model):
        nonlocal first_lookup
        m = MagicMock()
        if model == HairAssessment:
            m.filter.return_value.first.return_value = mock_assessment
        elif model == RulesConfig:
            m.filter.return_value.all.return_value = [mock_rule]
        elif model == UserRoutine:
            if first_lookup:
                first_lookup = False
                m.filter.return_value.first.return_value = None
            else:
                m.filter.return_value.first.return_value = fallback_routine
        return m

    mock_db.query.side_effect = mock_query

    commit_count = 0
    def mock_commit():
        nonlocal commit_count
        commit_count += 1
        if commit_count == 1:
            raise IntegrityError("duplicate key", params=None, orig=Exception())

    mock_db.commit.side_effect = mock_commit

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app)

    try:
        response = client.post("/api/recommendations/generate", json={"concern": "dryness"})
        assert response.status_code == 200
        assert mock_db.rollback.called
        assert fallback_routine.assessment_id == mock_assessment.id
    finally:
        app.dependency_overrides.clear()


