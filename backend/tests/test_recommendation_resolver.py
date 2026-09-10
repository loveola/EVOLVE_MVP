import pytest
from app.modules.recommendation.resolver import resolve_roadmap

PROTO_RETENTION = {
    "id": "PROTO_RETENTION",
    "goal": "Reduce the rate at which hair is lost to breakage.",
    "phases": [
        {
            "phase": 0,
            "name": "Stop the loss",
            "days": "0-14",
            "actions": [
                {"type": "behaviour", "id": "wet_detangle_only", "instruction": "Detangle only on soaked hair."},
                {"type": "product", "class": "pre_wash_treatment", "cadence": "every wash day"},
                {
                    "type": "behaviour",
                    "id": "section_work",
                    "instruction": "Work in sections",
                    "conditional_on": "q7_density in ['medium_high','high']"
                }
            ],
            "checkpoint_day": 14,
            "checkpoint_metric": "breakage_fragment_count",
        },
        {
            "phase": 1,
            "name": "Strengthen",
            "days": "15-42",
            "actions": [
                {"type": "product", "class": "strengthening_treatment", "actives": ["hydrolysed_keratin_mid_mw"]}
            ]
        }
    ],
}

PROTO_TENSION = {
    "id": "PROTO_TENSION",
    "goal": "Take load off the hairline.",
    "runs_as_module": True,
    "phases": [
        {
            "phase": 0,
            "name": "Unload",
            "days": "0-56",
            "actions": [{"type": "stop", "id": "no_tight_styles", "instruction": "No braids for 8 weeks."}],
            "checkpoint_day": 56,
            "checkpoint_metric": "edge_density_self_report",
        }
    ],
}

PROTOCOLS_STORE = {
    "PROTO_RETENTION": PROTO_RETENTION,
    "PROTO_TENSION": PROTO_TENSION,
}


def test_resolve_returns_correct_structure():
    matched = [{
        "problem_id": "mechanical_breakage",
        "protocol_id": "PROTO_RETENTION",
        "root_cause_explanation_key": "cause.mechanical_breakage",
        "realistic_timeline_weeks": {"first_measurable_change": 2, "consolidation": 8}
    }]
    derived = {"product_weight_ceiling": "light", "moisture_protein_state": "balanced"}
    res = resolve_roadmap(matched, derived, PROTOCOLS_STORE)
    assert res["product_weight_ceiling"] == "light"
    assert "PROTO_RETENTION" in res["protocols"]
    assert len(res["roadmap"]) == 2


def test_resolve_retains_conditional_action_from_answers():
    matched = [{
        "problem_id": "mechanical_breakage",
        "protocol_id": "PROTO_RETENTION",
        "root_cause_explanation_key": "cause.mechanical_breakage"
    }]
    derived = {"product_weight_ceiling": "light", "moisture_protein_state": "balanced"}
    answers = {"q7_density": "high"}
    res = resolve_roadmap(matched, derived, PROTOCOLS_STORE, answers=answers)
    actions = res["roadmap"][0]["actions"]
    assert any(a.get("id") == "section_work" for a in actions)


def test_resolve_deduplicates_shared_protocols():
    matched = [
        {
            "problem_id": "length_retention_failure",
            "protocol_id": "PROTO_RETENTION",
            "root_cause_explanation_key": "cause.retention"
        },
        {
            "problem_id": "mechanical_breakage",
            "protocol_id": "PROTO_RETENTION",
            "root_cause_explanation_key": "cause.breakage"
        }
    ]
    derived = {"product_weight_ceiling": "medium", "moisture_protein_state": "balanced"}
    res = resolve_roadmap(matched, derived, PROTOCOLS_STORE)
    assert res["protocols"].count("PROTO_RETENTION") == 1
    assert len(res["roadmap"]) == 2


