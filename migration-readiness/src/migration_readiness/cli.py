from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from migration_readiness.orchestrator import MigrationOrchestrator
from migration_readiness.state import StateStore


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="migration-readiness",
        description=(
            "Run the multi-agent payment migration readiness workflow."
        ),
    )
    parser.add_argument(
        "request",
        nargs="?",
        default=(
            "Prepare Shopify merchant ABC for migration to the new payment integration."
        ),
        help="Migration request text",
    )
    parser.add_argument("--case-id", default=None, help="Optional case id override")
    parser.add_argument(
        "--state-dir",
        default=".migration-state",
        help="Directory for durable JSON case state",
    )
    parser.add_argument(
        "--reports-dir",
        default="reports",
        help="Directory for generated markdown reports",
    )
    parser.add_argument(
        "--auto-approve",
        action="store_true",
        help="Skip interactive human approval (for demos/CI)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable orchestration summary",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    store = StateStore(Path(args.state_dir))
    orchestrator = MigrationOrchestrator(
        store=store,
        reports_dir=args.reports_dir,
        auto_approve=args.auto_approve,
    )
    result = orchestrator.run(args.request, case_id=args.case_id)

    if args.json:
        payload = {
            "case_id": result.state.case_id,
            "stage": result.state.stage,
            "approved": result.approved,
            "readiness": (
                result.state.readiness.__dict__ if result.state.readiness else None
            ),
            "report_path": result.state.report_path,
            "agents": [
                {"agent": r.agent, "summary": r.summary, "details": r.details}
                for r in result.results
            ],
            "blockers": [
                g.__dict__ for g in result.state.gaps if g.severity == "blocker"
            ],
        }
        print(json.dumps(payload, indent=2))
        return 0 if result.state.stage in {"complete", "awaiting_approval"} else 1

    print(f"Case: {result.state.case_id}")
    print(f"Stage: {result.state.stage}")
    print(f"Approved: {result.approved}")
    for item in result.results:
        print(f"- [{item.agent}] {item.summary}")
    if result.state.readiness:
        r = result.state.readiness
        print(
            f"Readiness: {r.score}/100 ({r.band}) — {r.summary}"
        )
    if result.state.report_path:
        print(f"Report: {result.state.report_path}")
    if not result.approved:
        print("Stopped before validation: human approval was denied.")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
