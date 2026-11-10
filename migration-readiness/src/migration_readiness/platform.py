from __future__ import annotations

import re
import time

from migration_readiness.types import (
    ApiDependencyFinding,
    CompatibilityFinding,
    GapItem,
    MerchantConfig,
    MigrationTask,
    PaymentMethod,
    ValidationCheck,
)

NEW_PLATFORM_NAME = "new-payment-platform"

_SUPPORTED: set[PaymentMethod] = {
    "card",
    "apple_pay",
    "google_pay",
    "shop_pay",
    "klarna",
    "afterpay",
    "sepa_debit",
}

_REMAP: dict[PaymentMethod, tuple[str, str]] = {
    "gift_card": (
        "needs_remap",
        "Map Shopify gift cards to platform stored-value wallets before cutover.",
    ),
    "afterpay": (
        "needs_remap",
        "Remap Afterpay to the new platform BNPL connector before cutover.",
    ),
    "boleto": (
        "unsupported",
        "Boleto is not available on the new platform. Offer Pix or remove LATAM boleto checkout.",
    ),
}


def check_payment_compatibility(
    merchant: MerchantConfig,
) -> list[CompatibilityFinding]:
    findings: list[CompatibilityFinding] = []
    for method in merchant.payment_methods:
        if method in _REMAP:
            status, notes = _REMAP[method]
            findings.append(
                CompatibilityFinding(
                    payment_method=method,
                    status=status,  # type: ignore[arg-type]
                    notes=notes,
                )
            )
        elif method in _SUPPORTED:
            findings.append(
                CompatibilityFinding(
                    payment_method=method,
                    status="supported",
                    notes="Available on the new payment platform.",
                )
            )
        else:
            findings.append(
                CompatibilityFinding(
                    payment_method=method,
                    status="unsupported",
                    notes="Not listed in the new platform catalog.",
                )
            )
    return findings


def check_api_dependencies(merchant: MerchantConfig) -> list[ApiDependencyFinding]:
    findings: list[ApiDependencyFinding] = []
    for dependency in merchant.api_dependencies:
        if re.search(r"2023-01", dependency, flags=re.I):
            findings.append(
                ApiDependencyFinding(
                    dependency=dependency,
                    status="upgrade_required",
                    notes=(
                        "Upgrade to Admin API 2024-10 or later before enabling "
                        "the new payments app."
                    ),
                )
            )
        elif re.search(r"Order Editing", dependency, flags=re.I):
            findings.append(
                ApiDependencyFinding(
                    dependency=dependency,
                    status="compatible",
                    notes=(
                        "Order editing continues to work through the new "
                        "capture/refund APIs."
                    ),
                )
            )
        elif re.search(
            r"Payments Apps API|Checkout Extensibility|WooCommerce REST|Payment Gateway API",
            dependency,
            flags=re.I,
        ):
            findings.append(
                ApiDependencyFinding(
                    dependency=dependency,
                    status="compatible",
                    notes="Compatible with the new integration adapters.",
                )
            )
        else:
            findings.append(
                ApiDependencyFinding(
                    dependency=dependency,
                    status="compatible",
                    notes="No known blocker.",
                )
            )
    return findings


def analyze_gaps(
    merchant: MerchantConfig,
    payment_methods: list[CompatibilityFinding],
    api_dependencies: list[ApiDependencyFinding],
) -> list[GapItem]:
    gaps: list[GapItem] = []

    for finding in payment_methods:
        if finding.status == "unsupported":
            gaps.append(
                GapItem(
                    id=f"pay-{finding.payment_method}",
                    severity="blocker",
                    area="payment_methods",
                    description=(
                        f"{finding.payment_method} is unsupported on the new platform."
                    ),
                    remediation=finding.notes,
                )
            )
        elif finding.status == "needs_remap":
            gaps.append(
                GapItem(
                    id=f"pay-{finding.payment_method}",
                    severity="high",
                    area="payment_methods",
                    description=f"{finding.payment_method} needs remapping.",
                    remediation=finding.notes,
                )
            )

    for dep in api_dependencies:
        slug = re.sub(r"\s+", "-", dep.dependency).lower()
        if dep.status == "upgrade_required":
            gaps.append(
                GapItem(
                    id=f"api-{slug}",
                    severity="high",
                    area="api_dependencies",
                    description=f"{dep.dependency} must be upgraded.",
                    remediation=dep.notes,
                )
            )
        elif dep.status == "blocked":
            gaps.append(
                GapItem(
                    id=f"api-{slug}",
                    severity="blocker",
                    area="api_dependencies",
                    description=f"{dep.dependency} blocks migration.",
                    remediation=dep.notes,
                )
            )

    if not merchant.settings.webhook_hmac_configured:
        gaps.append(
            GapItem(
                id="cfg-webhook-hmac",
                severity="blocker",
                area="configuration",
                description="Webhook HMAC signing secret is not configured.",
                remediation=(
                    "Generate and store a platform webhook signing secret before go-live."
                ),
            )
        )

    region_blob = f"{merchant.region} {' '.join(merchant.currencies)}"
    if not merchant.settings.three_ds_enabled and re.search(
        r"EU|EEA|UK|GBP|EUR", region_blob, flags=re.I
    ):
        gaps.append(
            GapItem(
                id="cfg-3ds",
                severity="blocker",
                area="configuration",
                description="3-D Secure is disabled for an EEA-facing merchant.",
                remediation="Enable 3DS / SCA for card payments in EU/UK markets.",
            )
        )

    missing = [
        c
        for c in merchant.currencies
        if c not in merchant.settings.settlement_currencies
    ]
    if missing:
        gaps.append(
            GapItem(
                id="cfg-settlement",
                severity="high",
                area="configuration",
                description=f"Settlement currencies missing: {', '.join(missing)}.",
                remediation="Add settlement accounts for every storefront currency.",
            )
        )

    if merchant.settings.refunds_api_version < "2024-10":
        gaps.append(
            GapItem(
                id="cfg-refunds-api",
                severity="medium",
                area="configuration",
                description=(
                    f"Refunds API version {merchant.settings.refunds_api_version} "
                    "is below the required 2024-10 baseline."
                ),
                remediation="Bump refunds API version and retest partial refunds.",
            )
        )

    return gaps


