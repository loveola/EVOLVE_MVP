from typing import Any

ALLOWED_INPUT_FIELDS = {
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
    "scalp",
    "porosity",
    "elasticity",
    "thickness",
    "density",
    "treatments",
    "timing",
    "heat",
}



def normalize_assessment_answers(raw: dict[str, Any]) -> dict[str, Any]:
    norm = dict(raw)

    if "scalp" in norm and "q3_scalp_type" not in norm:
        norm["q3_scalp_type"] = norm["scalp"]

    if "porosity" in norm and "q4_porosity" not in norm:
        val = norm["porosity"]
        if val == "under_2_hrs":
            norm["q4_porosity"] = "high"
            norm.setdefault("q4_drying_time", "under_2h")
        elif val in ["takes_2_to_4_hrs", "2_to_4_hrs"]:
            norm["q4_porosity"] = "medium"
        elif val == "takes_over_4_hrs":
            norm["q4_porosity"] = "low"
        else:
            norm["q4_porosity"] = "unsure"

    if "elasticity" in norm and "q5_elasticity" not in norm:
        val = norm["elasticity"]
        if val == "stretches_returns":
            norm["q5_elasticity"] = "healthy"
        elif val in ["stretches_far_mushy", "stretches_snaps"]:
            norm["q5_elasticity"] = "over_elastic"
        elif val == "snaps_immediately":
            norm["q5_elasticity"] = "low"
        else:
            norm["q5_elasticity"] = "unsure"

    if "thickness" in norm and "q6_thickness" not in norm:
        val = norm["thickness"]
        if val in ["fine", "fine_whisper"]:
            norm["q6_thickness"] = "fine"
        elif val in ["coarse", "thick_coarse"]:
            norm["q6_thickness"] = "coarse"
        else:
            norm["q6_thickness"] = "medium"

    if "density" in norm and "q7_density" not in norm:
        val = norm["density"]
        if val in ["low", "scalp_visible"]:
            norm["q7_density"] = "low"
        elif val in ["high", "scalp_hardly_visible"]:
            norm["q7_density"] = "high"
        else:
            norm["q7_density"] = "medium"

    if "treatments" in norm and "q1_treatments" not in norm:
        raw_treatments = norm.get("treatments") or []
        if isinstance(raw_treatments, str):
            raw_treatments = [raw_treatments]
        norm["q1_treatments"] = [
            "permanent_colour" if t == "permanent_color" else t
            for t in raw_treatments
        ]


    if "timing" in norm and "q1b_last_treatment_recency" not in norm:
        val = norm["timing"]
        recency_map = {
            "within_2_weeks": "lt_2w",
            "under_2_weeks": "lt_2w",
            "2_to_8_weeks": "2_4w",
            "over_8_weeks": "1_3m",
        }
        norm["q1b_last_treatment_recency"] = recency_map.get(val, "lt_2w")

    if "heat" in norm and "q2_heat_frequency" not in norm:
        val = norm["heat"]
        if val == "daily":
            norm["q2_heat_frequency"] = "9_plus"
        elif val in ["1_to_2_weekly", "special_occasions"]:
            norm["q2_heat_frequency"] = "3_8"
        else:
            norm["q2_heat_frequency"] = "rarely"

    return norm


