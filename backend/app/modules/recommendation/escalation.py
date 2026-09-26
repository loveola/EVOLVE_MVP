from typing import Any
from dataclasses import dataclass, field
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.modules.recommendation.models import EscalationFlagConfig
from app.modules.recommendation.deriver import normalize_assessment_answers


@dataclass
class EscalationResult:
    tier: str = "GREEN"
    requires_escalation: bool = False
    flag_code: str | None = None
    trigger_reason: str | None = None
    message: str | None = None
    fired_flags: list[dict[str, Any]] = field(default_factory=list)
    referral_summary: dict[str, Any] | None = None
    protocol_constraints: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.message and not self.trigger_reason:
            self.trigger_reason = self.message
        elif self.trigger_reason and not self.message:
            self.message = self.trigger_reason


def _get_field_val(field: str, context: dict[str, Any]) -> Any:
    if field in context:
        return context[field]
    if "." in field:
        curr: Any = context
        for part in field.split("."):
            if isinstance(curr, dict) and part in curr:
                curr = curr[part]
            else:
                return None
        return curr
    return None


def _eval_leaf(cond: dict[str, Any], context: dict[str, Any], fired_codes: set[str]) -> bool:
    field = cond.get("field")
    if not isinstance(field, str):
        return False

    if field == "flag_not_fired":
        target = cond.get("equals")
        return target not in fired_codes

    val = _get_field_val(field, context)

    if "equals" in cond:
        return val == cond["equals"]

    if "in" in cond:
        targets = cond["in"]
        return isinstance(targets, (list, set, tuple)) and val in targets

    if "gte" in cond:
        thresh = cond["gte"]
        return isinstance(val, (int, float)) and isinstance(thresh, (int, float)) and val >= thresh

    if "lte" in cond:
        thresh = cond["lte"]
        return isinstance(val, (int, float)) and isinstance(thresh, (int, float)) and val <= thresh

    if "contains" in cond:
        target = cond["contains"]
        if isinstance(val, (list, set, tuple)):
            return target in val
        if isinstance(val, str):
            return target == val or target in val.split(",")
        return False

    if "not_contains" in cond:
        target = cond["not_contains"]
        if val is None:
            return True
        if isinstance(val, (list, set, tuple)):
            return target not in val
        if isinstance(val, str):
            return target != val and target not in val.split(",")
        return True

    if "contains_any" in cond:
        targets = cond["contains_any"]
        if not isinstance(targets, (list, set, tuple)):
            return False
        if isinstance(val, (list, set, tuple)):
            return any(t in val for t in targets)
        if isinstance(val, str):
            return val in targets or any(t == val for t in targets)
        return False

    if "not_contains_any" in cond:
        targets = cond["not_contains_any"]
        if not isinstance(targets, (list, set, tuple)):
            return True
        if val is None:
            return True
        if isinstance(val, (list, set, tuple)):
            return not any(t in val for t in targets)
        if isinstance(val, str):
            return val not in targets
        return True

    if "equals_or_contains_only" in cond:
        targets = cond["equals_or_contains_only"]
        if not isinstance(targets, (list, set, tuple)):
            return False
        if val is None:
            return False
        if isinstance(val, (list, set, tuple)):
            return bool(val) and set(val).issubset(set(targets))
        if isinstance(val, str):
            return val in targets
        return False

    return False


def _eval_ast(node: dict[str, Any], context: dict[str, Any], fired_codes: set[str]) -> bool:
    if not isinstance(node, dict):
        return False
    if "all_of" in node:
        children = node["all_of"]
        if not isinstance(children, list) or not children:
            return False
        return all(_eval_ast(c, context, fired_codes) for c in children)
    if "any_of" in node:
        children = node["any_of"]
        if not isinstance(children, list) or not children:
            return False
        return any(_eval_ast(c, context, fired_codes) for c in children)
    return _eval_leaf(node, context, fired_codes)


def _get_flag_priority(flag: EscalationFlagConfig) -> int:
    if hasattr(flag, "priority") and flag.priority is not None:
        try:
            return int(flag.priority)
        except (ValueError, TypeError):
            pass
    meta = getattr(flag, "metadata_info", None) or {}
    if isinstance(meta, dict):
        prio = meta.get("priority")
        if prio is not None:
            try:
                return int(prio)
            except (ValueError, TypeError):
                pass
    return 0


# // check escalation engine
def evaluate_escalation(answers: dict[str, Any], db: Session | None = None) -> EscalationResult:
    # // check escalation engine
    raw_answers = answers or {}
    try:
        normalized = normalize_assessment_answers(raw_answers)
    except Exception:
        normalized = {}
    context = {**raw_answers, **normalized}

    session = db
    close_session = False
    if session is None:
        if SessionLocal is not None:
            try:
                session = SessionLocal()
                close_session = True
            except Exception:
                session = None

    if session is None:
        return EscalationResult(tier="GREEN", requires_escalation=False)

    try:
        flags = (
            session.query(EscalationFlagConfig)
            .filter(EscalationFlagConfig.active == True)
            .all()
        )
    except Exception:
        flags = []
    finally:
        if close_session and session is not None:
            session.close()

    flags.sort(key=_get_flag_priority, reverse=True)

    fired_codes: set[str] = set()
    matched_flags: list[EscalationFlagConfig] = []
    for flag in flags:
        cond = getattr(flag, "conditions", None) or getattr(flag, "condition", None) or {}
        if _eval_ast(cond, context, fired_codes):
            fired_codes.add(flag.flag_code)
            matched_flags.append(flag)

    if not matched_flags:
        return EscalationResult(tier="GREEN", requires_escalation=False)

    top_flag = matched_flags[0]
    fired_list = [
        {
            "flag_code": f.flag_code,
            "tier": f.tier,
            "reason": f.trigger_reason,
        }
        for f in matched_flags
    ]
    ref_summary = getattr(top_flag, "metadata_info", None)
    # // check escalation engine
    return EscalationResult(
        tier=top_flag.tier or "RED",
        requires_escalation=True,
        flag_code=top_flag.flag_code,
        trigger_reason=top_flag.trigger_reason,
        message=top_flag.trigger_reason,
        fired_flags=fired_list,
        referral_summary=ref_summary if isinstance(ref_summary, dict) else None,
    )
