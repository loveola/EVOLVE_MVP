import uuid
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import UserResponse
from app.modules.assessment.models import HairAssessment
from app.modules.recommendation.models import EscalationFlagConfig
from app.modules.recommendation.escalation import EscalationResult


def test_flagged_submission_returns_escalation_response_and_never_calls_recommendation_engine():
    user_id = str(uuid.uuid4())
    mock_user = UserResponse(uid=user_id, email="flagged@example.com", role="authenticated", is_admin=False)

    flagged_answers = {
        "h1_age_bracket": "18_plus",
        "h2_loss_location": ["crown_vertex"],
        "h3_smooth_shiny_no_visible_pores": "yes",
        "h4_scalp_symptoms": ["tingling_crawling"],
        "h5_scalp_lesions": ["none"],
        "g1_primary_concern": ["breakage"],
        "g4_concern_duration": "gt_12m",
        "scalp": "dry",
        "porosity": "takes_over_4_hrs",
        "elasticity": "snaps_immediately",
        "thickness": "medium",
        "density": "medium"
    }

    mock_db = MagicMock()
    stored_assessment = None

    def mock_add(instance):
        nonlocal stored_assessment
        if isinstance(instance, HairAssessment):
            instance.id = uuid.uuid4()
            stored_assessment = instance

    mock_db.add.side_effect = mock_add
    mock_db.query.return_value.filter.return_value.first.side_effect = lambda: stored_assessment

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app)

    mock_escalation = EscalationResult(
        tier="RED",
        requires_escalation=True,
        flag_code="RED_01_SCARRING_CENTRAL",
        trigger_reason="Central scalp loss with shiny skin indicates scarring.",
        fired_flags=[{"flag_code": "RED_01_SCARRING_CENTRAL"}]
    )

    try:
        with patch("app.modules.assessment.router.evaluate_escalation", return_value=mock_escalation), \
             patch("app.modules.recommendation.router.evaluate_escalation", return_value=mock_escalation), \
             patch("app.modules.recommendation.engine.run_engine") as mock_run_engine:
            response = client.post("/api/assessment/submit", json={"answers": flagged_answers})
            assert response.status_code == 200
            data = response.json()

            assert data.get("status") in ["escalated", "completed"]
            results = data.get("results", {})
            assert results.get("tier") == "RED"
            assert results.get("flag_code") == "RED_01_SCARRING_CENTRAL"
            assert results.get("trigger_reason") is not None
            assert len(results.get("trigger_reason")) > 0

            mock_run_engine.assert_not_called()

            rec_response = client.post("/api/recommendations/generate", json={"concern": "breakage"})
            assert rec_response.status_code == 400
            assert "RED" in rec_response.json()["detail"]
            mock_run_engine.assert_not_called()
    finally:
        app.dependency_overrides.clear()


def test_non_flagged_submission_proceeds_normally():
    user_id = str(uuid.uuid4())
    mock_user = UserResponse(uid=user_id, email="clean@example.com", role="authenticated", is_admin=False)

    clean_answers = {
        "h1_age_bracket": "18_plus",
        "h2_loss_location": ["none"],
        "h3_smooth_shiny_no_visible_pores": "no",
        "h4_scalp_symptoms": ["none"],
        "h5_scalp_lesions": ["none"],
        "g1_primary_concern": ["breakage"],
        "g4_concern_duration": "lt_6m",
        "scalp": "balanced",
        "porosity": "medium",
        "elasticity": "medium",
        "thickness": "medium",
        "density": "medium"
    }

    mock_db = MagicMock()
    stored_assessment = None

    def mock_add(instance):
        nonlocal stored_assessment
        if isinstance(instance, HairAssessment):
            instance.id = uuid.uuid4()
            stored_assessment = instance

    mock_db.add.side_effect = mock_add
    mock_db.query.return_value.filter.return_value.first.side_effect = lambda: stored_assessment

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app)

    try:
        response = client.post("/api/assessment/submit", json={"answers": clean_answers})
        assert response.status_code == 200
        data = response.json()

        assert data.get("status") == "completed"
        results = data.get("results", {})
        assert results.get("tier") in ["GREEN", "AMBER"]
    finally:
        app.dependency_overrides.clear()
