import json
from pathlib import Path
import importlib.util
from typing import Any
from dataclasses import dataclass, field
from sqlalchemy.orm import Session
from app.modules.recommendation.models import EscalationFlagConfig

_URGENCY_RANK = {
    "within_72_hours": 0,
    "within_1_week": 1,
    "within_2_weeks": 2,
    "within_4_weeks": 3,
    "routine": 4,
    "continue_existing_care": 5,
}


@dataclass
class EscalationResult:
    tier: str
    requires_escalation: bool
    flag_code: str | None = None
    trigger_reason: str | None = None
    fired_flags: list[dict[str, Any]] = field(default_factory=list)
    referral_summary: dict[str, Any] | None = None
    protocol_constraints: dict[str, Any] = field(default_factory=dict)


def _load_embedded_migration_flags() -> list[dict[str, Any]]:
    migration_path = Path(__file__).parent.parent.parent.parent / "alembic" / "versions" / "006_create_escalation_flags.py"
    if not migration_path.exists():
        return []
    try:
        spec = importlib.util.spec_from_file_location("migration_006", migration_path)
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return getattr(mod, "SEED_FLAGS", [])
    except Exception:
        pass
    return []


def load_escalation_flags(db: Session | None = None) -> list[dict[str, Any]]:
    if db is not None:
        try:
            records = db.query(EscalationFlagConfig).filter(EscalationFlagConfig.active.is_(True)).all()
            if records and len(records) > 0 and isinstance(getattr(records[0], "flag_code", None), str):
                flags = []
                for r in records:
                    meta = r.metadata_info if isinstance(r.metadata_info, dict) else {}
                    item = {
                        "flag_code": r.flag_code,
                        "description": r.description,
                        "trigger_reason": r.trigger_reason,
                        "tier": r.tier,
                        "conditions": r.conditions if isinstance(r.conditions, dict) else {},
                        "metadata": meta,
                        "active": r.active,
                        **meta
                    }
                    flags.append(item)
                return flags
        except Exception:
            pass
    return _load_embedded_migration_flags()


def _eval_leaf(condition: dict[str, Any], answers: dict[str, Any], fired_flag_codes: set[str]) -> bool:
    field_name = condition.get("field")
    if not field_name:
        return False

    if field_name == "flag_not_fired":
        target = condition.get("equals")
        return target not in fired_flag_codes

    value = answers.get(field_name)

    if "equals" in condition:
        target = condition["equals"]
        if isinstance(value, str) and isinstance(target, str):
            return value.strip().lower() == target.strip().lower()
        return value == target

    if "not_equals" in condition:
        target = condition["not_equals"]
        if isinstance(value, str) and isinstance(target, str):
            return value.strip().lower() != target.strip().lower()
        return value != target

    if "in" in condition:
        targets = condition["in"]
        if value is None:
            return False
        return value in targets

    if "not_in" in condition:
        targets = condition["not_in"]
        if value is None:
            return True
        return value not in targets

    if "contains" in condition:
        target = condition["contains"]
        if isinstance(value, list):
            return target in value
        if isinstance(value, str):
            return value == target or target in value
        return False

    if "not_contains" in condition:
        target = condition["not_contains"]
        if isinstance(value, list):
            return target not in value
        if isinstance(value, str):
            return value != target and target not in value
        return True

    if "contains_any" in condition:
        targets = condition["contains_any"]
        if isinstance(value, list):
            return any(t in value for t in targets)
        if isinstance(value, str):
            return value in targets
        return False

    if "not_contains_any" in condition:
        targets = condition["not_contains_any"]
        if isinstance(value, list):
            return not any(t in value for t in targets)
        if isinstance(value, str):
            return value not in targets
        return True

    if "equals_or_contains_only" in condition:
        target = condition["equals_or_contains_only"]
        target_list = target if isinstance(target, list) else [target]
        if isinstance(value, list):
            return set(value) == set(target_list)
        if isinstance(value, str):
            return value in target_list and len(target_list) == 1
        return False

    if "gte" in condition:
        target = condition["gte"]
        return value is not None and value >= target

    if "lte" in condition:
        target = condition["lte"]
        return value is not None and value <= target

    if "gt" in condition:
        target = condition["gt"]
        return value is not None and value > target

    if "lt" in condition:
        target = condition["lt"]
        return value is not None and value < target

    return False


def _evaluate_node(node: dict[str, Any], answers: dict[str, Any], fired_flag_codes: set[str]) -> bool:
    if not isinstance(node, dict) or not node:
        return False

    if "all_of" in node:
        children = node["all_of"]
        if not isinstance(children, list) or len(children) == 0:
            return False
        return all(_evaluate_node(child, answers, fired_flag_codes) for child in children)

    if "any_of" in node:
        children = node["any_of"]
        if not isinstance(children, list) or len(children) == 0:
            return False
        return any(_evaluate_node(child, answers, fired_flag_codes) for child in children)

    return _eval_leaf(node, answers, fired_flag_codes)


