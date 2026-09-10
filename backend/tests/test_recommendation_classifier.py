import pytest
from app.modules.recommendation.classifier import classify_problems

MECHANICAL_BREAKAGE_RULE = {
    "problem_id": "mechanical_breakage",
    "display_name": "Breakage from handling",
    "classifier": {
        "all_of": [
            {"field": "g1_primary_concern", "contains": "breakage"},
            {"field": "mechanical_load", "gte": 2},
        ]
    },
    "score_boosters": [
        {"condition": "mechanical_load >= 3", "weight": 3}
    ],
    "protocol_id": "PROTO_RETENTION",
    "always_runs_as_module": False,
    "priority": 50,
}

TENSION_MODULE_RULE = {
    "problem_id": "tension_reduction",
    "display_name": "Protecting the edges and nape",
    "classifier": {
        "all_of": [
            {"field": "tension_load", "gte": 3}
        ]
    },
    "score_boosters": [],
    "protocol_id": "PROTO_TENSION",
    "always_runs_as_module": True,
    "priority": 90,
}

CHRONIC_DRYNESS_RULE = {
    "problem_id": "chronic_dryness",
    "display_name": "Hair that will not stay moisturised",
    "classifier": {
        "any_of": [
            {
                "all_of": [
                    {"field": "g1_primary_concern", "contains": "dryness"},
                    {"field": "q5_elasticity", "in": ["low", "healthy"]},
                ]
            }
        ]
    },
    "score_boosters": [],
    "protocol_id": "PROTO_MOISTURE",
    "always_runs_as_module": False,
    "priority": 60,
}


def test_classify_matches_mechanical_breakage():
    answers = {"g1_primary_concern": ["breakage"]}
    derived = {"mechanical_load": 3, "tension_load": 0}
    matched = classify_problems(derived, answers, [MECHANICAL_BREAKAGE_RULE, CHRONIC_DRYNESS_RULE])
    assert len(matched) == 1
    assert matched[0]["problem_id"] == "mechanical_breakage"


def test_classify_tension_module_always_appended():
    answers = {"g1_primary_concern": ["breakage"]}
    derived = {"mechanical_load": 2, "tension_load": 4}
    matched = classify_problems(derived, answers, [MECHANICAL_BREAKAGE_RULE, TENSION_MODULE_RULE])
    pids = [m["problem_id"] for m in matched]
    assert "tension_reduction" in pids
    assert pids.index("tension_reduction") > 0


def test_classify_caps_at_two_primary_problems():
    answers = {"g1_primary_concern": ["breakage", "dryness"], "q5_elasticity": "healthy"}
    derived = {"mechanical_load": 2, "tension_load": 4}
    matched = classify_problems(derived, answers, [MECHANICAL_BREAKAGE_RULE, CHRONIC_DRYNESS_RULE, TENSION_MODULE_RULE])
    primary = [m for m in matched if not m.get("always_runs_as_module")]
    assert len(primary) <= 2


def test_classify_score_booster_ranking():
    rule_low_score = {
        "problem_id": "rule_1",
        "classifier": {"all_of": [{"field": "mechanical_load", "gte": 2}]},
        "score_boosters": [],
        "priority": 50,
        "always_runs_as_module": False,
    }
    rule_high_score = {
        "problem_id": "rule_2",
        "classifier": {"all_of": [{"field": "mechanical_load", "gte": 2}]},
        "score_boosters": [{"condition": "mechanical_load >= 3", "weight": 10}],
        "priority": 50,
        "always_runs_as_module": False,
    }
    derived = {"mechanical_load": 3}
    matched = classify_problems(derived, {}, [rule_low_score, rule_high_score])
    assert matched[0]["problem_id"] == "rule_2"
