from __future__ import annotations

from migration_readiness.types import (
    CompatibilityFinding,
    GapItem,
    ReadinessScore,
    ValidationCheck,
)


def compute_readiness(
    *,
    gaps: list[GapItem],
    payment_methods: list[CompatibilityFinding],
    checks: list[ValidationCheck],
    approved: bool,
) -> ReadinessScore:
    blockers = sum(1 for g in gaps if g.severity == "blocker")
    highs = sum(1 for g in gaps if g.severity == "high")
    unsupported = sum(1 for p in payment_methods if p.status == "unsupported")
    failed = sum(1 for c in checks if c.status == "fail")
    passed = sum(1 for c in checks if c.status == "pass")

    score = 100
    score -= blockers * 20
    score -= highs * 8
    score -= unsupported * 10
    score -= failed * 12
    score += min(10, passed * 2)
    if not approved:
        score -= 15
    score = max(0, min(100, score))

    if score >= 80 and blockers == 0 and failed == 0:
        band = "ready"
    elif score >= 55:
        band = "at_risk"
    else:
        band = "not_ready"

    if band == "ready":
        summary = "Merchant is ready for cutover after final monitoring setup."
    elif band == "at_risk":
        summary = "Merchant can proceed only after closing remaining high-risk gaps."
    else:
        summary = "Merchant is not ready; resolve blockers before validation sign-off."

    return ReadinessScore(
        score=score,
        band=band,
        blockers=blockers,
        unsupported_methods=unsupported,
        failed_checks=failed,
        summary=summary,
    )
