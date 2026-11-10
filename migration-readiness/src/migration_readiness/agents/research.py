from __future__ import annotations

from typing import Any

from migration_readiness.agents.base import AgentResult
from migration_readiness.catalog import resolve_merchant
from migration_readiness.state import StateStore, utc_now
from migration_readiness.types import MigrationState, ResearchData


class ResearchAgent:
    name = "research"

    def run(
        self,
        state: MigrationState,
        store: StateStore,
        **_: Any,
    ) -> AgentResult:
        if state.intake is None:
            raise ValueError("Intake required before research.")
        merchant = resolve_merchant(state.intake.merchant_hint)
        if merchant is None:
            raise ValueError(
                f'No merchant catalog entry for "{state.intake.merchant_hint}". '
                "Known demos: ABC, ACME."
            )
        state.research = ResearchData(
            merchant=merchant,
            notes=[
                f"Old integration: {merchant.old_integration}",
                f"Commerce platform: {merchant.commerce_platform}",
                f"Region: {merchant.region}",
            ],
        )
        state.stage = "research"
        state.agent_log.append(
            f"{utc_now()} [{self.name}] loaded {merchant.merchant_id} catalog profile"
        )
        saved = store.save(state)
        return AgentResult(
            agent=self.name,
            summary=f"Researched {merchant.display_name}.",
            state=saved,
            details={"merchant_id": merchant.merchant_id, "notes": state.research.notes},
        )
