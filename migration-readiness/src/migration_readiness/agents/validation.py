from __future__ import annotations

from typing import Any

from migration_readiness.agents.base import AgentResult
from migration_readiness.platform import run_validation_suite
from migration_readiness.readiness import compute_readiness
from migration_readiness.state import StateStore, utc_now
from migration_readiness.types import MigrationState, ValidationData


class ValidationAgent:
    name = "validation"

    def run(
        self,
        state: MigrationState,
        store: StateStore,
        *,
        max_retries: int = 3,
        **_: Any,
    ) -> AgentResult:
        if not state.approval or not state.approval.approved:
            raise ValueError(
                "Cutover is not approved. Obtain human approval before validation."
            )
        if state.research is None or state.compatibility is None:
            raise ValueError("Research and compatibility required before validation.")

        checks, retries_used = run_validation_suite(
            state.research.merchant,
            state.gaps,
            max_retries=max_retries,
        )
        readiness = compute_readiness(
            gaps=state.gaps,
            payment_methods=state.compatibility.payment_methods,
            checks=checks,
            approved=True,
        )
        state.validation = ValidationData(checks=checks, retries_used=retries_used)
        state.readiness = readiness
        state.stage = "reporting"
        state.agent_log.append(
            f"{utc_now()} [{self.name}] score={readiness.score} "
            f"band={readiness.band} retries={retries_used}"
        )
        saved = store.save(state)
        return AgentResult(
            agent=self.name,
            summary=(
                f"Validation complete. Readiness {readiness.score}/100 ({readiness.band})."
            ),
            state=saved,
            details={
                "readiness": readiness.__dict__,
                "retries_used": retries_used,
                "failed_checks": [c.id for c in checks if c.status == "fail"],
            },
        )
