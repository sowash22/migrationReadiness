from __future__ import annotations

from typing import Any

from migration_readiness.agents.base import AgentResult
from migration_readiness.platform import analyze_gaps
from migration_readiness.state import StateStore, utc_now
from migration_readiness.types import MigrationState


class GapAnalysisAgent:
    name = "gap-analysis"

    def run(
        self,
        state: MigrationState,
        store: StateStore,
        **_: Any,
    ) -> AgentResult:
        if state.research is None or state.compatibility is None:
            raise ValueError("Research and compatibility required before gap analysis.")
        gaps = analyze_gaps(
            state.research.merchant,
            state.compatibility.payment_methods,
            state.compatibility.api_dependencies,
        )
        state.gaps = gaps
        state.stage = "gap_analysis"
        blockers = [g for g in gaps if g.severity == "blocker"]
        state.agent_log.append(
            f"{utc_now()} [{self.name}] identified {len(gaps)} gaps "
            f"({len(blockers)} blockers)"
        )
        saved = store.save(state)
        return AgentResult(
            agent=self.name,
            summary=f"Gap analysis complete: {len(blockers)} blocker(s), {len(gaps)} total.",
            state=saved,
            details={
                "blocker_ids": [g.id for g in blockers],
                "gap_ids": [g.id for g in gaps],
            },
        )