def evaluate_escalation(
    answers: dict[str, Any],
    flags: list[dict[str, Any]] | None = None,
    db: Session | None = None
) -> EscalationResult:
    if flags is None:
        flags = load_escalation_flags(db=db)

    red_flags = [f for f in flags if f.get("tier") == "RED"]
    amber_flags = [f for f in flags if f.get("tier") == "AMBER"]

    fired_flags: list[dict[str, Any]] = []
    fired_codes: set[str] = set()

    for flag in red_flags:
        conditions = flag.get("conditions") or flag.get("logic") or {}
        if _evaluate_node(conditions, answers, fired_codes):
            fired_flags.append(flag)
            fired_codes.add(flag.get("flag_code") or flag.get("id"))

    for flag in amber_flags:
        conditions = flag.get("conditions") or flag.get("logic") or {}
        if _evaluate_node(conditions, answers, fired_codes):
            fired_flags.append(flag)
            fired_codes.add(flag.get("flag_code") or flag.get("id"))

    has_red = any(f.get("tier") == "RED" for f in fired_flags)
    has_amber = any(f.get("tier") == "AMBER" for f in fired_flags)

    final_tier = "RED" if has_red else ("AMBER" if has_amber else "GREEN")
    requires_escalation = has_red

    primary_code = None
    trigger_reason = None
    referral_summary: dict[str, Any] | None = None
    protocol_constraints: dict[str, Any] = {}

    if has_red:
        red_fired = [f for f in fired_flags if f.get("tier") == "RED"]
        red_fired.sort(key=lambda x: (x.get("priority", 1), _URGENCY_RANK.get(x.get("referral_urgency", ""), 99)))
        primary = red_fired[0]
        primary_code = primary.get("flag_code") or primary.get("id")
        trigger_reason = primary.get("trigger_reason") or primary.get("clinical_basis") or primary.get("description")

        urgencies = [f.get("referral_urgency") for f in red_fired if f.get("referral_urgency")]
        most_urgent = min(urgencies, key=lambda u: _URGENCY_RANK.get(u, 99)) if urgencies else primary.get("referral_urgency")

        product_sale_blocked = any(f.get("hard_block_product_sale", False) for f in red_fired)
        account_creation_blocked = any(f.get("hard_block_account_creation", False) for f in red_fired)

        workup = primary.get("suggested_workup_to_surface_to_user") or primary.get("suggested_workup") or []
        for f in red_fired:
            w = f.get("suggested_workup_to_surface_to_user") or f.get("suggested_workup")
            if w and isinstance(w, list):
                for item in w:
                    if item not in workup:
                        workup.append(item)

        household_prompt = False
        for f in red_fired:
            h_trigger = f.get("trigger_household_screening_prompt_when")
            if h_trigger and isinstance(h_trigger, dict):
                if _eval_leaf(h_trigger, answers, fired_codes):
                    household_prompt = True

        clinical_summary = {
            "reported_loss_location": answers.get("h2_loss_location"),
            "scalp_symptoms": answers.get("h4_scalp_symptoms"),
            "scalp_lesions": answers.get("h5_scalp_lesions"),
            "concern_duration": answers.get("g4_concern_duration"),
            "chemical_treatments": answers.get("q1_treatments"),
            "recent_treatment_recency": answers.get("q1b_last_treatment_recency"),
            "trigger_events": answers.get("h11_trigger_event_2_3_months_ago"),
            "systemic_context": answers.get("h10_systemic_context"),
        }

        referral_summary = {
            "primary_flag_code": primary_code,
            "referral_specialty": primary.get("referral_specialty"),
            "referral_urgency": most_urgent,
            "user_message_key": primary.get("user_message_key"),
            "description": primary.get("description"),
            "trigger_reason": trigger_reason,
            "suggested_workup": workup,
            "hard_block_product_sale": product_sale_blocked,
            "product_sale_blocked": product_sale_blocked,
            "hard_block_account_creation": account_creation_blocked,
            "account_creation_blocked": account_creation_blocked,
            "household_prompt_shown": household_prompt,
            "assert_household_prompt_shown": household_prompt,
            "clinical_summary": clinical_summary,
        }

    elif has_amber:
        amber_fired = [f for f in fired_flags if f.get("tier") == "AMBER"]
        for f in amber_fired:
            constraints = f.get("protocol_constraints") or f.get("metadata", {}).get("protocol_constraints", {})
            for k, v in constraints.items():
                if k == "block_products" and "block_products" in protocol_constraints:
                    protocol_constraints[k] = list(set(protocol_constraints[k] + (v if isinstance(v, list) else [v])))
                elif k == "forbid_styles" and "forbid_styles" in protocol_constraints:
                    protocol_constraints[k] = list(set(protocol_constraints[k] + (v if isinstance(v, list) else [v])))
                else:
                    protocol_constraints[k] = v
            recheck = f.get("mandatory_recheck_day") or f.get("metadata", {}).get("mandatory_recheck_day")
            if recheck:
                protocol_constraints["mandatory_recheck_day"] = recheck
            advisory = f.get("advisory_key") or f.get("metadata", {}).get("advisory_key")
            if advisory:
                protocol_constraints["advisory_key"] = advisory

    return EscalationResult(
        tier=final_tier,
        requires_escalation=requires_escalation,
        flag_code=primary_code,
        trigger_reason=trigger_reason,
        fired_flags=fired_flags,
        referral_summary=referral_summary,
        protocol_constraints=protocol_constraints,
    )
