from __future__ import annotations

from typing import Any

from migration_readiness.agents.base import AgentResult
from migration_readiness.platform import (
    check_api_dependencies,
    check_payment_compatibility,
)
from migration_readiness.state import StateStore, utc_now
from migration_readiness.types import CompatibilityData, MigrationState


class CompatibilityAgent:
    name = "compatibility"

    def run(
        self,
        state: MigrationState,
        store: StateStore,
        **_: Any,
    ) -> AgentResult:
        if state.research is None:
            raise ValueError("Research required before compatibility.")
        merchant = state.research.merchant
        payment_methods = check_payment_compatibility(merchant)
        api_dependencies = check_api_dependencies(merchant)
        state.compatibility = CompatibilityData(
            payment_methods=payment_methods,
            api_dependencies=api_dependencies,
        )
        state.stage = "compatibility"
        unsupported = [p for p in payment_methods if p.status == "unsupported"]
        state.agent_log.append(
            f"{utc_now()} [{self.name}] found {len(unsupported)} unsupported method(s)"
        )
        saved = store.save(state)
        return AgentResult(
            agent=self.name,
            summary=(
                f"Compatibility checked: {len(unsupported)} unsupported payment method(s)."
            ),
            state=saved,
            details={
                "unsupported": [p.payment_method for p in unsupported],
                "upgrade_required": [
                    d.dependency
                    for d in api_dependencies
                    if d.status == "upgrade_required"
                ],
            },
        )
