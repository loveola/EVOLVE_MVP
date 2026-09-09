import pytest
from app.modules.recommendation.deriver import compute_derived_variables, normalize_assessment_answers



def test_moisture_protein_state_low_elasticity():
    derived = compute_derived_variables({"q5_elasticity": "low"})
    assert derived["moisture_protein_state"] == "moisture_deficit"


def test_moisture_protein_state_over_elastic():
    derived = compute_derived_variables({"q5_elasticity": "over_elastic"})
    assert derived["moisture_protein_state"] == "protein_deficit"


def test_build_up_signal_beads_and_fast_drying():
    derived = compute_derived_variables({
        "q4_porosity_water_behaviour": "beads_on_surface",
        "q4_drying_time": "under_2h"
    })
    assert derived["build_up_signal"] is True


def test_product_weight_ceiling_rich():
    derived = compute_derived_variables({
        "q6_thickness": "coarse",
        "q7_density": "high",
        "q4_porosity": "high"
    })
    assert derived["product_weight_ceiling"] == "rich"


def test_product_weight_ceiling_ultralight():
    derived = compute_derived_variables({
        "q6_thickness": "fine",
        "q7_density": "low",
        "q4_porosity": "low"
    })
    assert derived["product_weight_ceiling"] == "ultralight"


def test_tension_load_calculation():
    derived = compute_derived_variables({
        "g6_style_tension_pain": "often",
        "g5_current_style": "braids_twists",
        "g7_install_duration_weeks": 10,
        "g10_nighttime_protection": "none"
    })
    assert derived["tension_load"] >= 3


def test_mechanical_load_calculation():
    derived = compute_derived_variables({
        "g9_detangle_method": "dry_comb",
        "q2_heat_frequency": "9_plus"
    })
    assert derived["mechanical_load"] >= 3


def test_cleansing_interval_oily_scalp():
    derived = compute_derived_variables({
        "q3_scalp_type": "oily",
        "g5_current_style": "braids_twists"
    })
    assert derived["cleansing_interval_days"] == 7


def test_baseline_validity_provisional_recent_chemical():
    derived = compute_derived_variables({
        "q1_treatments": ["bleach"],
        "q1b_last_treatment_recency": "lt_2w"
    })
    assert derived["baseline_validity"] == "provisional"


def test_normalize_assessment_answers_null_treatments():
    norm = normalize_assessment_answers({
        "treatments": None,
        "timing": "within_2_weeks"
    })
    assert norm["q1_treatments"] == []
    assert norm["q1b_last_treatment_recency"] == "lt_2w"

