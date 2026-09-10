import pytest
from app.modules.recommendation.deriver import compute_derived_variables
from app.modules.recommendation.classifier import classify_problems
from app.modules.recommendation.resolver import resolve_roadmap

SAMPLE_RULES = [
    {
        "problem_id": "mechanical_breakage",
        "classifier": {
            "all_of": [
                {"field": "g1_primary_concern", "contains": "breakage"},
                {"field": "mechanical_load", "gte": 2}
            ]
        },
        "score_boosters": [{"condition": "mechanical_load >= 3", "weight": 5}],
        "protocol_id": "PROTO_RETENTION",
        "always_runs_as_module": False,
        "priority": 50,
        "root_cause_explanation_key": "cause.breakage"
    },
    {
        "problem_id": "chronic_dryness",
        "classifier": {
            "any_of": [
                {
                    "all_of": [
                        {"field": "g1_primary_concern", "contains": "dryness"},
                        {"field": "q5_elasticity", "in": ["low", "healthy"]}
                    ]
                }
            ]
        },
        "score_boosters": [],
        "protocol_id": "PROTO_MOISTURE",
        "always_runs_as_module": False,
        "priority": 60,
        "root_cause_explanation_key": "cause.dryness"
    },
    {
        "problem_id": "tension_reduction",
        "classifier": {
            "all_of": [{"field": "tension_load", "gte": 3}]
        },
        "score_boosters": [],
        "protocol_id": "PROTO_TENSION",
        "always_runs_as_module": True,
        "priority": 90,
        "root_cause_explanation_key": "cause.tension"
    }
]

SAMPLE_PROTOCOLS = {
    "PROTO_RETENTION": {
        "id": "PROTO_RETENTION",
        "phases": [
            {
                "phase": 0,
                "name": "Stop the loss",
                "days": "0-14",
                "actions": [
                    {"type": "behaviour", "instruction": "Detangle wet with slip conditioner"},
                    {"type": "product", "class": "strengthening_protein", "actives": ["hydrolysed_protein"]}
                ]
            }
        ]
    },
    "PROTO_MOISTURE": {
        "id": "PROTO_MOISTURE",
        "phases": [
            {
                "phase": 0,
                "name": "Hydrate",
                "days": "0-14",
                "actions": [{"type": "product", "class": "leave_in_humectant"}]
            }
        ]
    },
    "PROTO_TENSION": {
        "id": "PROTO_TENSION",
        "phases": [
            {
                "phase": 0,
                "name": "Unload",
                "days": "0-56",
                "actions": [{"type": "stop", "instruction": "No tight braiding"}]
            }
        ]
    }
}


def test_rule_branch_mechanical_breakage_and_tension_module():
    answers = {
        "g1_primary_concern": ["breakage"],
        "g9_detangle_method": "dry_comb",
        "q2_heat_frequency": "9_plus",
        "g6_style_tension_pain": "often",
        "g5_current_style": "braids_twists",
        "g7_install_duration_weeks": 10,
        "q5_elasticity": "healthy"
    }
    derived = compute_derived_variables(answers)
    assert derived["mechanical_load"] >= 3
    assert derived["tension_load"] >= 3

    matched = classify_problems(derived, answers, SAMPLE_RULES)
    pids = [m["problem_id"] for m in matched]
    assert "mechanical_breakage" in pids
    assert "tension_reduction" in pids

    res = resolve_roadmap(matched, derived, SAMPLE_PROTOCOLS)
    assert "PROTO_RETENTION" in res["protocols"]
    assert "PROTO_TENSION" in res["protocols"]
    assert len(res["hard_guards_fired"]) == 0


def test_rule_branch_dryness_with_moisture_deficit_hard_guard():
    answers = {
        "g1_primary_concern": ["dryness"],
        "q5_elasticity": "low",
        "q6_thickness": "fine",
        "q7_density": "low",
        "q4_porosity": "low"
    }
    derived = compute_derived_variables(answers)
    assert derived["moisture_protein_state"] == "moisture_deficit"
    assert derived["product_weight_ceiling"] == "ultralight"

    matched = classify_problems(derived, answers, SAMPLE_RULES)
    assert len(matched) == 1
    assert matched[0]["problem_id"] == "chronic_dryness"

    res = resolve_roadmap(matched, derived, SAMPLE_PROTOCOLS)
    assert any("PROTEIN BLOCKED" in g for g in res["hard_guards_fired"])


def test_unknown_or_malformed_conditions_fail_safely():
    malformed_rule = {
        "problem_id": "malformed",
        "classifier": {
            "all_of": [
                {"field": "__class__", "equals": "object"},
                {"field": "non_existent_field", "gte": 999}
            ]
        },
        "score_boosters": [{"condition": "malformed expression", "weight": 5}],
        "protocol_id": "PROTO_MOISTURE"
    }
    derived = compute_derived_variables({})
    matched = classify_problems(derived, {}, [malformed_rule])
    assert len(matched) == 0
