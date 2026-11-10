from __future__ import annotations

from typing import Any

from migration_readiness.agents.base import AgentResult
from migration_readiness.platform import build_migration_plan
from migration_readiness.state import StateStore, utc_now
from migration_readiness.types import ApprovalData, MigrationState, PlanData


class MigrationPlanningAgent:
    name = "migration-planning"

    def run(
        self,
        state: MigrationState,
        store: StateStore,
        **_: Any,
    ) -> AgentResult:
        if state.research is None:
            raise ValueError("Research required before planning.")
        tasks, hint = build_migration_plan(state.research.merchant, state.gaps)
        state.plan = PlanData(tasks=tasks, cutover_window_hint=hint)
        state.approval = ApprovalData(
            requested=True,
            approved=False,
            note="Human approval required before validation and cutover.",
        )
        state.stage = "awaiting_approval"
        state.agent_log.append(
            f"{utc_now()} [{self.name}] created {len(tasks)} tasks; awaiting approval"
        )
        saved = store.save(state)
        return AgentResult(
            agent=self.name,
            summary=f"Migration plan ready with {len(tasks)} tasks. Approval required.",
            state=saved,
            details={
                "task_ids": [t.id for t in tasks],
                "cutover_window_hint": hint,
                "approval_required": True,
            },
        )