def test_hard_guard_protein_blocked_when_moisture_deficit():
    matched = [{
        "problem_id": "mechanical_breakage",
        "protocol_id": "PROTO_RETENTION",
        "root_cause_explanation_key": "cause.mechanical_breakage",
        "realistic_timeline_weeks": {"first_measurable_change": 2, "consolidation": 8}
    }]
    derived = {"product_weight_ceiling": "light", "moisture_protein_state": "moisture_deficit"}
    res = resolve_roadmap(matched, derived, PROTOCOLS_STORE)
    assert len(res["hard_guards_fired"]) > 0
    assert any("protein" in g.lower() for g in res["hard_guards_fired"])

    phase_1_actions = res["roadmap"][1]["actions"]
    assert len(phase_1_actions) == 0


def test_resolve_includes_module_phases():
    matched = [
        {
            "problem_id": "mechanical_breakage",
            "protocol_id": "PROTO_RETENTION",
            "root_cause_explanation_key": "cause.mechanical_breakage",
            "always_runs_as_module": False
        },
        {
            "problem_id": "tension_reduction",
            "protocol_id": "PROTO_TENSION",
            "root_cause_explanation_key": "cause.tension",
            "always_runs_as_module": True
        }
    ]
    derived = {"product_weight_ceiling": "medium", "moisture_protein_state": "balanced"}
    res = resolve_roadmap(matched, derived, PROTOCOLS_STORE)
    assert "PROTO_TENSION" in res["protocols"]
    assert any(p["name"] == "Unload" for p in res["roadmap"])


def test_action_with_unsupported_condition_fails_closed():
    store = {
        "PROTO_TEST": {
            "id": "PROTO_TEST",
            "phases": [
                {
                    "phase": 1,
                    "name": "Phase 1",
                    "days": "Day 1 - 7",
                    "actions": [
                        {
                            "type": "custom",
                            "conditional_on": "unsupported_syntax_>=_5",
                            "instruction": "Do something"
                        }
                    ]
                }
            ]
        }
    }
    matched = [{
        "problem_id": "test_problem",
        "protocol_id": "PROTO_TEST",
        "always_runs_as_module": False
    }]
    res = resolve_roadmap(matched, {"product_weight_ceiling": "light"}, store)
    assert len(res["roadmap"][0]["actions"]) == 0


def test_action_with_non_string_condition_fails_closed():
    store = {
        "PROTO_TEST": {
            "id": "PROTO_TEST",
            "phases": [
                {
                    "phase": 1,
                    "name": "Phase 1",
                    "days": "Day 1 - 7",
                    "actions": [
                        {
                            "type": "custom",
                            "conditional_on": 12345,
                            "instruction": "Integer condition"
                        },
                        {
                            "type": "custom",
                            "conditional_on": ["invalid_list"],
                            "instruction": "List condition"
                        }
                    ]
                }
            ]
        }
    }
    matched = [{
        "problem_id": "test_problem",
        "protocol_id": "PROTO_TEST",
        "always_runs_as_module": False
    }]
    res = resolve_roadmap(matched, {"product_weight_ceiling": "light"}, store)
    assert len(res["roadmap"][0]["actions"]) == 0


def test_unresolved_protocol_id_is_omitted():
    store = {
        "PROTO_VALID": {
            "id": "PROTO_VALID",
            "phases": [
                {
                    "phase": 1,
                    "name": "Phase 1",
                    "days": "Day 1 - 7",
                    "actions": []
                }
            ]
        }
    }
    matched = [
        {
            "problem_id": "valid_problem",
            "protocol_id": "PROTO_VALID",
            "always_runs_as_module": False
        },
        {
            "problem_id": "ghost_problem",
            "protocol_id": "PROTO_NON_EXISTENT",
            "always_runs_as_module": False
        }
    ]
    res = resolve_roadmap(matched, {"product_weight_ceiling": "light"}, store)
    assert "PROTO_VALID" in res["protocols"]
    assert "PROTO_NON_EXISTENT" not in res["protocols"]
    assert len(res["protocols"]) == 1


