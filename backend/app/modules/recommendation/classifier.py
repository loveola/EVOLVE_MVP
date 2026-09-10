from typing import Any

SAFE_FIELDS = {
    "q1_treatments",
    "q1b_last_treatment_recency",
    "q2_heat_frequency",
    "q3_scalp_type",
    "q4_porosity",
    "q4_porosity_water_behaviour",
    "q4_drying_time",
    "q5_elasticity",
    "q6_thickness",
    "q7_density",
    "g1_primary_concern",
    "g2_shed_hair_morphology",
    "g4_concern_duration",
    "g5_current_style",
    "g6_style_tension_pain",
    "g7_install_duration_weeks",
    "g8_wash_interval_days",
    "g9_detangle_method",
    "g10_nighttime_protection",
    "g13_protein_treatment_frequency",
    "g14_hair_state",
    "baseline_validity",
    "porosity_confidence",
    "build_up_signal",
    "moisture_protein_state",
    "product_weight_ceiling",
    "cleansing_interval_days",
    "tension_load",
    "mechanical_load",
}


def _evaluate_leaf_condition(cond: dict[str, Any], context: dict[str, Any]) -> bool:
    field = cond.get("field")
    if not isinstance(field, str) or field not in SAFE_FIELDS:
        return False

    val = context.get(field)

    if "equals" in cond:
        return val == cond["equals"]
    if "in" in cond:
        target_list = cond["in"]
        return isinstance(target_list, (list, set, tuple)) and val in target_list
    if "gte" in cond:
        thresh = cond["gte"]
        return isinstance(val, (int, float)) and isinstance(thresh, (int, float)) and val >= thresh
    if "lte" in cond:
        thresh = cond["lte"]
        return isinstance(val, (int, float)) and isinstance(thresh, (int, float)) and val <= thresh
    if "contains" in cond:
        target = cond["contains"]
        if isinstance(val, list):
            return target in val
        return val == target
    if "contains_any" in cond:
        target_list = cond["contains_any"]
        if not isinstance(target_list, (list, set, tuple)):
            return False
        if isinstance(val, list):
            return any(item in val for item in target_list)
        return val in target_list

    return False


def _evaluate_ast(node: dict[str, Any], context: dict[str, Any]) -> bool:
    if not isinstance(node, dict):
        return False

    if "all_of" in node:
        children = node["all_of"]
        if not isinstance(children, list) or not children:
            return False
        return all(_evaluate_ast(child, context) for child in children)

    if "any_of" in node:
        children = node["any_of"]
        if not isinstance(children, list) or not children:
            return False
        return any(_evaluate_ast(child, context) for child in children)

    return _evaluate_leaf_condition(node, context)


def _score_rule(rule: dict[str, Any], context: dict[str, Any]) -> int:
    score = 100
    for booster in rule.get("score_boosters", []):
        if not isinstance(booster, dict):
            continue
        weight = booster.get("weight", 0)
        if not isinstance(weight, (int, float)):
            continue

        cond_str = booster.get("condition")
        if not isinstance(cond_str, str):
            continue

        matched = False
        try:
            if " >= " in cond_str:
                field, threshold = cond_str.split(" >= ", 1)
                f_strip = field.strip()
                if f_strip in SAFE_FIELDS:
                    val = context.get(f_strip)
                    if isinstance(val, (int, float)) and val >= float(threshold.strip()):
                        matched = True
            elif " == " in cond_str:
                field, expected = cond_str.split(" == ", 1)
                f_strip = field.strip()
                if f_strip in SAFE_FIELDS:
                    val = str(context.get(f_strip, ""))
                    exp_clean = expected.strip().strip("'\"")
                    if val == exp_clean:
                        matched = True
            elif " != " in cond_str:
                field, expected = cond_str.split(" != ", 1)
                f_strip = field.strip()
                if f_strip in SAFE_FIELDS and f_strip in context and context[f_strip] is not None:
                    val = str(context[f_strip])
                    exp_clean = expected.strip().strip("'\"")
                    if val != exp_clean:
                        matched = True
            elif "contains_any" in cond_str:
                field, items_part = cond_str.split("contains_any", 1)
                f_strip = field.strip()
                if f_strip in SAFE_FIELDS:
                    raw_items = items_part.strip().lstrip("[").rstrip("]")
                    items = [it.strip().strip("'\"") for it in raw_items.split(",") if it.strip()]
                    val = context.get(f_strip)
                    if isinstance(val, list) and any(it in val for it in items):
                        matched = True
                    elif str(val) in items:
                        matched = True
            elif " in " in cond_str:
                field, items_part = cond_str.split(" in ", 1)
                f_strip = field.strip()
                if f_strip in SAFE_FIELDS:
                    raw_items = items_part.strip().lstrip("[").rstrip("]")
                    items = [it.strip().strip("'\"") for it in raw_items.split(",") if it.strip()]
                    val = context.get(f_strip)
                    if isinstance(val, list) and any(it in val for it in items):
                        matched = True
                    elif str(val) in items:
                        matched = True
        except Exception:
            matched = False

        if matched:
            score += int(weight)

    return score


def classify_problems(
    derived: dict[str, Any],
    answers: dict[str, Any],
    rules: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    context = {}
    context.update({k: v for k, v in answers.items() if k in SAFE_FIELDS})
    context.update({k: v for k, v in derived.items() if k in SAFE_FIELDS})

    primary_matches: list[tuple[int, int, dict[str, Any]]] = []
    module_matches: list[dict[str, Any]] = []

    for rule in rules:
        classifier = rule.get("classifier")
        if not classifier:
            continue

        if not _evaluate_ast(classifier, context):
            continue

        if rule.get("always_runs_as_module", False):
            module_matches.append(rule)
        else:
            score = _score_rule(rule, context)
            prio = int(rule.get("priority", 50))
            primary_matches.append((score, prio, rule))

    primary_matches.sort(key=lambda x: (-x[0], x[1]))
    top_two = [item[2] for item in primary_matches[:2]]

    return top_two + module_matches
