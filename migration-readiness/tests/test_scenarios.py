from __future__ import annotations

from pathlib import Path

import pytest

from migration_readiness.catalog import UnknownMerchantError
from migration_readiness.orchestrator import MigrationOrchestrator
from migration_readiness.scenarios import SCENARIOS
from migration_readiness.state import StateStore


def _orch(tmp_path: Path) -> MigrationOrchestrator:
    return MigrationOrchestrator(
        store=StateStore(tmp_path / "state"),
        reports_dir=tmp_path / "reports",
        auto_approve=True,
    )


@pytest.mark.parametrize(
    "scenario_id,band",
    [("ABC", "not_ready"), ("RISK", "at_risk"), ("ACME", "ready")],
)
def test_scenario_bands(tmp_path: Path, scenario_id: str, band: str) -> None:
    scenario = next(s for s in SCENARIOS if s["id"] == scenario_id)
    result = _orch(tmp_path).run(scenario["request"])
    assert result.state.stage == "complete"
    assert result.state.readiness is not None
    assert result.state.readiness.band == band


def test_unknown_scenario_fails(tmp_path: Path) -> None:
    scenario = next(s for s in SCENARIOS if s["id"] == "UNKNOWN")
    with pytest.raises(UnknownMerchantError):
        _orch(tmp_path).run(scenario["request"])
