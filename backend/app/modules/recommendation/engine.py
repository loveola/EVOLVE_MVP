from typing import Any
from sqlalchemy.orm import Session

from app.modules.recommendation.deriver import compute_derived_variables, normalize_assessment_answers
from app.modules.recommendation.classifier import classify_problems
from app.modules.recommendation.resolver import resolve_roadmap
from app.modules.recommendation.models import RulesConfig


CONCERN_MAPPING = {
    "breakage": "breakage",
    "dryness": "dryness",
    "split_ends": "split_ends",
    "length_retention": "no_length",
    "scalp": "scalp_flaking",
    "tangling": "tangling",
    "over_conditioning": "over_conditioning",
}


def run_engine(answers: dict[str, Any], concern: str, db: Session) -> dict[str, Any]:
    enriched_answers = dict(answers)
    raw_concern = enriched_answers.get("g1_primary_concern")
    if isinstance(raw_concern, str):
        existing_concerns = [raw_concern]
    elif isinstance(raw_concern, list):
        existing_concerns = list(raw_concern)
    else:
        existing_concerns = []

    internal_concern = CONCERN_MAPPING.get(concern, concern)
    if internal_concern not in existing_concerns:
        existing_concerns.insert(0, internal_concern)
    enriched_answers["g1_primary_concern"] = existing_concerns


    normalized_answers = normalize_assessment_answers(enriched_answers)
    derived = compute_derived_variables(normalized_answers)

    db_rules = db.query(RulesConfig).filter(RulesConfig.is_active).all()
    rules_dicts = [
        {
            "problem_id": r.problem_id,
            "display_name": r.display_name,
            "classifier": r.classifier,
            "score_boosters": r.score_boosters,
            "hard_guards": r.hard_guards,
            "protocol_id": r.protocol_id,
            "primary_metric": r.primary_metric,
            "root_cause_explanation_key": r.root_cause_explanation_key,
            "realistic_timeline_weeks": r.realistic_timeline_weeks,
            "always_runs_as_module": r.always_runs_as_module,
            "priority": r.priority,
        }
        for r in db_rules
    ]

    matched_rules = classify_problems(derived, normalized_answers, rules_dicts)
    return resolve_roadmap(matched_rules, derived, answers=normalized_answers)
