from __future__ import annotations

from pathlib import Path

import pytest

from migration_readiness.catalog import UnknownMerchantError
from migration_readiness.orchestrator import MigrationOrchestrator
from migration_readiness.state import StateStore


def test_shopify_abc_end_to_end(tmp_path: Path) -> None:
    store = StateStore(tmp_path / "state")
    reports = tmp_path / "reports"
    orch = MigrationOrchestrator(
        store=store,
        reports_dir=reports,
        auto_approve=True,
    )
    result = orch.run(
        "Prepare Shopify merchant ABC for migration to the new payment integration."
    )

    assert result.approved is True
    assert result.state.case_id == "ABC"
    assert result.state.stage == "complete"
    assert result.state.readiness is not None
    assert result.state.readiness.band == "not_ready"
    assert result.state.readiness.blockers == 3
    assert result.state.readiness.unsupported_methods == 1
    assert result.state.validation is not None
    assert result.state.validation.retries_used >= 1

    unsupported = [
        p.payment_method
        for p in result.state.compatibility.payment_methods  # type: ignore[union-attr]
        if p.status == "unsupported"
    ]
    assert "boleto" in unsupported

    blocker_ids = {g.id for g in result.state.gaps if g.severity == "blocker"}
    assert "pay-boleto" in blocker_ids
    assert "cfg-webhook-hmac" in blocker_ids
    assert "cfg-3ds" in blocker_ids

    assert result.state.report_path is not None
    report = Path(result.state.report_path)
    assert report.exists()
    text = report.read_text(encoding="utf-8")
    assert "Shopify Merchant ABC" in text
    assert "boleto" in text

    agent_names = [r.agent for r in result.results]
    assert agent_names == [
        "intake",
        "research",
        "compatibility",
        "gap-analysis",
        "migration-planning",
        "validation",
        "reporting",
    ]


def test_unknown_merchant_is_rejected(tmp_path: Path) -> None:
    store = StateStore(tmp_path / "state")
    orch = MigrationOrchestrator(
        store=store,
        reports_dir=tmp_path / "reports",
        auto_approve=True,
    )
    with pytest.raises(UnknownMerchantError, match="andrew"):
        orch.run("andrew")


def test_approval_denial_stops_before_validation(tmp_path: Path) -> None:
    store = StateStore(tmp_path / "state")
    orch = MigrationOrchestrator(
        store=store,
        reports_dir=tmp_path / "reports",
        approval_fn=lambda _state, _summary: False,
    )
    result = orch.run(
        "Prepare Shopify merchant ABC for migration to the new payment integration."
    )
    assert result.approved is False
    assert result.state.stage == "awaiting_approval"
    assert result.state.readiness is None
    assert result.state.report_path is None
    assert [r.agent for r in result.results] == [
        "intake",
        "research",
        "compatibility",
        "gap-analysis",
        "migration-planning",
    ]
