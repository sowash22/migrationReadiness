from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from migration_readiness.agents import (
    CompatibilityAgent,
    GapAnalysisAgent,
    IntakeAgent,
    MigrationPlanningAgent,
    ReportingAgent,
    ResearchAgent,
    ValidationAgent,
)
from migration_readiness.agents.base import AgentResult
from migration_readiness.state import StateStore, utc_now
from migration_readiness.types import ApprovalData, MigrationState


ApprovalFn = Callable[[MigrationState, str], bool]


@dataclass
class OrchestrationResult:
    state: MigrationState
    results: list[AgentResult] = field(default_factory=list)
    approved: bool = False


def default_cli_approval(state: MigrationState, summary: str) -> bool:
    print("\n=== Human-in-the-loop approval required ===")
    print(f"Case: {state.case_id}")
    print(summary)
    blockers = [g.id for g in state.gaps if g.severity == "blocker"]
    print(f"Blockers: {', '.join(blockers) or 'none'}")
    answer = input("Approve cutover validation? [y/N]: ").strip().lower()
    return answer in {"y", "yes"}


def auto_approval(_state: MigrationState, _summary: str) -> bool:
    return True


class MigrationOrchestrator:
    """Coordinates the seven specialist agents in stage order."""

    def __init__(
        self,
        store: StateStore | None = None,
        *,
        reports_dir: Path | str = "reports",
        approval_fn: ApprovalFn | None = None,
        auto_approve: bool = False,
    ) -> None:
        self.store = store or StateStore()
        self.reports_dir = Path(reports_dir)
        self.approval_fn = (
            auto_approval
            if auto_approve
            else (approval_fn or default_cli_approval)
        )
        self.intake = IntakeAgent()
        self.research = ResearchAgent()
        self.compatibility = CompatibilityAgent()
        self.gap_analysis = GapAnalysisAgent()
        self.planning = MigrationPlanningAgent()
        self.validation = ValidationAgent()
        self.reporting = ReportingAgent()

    def run(
        self,
        request: str,
        *,
        case_id: str | None = None,
        max_retries: int = 3,
    ) -> OrchestrationResult:
        results: list[AgentResult] = []

        intake = self.intake.run(None, self.store, request=request, case_id=case_id)
        results.append(intake)
        state = intake.state

        for agent in (
            self.research,
            self.compatibility,
            self.gap_analysis,
            self.planning,
        ):
            result = agent.run(state, self.store)
            results.append(result)
            state = result.state

        summary = self._approval_summary(state)
        approved = self.approval_fn(state, summary)
        state.approval = ApprovalData(
            requested=True,
            approved=approved,
            approved_at=utc_now() if approved else None,
            note=summary,
        )
        state.stage = "validation" if approved else "awaiting_approval"
        state.agent_log.append(
            f"{utc_now()} [orchestrator] approval={'granted' if approved else 'denied'}"
        )
        state = self.store.save(state)

        if not approved:
            return OrchestrationResult(state=state, results=results, approved=False)

        validation = self.validation.run(
            state, self.store, max_retries=max_retries
        )
        results.append(validation)
        state = validation.state

        reporting = self.reporting.run(
            state, self.store, reports_dir=self.reports_dir
        )
        results.append(reporting)

        return OrchestrationResult(
            state=reporting.state,
            results=results,
            approved=True,
        )

    def _approval_summary(self, state: MigrationState) -> str:
        blockers = [g for g in state.gaps if g.severity == "blocker"]
        unsupported = [
            p.payment_method
            for p in (
                state.compatibility.payment_methods if state.compatibility else []
            )
            if p.status == "unsupported"
        ]
        task_count = len(state.plan.tasks) if state.plan else 0
        return (
            f"{state.case_id}: {len(blockers)} blocker(s), "
            f"unsupported={unsupported or ['none']}, "
            f"{task_count} planned tasks. "
            f"{state.plan.cutover_window_hint if state.plan else ''}"
        ).strip()