def compute_derived_variables(raw_answers: dict[str, Any]) -> dict[str, Any]:
    answers = normalize_assessment_answers(
        {k: v for k, v in raw_answers.items() if k in ALLOWED_INPUT_FIELDS}
    )
    d: dict[str, Any] = {}

    treatments: list[str] = answers.get("q1_treatments") or []
    recency: str = str(answers.get("q1b_last_treatment_recency", ""))
    heat: str = str(answers.get("q2_heat_frequency", ""))
    scalp: str = str(answers.get("q3_scalp_type", ""))
    porosity: str = str(answers.get("q4_porosity", ""))
    water_behaviour: str = str(answers.get("q4_porosity_water_behaviour", ""))
    drying_time: str = str(answers.get("q4_drying_time", ""))
    elasticity: str = str(answers.get("q5_elasticity", ""))
    thickness: str = str(answers.get("q6_thickness", ""))
    density: str = str(answers.get("q7_density", ""))
    style: str = str(answers.get("g5_current_style", "loose_natural"))
    tension_pain: str = str(answers.get("g6_style_tension_pain", "never"))
    try:
        install_weeks: int = int(answers.get("g7_install_duration_weeks") or 0)
    except (ValueError, TypeError):
        install_weeks = 0

    wash_interval: str = str(answers.get("g8_wash_interval_days", "3_7"))
    detangle: str = str(answers.get("g9_detangle_method", ""))
    night_protection: str = str(answers.get("g10_nighttime_protection", "yes"))
    primary_concern: list[str] = answers.get("g1_primary_concern") or []

    chemical_recent = any(t in treatments for t in ["bleach", "relaxer", "permanent_colour", "keratin", "henna"])
    recency_recent = recency in ["lt_2w", "2_4w", "1_3m"]
    masking = any(t in treatments for t in ["keratin", "henna"])

    if masking and recency_recent:
        d["baseline_validity"] = "masked"
    elif chemical_recent and recency == "lt_2w":
        d["baseline_validity"] = "provisional"
    elif heat == "9_plus":
        d["baseline_validity"] = "provisional"
    else:
        d["baseline_validity"] = "clean"

    conf = 0.8
    if porosity == "unsure":
        conf -= 0.4
    if d["baseline_validity"] != "clean":
        conf -= 0.3
    d["porosity_confidence"] = max(0.1, round(conf, 2))

    build_up = (
        water_behaviour == "beads_on_surface" and drying_time == "under_2h"
    ) or (
        wash_interval in ["15_28", "28_plus"]
        and any(c in primary_concern for c in ["dullness", "scalp_flaking", "product_not_absorbing"])
    )
    d["build_up_signal"] = build_up
    if build_up:
        d["porosity_confidence"] = max(0.1, round(d["porosity_confidence"] - 0.2, 2))

    d["moisture_protein_state"] = {
        "healthy": "balanced",
        "over_elastic": "protein_deficit",
        "low": "moisture_deficit",
    }.get(elasticity, "unknown")

    ts = {"fine": 0, "medium": 1, "coarse": 2}.get(thickness, 1)
    ds = {"low": 0, "medium": 1, "medium_high": 2, "high": 2}.get(density, 1)
    ps = {"low": 0, "medium": 1, "high": 2}.get(porosity, 1)
    total = ts + ds + ps
    if total <= 1:
        d["product_weight_ceiling"] = "ultralight"
    elif total <= 3:
        d["product_weight_ceiling"] = "light"
    elif total == 4:
        d["product_weight_ceiling"] = "medium"
    else:
        d["product_weight_ceiling"] = "rich"

    base_interval = {
        "loose_natural": 7,
        "braids_twists": 10,
        "cornrows": 10,
        "weave_wig": 10,
        "locs": 10,
        "relaxed_loose": 7,
        "straightened": 7,
    }.get(style, 7)
    if scalp == "oily":
        base_interval -= 3
    if build_up:
        base_interval -= 2
    if scalp == "dry" and "scalp_flaking" not in primary_concern and "scalp_itch" not in primary_concern:
        base_interval += 3

    interval = max(4, min(14, base_interval))
    if any(c in primary_concern for c in ["scalp_flaking", "scalp_itch"]):
        interval = min(7, interval)
    d["cleansing_interval_days"] = interval

    tension = 0
    if tension_pain == "often":
        tension += 2
    elif tension_pain == "sometimes":
        tension += 1
    if style in ["braids_twists", "cornrows", "weave_wig"]:
        tension += 1
    if install_weeks > 8:
        tension += 1
    if night_protection == "none":
        tension += 1
    d["tension_load"] = min(5, tension)

    mechanical = 0
    if detangle == "dry_comb":
        mechanical += 2
    elif detangle == "rarely":
        mechanical += 1
    if heat in ["3_8", "9_plus"]:
        mechanical += 1
    if night_protection == "none":
        mechanical += 1
    if style == "loose_natural" and wash_interval == "3_7":
        mechanical += 1
    d["mechanical_load"] = min(5, mechanical)

    return d
