from app.modules.assessment.engine import evaluate_assessment

def test_evaluate_standard_healthy_hair():
    answers = {
        "scalp": "normal",
        "porosity": "takes_2_to_4_hrs",
        "elasticity": "stretches_returns",
        "thickness": "medium",
        "density": "high",
        "treatments": [],
        "heat": "rarely"
    }
    result = evaluate_assessment(answers)
    assert result["traits"]["scalp_type"] == "Normal"
    assert result["traits"]["porosity"] == "Medium"
    assert result["traits"]["elasticity"] == "Healthy (Balanced)"
    assert result["traits"]["thickness"] == "Medium"
    assert result["traits"]["density"] == "High"
    assert len(result["flags"]) == 0

def test_evaluate_bleach_and_heat_warning_flags():
    answers = {
        "scalp": "oily",
        "porosity": "under_2_hrs",
        "elasticity": "stretches_far_mushy",
        "thickness": "fine",
        "density": "low",
        "treatments": ["bleach"],
        "timing": "within_2_weeks",
        "heat": "daily"
    }
    result = evaluate_assessment(answers)
    assert result["traits"]["porosity"] == "High"
    assert result["traits"]["elasticity"] == "Over-elastic (Needs Protein)"
    assert len(result["flags"]) == 2

def test_evaluate_relaxer_and_keratin_flags():
    answers = {
        "scalp": "dry",
        "porosity": "takes_over_4_hrs",
        "elasticity": "snaps_immediately",
        "thickness": "coarse",
        "density": "medium",
        "treatments": ["relaxer", "keratin"],
        "heat": "weekly"
    }
    result = evaluate_assessment(answers)
    assert result["traits"]["scalp_type"] == "Dry"
    assert result["traits"]["porosity"] == "Low"
    assert result["traits"]["elasticity"] == "Low (Needs Moisture)"
    assert len(result["flags"]) == 2
