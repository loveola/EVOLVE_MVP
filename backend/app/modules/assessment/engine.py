from typing import Dict, Any, List

def evaluate_assessment(answers: Dict[str, Any]) -> Dict[str, Any]:
    scalp_map = {
        "dry": "Dry",
        "oily": "Oily",
        "combination": "Combination",
        "normal": "Normal"
    }
    scalp_type = scalp_map.get(answers.get("scalp", ""), "Unknown")

    porosity_map = {
        "takes_over_4_hrs": "Low",
        "takes_2_to_4_hrs": "Medium",
        "under_2_hrs": "High"
    }
    porosity = porosity_map.get(answers.get("porosity", ""), "Unknown")

    elasticity_map = {
        "stretches_returns": "Healthy (Balanced)",
        "stretches_far_mushy": "Over-elastic (Needs Protein)",
        "snaps_immediately": "Low (Needs Moisture)"
    }
    elasticity = elasticity_map.get(answers.get("elasticity", ""), "Unknown")

    thickness_map = {
        "fine": "Fine",
        "medium": "Medium",
        "coarse": "Coarse"
    }
    thickness = thickness_map.get(answers.get("thickness", ""), "Unknown")

    density_map = {
        "low": "Low",
        "medium": "Medium",
        "high": "High"
    }
    density = density_map.get(answers.get("density", ""), "Unknown")

    flags: List[Dict[str, str]] = []
    treatments = answers.get("treatments") or []
    if isinstance(treatments, str):
        treatments = [treatments]

    has_color_bleach = any(t in treatments for t in ["permanent_color", "bleach"])
    if has_color_bleach and answers.get("timing") == "within_2_weeks":
        flags.append({
            "affects": "Porosity, Elasticity",
            "message": "Color or lightener applied within the last 2 weeks lifts the cuticle; porosity is marked provisional until 2 weeks have passed."
        })

    if "relaxer" in treatments:
        flags.append({
            "affects": "Elasticity",
            "message": "Relaxed hair and new growth behave as two different hair textures and must be treated with tailored regimens."
        })

    if "keratin" in treatments:
        flags.append({
            "affects": "Porosity, Elasticity",
            "message": "Keratin treatments coat the strand; your current Hair ID describes the treatment coating rather than your natural cuticle."
        })

    if answers.get("heat") == "daily":
        flags.append({
            "affects": "Moisture, Cuticle Integrity",
            "message": "Daily direct heat causes thermal cuticle fatigue; heat protection and bond building are recommended."
        })

    return {
        "traits": {
            "scalp_type": scalp_type,
            "porosity": porosity,
            "elasticity": elasticity,
            "thickness": thickness,
            "density": density
        },
        "flags": flags
    }
