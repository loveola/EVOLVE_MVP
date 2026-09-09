"""seed rules_config and derived_variable_config tables from rules_config.json

Revision ID: 003_seed_rules_config
Revises: 002_create_rules_config
Create Date: 2026-09-09 17:05:00.000000
"""
import copy
import json
from pathlib import Path
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "003_seed_rules_config"
down_revision: Union[str, None] = "002_create_rules_config"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_BUNDLED_JSON = Path(__file__).parent.parent.parent / "app" / "modules" / "recommendation" / "seed_data" / "rules_config.json"
_ARTIFACTS_JSON = Path(__file__).parent.parent.parent.parent / "artifacts" / "rules_config.json"


def _load_json():
    if _BUNDLED_JSON.exists():
        target_path = _BUNDLED_JSON
    elif _ARTIFACTS_JSON.exists():
        target_path = _ARTIFACTS_JSON
    else:
        raise FileNotFoundError(
            f"Seed data rules_config.json not found at {_BUNDLED_JSON} nor {_ARTIFACTS_JSON}"
        )
    with open(target_path, encoding="utf-8") as f:
        return json.load(f)


def upgrade() -> None:
    data = _load_json()
    conn = op.get_bind()

    tie_break = data["problem_taxonomy"]["classification_rules"]["tie_break_order"]
    priority_map = {pid: (i + 1) * 10 for i, pid in enumerate(tie_break)}

    for var in data["derived_variables"]:
        conn.execute(
            sa.text(
                "INSERT INTO derived_variable_config (name, var_type, rule_text, consumes, effect_text) "
                "VALUES (:name, :var_type, :rule_text, CAST(:consumes AS jsonb), :effect_text)"
            ),
            {
                "name": var["name"],
                "var_type": var.get("type", "unknown"),
                "rule_text": var.get("rule", ""),
                "consumes": json.dumps(var.get("consumes", [])),
                "effect_text": var.get("effect") or var.get("note"),
            },
        )

    for problem in data["problem_taxonomy"]["problems"]:
        pid = problem["id"]
        classifier_raw = copy.deepcopy(problem.get("classifier", {}))

        score_boosters = problem.get("score_boosters") or []
        if not score_boosters and isinstance(classifier_raw, dict) and "score_boosters" in classifier_raw:
            score_boosters = classifier_raw.pop("score_boosters")

        if "field" in classifier_raw and "all_of" not in classifier_raw and "any_of" not in classifier_raw:
            classifier = {"all_of": [classifier_raw]}
        else:
            classifier = classifier_raw

        conn.execute(
            sa.text(
                "INSERT INTO rules_config "
                "(problem_id, display_name, replaces, classifier, score_boosters, hard_guards, "
                "protocol_id, primary_metric, root_cause_explanation_key, realistic_timeline_weeks, "
                "always_runs_as_module, priority) "
                "VALUES (:problem_id, :display_name, :replaces, CAST(:classifier AS jsonb), "
                "CAST(:score_boosters AS jsonb), CAST(:hard_guards AS jsonb), :protocol_id, "
                ":primary_metric, :root_cause_explanation_key, CAST(:realistic_timeline_weeks AS jsonb), "
                ":always_runs_as_module, :priority)"
            ),
            {
                "problem_id": pid,
                "display_name": problem.get("display_name", pid),
                "replaces": problem.get("replaces"),
                "classifier": json.dumps(classifier),
                "score_boosters": json.dumps(score_boosters),
                "hard_guards": json.dumps([problem["hard_guard"]] if problem.get("hard_guard") else []),
                "protocol_id": problem.get("protocol_id", "UNKNOWN"),
                "primary_metric": problem.get("primary_metric"),
                "root_cause_explanation_key": problem.get("root_cause_explanation_key", f"cause.{pid}"),
                "realistic_timeline_weeks": json.dumps(problem.get("realistic_timeline_weeks", {})),
                "always_runs_as_module": problem.get("always_runs_as_module", False),
                "priority": priority_map.get(pid, 50),
            },
        )


def downgrade() -> None:
    data = _load_json()
    conn = op.get_bind()
    seed_pids = [p["id"] for p in data["problem_taxonomy"]["problems"]]
    seed_names = [v["name"] for v in data["derived_variables"]]

    conn.execute(
        sa.text("DELETE FROM rules_config WHERE problem_id = ANY(:pids)"),
        {"pids": seed_pids},
    )
    conn.execute(
        sa.text("DELETE FROM derived_variable_config WHERE name = ANY(:names)"),
        {"names": seed_names},
    )
