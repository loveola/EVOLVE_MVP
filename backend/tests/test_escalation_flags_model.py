import importlib
import pytest
from app.modules.recommendation.models import EscalationFlagConfig


def test_escalation_flag_model_columns():
    table = EscalationFlagConfig.__table__
    assert table.name == "escalation_flags"
    columns = {c.name for c in table.columns}
    expected = {
        "id",
        "flag_code",
        "description",
        "trigger_reason",
        "tier",
        "conditions",
        "metadata",
        "active",
        "created_at",
        "updated_at",
    }
    assert expected.issubset(columns)
    assert table.primary_key.columns.keys() == ["id"]
    assert table.columns["flag_code"].unique is True


def test_migration_contains_embedded_seed_data_without_file_io():
    from pathlib import Path
    import importlib.util

    migration_path = Path(__file__).parent.parent / "alembic" / "versions" / "006_create_escalation_flags.py"
    spec = importlib.util.spec_from_file_location("migration_006", migration_path)
    migration_006 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration_006)

    assert hasattr(migration_006, "SEED_FLAGS")
    assert isinstance(migration_006.SEED_FLAGS, list)
    assert len(migration_006.SEED_FLAGS) >= 18

    flag_codes = [f["flag_code"] for f in migration_006.SEED_FLAGS]
    assert "RED_01_SCARRING_CENTRAL" in flag_codes
    assert "RED_02_TRACTION_ADVANCED" in flag_codes
    assert "RED_04_INFECTION_INFLAMMATORY" in flag_codes
    assert "RED_05_CHEMICAL_THERMAL_INJURY" in flag_codes
    assert "RED_06_ACUTE_DIFFUSE_SHEDDING" in flag_codes
    assert "RED_08_PAEDIATRIC" in flag_codes
    assert "AMBER_01_EARLY_TENSION" in flag_codes
    assert "AMBER_03_PROVISIONAL_BASELINE" in flag_codes

    for flag in migration_006.SEED_FLAGS:
        assert "flag_code" in flag
        assert "description" in flag
        assert "trigger_reason" in flag
        assert "tier" in flag
        assert "conditions" in flag
        assert flag["tier"] in ["RED", "AMBER"]
