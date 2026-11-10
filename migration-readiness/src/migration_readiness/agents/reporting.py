from __future__ import annotations

from pathlib import Path
from typing import Any

from migration_readiness.agents.base import AgentResult
from migration_readiness.state import StateStore, utc_now
from migration_readiness.types import MigrationState


class ReportingAgent:
    name = "reporting"

    def run(
        self,
        state: MigrationState,
        store: StateStore,
        *,
        reports_dir: Path | str = "reports",
        executive_summary: str | None = None,
        **_: Any,
    ) -> AgentResult:
        if state.readiness is None:
            raise ValueError("Validation/readiness required before reporting.")

        summary = executive_summary or self._default_summary(state)
        body = self._render(state, summary)
        out_dir = Path(reports_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        report_path = out_dir / f"{state.case_id}-migration-readiness.md"
        report_path.write_text(body, encoding="utf-8")

        state.report_path = str(report_path)
        state.stage = "complete"
        state.agent_log.append(
            f"{utc_now()} [{self.name}] wrote {state.report_path}"
        )
        saved = store.save(state)
        return AgentResult(
            agent=self.name,
            summary=f"Report published at {saved.report_path}.",
            state=saved,
            details={
                "report_path": saved.report_path,
                "readiness": state.readiness.__dict__ if state.readiness else None,
                "executive_summary": summary,
            },
        )

    def _default_summary(self, state: MigrationState) -> str:
        readiness = state.readiness
        assert readiness is not None
        blockers = [g.id for g in state.gaps if g.severity == "blocker"]
        blocker_text = ", ".join(blockers) if blockers else "none"
        return (
            f"Case {state.case_id} readiness is {readiness.score}/100 "
            f"({readiness.band}). Blockers: {blocker_text}. "
            f"{readiness.summary}"
        )

    def _render(self, state: MigrationState, executive_summary: str) -> str:
        merchant = state.research.merchant if state.research else None
        readiness = state.readiness
        assert readiness is not None

        payment_lines = "\n".join(
            f"- {p.payment_method}: **{p.status}** — {p.notes}"
            for p in (state.compatibility.payment_methods if state.compatibility else [])
        ) or "- none"
        api_lines = "\n".join(
            f"- {d.dependency}: **{d.status}** — {d.notes}"
            for d in (
                state.compatibility.api_dependencies if state.compatibility else []
            )
        ) or "- none"
        gap_lines = "\n".join(
            f"- **[{g.severity}]** {g.id} ({g.area}): {g.description} → {g.remediation}"
            for g in state.gaps
        ) or "- none"
        task_lines = "\n".join(
            f"- {t.id} [{t.priority}] {t.title} "
            f"(owner: {t.owner}; depends: {', '.join(t.depends_on) or '—'})"
            for t in (state.plan.tasks if state.plan else [])
        ) or "- none"
        check_lines = "\n".join(
            f"- {c.id}: **{c.status}** (attempts={c.attempts}) — {c.detail}"
            for c in (state.validation.checks if state.validation else [])
        ) or "- none"

        return f"""# Migration readiness report — {state.case_id}

## Executive summary

{executive_summary}

## Merchant

- **Id:** {merchant.merchant_id if merchant else "unknown"}
- **Name:** {merchant.display_name if merchant else "unknown"}
- **Commerce platform:** {merchant.commerce_platform if merchant else "unknown"}
- **Old integration:** {merchant.old_integration if merchant else "unknown"}
- **Target:** {state.intake.target_platform if state.intake else "new-payment-platform"}

## Readiness

- **Score:** {readiness.score}/100
- **Band:** {readiness.band}
- **Blockers:** {readiness.blockers}
- **Unsupported methods:** {readiness.unsupported_methods}
- **Failed checks:** {readiness.failed_checks}
- **Summary:** {readiness.summary}

## Compatibility

### Payment methods
{payment_lines}

### API dependencies
{api_lines}

## Gaps
{gap_lines}

## Migration plan
{task_lines}

Cutover hint: {state.plan.cutover_window_hint if state.plan else "n/a"}

## Validation
{check_lines}

Retries used: {state.validation.retries_used if state.validation else 0}

## Approval

- Approved: {"yes" if state.approval and state.approval.approved else "no"}
- At: {state.approval.approved_at if state.approval and state.approval.approved_at else "n/a"}
- Note: {state.approval.note if state.approval and state.approval.note else "n/a"}

## Agent log
{chr(10).join(f"- {line}" for line in state.agent_log) or "- none"}

---
Generated at {utc_now()}
"""
