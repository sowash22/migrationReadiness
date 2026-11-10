from __future__ import annotations

from typing import Any

from migration_readiness.agents.base import AgentResult
from migration_readiness.catalog import (
    UnknownMerchantError,
    extract_merchant_hint,
    resolve_merchant,
)
from migration_readiness.platform import NEW_PLATFORM_NAME
from migration_readiness.state import StateStore, utc_now
from migration_readiness.types import IntakeData, MigrationState


class IntakeAgent:
    name = "intake"

    def run(
        self,
        state: MigrationState | None,
        store: StateStore,
        *,
        request: str,
        goals: list[str] | None = None,
        case_id: str | None = None,
        **_: Any,
    ) -> AgentResult:
        hint = extract_merchant_hint(request)
        if resolve_merchant(hint) is None:
            raise UnknownMerchantError(hint)
        cid = (case_id or hint).upper()
        current = store.load(cid) or store.create(cid)
        current.intake = IntakeData(
            raw_request=request,
            merchant_hint=hint,
            target_platform=NEW_PLATFORM_NAME,
            goals=goals
            or [
                "Inventory current payment integration",
                "Identify unsupported methods and missing config",
                "Produce a migration plan with readiness score",
            ],
        )
        current.stage = "intake"
        current.agent_log.append(f"{utc_now()} [{self.name}] captured request for {hint}")
        saved = store.save(current)
        return AgentResult(
            agent=self.name,
            summary=f"Intake complete for merchant hint '{hint}' (case {saved.case_id}).",
            state=saved,
            details={
                "merchant_hint": hint,
                "goals": saved.intake.goals if saved.intake else [],
            },
        )
