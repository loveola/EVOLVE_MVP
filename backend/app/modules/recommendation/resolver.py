import json
from pathlib import Path
from typing import Any

_BUNDLED_JSON = Path(__file__).parent / "seed_data" / "rules_config.json"
_protocols_cache: dict[str, dict[str, Any]] | None = None


def _load_protocols() -> dict[str, dict[str, Any]]:
    global _protocols_cache
    if _protocols_cache is None:
        if _BUNDLED_JSON.exists():
            with open(_BUNDLED_JSON, encoding="utf-8") as f:
                data = json.load(f)
            _protocols_cache = {p["id"]: p for p in data.get("protocols", [])}
        else:
            _protocols_cache = {}
    return _protocols_cache


def _is_action_allowed_by_condition(action: dict[str, Any], context: dict[str, Any]) -> bool:
    cond = action.get("conditional_on")
    if cond is None or cond == "":
        return True
    if not isinstance(cond, str):
        return False

    try:
        if " in [" in cond:
            field, vals_part = cond.split(" in [", 1)
            f_clean = field.strip()
            items = [v.strip().strip("'\"") for v in vals_part.rstrip("]").split(",") if v.strip()]
            val = context.get(f_clean)
            return val in items
        elif " == " in cond:
            field, expected = cond.split(" == ", 1)
            f_clean = field.strip()
            exp_clean = expected.strip().strip("'\"")
            return str(context.get(f_clean, "")) == exp_clean
    except Exception:
        return False

    return False




def resolve_roadmap(
    matched_rules: list[dict[str, Any]],
    derived: dict[str, Any],
    protocols_store: dict[str, dict[str, Any]] | None = None,
    answers: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if protocols_store is None:
        protocols_store = _load_protocols()

    eval_context = dict(answers or {})
    eval_context.update(derived)

    if not matched_rules:
        return {
            "active_problems": [],
            "cause_explanation_keys": [],
            "protocols": [],
            "roadmap": [],
            "product_weight_ceiling": derived.get("product_weight_ceiling", "light"),
            "hard_guards_fired": [],
            "realistic_timeline_weeks": {},
        }

    hard_guards_fired: list[str] = []
    moisture_state = derived.get("moisture_protein_state", "unknown")

    if moisture_state == "moisture_deficit":
        hard_guards_fired.append(
            "PROTEIN BLOCKED: elasticity is low (moisture deficit). Protein treatments are excluded "
            "from all phases. Adding protein to dry brittle hair increases breakage."
        )

    active_problems = [r["problem_id"] for r in matched_rules]
    cause_keys = [r.get("root_cause_explanation_key", "") for r in matched_rules if r.get("root_cause_explanation_key")]
    protocol_ids: list[str] = []
    roadmap_phases: list[dict[str, Any]] = []

    primary_rules = [r for r in matched_rules if not r.get("always_runs_as_module", False)]
    module_rules = [r for r in matched_rules if r.get("always_runs_as_module", False)]

    for rule in primary_rules + module_rules:
        pid = rule.get("protocol_id")
        if not pid:
            continue

        if pid in protocol_ids:
            continue

        protocol = protocols_store.get(pid)
        if not protocol:
            continue

        protocol_ids.append(pid)

        for phase in protocol.get("phases", []):
            raw_actions = phase.get("actions", [])
            filtered_actions = []

            for act in raw_actions:
                if not _is_action_allowed_by_condition(act, eval_context):
                    continue

                if moisture_state == "moisture_deficit":
                    actives = act.get("actives") or []
                    if any(blocked in actives for blocked in ["hydrolysed_keratin_mid_mw", "hydrolysed_protein"]):
                        continue
                    act_class = str(act.get("class", "")).lower()
                    if "protein" in act_class or "strengthening" in act_class:
                        continue

                filtered_actions.append(act)

            roadmap_phases.append({
                "phase": phase.get("phase", 0),
                "name": phase.get("name", ""),
                "days": phase.get("days", ""),
                "actions": filtered_actions,
                "checkpoint_day": phase.get("checkpoint_day"),
                "checkpoint_metric": phase.get("checkpoint_metric"),
            })

    primary_timeline = primary_rules[0].get("realistic_timeline_weeks", {}) if primary_rules else {}

    return {
        "active_problems": active_problems,
        "cause_explanation_keys": cause_keys,
        "protocols": protocol_ids,
        "roadmap": roadmap_phases,
        "product_weight_ceiling": derived.get("product_weight_ceiling", "light"),
        "hard_guards_fired": hard_guards_fired,
        "realistic_timeline_weeks": primary_timeline,
    }