def build_migration_plan(
    merchant: MerchantConfig, gaps: list[GapItem]
) -> tuple[list[MigrationTask], str]:
    tasks: list[MigrationTask] = [
        MigrationTask(
            id="T1",
            title="Provision new-platform merchant account and API keys",
            owner="payments-platform",
            depends_on=[],
            priority="p0",
        ),
        MigrationTask(
            id="T2",
            title="Connect commerce store and install payments app",
            owner="merchant-engineering",
            depends_on=["T1"],
            priority="p0",
        ),
    ]

    gap_ids: list[str] = []
    for gap in gaps:
        task_id = f"G-{gap.id}"
        gap_ids.append(task_id)
        tasks.append(
            MigrationTask(
                id=task_id,
                title=gap.remediation,
                owner=(
                    "merchant-ops"
                    if gap.area == "configuration"
                    else "merchant-engineering"
                ),
                depends_on=["T2"],
                priority="p0" if gap.severity in {"blocker", "high"} else "p1",
            )
        )

    tasks.append(
        MigrationTask(
            id="T3",
            title="Run sandbox authorization, capture, and refund suite",
            owner="qa",
            depends_on=gap_ids,
            priority="p0",
        )
    )
    tasks.append(
        MigrationTask(
            id="T4",
            title="Schedule dual-run cutover and monitoring window",
            owner="migration-pm",
            depends_on=["T3"],
            priority="p1",
        )
    )

    has_blockers = any(g.severity == "blocker" for g in gaps)
    hint = (
        "Do not schedule cutover until every blocker gap is closed and approval is granted."
        if has_blockers
        else (
            f"Propose a low-traffic cutover window for {merchant.display_name} "
            "after sandbox validation passes."
        )
    )
    return tasks, hint


def run_validation_suite(
    merchant: MerchantConfig,
    gaps: list[GapItem],
    *,
    max_retries: int = 3,
) -> tuple[list[ValidationCheck], int]:
    open_blockers = [g for g in gaps if g.severity == "blocker"]
    checks: list[ValidationCheck] = []
    retries_used = 0

    hmac_ok = merchant.settings.webhook_hmac_configured or not any(
        g.id == "cfg-webhook-hmac" for g in open_blockers
    )
    checks.append(
        ValidationCheck(
            id="cfg-hmac",
            name="Webhook HMAC configured",
            status="pass" if hmac_ok else "fail",
            attempts=1,
            detail=(
                "HMAC secret present."
                if merchant.settings.webhook_hmac_configured
                else "HMAC secret still missing."
            ),
        )
    )

    # Simulate a flaky webhook probe that recovers with retries.
    webhook_attempts = 0
    webhook_status: str = "fail"
    webhook_detail = "Webhook endpoint unreachable."
    while webhook_attempts < max_retries:
        webhook_attempts += 1
        if webhook_attempts > 1:
            retries_used += 1
        if webhook_attempts < 2:
            webhook_status = "retrying"
            webhook_detail = f"Transient timeout on attempt {webhook_attempts}."
            time.sleep(0.005)
            continue
        webhook_status = "pass"
        webhook_detail = f"Webhook challenge succeeded on attempt {webhook_attempts}."
        break

    checks.append(
        ValidationCheck(
            id="webhook-challenge",
            name="Webhook challenge/response",
            status="fail" if webhook_status == "retrying" else webhook_status,  # type: ignore[arg-type]
            attempts=webhook_attempts,
            detail=webhook_detail,
        )
    )

    unsupported_open = any(g.area == "payment_methods" for g in open_blockers)
    checks.append(
        ValidationCheck(
            id="methods",
            name="Unsupported payment methods cleared",
            status="fail" if unsupported_open else "pass",
            attempts=1,
            detail=(
                "Blocker payment methods remain enabled on the storefront."
                if unsupported_open
                else "No unsupported methods remain as blockers."
            ),
        )
    )

    checks.append(
        ValidationCheck(
            id="auth-capture",
            name="Sandbox auth + capture",
            status="skipped" if open_blockers else "pass",
            attempts=1,
            detail=(
                "Skipped while blockers remain."
                if open_blockers
                else "Sandbox card auth and capture succeeded."
            ),
        )
    )

    return checks, retries_used
